import pandas as pd
import streamlit as st
import pickle
import requests
import gzip
import os
import time
from dotenv import load_dotenv

# =========================
# ENV SETUP
# =========================
load_dotenv()
API_KEY = os.getenv("TMDB_API_KEY")

# =========================
# LOAD DATA
# =========================
movies = pickle.load(open('movies.pkl', 'rb'))
similarity = pickle.load(gzip.open('similarity.pkl.gz', 'rb'))

movies = movies.drop_duplicates(subset=['title']).reset_index(drop=True)

# =========================
# SESSION
# =========================
session = requests.Session()

# =========================
# FETCH POSTER (WITH RETRY)
# =========================
@st.cache_data(show_spinner=False)
def fetch_poster(movie_id):
    if not API_KEY:
        return None

    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"

    for attempt in range(3):
        try:
            response = session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                poster_path = data.get("poster_path")

                if poster_path:
                    return "https://image.tmdb.org/t/p/w500" + poster_path

            time.sleep(0.5 * (attempt + 1))

        except:
            time.sleep(0.5 * (attempt + 1))

    return None


# =========================
# RECOMMENDATION ENGINE
# =========================
@st.cache_data(show_spinner=False)
def recommend(movie):
    if movie not in movies['title'].values:
        return [], []

    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]

    movies_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:6]

    names = []
    posters = []

    for i in movies_list:
        name = movies.iloc[i[0]].title
        poster = fetch_poster(movies.iloc[i[0]].movie_id)

        names.append(name)
        posters.append(poster)  # can be None

    return names, posters


# =========================
# STREAMLIT UI
# =========================
st.set_page_config(page_title="Movie Recommender", layout="wide")

st.title("🎬 Movie Recommendation System")

selected_movie = st.selectbox(
    "Select a movie",
    movies['title'].values
)

# =========================
# RECOMMEND BUTTON
# =========================
if st.button("Recommend"):

    with st.spinner("Fetching movies... ⏳"):
        names, posters = recommend(selected_movie)

    if len(names) == 5:

        cols = st.columns(5)

        failed = False

        for col, name, poster in zip(cols, names, posters):
            with col:
                st.markdown(f"**{name}**")

                if poster:
                    st.image(poster, use_container_width=True)
                else:
                    failed = True
                    st.markdown("🚫 Poster not available")

        # ⚠️ WARNING IF ANY FAILED
        if failed:
            st.warning("⚠️ Unable to fetch all posters due to network issue")

    else:
        st.error("Something went wrong. Try again.")


# =========================
# RESET BUTTON
# =========================
st.markdown("---")

if st.button("🔄 Reset"):
    st.rerun()           