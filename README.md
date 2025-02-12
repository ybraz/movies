# Sistema de Busca de Filmes e Top 100

Este projeto é uma aplicação web desenvolvida em Python com Flask que permite:

- **Busca de Filmes Semelhantes:**  
  Utiliza o algoritmo de clustering (K-Means) para agrupar filmes e, a partir de um filme pesquisado, retorna os filmes do mesmo cluster com nota IMDb igual ou superior a 7.5.  
  Caso a busca não encontre uma correspondência exata, o sistema utiliza regex para sugerir opções de seleção.

- **Top 100 Filmes:**  
  Exibe os 100 filmes com as maiores notas IMDb, com a opção de ordenar por nota ou por ano de lançamento e filtrar por gênero.

## Recursos

- **Busca de Filmes Semelhantes:**  
  - Pesquisa por nome de filme.  
  - Sugestão de candidatos caso a correspondência exata não seja encontrada.  
  - Exibição dos filmes do mesmo cluster, **incluindo o próprio filme pesquisado**, ordenados por nota (ou por ano, conforme a escolha do usuário).

- **Top 100 Filmes:**  
  - Exibição dos 100 filmes com melhor score IMDb.  
  - Filtro por gênero (busca substring, case-insensitive).  
  - Ordenação por score ou ano de lançamento.

## Requisitos

- Python 3.x
- [Flask](https://palletsprojects.com/p/flask/)
- [pandas](https://pandas.pydata.org/)
- [scikit-learn](https://scikit-learn.org/)

## Instalação

1. **Clone o repositório ou baixe os arquivos:**
   - `app.py`
   - Pasta `templates` com os arquivos `index.html` e `top100.html`
   - O dataset `movie_metadata.csv` (certifique-se de que o arquivo esteja no mesmo diretório de `app.py` ou ajuste o caminho conforme necessário).

2. **Crie e ative um ambiente virtual (opcional, mas recomendado):**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # No Linux/Mac
   .\.venv\Scripts\activate   # No Windows
