"""
Utilitários reutilizáveis: logging estruturado e retry automático.
"""

from __future__ import annotations

import functools
import logging
import time
from typing import Callable, TypeVar

T = TypeVar("T")


def setup_logging(debug: bool = False) -> logging.Logger:
    """Configura e retorna o logger principal da aplicação.

    Args:
        debug: se True, define o nível como DEBUG; caso contrário, INFO.

    Returns:
        Instância de logger configurada com saída no console.
    """
    logger = logging.getLogger("movie_scraper")
    level = logging.DEBUG if debug else logging.INFO

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(threadName)s | %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(level)
    return logger


def retry(
    max_retries: int = 3,
    backoff: float = 1.5,
    exceptions: tuple = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator que reexecuta a função em caso de falha, com backoff exponencial.

    Implementa o item "sistema de retry" e "tratamento de exceções" do
    checklist de revisão, evitando que uma falha de rede pontual derrube
    a extração de um filme inteiro.

    Args:
        max_retries: número máximo de tentativas antes de desistir.
        backoff: tempo base (segundos) multiplicado exponencialmente entre tentativas.
        exceptions: tupla de exceções que disparam nova tentativa.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            logger = logging.getLogger("movie_scraper")
            last_exc: Exception | None = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:  # noqa: BLE001
                    last_exc = exc
                    wait = backoff ** attempt
                    logger.warning(
                        "Tentativa %s/%s falhou em %s: %s. Aguardando %.1fs...",
                        attempt,
                        max_retries,
                        func.__name__,
                        exc,
                        wait,
                    )
                    if attempt < max_retries:
                        time.sleep(wait)
            logger.error("Todas as %s tentativas falharam em %s.", max_retries, func.__name__)
            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator
