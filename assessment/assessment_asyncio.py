"""
Web scraping assíncrono com asyncio + aiohttp.

Segue o mesmo padrão dos outros arquivos do assessment
(assessment_single_thread.py e assessment_multithreading.py),
mas substitui requests/threads por corrotinas assíncronas.

Fonte: http://quotes.toscrape.com (site público feito para prática
de scraping, já referenciado em algorithms/web-scraping.py).
"""

import asyncio
import csv
import time

import aiohttp
from bs4 import BeautifulSoup

BASE_URL = "http://quotes.toscrape.com/page/{}/"
TOTAL_PAGES = 10          # quotes.toscrape.com tem 10 páginas
MAX_CONCURRENT_REQUESTS = 10
OUTPUT_FILE = "quotes.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/117.0 Safari/537.36"
    )
}


async def fetch_page(session: aiohttp.ClientSession, url: str) -> str:
    """Faz o request assíncrono e devolve o HTML da página."""
    async with session.get(url, headers=HEADERS) as response:
        response.raise_for_status()
        return await response.text()


def parse_quotes(html: str) -> list[dict]:
    """Extrai (texto, autor, tags) de cada citação da página."""
    soup = BeautifulSoup(html, "html.parser")
    quotes = []

    for quote_div in soup.find_all("div", class_="quote"):
        text = quote_div.find("span", class_="text").get_text(strip=True)
        author = quote_div.find("small", class_="author").get_text(strip=True)
        tags = [tag.get_text(strip=True) for tag in quote_div.find_all("a", class_="tag")]

        quotes.append({"text": text, "author": author, "tags": ", ".join(tags)})

    return quotes


async def scrape_page(session: aiohttp.ClientSession, page: int, semaphore: asyncio.Semaphore) -> list[dict]:
    """Baixa e faz o parsing de uma página, limitado pelo semáforo de concorrência."""
    url = BASE_URL.format(page)
    async with semaphore:
        try:
            html = await fetch_page(session, url)
        except aiohttp.ClientError as exc:
            print(f"Falha ao buscar {url}: {exc}")
            return []

    quotes = parse_quotes(html)
    print(f"Página {page}: {len(quotes)} citações encontradas ({url})")
    return quotes


def save_to_csv(rows: list[dict], filename: str) -> None:
    """Salva os resultados em CSV, sobrescrevendo o arquivo a cada execução."""
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["text", "author", "tags"])
        writer.writeheader()
        writer.writerows(rows)


async def main() -> None:
    start_time = time.time()
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async with aiohttp.ClientSession() as session:
        tasks = [scrape_page(session, page, semaphore) for page in range(1, TOTAL_PAGES + 1)]
        results = await asyncio.gather(*tasks)

    all_quotes = [quote for page_quotes in results for quote in page_quotes]
    save_to_csv(all_quotes, OUTPUT_FILE)

    end_time = time.time()
    print(f"\nTotal de citações extraídas: {len(all_quotes)}")
    print(f"Arquivo gerado: {OUTPUT_FILE}")
    print(f"Tempo total: {end_time - start_time:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())