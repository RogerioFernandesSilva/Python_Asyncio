"""
Scraper concorrente de filmes.

Correções e melhorias em relação à versão anterior (ver Issue #6 do
repositório original):
    - Tratamento de exceções em toda chamada de rede/parsing.
    - I/O do CSV otimizado: os resultados são acumulados em memória e
      gravados em uma única escrita ao final, em vez de abrir o arquivo
      a cada filme processado (o que também eliminava uma condição de
      corrida entre as threads).
    - Logging estruturado no lugar de "print".
    - Tipagem estática (type hints) em todas as funções públicas.
    - Docstrings em todas as classes/funções.
    - Suporte a proxy e a retry configurável (ver scraper/config.py).
    - Suporte a exportação em CSV ou JSON.
"""

from __future__ import annotations

import concurrent.futures
import csv
import json
import random
import threading
import time
from dataclasses import asdict, dataclass
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from scraper.config import DEFAULT_HEADERS, ScraperConfig
from scraper.utils import retry, setup_logging

logger = setup_logging()


@dataclass
class MovieData:
    """Representa os dados extraídos de um filme."""

    title: str
    release_date: str
    rating: str
    synopsis: str


class MovieScraper:
    """Encapsula a extração concorrente de filmes de um catálogo estático."""

    def __init__(self, config: ScraperConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        if config.proxies:
            self.session.proxies.update(config.proxies)

        self._results: List[MovieData] = []
        self._lock = threading.Lock()

    def run(self) -> List[MovieData]:
        """Executa o fluxo completo: lista -> detalhes -> exportação.

        Returns:
            Lista de MovieData extraídos com sucesso.
        """
        start = time.time()
        logger.info("Iniciando scraping em %s", self.config.base_url)

        try:
            movie_links = self._fetch_movie_links()
        except Exception:
            logger.exception("Falha ao obter a lista de filmes. Abortando.")
            return []

        if not movie_links:
            logger.warning("Nenhum link de filme encontrado.")
            return []

        threads = min(self.config.max_threads, len(movie_links))
        logger.info("Extraindo %s filmes usando %s threads.", len(movie_links), threads)

        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(self._safe_extract, link) for link in movie_links]
            concurrent.futures.wait(futures)

        self._export()

        elapsed = time.time() - start
        logger.info(
            "Concluído: %s/%s filmes extraídos em %.2fs.",
            len(self._results),
            len(movie_links),
            elapsed,
        )
        return self._results

    def _fetch_movie_links(self) -> List[str]:
        """Busca a página principal e retorna os links de detalhe de cada filme."""
        response = self._get(self.config.base_url)
        soup = BeautifulSoup(response.content, "html.parser")

        container = soup.find("section", attrs={"data-testid": "movies-list"})
        if container is None:
            logger.error("Container principal ('movies-list') não encontrado.")
            if self.config.debug:
                self._dump_debug_html("debug_container.html", soup.prettify())
            return []

        movie_items = container.find_all("article", attrs={"data-testid": "movie-item"})
        if not movie_items:
            logger.error("Nenhum item de filme ('movie-item') encontrado.")
            return []

        links: List[str] = []
        for item in movie_items:
            a_tag = item.find("a", attrs={"data-testid": "movie-link"}, href=True)
            if a_tag:
                links.append(self._resolve_url(a_tag["href"]))

        return links

    def _safe_extract(self, movie_link: str) -> None:
        """Wrapper com tratamento de exceção para rodar dentro de uma thread."""
        try:
            time.sleep(random.uniform(0, 0.2))  # pequeno jitter, evita rajadas
            movie = self._extract_movie_details(movie_link)
            if movie:
                with self._lock:
                    self._results.append(movie)
                logger.debug("Extraído: %s", movie.title)
        except Exception:  # noqa: BLE001
            logger.exception("Erro ao processar %s", movie_link)

    @retry(max_retries=3, backoff=1.5, exceptions=(requests.RequestException,))
    def _get(self, url: str) -> requests.Response:
        """Executa uma requisição GET com retry automático em caso de falha de rede."""
        response = self.session.get(url, timeout=self.config.timeout)
        response.raise_for_status()
        return response

    def _extract_movie_details(self, movie_link: str) -> Optional[MovieData]:
        """Extrai título, data de lançamento, nota e sinopse de uma página de filme."""
        response = self._get(movie_link)
        return parse_movie_detail(response.content)

    def _resolve_url(self, href: str) -> str:
        """Resolve uma URL relativa em relação à base do catálogo."""
        if href.startswith("http"):
            return href
        base = self.config.base_url.split("/movie-catalog", 1)[0]
        return base + href

    def _dump_debug_html(self, filename: str, content: str) -> None:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

    def _export(self) -> None:
        """Exporta os resultados no formato configurado (csv ou json)."""
        if not self._results:
            logger.warning("Nenhum resultado para exportar.")
            return

        if self.config.output_format == "json":
            self._export_json()
        else:
            self._export_csv()

    def _export_csv(self) -> None:
        with open(self.config.output_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["title", "release_date", "rating", "synopsis"])
            for movie in self._results:
                writer.writerow([movie.title, movie.release_date, movie.rating, movie.synopsis])
        logger.info("Dados salvos em %s (CSV).", self.config.output_file)

    def _export_json(self) -> None:
        with open(self.config.output_file, mode="w", encoding="utf-8") as f:
            json.dump([asdict(m) for m in self._results], f, ensure_ascii=False, indent=2)
        logger.info("Dados salvos em %s (JSON).", self.config.output_file)


def parse_movie_detail(html_content: bytes | str) -> Optional[MovieData]:
    """Faz o parsing do HTML de uma página de filme e retorna um MovieData.

    Função pura (sem I/O de rede), o que permite testá-la isoladamente
    com HTML de exemplo, sem precisar mockar `requests`.

    Args:
        html_content: conteúdo HTML da página de detalhe do filme.

    Returns:
        MovieData preenchido, ou None se algum campo obrigatório faltar.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    detail = soup.find("section", attrs={"data-testid": "movie-detail"})
    if detail is None:
        return None

    title_tag = detail.find(attrs={"data-testid": "movie-title"})
    release_tag = detail.find(attrs={"data-testid": "movie-release"})
    rating_tag = detail.find(attrs={"data-testid": "movie-rating"})
    synopsis_tag = detail.find(attrs={"data-testid": "movie-synopsis"})

    title = title_tag.get_text(strip=True) if title_tag else None
    release_date = (
        release_tag.get_text(strip=True).replace("Lançamento:", "").strip()
        if release_tag
        else None
    )
    rating = (
        rating_tag.get_text(strip=True).replace("Nota:", "").strip() if rating_tag else None
    )
    synopsis = (
        synopsis_tag.get_text(strip=True).replace("Sinopse:", "").strip()
        if synopsis_tag
        else None
    )

    if not all([title, release_date, rating, synopsis]):
        return None

    return MovieData(
        title=title,
        release_date=release_date,
        rating=rating,
        synopsis=synopsis,
    )
