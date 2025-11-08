"""Movies Clustering & Exploration Application

Este módulo inicializa uma aplicação Flask que:
    - Carrega e pré-processa um dataset de filmes (`movie_metadata.csv`).
    - Executa clustering (K-Means) em features numéricas para agrupar filmes semelhantes.
    - Fornece rotas de API para busca de filmes similares e listagem de Top 100.
    - Expõe páginas HTML simples para interação.

Principais etapas:
    1. Carregamento do dataset.
    2. Tratamento de valores ausentes nas features numéricas (preenchimento por mediana).
    3. Normalização via `StandardScaler`.
    4. Clustering K-Means (n_clusters=10) e atribuição de rótulos.

Rotas principais:
    - `/api/search`: Busca um filme e retorna títulos similares (mesmo cluster, score >= 7.5).
    - `/api/top100`: Lista Top 100 por score ou ano, com filtro opcional de gênero.

Observações:
    - Ajustes como número de clusters e limiar de score podem ser parametrizados futuramente.
    - O arquivo README contém detalhes adicionais de uso.
"""

from flask import Flask, request, jsonify, render_template
import pandas as pd
import re
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

app = Flask(__name__)

# --- Carregamento e pré-processamento do dataset ---
# Lê o CSV principal. Espera colunas como movie_title, duration, budget, imdb_score, title_year, gross, director_name, genres.
df = pd.read_csv("movie_metadata.csv")

# Features numéricas que alimentam o clustering.
numeric_features = ['duration', 'budget', 'imdb_score', 'title_year', 'gross']

# Preenche valores ausentes nessas features usando a mediana (robusto a outliers).
df[numeric_features] = df[numeric_features].fillna(df[numeric_features].median())

# Normalização (z-score) para evitar que escalas diferentes distorçam o K-Means.
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df[numeric_features])

# Execução do K-Means. n_clusters fixo (10) para simplicidade. random_state garante reprodutibilidade.
kmeans = KMeans(n_clusters=10, random_state=42)
df['cluster'] = kmeans.fit_predict(X_scaled)

# --- Rotas da API e Frontend ---

@app.route('/')
def index():
    """Renderiza a página inicial (`index.html`).

    Retorna:
        HTML: Página com interface de busca de filmes.
    """
    return render_template('index.html')

@app.route('/api/search', methods=['GET'])
def search_movie():
    """Busca um filme e retorna similares do mesmo cluster.

    Lógica:
        1. Tenta match exato pelo título normalizado.
        2. Se não encontrar, retorna candidatos que contenham o termo (substring case-insensitive).
        3. Se o usuário envia `selection` escolhe um candidato específico.
        4. Obtém o cluster do filme selecionado e lista filmes com `imdb_score >= 7.5` naquele cluster.
        5. Ordena por score (padrão) ou ano se `order=year`.

    Parâmetros (query string):
        movie (str, obrigatório): título pesquisado.
        selection (int, opcional): índice de um candidato retornado previamente.
        order (str, opcional): 'imdb' (default) ou 'year'.

    Retornos:
        200 JSON:
            - Caso similares: {
                    "selected_movie": str,
                    "cluster": int,
                    "order": str,
                    "similar_movies": [ {movie_title, title_year, director_name, genres, imdb_score}, ... ]
                }
            - Caso candidatos: {
                    "message": str,
                    "candidates": [ {id, movie_title, title_year}, ... ]
                }
        400 JSON: {"error": mensagem}

    Exemplos:
        /api/search?movie=Inception
        /api/search?movie=Inception&order=year
        /api/search?movie=Matrix&selection=123
    """
    movie_input = request.args.get('movie', '').strip()
    selection = request.args.get('selection', None)
    order = request.args.get('order', 'imdb').lower()

    if movie_input == "":
        return jsonify({"error": "Parâmetro 'movie' é obrigatório."}), 400

    movie_input_lower = movie_input.lower()

    if selection is not None:
        try:
            selection = int(selection)
        except ValueError:
            return jsonify({"error": "Parâmetro 'selection' deve ser um inteiro."}), 400

        pattern = re.compile(".*" + re.escape(movie_input) + ".*", re.IGNORECASE)
        candidate_matches = df[df['movie_title'].str.strip().apply(lambda x: bool(pattern.search(x)))]
        if candidate_matches.empty or selection not in candidate_matches.index:
            return jsonify({"error": "Seleção inválida."}), 400
        filme_selecionado = candidate_matches.loc[selection:selection]
    else:
        exact_match = df[df['movie_title'].str.strip().str.lower() == movie_input_lower]
        if exact_match.empty:
            pattern = re.compile(".*" + re.escape(movie_input) + ".*", re.IGNORECASE)
            candidate_matches = df[df['movie_title'].str.strip().apply(lambda x: bool(pattern.search(x)))]
            if candidate_matches.empty:
                return jsonify({"error": "Nenhum filme encontrado."}), 400
            else:
                candidates_list = []
                for idx, row in candidate_matches.iterrows():
                    candidate = {
                        "id": idx,
                        "movie_title": row['movie_title'],
                        "title_year": row['title_year'] if pd.notnull(row['title_year']) else "N/D"
                    }
                    candidates_list.append(candidate)
                return jsonify({
                    "message": "Filme não encontrado exatamente. Selecione uma das opções.",
                    "candidates": candidates_list
                })
        else:
            filme_selecionado = exact_match.iloc[[0]]

    # Cluster do filme base usado para obter similares.
    cluster_id = filme_selecionado.iloc[0]['cluster']

    # Filtra filmes do mesmo cluster com imdb_score >= 7.5 (limiar simples de qualidade).
    filmes_semelhantes = df[
        (df['cluster'] == cluster_id) &
        (df['imdb_score'] >= 7.5)
    ]
    
    # Para esta rota, a ordenação segue o parâmetro 'order', embora o padrão seja por imdb_score.
    if order == "year":
        filmes_semelhantes = filmes_semelhantes.sort_values(by="title_year", ascending=False)
    else:
        filmes_semelhantes = filmes_semelhantes.sort_values(by="imdb_score", ascending=False)

    # Monta payload de similares.
    similares = []
    for _, row in filmes_semelhantes.iterrows():
        similares.append({
            "movie_title": row['movie_title'],
            "title_year": int(row['title_year']) if pd.notnull(row['title_year']) else "N/D",
            "director_name": row['director_name'] if pd.notnull(row['director_name']) else "N/D",
            "genres": row['genres'] if pd.notnull(row['genres']) else "N/D",
            "imdb_score": row['imdb_score']
        })
    
    response = {
        "selected_movie": filme_selecionado.iloc[0]['movie_title'],
        "cluster": int(cluster_id),
        "order": order,
        "similar_movies": similares
    }
    return jsonify(response)

