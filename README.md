# 🛍️ Product Review Summarizer

AI-powered sentiment analysis and review summarization tool, built with **FastAPI** + **Streamlit**, and backed by a **DistilBERT** sentiment model. Paste a review, analyze a whole product line, batch-process a CSV of reviews, or pull historical reports — all from one clean web app.

> **Academic Project — PRJ-079**
> Student: Selvarani KP · Reg No: 411623149039
> Built and shipped over 3 weekly milestones (see [Development Timeline](#development-timeline))

---

## ✨ Features

- **Single review analysis** — instant sentiment (Positive / Negative / Neutral) with confidence score
- **Text summarization** — paste any long review or paragraph, get a concise extractive summary
- **Product dashboard** — verdict banner, sentiment chart, and top pros/cons for any product in the dataset
- **Batch CSV analysis** — upload a file of reviews, get per-product sentiment breakdown + charts
- **Social export columns** - batch uploads accept `review`, `tweet_text`, `full_text`, `text`, `content`, `comment`, or `message`
- **History & reports** — every analysis is logged to SQLite; filter history and export CSV/TXT reports
- **Live health check** — sidebar indicator shows backend connection and model-load status
- **Hardened error handling** — malformed input, empty rows, and bad batches degrade gracefully instead of crashing

## 🖼️ Preview

See [`SCREENSHOTS.md`](./SCREENSHOTS.md) for a walkthrough of each tab.

## 🏗️ Architecture

```
data/reviews.csv ──┐
                    ├──▶  FastAPI (main.py)  ──▶  DistilBERT sentiment pipeline
data/history.db ────┘            │                        │
   (SQLite log)                  │                        ▼
                                  ▼                 sentiment / summary
                           REST JSON + file           results returned
                            responses                        │
                                  │                           ▼
                                  └──────────▶  Streamlit UI (app.py)
                                              5 tabs: Single Review · Summarize
                                              Text · Product Dashboard ·
                                              Batch CSV · History & Reports
```

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + Uvicorn |
| Sentiment model | DistilBERT (`distilbert-base-uncased-finetuned-sst-2-english`) |
| Summarization | Extractive sentence-scoring (pure Python) |
| History storage | SQLite |
| Frontend | Streamlit |
| Data handling | Pandas |
| HTTP client | Requests |

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- pip

### 1. Clone the repo
```bash
git clone https://github.com/<your-username>/product-review-summarizer.git
cd product-review-summarizer
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the backend
```bash
uvicorn main:app --reload
```
- API: `http://127.0.0.1:8000`
- Interactive docs: `http://127.0.0.1:8000/docs`

### 4. Start the frontend (in a new terminal)
```bash
streamlit run app.py
```
- App: `http://localhost:8501`

### Pointing the frontend at a deployed backend
```bash
export API_URL="https://your-backend.onrender.com"
streamlit run app.py
```

## 📡 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/analyze/` | POST | Sentiment for a single review |
| `/analyze-batch/` | POST | Sentiment for an uploaded CSV of reviews (optional product filter) |
| `/summarize-text/` | POST | Extractive summary of a long paragraph |
| `/products/` | GET | List unique product names in the dataset |
| `/product-summary/` | GET | Verdict, top pros/cons, and sentiment counts for a product |
| `/reload-dataset/` | POST | Hot-reload the CSV without restarting the server |
| `/history/` | GET | Recent analysis history (filter by product/sentiment) |
| `/history/` | DELETE | Clear all logged history |
| `/export-report/` | GET | Download a CSV/TXT report for a product |
| `/health/` | GET | Backend status, model-loaded state, dataset row count |

CSV upload endpoints normalize the detected review text field to the existing
`review` contract internally and return `detected_review_column` in the JSON
response. This keeps the backend compatible with exports that name the text
field `tweet_text`, `full_text`, `text`, `content`, `comment`, or `message`.

## 📁 Project Structure

```
product_review_summarizer_week3/
├── main.py                  # FastAPI backend
├── app.py                   # Streamlit frontend (5 tabs)
├── test_main.py              # 33 automated test cases
├── test_cases.md              # Test case documentation
├── test_results_week3.md      # End-to-end test results
├── SCREENSHOTS.md              # Screenshot checklist
├── requirements.txt            # Python dependencies
└── data/
    ├── reviews.csv          # Sample dataset (15 reviews, 5 products)
    └── history.db           # SQLite history log (auto-created)
```

## 🧪 Testing

```bash
# with the backend running:
python test_main.py
```

33 automated test cases spanning regression, boundary conditions, and feature coverage. Full case-by-case documentation in [`test_cases.md`](./test_cases.md); manually verified end-to-end results in [`test_results_week3.md`](./test_results_week3.md).

## ☁️ Deployment

- **Backend:** deploy `main.py` to [Render](https://render.com) (or any host running `uvicorn main:app --host 0.0.0.0 --port $PORT`)
- **Frontend:** deploy `app.py` to [Streamlit Community Cloud](https://streamlit.io/cloud), with `API_URL` set to your backend's public URL
- **Health check:** `GET <backend-url>/health/` → `{"status": "ok", "model_loaded": true, "dataset_rows": 15}`

## 📅 Development Timeline

<details>
<summary><strong>Week 1 — Foundation</strong></summary>

Core sentiment analysis endpoint, DistilBERT integration, and initial Streamlit UI.
</details>

<details>
<summary><strong>Week 2 — Summarization & Dashboards</strong></summary>

- `GET /products/`, `POST /summarize-text/`, `GET /product-summary/`, `POST /reload-dataset/`
- NEUTRAL sentiment threshold, batch product filtering, per-product breakdown
- New tabs: Summarize Text, Product Dashboard; extended Batch CSV tab
</details>

<details>
<summary><strong>Week 3 — History, Reports & Hardening</strong></summary>

- SQLite-backed history logging across all analysis endpoints
- `GET`/`DELETE /history/`, `GET /export-report/`, `GET /health/`
- Hardened batch handling (skips malformed rows instead of failing)
- New History & Reports tab, live backend status indicator, full test coverage
</details>

## 📄 License

This project was built for academic coursework. Feel free to fork and adapt for learning purposes.

---

**Author:** Selvarani KP
