"""
Configurações centrais do scraper.

Manter todos os parâmetros ajustáveis em um único lugar facilita
testes, reuso e leitura do código (item "Criar arquivo de configuração
para parâmetros" do checklist de revisão).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ScraperConfig:
    """Parâmetros de execução do scraper de filmes.

    Attributes:
        base_url: URL do catálogo de filmes.
        output_file: Caminho do arquivo de saída.
        output_format: Formato de saída, "csv" ou "json".
        max_threads: Número máximo de threads simultâneas.
        max_retries: Número máximo de tentativas por requisição.
        retry_backoff: Fator de espera (segundos) entre tentativas.
        timeout: Timeout (segundos) de cada requisição HTTP.
        proxy: URL de proxy HTTP/HTTPS opcional (ex.: "http://usuario:senha@host:porta").
        debug: Ativa logs detalhados (nível DEBUG) e salva HTML de páginas com falha.
    """

    base_url: str = "https://havokkmorands.github.io/movie-catalog/"
    output_file: str = "movies.csv"
    output_format: str = "csv"
    max_threads: int = 10
    max_retries: int = 3
    retry_backoff: float = 1.5
    timeout: int = 20
    proxy: Optional[str] = None
    debug: bool = False

    @property
    def proxies(self) -> Optional[dict]:
        """Retorna o dicionário de proxies no formato esperado pelo requests."""
        if not self.proxy:
            return None
        return {"http": self.proxy, "https": self.proxy}


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