@app.route('/top100')
def top100_page():
    """Renderiza a página `top100.html` que consome o endpoint /api/top100.

    Retorna:
        HTML: Página de listagem dos Top 100 filmes segundo critérios escolhidos.
    """
    return render_template('top100.html')

@app.route('/api/top100', methods=['GET'])
def top100_api():
    """Retorna lista de Top 100 filmes.

    Processo:
        1. Aplica filtro de gênero (substring case-insensitive) se fornecido.
        2. Seleciona inicialmente top 100 por `imdb_score`.
        3. Reordena por ano se `order=year`, caso contrário mantém por score.

    Parâmetros (query string):
        order (str, opcional): 'score' (default) ou 'year'.
        genre (str, opcional): termo para filtro em `genres`.

    Retorno (200 JSON): {
            "order": str,
            "genre": str,
            "movies": [ {movie_title, title_year, director_name, genres, imdb_score}, ... ]
    }

    Erros:
        - Atualmente não há erros explícitos além de retorno vazio se filtro restringir demais.

    Exemplos:
        /api/top100
        /api/top100?order=year
        /api/top100?genre=Drama&order=score
    """
    genre = request.args.get('genre', '').strip()
    order = request.args.get('order', 'score').lower()

    # Filtro de gênero (substring case-insensitive). Evita NaN com na=False.
    filtered_df = df.copy()
    if genre:
        filtered_df = filtered_df[filtered_df['genres'].str.contains(genre, case=False, na=False)]
    
    # Seleciona os top 100 filmes por imdb_score (maior -> menor).
    top_df = filtered_df.sort_values(by='imdb_score', ascending=False).head(100)
    
    # Reordena por ano de lançamento se solicitado.
    if order == 'year':
        top_df = top_df.sort_values(by='title_year', ascending=False)
    else:
        top_df = top_df.sort_values(by='imdb_score', ascending=False)

    # Constrói lista de filmes (padroniza campos e trata ausentes).
    movies = []
    for _, row in top_df.iterrows():
        movies.append({
            "movie_title": row['movie_title'],
            "title_year": int(row['title_year']) if pd.notnull(row['title_year']) else "N/D",
            "director_name": row['director_name'] if pd.notnull(row['director_name']) else "N/D",
            "genres": row['genres'] if pd.notnull(row['genres']) else "N/D",
            "imdb_score": row['imdb_score']
        })
    
    return jsonify({
        "order": order,
        "genre": genre,
        "movies": movies
    })

if __name__ == '__main__':
    app.run(debug=True)
