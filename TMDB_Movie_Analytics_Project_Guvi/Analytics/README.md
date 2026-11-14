# 🎬 Reel Insights: TMDB Movie Analysis

An end-to-end exploratory data analysis of ~2,500 movies from The Movie Database (TMDB), covering data cleaning, a relational SQL database, SQL and Pandas analysis, visualizations, and an interactive multi-page Streamlit app.

**Tech stack:** Python, Pandas, SQLite, SQLAlchemy, Matplotlib, Seaborn, Plotly, Streamlit

## Dataset

Six linked CSV tables: `movies`, `genres`, `movie_genres`, `cast`, `crew`, `movie_keywords`.

After cleaning: **2,503 movies, 19 genres, 11,300 unique cast members, 2,848 unique crew members.**

## Project Structure

```
Analytics/
├── 01_data_cleaning.ipynb      # Clean the 6 CSVs and load them into SQLite
├── 02_sql_analysis.ipynb       # 10 SQL questions
├── 03_pandas_analysis.ipynb    # 10 Pandas questions
├── 04_visualizations.ipynb     # Univariate, bivariate, multivariate charts
├── app.py                      # Streamlit app (Filters, Dashboard, Query Explorer)
├── dataset/                    # Raw CSV files
├── data/
│   └── TMDB_database.db        # SQLite database created by notebook 01
├── requirements.txt
└── README.md
```

## How to Run

1. Install the libraries:
   ```
   pip install -r requirements.txt
   ```
2. Run `01_data_cleaning.ipynb` first. It cleans the CSVs and creates `data/TMDB_database.db`.
3. Run notebooks `02`, `03`, `04` in order (optional, for the analysis).
4. Start the app from the project folder:
   ```
   streamlit run app.py
   ```

## Streamlit App

| Page | What it does |
|------|--------------|
| **Filters** | Release year, minimum rating, language and genre filters (kept in `st.session_state`), live movie count, a "Surprise me" random pick |
| **Dashboard** | KPI cards, Top 10 movies by revenue, genre distribution, budget vs revenue scatter, text insight |
| **Query Explorer** | 10 saved queries with a results table, chart and insight |

All pages read from the SQLite database and respond to the sidebar filters.

## Data Cleaning Decisions

- Removed duplicate rows and orphaned rows (records pointing to movies that no longer exist).
- Parsed `release_date` as a date and enforced integer types for IDs, budget and revenue.
- **Budget and revenue values of 0 were treated as "unknown", not as zero.** 133 movies have a zero budget or revenue, so profit and ROI were calculated only for the 2,370 movies with valid figures.

## Top 5 Insights and Recommendations

### 1. A big budget does not guarantee big revenue
Avatar is the highest-grossing movie ($2.92B), but many expensive films underperform. For example, The Marvels had a $275M budget and earned only $206M, below the dataset average.
**Recommendation:** Judge projects by expected ROI and risk, not by budget size or revenue alone.

### 2. Small-budget films deliver the best return per dollar
Among movies with a budget of at least $1M, the top ROI films are mostly low-budget titles: Dragon Ball Super: Broly (124x), Snow White and the Seven Dwarfs (123x), The Rocky Horror Picture Show (121x) and Rocky (116x).
**Recommendation:** Keep a portfolio of low-budget bets next to blockbusters to balance risk.

### 3. Genre decides revenue, popularity and ratings
Adventure has the highest average revenue ($401M) while Drama averages $147M but costs less to make. Science Fiction has the highest average popularity (21.26) and Documentary the lowest (7.73). War has the highest average rating (7.36) among genres with at least 20 movies.
**Recommendation:** Pick genres by the goal: Adventure and Sci-Fi for box-office and attention, War and Drama for critical reception at lower cost.

### 4. Familiar stories and franchises dominate the industry
The most common keywords are "based on novel or book" (449) and "sequel" (416), and many titles are remakes, such as Aladdin (1992 and 2019). Studios and platforms lean on known stories to reduce risk.
**Recommendation:** Existing IP is a lower-risk choice, but original stories can stand out in a crowded market.

### 5. Popularity and vote count measure different things
Older hits like Home Alone and The Silence of the Lambs have very high vote counts but low popularity scores, while some new releases are very popular with few votes. Popularity reflects current attention, while vote count reflects total audience over time.
**Recommendation:** Use both metrics together. Use popularity to spot trending titles and vote count and rating to find lasting, well-loved content.

## Other Notable Findings

- 2016 had the most releases (121 movies). The low counts for 2025 and 2026 are because those years are only partly covered.
- Samuel L. Jackson appeared in the most movies (39). Among the top 10 most prolific actors, Tom Hanks has the best average rating (7.29).
- 217 directors made more than 3 movies. Steven Spielberg has the most (27).
- 84 actors have worked with Christopher Nolan.
