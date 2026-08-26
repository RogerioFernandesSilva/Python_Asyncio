# 🎬 Multithreading Web Scraper (v3)

![CI](https://github.com/havokkmorands/multithreading/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Projeto que demonstra o uso de **multithreading em Python** para realizar
**web scraping concorrente de múltiplas páginas**, coletando dados de um
catálogo de filmes e exportando-os para `movies.csv` (ou `movies.json`).

Esta é a **versão 3** do projeto, criada a partir das sugestões de melhoria
registradas na [Issue #6](../../issues/6): estrutura de pastas, tratamento de
exceções, logging, tipagem, retry, proxy, testes e CI.

---

## Sumário

- [Sobre o projeto](#sobre-o-projeto)
- [Dados coletados](#dados-coletados)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Instalação](#instalação)
- [Como executar](#como-executar)
- [Configurações disponíveis](#configurações-disponíveis)
- [Testes](#testes)
- [Como funciona a concorrência](#como-funciona-a-concorrência)
- [Possíveis melhorias futuras](#possíveis-melhorias-futuras)

---

## Sobre o projeto

- A **versão 1** fazia scraping diretamente do IMDb, mas mudanças no site e
  mecanismos de proteção (WAF, bloqueios) tornaram a abordagem instável.
- A **versão 2** passou a usar um catálogo fictício próprio, hospedado no
  GitHub Pages, garantindo um ambiente controlado e estável para scraping.
- A **versão 3** (esta) reorganiza o código em módulos, adiciona tratamento
  de erros, retry automático, logging, testes e CI, conforme os pontos
  levantados na revisão do projeto.

Fonte dos dados: <https://havokkmorands.github.io/movie-catalog/>

## Dados coletados

Para cada filme:

- Nome
- Data de lançamento
- Nota
- Sinopse

## Estrutura do projeto

```
multithreading/
├── main.py                  # ponto de entrada (CLI)
├── scraper/
│   ├── config.py             # parâmetros configuráveis (dataclass tipada)
│   ├── scraper.py             # lógica de scraping, parsing e exportação
│   └── utils.py                # logging e decorator de retry
├── tests/
│   └── test_scraper.py         # testes unitários e de integração
├── .github/workflows/ci.yml     # pipeline de CI (roda os testes a cada push/PR)
├── requirements.txt
├── Makefile
└── .gitignore
```

## Instalação

Pré-requisitos: Python 3.9+.

**Linux/Mac:**

```bash
make install
```

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

## Como executar

```bash
python main.py
```

Ou, usando o atalho do Makefile:

```bash
make run
```

Exemplos com opções:

```bash
# Exportar em JSON em vez de CSV
python main.py --format json --output filmes.json

# Aumentar o número de threads e tentativas de retry
python main.py --threads 20 --retries 5

# Ativar modo debug (logs detalhados + HTML salvo em caso de falha de parsing)
python main.py --debug

# Rodar através de um proxy HTTP
python main.py --proxy http://usuario:senha@host:porta
```

## Configurações disponíveis

| Opção         | Padrão                                          | Descrição                                         |
| ------------- | ------------------------------------------------ | -------------------------------------------------- |
| `--url`       | catálogo oficial de filmes                        | URL da página de listagem a ser raspada             |
| `--output`    | `movies.csv` / `movies.json`                      | Caminho do arquivo de saída                         |
| `--format`    | `csv`                                             | Formato de exportação: `csv` ou `json`              |
| `--threads`   | `10`                                              | Número máximo de threads simultâneas                |
| `--retries`   | `3`                                               | Tentativas por requisição antes de desistir         |
| `--timeout`   | `20`                                              | Timeout (segundos) de cada requisição               |
| `--proxy`     | nenhum                                            | URL de proxy HTTP/HTTPS                             |
| `--debug`     | desativado                                        | Logs em nível DEBUG e HTML de páginas com falha      |

## Testes

O projeto tem testes unitários (parsing puro, sem rede) e testes de
integração (fluxo completo, com rede mockada via `unittest.mock`):

```bash
make test
# ou
pytest -v
```

Um workflow de **CI** (`.github/workflows/ci.yml`) roda esses testes
automaticamente a cada `push`/`pull request` na branch `main`.

## Como funciona a concorrência

1. `main()` inicia o processo e monta a configuração.
2. `_fetch_movie_links()` coleta os links de todos os filmes da listagem.
3. Um `ThreadPoolExecutor` distribui a extração de cada página de detalhe
   entre até `--threads` threads simultâneas.
4. Cada thread grava seu resultado em uma lista compartilhada, protegida por
   um `threading.Lock` (evitando condição de corrida).
5. Ao final, todos os resultados são gravados em **uma única escrita** no
   arquivo de saída — isto substitui a abordagem anterior, que abria o
   arquivo a cada filme processado, gerando I/O desnecessário e um risco
   real de corrupção do CSV quando duas threads escreviam ao mesmo tempo.

## Possíveis melhorias futuras

- Paralelismo com `asyncio`/`aiohttp` para comparação de desempenho.
- Suporte à rotação de múltiplos proxies.
- Exportação direta para um banco de dados (SQLite/Postgres).

---

Projeto desenvolvido para fins educacionais, com foco em demonstrar
conceitos de scraping e concorrência em Python.
