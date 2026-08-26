"""
Testes unitários e de integração do scraper.

Rodar com:
    pytest
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from scraper.config import ScraperConfig
from scraper.scraper import MovieData, MovieScraper, parse_movie_detail

VALID_DETAIL_HTML = """
<section data-testid="movie-detail">
    <h1 data-testid="movie-title">A Última Luz de Arken</h1>
    <p data-testid="movie-release">Lançamento: 2018</p>
    <p data-testid="movie-rating">Nota: 8.3</p>
    <p data-testid="movie-synopsis">Sinopse: Uma engenheira busca salvar a cidade.</p>
</section>
"""

INCOMPLETE_DETAIL_HTML = """
<section data-testid="movie-detail">
    <h1 data-testid="movie-title">Filme Sem Nota</h1>
    <p data-testid="movie-release">Lançamento: 2020</p>
</section>
"""

LIST_HTML = """
<section data-testid="movies-list">
    <article data-testid="movie-item">
        <a data-testid="movie-link" href="/movie-catalog/movies/1/">Filme 1</a>
    </article>
    <article data-testid="movie-item">
        <a data-testid="movie-link" href="/movie-catalog/movies/2/">Filme 2</a>
    </article>
</section>
"""


class TestParseMovieDetail:
    """Testes unitários da função pura de parsing (sem rede)."""

    def test_parses_all_fields_correctly(self):
        movie = parse_movie_detail(VALID_DETAIL_HTML)
        assert movie == MovieData(
            title="A Última Luz de Arken",
            release_date="2018",
            rating="8.3",
            synopsis="Uma engenheira busca salvar a cidade.",
        )

    def test_returns_none_when_fields_are_missing(self):
        assert parse_movie_detail(INCOMPLETE_DETAIL_HTML) is None

    def test_returns_none_when_detail_section_is_absent(self):
        assert parse_movie_detail("<html><body>sem dados</body></html>") is None


class TestMovieScraperIntegration:
    """Testes de integração: rede é mockada, mas o fluxo completo é exercitado."""

    def _make_response(self, content: str, status: int = 200) -> MagicMock:
        response = MagicMock()
        response.content = content.encode("utf-8")
        response.status_code = status
        response.raise_for_status = MagicMock()
        return response

    @patch("scraper.scraper.requests.Session.get")
    def test_run_extracts_and_exports_all_movies(self, mock_get, tmp_path):
        list_response = self._make_response(LIST_HTML)
        detail_response = self._make_response(VALID_DETAIL_HTML)
        # primeira chamada retorna a listagem, as seguintes retornam o detalhe
        mock_get.side_effect = [list_response, detail_response, detail_response]

        output_file = tmp_path / "movies.csv"
        config = ScraperConfig(
            base_url="https://exemplo.test/movie-catalog/",
            output_file=str(output_file),
            max_threads=2,
        )

        scraper = MovieScraper(config)
        results = scraper.run()

        assert len(results) == 2
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "A Última Luz de Arken" in content

    @patch("scraper.scraper.requests.Session.get")
    def test_run_returns_empty_list_when_listing_fails(self, mock_get):
        mock_get.side_effect = ConnectionError("falha simulada de rede")

        config = ScraperConfig(base_url="https://exemplo.test/movie-catalog/", max_retries=1)
        scraper = MovieScraper(config)
        results = scraper.run()

        assert results == []
