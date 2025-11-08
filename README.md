# Movies Clustering & Exploration

Este projeto fornece uma aplicação Flask para explorar um dataset de filmes, sugerir títulos semelhantes via clustering (K-Means) e listar um Top 100 com filtros.

## Visão Geral
- Carrega o dataset `movie_metadata.csv`.
- Faz pré-processamento básico (preenchimento de valores ausentes e normalização).
- Executa K-Means (10 clusters) sobre as features numéricas: `duration`, `budget`, `imdb_score`, `title_year`, `gross`.
- Disponibiliza endpoints de busca e recomendação e páginas HTML simples.

## Estrutura
```
main.py                # App Flask principal e rotas
movie_metadata.csv     # Dataset de filmes
requirements.txt       # Dependências Python
templates/
  index.html           # Página inicial (busca)
  top100.html          # Página com Top 100
  metrics.html         # (Reservada para futuras métricas / visualizações)
```

## Requisitos
Python 3.11+ (recomendado). Dependências listadas em `requirements.txt`:

Principais libs:
- Flask (API e Frontend)
- pandas, numpy (manipulação de dados)
- scikit-learn (K-Means, escalonamento)

## Instalação
```bash
# Criar e ativar virtualenv (opcional mas recomendado)
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# Instalar dependências
pip install -r requirements.txt
```

## Executando
```bash
python main.py
```
A aplicação roda em modo debug (padrão Flask) em `http://127.0.0.1:5000/`.

## Endpoints da API
### 1. `GET /api/search`
Busca um filme e retorna filmes similares dentro do mesmo cluster com `imdb_score >= 7.5`.

Parâmetros:
- `movie` (obrigatório): nome do filme a pesquisar.
- `selection` (opcional): índice de um candidato quando não há correspondência exata.
- `order` (opcional): `imdb` (padrão) ordena por score, `year` ordena por ano.

Respostas possíveis:
1. Erro de validação / não encontrado: `{"error": "..."}`.
2. Lista de candidatos quando não há match exato:
```json
{
  "message": "Filme não encontrado exatamente. Selecione uma das opções.",
  "candidates": [
    {"id": 123, "movie_title": "The Matrix", "title_year": 1999},
    ...
  ]
}
```
3. Resultado com similares:
```json
{
  "selected_movie": "Inception",
  "cluster": 4,
  "order": "imdb",
  "similar_movies": [
    {
      "movie_title": "Interstellar",
      "title_year": 2014,
      "director_name": "Christopher Nolan",
      "genres": "Adventure|Drama|Sci-Fi",
      "imdb_score": 8.6
    }
  ]
}
```

### 2. `GET /api/top100`
Retorna os 100 melhores filmes (por `imdb_score`) e permite ordenar ou filtrar por gênero.

Parâmetros:
- `order` (opcional): `score` (padrão) ou `year`.
- `genre` (opcional): substring para filtrar em `genres` (case-insensitive).

Resposta exemplo:
```json
{
  "order": "score",
  "genre": "Drama",
  "movies": [
    {
      "movie_title": "The Shawshank Redemption",
      "title_year": 1994,
      "director_name": "Frank Darabont",
      "genres": "Crime|Drama",
      "imdb_score": 9.3
    }
  ]
}
```

## Páginas Frontend
- `/` usa `index.html` para interação básica com busca.
- `/top100` exibe o Top 100 (template `top100.html`).
- `metrics.html` reservado para métricas futuras (ex: distribuição de clusters, histograma de scores, etc.).

## Dataset
`movie_metadata.csv` deve conter as colunas usadas: `movie_title`, `duration`, `budget`, `imdb_score`, `title_year`, `gross`, `director_name`, `genres`.
Valores ausentes nas features numéricas são preenchidos pela mediana antes da normalização.

## Clustering
- Algoritmo: K-Means com `n_clusters=10` e `random_state=42`.
- Escalonamento: `StandardScaler` aplicado às features numéricas.
- Cada filme recebe um rótulo de cluster armazenado na coluna `cluster`.

## Possíveis Melhorias
- Tornar número de clusters configurável via variável de ambiente.
- Cachear resultados de busca popular.
- Adicionar testes unitários para rotas.
- Paginação na listagem do Top 100 (quando filtro reduz muito ou para explorar além dos 100).
- Visualizações em `metrics.html` (gráficos por cluster, score vs. budget, etc.).

## Licença
Defina aqui a licença (por exemplo, MIT). Adicione um arquivo `LICENSE` se necessário.

## Contato
Para dúvidas ou sugestões, abra uma issue ou envie PR.
