"""
Ponto de entrada da aplicação.

Uso:
    python main.py
    python main.py --format json --output filmes.json
    python main.py --threads 5 --retries 5 --debug
    python main.py --proxy http://usuario:senha@host:porta
"""

from __future__ import annotations

import argparse

from scraper.config import ScraperConfig
from scraper.scraper import MovieScraper
from scraper.utils import setup_logging


def parse_args() -> argparse.Namespace:
    """Define e interpreta os argumentos de linha de comando."""
    parser = argparse.ArgumentParser(description="Scraper concorrente de filmes.")
    parser.add_argument(
        "--url",
        default="https://havokkmorands.github.io/movie-catalog/",
        help="URL do catálogo de filmes.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Arquivo de saída (padrão: movies.csv ou movies.json).",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json"],
        default="csv",
        help="Formato do arquivo de saída.",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=10,
        help="Número máximo de threads simultâneas.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Número máximo de tentativas por requisição.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="Timeout (segundos) de cada requisição.",
    )
    parser.add_argument(
        "--proxy",
        default=None,
        help="URL de proxy HTTP/HTTPS, ex.: http://usuario:senha@host:porta",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Ativa logs em nível DEBUG e salva HTML de páginas com falha.",
    )
    return parser.parse_args()


def main() -> None:
    """Monta a configuração a partir da CLI e executa o scraper."""
    args = parse_args()
    setup_logging(debug=args.debug)

    output_file = args.output or f"movies.{args.format}"

    config = ScraperConfig(
        base_url=args.url,
        output_file=output_file,
        output_format=args.format,
        max_threads=args.threads,
        max_retries=args.retries,
        timeout=args.timeout,
        proxy=args.proxy,
        debug=args.debug,
    )

    scraper = MovieScraper(config)
    scraper.run()


if __name__ == "__main__":
    main()
