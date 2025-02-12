from flask import Flask, request, jsonify, render_template
import pandas as pd
import re
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

app = Flask(__name__)

# --- Carregamento e pré-processamento do dataset ---
df = pd.read_csv("movie_metadata.csv")

# Preencher valores ausentes para as features numéricas usadas no clustering
numeric_features = ['duration', 'budget', 'imdb_score', 'title_year', 'gross']
df[numeric_features] = df[numeric_features].fillna(df[numeric_features].median())

# Normaliza os dados
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df[numeric_features])

# Aplica o K-Means (neste exemplo, 10 clusters)
kmeans = KMeans(n_clusters=10, random_state=42)
df['cluster'] = kmeans.fit_predict(X_scaled)

# --- Rotas da API e Frontend ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['GET'])
def search_movie():
    """
    Parâmetros esperados:
      - movie: nome do filme pesquisado (obrigatório)
      - selection: (opcional) índice do candidato selecionado (caso a pesquisa inicial não retorne correspondência exata)
      - order: (opcional) 'imdb' para ordenar por nota (padrão) ou 'year' para ordenar por ano de lançamento (não afeta a listagem do clustering)
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

    cluster_id = filme_selecionado.iloc[0]['cluster']

    # Filtra filmes do mesmo cluster com imdb_score >= 7.5, incluindo o próprio filme pesquisado
    filmes_semelhantes = df[
        (df['cluster'] == cluster_id) &
        (df['imdb_score'] >= 7.5)
    ]
    
    # Para esta rota, a ordenação segue o parâmetro 'order', embora o padrão seja por imdb_score.
    if order == "year":
        filmes_semelhantes = filmes_semelhantes.sort_values(by="title_year", ascending=False)
    else:
        filmes_semelhantes = filmes_semelhantes.sort_values(by="imdb_score", ascending=False)

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

# Rota para o template que exibe o Top 100
@app.route('/top100')
def top100_page():
    return render_template('top100.html')

@app.route('/api/top100', methods=['GET'])
def top100_api():
    """
    Parâmetros:
      - order: 'score' (padrão) para ordenar por score IMDb ou 'year' para ordenar por ano de lançamento;
      - genre: (opcional) string para filtrar filmes cujo campo "genres" contenha o termo informado.
    """
    genre = request.args.get('genre', '').strip()
    order = request.args.get('order', 'score').lower()

    # Se um filtro por gênero for informado, aplica-o (busca substring, case-insensitive)
    filtered_df = df.copy()
    if genre:
        filtered_df = filtered_df[filtered_df['genres'].str.contains(genre, case=False, na=False)]
    
    # Seleciona os top 100 filmes por imdb_score (do maior para o menor)
    top_df = filtered_df.sort_values(by='imdb_score', ascending=False).head(100)
    
    # Se o usuário optar por ordenar por ano, reordena os top 100 por title_year
    if order == 'year':
        top_df = top_df.sort_values(by='title_year', ascending=False)
    else:
        top_df = top_df.sort_values(by='imdb_score', ascending=False)

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