import streamlit as st
import pandas as pd
import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import URL

st.set_page_config(page_title="TMDBS", page_icon="🎬", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "TMDB_database.db")

engine = create_engine(
    URL.create(
        "sqlite",
        database=DB_PATH
    )
)# database connection

# Backgroung color and theme 

def set_theme():
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(160deg, #1a0f2e, #3b1c4a, #6c2b6d); }
    [data-testid="stSidebar"] { background: #1a0f2e; }
    h1, h2, h3, label, p { color: #fdeee6 !important; }
    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.08);
        border-left: 6px solid #e98d6b;
        padding: 15px;
        border-radius: 15px;
    }
    [data-testid="stMetricValue"] { color: #f4a582 !important; }
    </style>
    """, unsafe_allow_html=True)

# Load all data 

def load_data():
    
    movies = pd.read_sql("SELECT * FROM movies", engine)
    genres = pd.read_sql("SELECT * FROM genres", engine)
    movie_genres = pd.read_sql("SELECT * FROM movie_genres", engine)
    cast = pd.read_sql("SELECT * FROM [cast]", engine)
    crew = pd.read_sql("SELECT * FROM crew", engine)
    movie_keywords = pd.read_sql("SELECT * FROM movie_keywords", engine)

    movies["release_year"] = pd.to_datetime(movies["release_date"]).dt.year
    return movies, genres, movie_genres, cast, crew, movie_keywords

# Filters

def sidebar_filters(movies, genres):
    st.sidebar.header("Filters")

    min_year = int(movies["release_year"].min())
    max_year = int(movies["release_year"].max())

    st.sidebar.slider("Release Year", min_year, max_year, (min_year, max_year), key="year_range")
    st.sidebar.slider("Minimum Rating", 0.0, 10.0, 0.0, step=0.5, key="min_rating")

    languages = ["All"] + sorted(movies["original_language"].dropna().unique())
    st.sidebar.selectbox("Language", languages, key="language")

    genre_list = sorted(genres["genre_name"].dropna().unique())
    st.sidebar.multiselect("Genre", genre_list, key="genres")

#  Apply filters 
    
def apply_filters(movies, genres, movie_genres):
    s = st.session_state

    filtered = movies[(movies["release_year"] >= s["year_range"][0])& (movies["release_year"] <= s["year_range"][1])&(movies["vote_average"] >= s["min_rating"])]

    if s["language"] != "All":
        filtered = filtered[filtered["original_language"] == s["language"]]

    if s["genres"]:
        genre_ids = genres[genres["genre_name"].isin(s["genres"])]["genre_id"]
        movie_ids = movie_genres[movie_genres["genre_id"].isin(genre_ids)]["movie_id"]
        filtered = filtered[filtered["movie_id"].isin(movie_ids)]

    return filtered

def surprise_me(filtered):
    if st.sidebar.button("🎲 Surprise me"):
        if len(filtered) > 0:
            pick = filtered.sample(1).iloc[0]
            st.sidebar.success(f"{pick['title']} ({int(pick['release_year'])}) ⭐ {pick['vote_average']}")
        else:
            st.sidebar.warning("No movies match the filters")

# ---------- Page 1: Filters ----------
def filters_page(filtered):
    st.header("🎯 Filters")
    st.write(len(filtered), "movies match your filters")
    st.dataframe(filtered[["title", "release_year", "original_language", "vote_average"]])

# ---------- Page 2: Dashboard ----------
def dashboard_page(filtered, genres, movie_genres, cast):
    st.header("📊 Dashboard")

    if filtered.empty:
        st.warning("No movies match the filters.")
        return

    f_genres = movie_genres[movie_genres["movie_id"].isin(filtered["movie_id"])]
    f_cast = cast[cast["movie_id"].isin(filtered["movie_id"])]

    ACTOR_COL = "person_id"  

    # KPI cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Movies", len(filtered))
    c2.metric("Genres", f_genres["genre_id"].nunique())
    c3.metric("Actors", f_cast[ACTOR_COL].nunique())
    c4.metric("Avg Rating", round(filtered["vote_average"].mean(), 2))

    # Top 10 by revenue
    st.subheader("🏆 Top 10 Movies by Revenue")
    top10 = filtered[filtered["revenue"] > 0].nlargest(10, "revenue")
    st.bar_chart(top10.set_index("title")["revenue"], color="#e98d6b")

    # Genre distribution
    st.subheader("🎭 Genre Distribution")
    genre_count = f_genres.merge(genres, on="genre_id")["genre_name"].value_counts()
    st.bar_chart(genre_count, color="#e3685c")

    # Budget vs Revenue
    st.subheader("💰 Budget vs Revenue")
    br = filtered[(filtered["budget"] > 0) & (filtered["revenue"] > 0)]
    st.scatter_chart(br, x="budget", y="revenue", color="#d14a61")

    # Insight
    st.subheader("💡 Insight")
    rev = (
        f_genres.merge(genres, on="genre_id")
        .merge(filtered[["movie_id", "revenue"]], on="movie_id")
        .groupby("genre_name")["revenue"].sum()
        .sort_values(ascending=False)
    )
    if len(rev) > 0 and rev.iloc[0] > 0:
        st.info(
            f"In this selection, {rev.index[0]} is the highest grossing genre "
            f"with ${rev.iloc[0]:,.0f} total revenue."
        )


# ---------- Page 3: Query Explorer (pandas) ----------
def query_page(filtered, genres, movie_genres, cast, crew, movie_keywords):
    st.header("🔍 Query Explorer")

    if filtered.empty:
        st.warning("No movies match the filters.")
        return

    choice = st.selectbox("Select a saved query", [
        "Q1. Action movies after 2015",
        "Q2. Top 10 movies by revenue with genres",
        "Q3. Average budget and revenue by genre",
        "Q4. Top 10 actors by movie count",
        "Q5. Directors with more than 3 movies",
        "Q6. Top 10 keywords",
        "Q7. High budget but low revenue movies",
        "Q8. Actors who worked with Christopher Nolan",
        "Q9. Genre with highest rating (20+ movies)",
        "Q10. Top 10 movies by keyword count",
    ])

    # movie + genre join
    gm = filtered.merge(movie_genres, on="movie_id").merge(genres, on="genre_id")

    if choice.startswith("Q1."):
        action = gm[(gm["genre_name"] == "Action") & (gm["release_year"] > 2015)]
        result = action[["title", "release_date"]].sort_values("release_date")

    elif choice.startswith("Q2."):
        top = filtered.nlargest(10, "revenue")
        gm_top = gm[gm["movie_id"].isin(top["movie_id"])]
        genre_list = gm_top.groupby("title")["genre_name"].apply(", ".join).reset_index()
        result = top[["title", "revenue"]].merge(genre_list, on="title")

    elif choice.startswith("Q3."):
        valid = gm[(gm["budget"] > 0) & (gm["revenue"] > 0)]
        result = valid.groupby("genre_name")[["budget", "revenue"]].mean().round(0).reset_index()
        result = result.sort_values("revenue", ascending=False)

    elif choice.startswith("Q4."):
        f_cast = cast[cast["movie_id"].isin(filtered["movie_id"])]
        result = f_cast.groupby("actor_name")["movie_id"].nunique().reset_index(name="movie_count")
        result = result.sort_values("movie_count", ascending=False).head(10)

    elif choice.startswith("Q5."):
        f_crew = crew[crew["movie_id"].isin(filtered["movie_id"])]
        directors = f_crew[f_crew["job"] == "Director"]
        result = directors.groupby("person_name")["movie_id"].nunique().reset_index(name="movie_count")
        result = result[result["movie_count"] > 3].sort_values("movie_count", ascending=False)

    elif choice.startswith("Q6."):
        f_kw = movie_keywords[movie_keywords["movie_id"].isin(filtered["movie_id"])]
        result = f_kw.groupby("keyword_name").size().reset_index(name="usage_count")
        result = result.sort_values("usage_count", ascending=False).head(10)

    elif choice.startswith("Q7."):
        avg_budget = filtered[filtered["budget"] > 0]["budget"].mean()
        avg_revenue = filtered[filtered["revenue"] > 0]["revenue"].mean()
        result = filtered[(filtered["budget"] > avg_budget) &
                          (filtered["revenue"] > 0) &
                          (filtered["revenue"] < avg_revenue)]
        result = result[["title", "budget", "revenue"]].sort_values("budget", ascending=False)

    elif choice.startswith("Q8."):
        nolan = crew[(crew["job"] == "Director") & (crew["person_name"] == "Christopher Nolan")]
        nolan_cast = cast[cast["movie_id"].isin(nolan["movie_id"])]
        result = nolan_cast.groupby("actor_name")["movie_id"].nunique().reset_index(name="movies_together")
        result = result.sort_values("movies_together", ascending=False)

    elif choice.startswith("Q9."):
        result = gm.groupby("genre_name").agg(avg_rating=("vote_average", "mean"),
                                              movie_count=("movie_id", "count")).reset_index()
        result = result[result["movie_count"] >= 20].round(2)
        result = result.sort_values("avg_rating", ascending=False).head(1)

    else:
        kw = movie_keywords[movie_keywords["movie_id"].isin(filtered["movie_id"])]
        counts = kw.groupby("movie_id").size().reset_index(name="keyword_count")
        result = counts.merge(filtered[["movie_id", "title"]], on="movie_id")
        result = result[["title", "keyword_count"]].sort_values("keyword_count", ascending=False).head(10)

    if result.empty:
        st.warning("No result for this query.")
    else:
        st.dataframe(result)
        # draw chart only if the second column is a number
        if pd.api.types.is_numeric_dtype(result[result.columns[1]]):
            st.bar_chart(result.set_index(result.columns[0])[result.columns[1]], color="#7b68ee")
        st.info(f"Top result: {result.iloc[0, 0]} ({result.columns[1]} = {result.iloc[0, 1]})")
        
# ---------- Main ----------
def main():
    set_theme()
    st.title("🎬 TMDBS")

    movies, genres, movie_genres, cast, crew, movie_keywords = load_data()

    page = st.sidebar.radio("Go to", ["Filters", "Dashboard", "Query Explorer"])

    sidebar_filters(movies, genres)
    filtered = apply_filters(movies, genres, movie_genres)

    st.sidebar.metric("Movies Matching Filters", len(filtered))
    surprise_me(filtered)

    if page == "Filters":
        filters_page(filtered)
    elif page == "Dashboard":
        dashboard_page(filtered, genres, movie_genres, cast)
    else:
        query_page(filtered, genres, movie_genres, cast, crew, movie_keywords)

main()
