"""
Product Review Summarizer — Week 3 Backend (main.py)
PRJ-079 | Student: Selvarani KP

New in Week 2:
  - GET  /products/         → list unique product names
  - POST /summarize-text/   → abstractive summary of a long paragraph
  - GET  /product-summary/  → verdict + pros + cons + sentiment counts for a product
  - POST /reload-dataset/   → hot-reload the CSV without restarting
  - Enhanced /analyze/      → NEUTRAL for low-confidence predictions
  - Enhanced /analyze-batch/→ product filter + per-product breakdown
  - Enhanced /summarize/    → extractive pros/cons + optional product filter

New in Week 3:
  - SQLite-backed history   → every /analyze/, /summarize-text/, /product-summary/
                              call is logged to data/history.db
  - GET    /history/        → view recent history (filter by product/sentiment)
  - DELETE /history/        → clear history (demo reset)
  - GET    /export-report/  → download a CSV/TXT report for a product
  - GET    /health/         → status check for deployment/demo readiness
  - Hardened error handling → malformed rows in a batch are skipped, not fatal
"""

from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from transformers import pipeline
import pandas as pd
import io
import os
import sqlite3
from datetime import datetime, timezone

app = FastAPI(title="Product Review Summarizer", version="3.0")

# ── Model loading ────────────────────────────────────────────────────────────
# Sentiment model (same as Week 1, DistilBERT fine-tuned on SST-2)
sentiment_pipeline = pipeline("sentiment-analysis")

# NOTE: Transformers 5.x removed the "summarization" pipeline task.
# We use a fast extractive approach (sentence scoring) instead —
# no extra model download needed, works fully offline.

# ── In-memory dataset ────────────────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "reviews.csv")

def _load_dataset() -> pd.DataFrame:
    try:
        df = pd.read_csv(DATA_PATH)
        if "review" not in df.columns:
            return pd.DataFrame(columns=["product", "review"])
        if "product" not in df.columns:
            df["product"] = "Unknown"
        return df.fillna("")
    except Exception:
        return pd.DataFrame(columns=["product", "review"])

_dataset: pd.DataFrame = _load_dataset()

# ── Week 3: SQLite history log ───────────────────────────────────────────────
HISTORY_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "history.db")


def _get_db():
    conn = sqlite3.connect(HISTORY_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_history_db():
    conn = _get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            input_text TEXT,
            product TEXT,
            sentiment TEXT,
            score REAL
        )
    """)
    conn.commit()
    conn.close()


_init_history_db()


def _log_history(endpoint: str, input_text: str, sentiment: str = None,
                  score: float = None, product: str = None):
    """Best-effort history logger — never let a logging failure break a request."""
    try:
        conn = _get_db()
        conn.execute(
            "INSERT INTO history (timestamp, endpoint, input_text, product, sentiment, score) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                endpoint,
                (input_text or "")[:300],
                product,
                sentiment,
                score,
            )
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


# ── Helpers ──────────────────────────────────────────────────────────────────
NEUTRAL_THRESHOLD = 0.65   # confidence below this → NEUTRAL


def _extractive_summary(text: str, num_sentences: int = 3) -> str:
    """
    Pure-Python extractive summarizer — no extra model required.
    Scores sentences by: word frequency × position boost.
    Returns the top `num_sentences` sentences in original order.
    """
    import re
    from collections import Counter

    # Split into sentences
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 10]
    if len(sentences) <= num_sentences:
        return text.strip()

    # Word frequency (lowercase, ignore short stop-words)
    stop = {"the","a","an","is","it","in","on","of","to","and","or","but",
            "for","with","this","that","was","are","be","been","have","has",
            "i","my","me","we","you","they","he","she","its","at","by","from"}
    words = [w.lower() for s in sentences for w in re.findall(r'\b[a-z]+\b', s) if w not in stop]
    freq = Counter(words)
    max_freq = max(freq.values()) if freq else 1

    # Score each sentence
    scores = []
    for idx, sent in enumerate(sentences):
        sent_words = [w.lower() for w in re.findall(r'\b[a-z]+\b', sent) if w not in stop]
        word_score = sum(freq.get(w, 0) / max_freq for w in sent_words)
        # Boost first and last sentences slightly
        position_boost = 1.2 if idx == 0 else (1.1 if idx == len(sentences) - 1 else 1.0)
        scores.append(word_score * position_boost)

    # Pick top sentences, preserve original order
    top_indices = sorted(sorted(range(len(scores)), key=lambda i: -scores[i])[:num_sentences])
    return " ".join(sentences[i] for i in top_indices)


def _classify(text: str) -> dict:
    """Run sentiment model; return NEUTRAL when confidence is low.
    Week 3: hardened so a single bad row never crashes a batch request."""
    try:
        pred = sentiment_pipeline(text[:512])[0]
        label = pred["label"]
        score = round(pred["score"], 4)
        if score < NEUTRAL_THRESHOLD:
            label = "NEUTRAL"
        return {"sentiment": label, "score": score, "ok": True}
    except Exception as e:
        return {"sentiment": "NEUTRAL", "score": 0.0, "ok": False, "error": str(e)}


def _extractive_pros_cons(reviews: list[str], top_n: int = 5) -> dict:
    """
    Simple keyword-based extractive pros/cons.
    Positive sentences → pros; negative sentences → cons.
    """
    pros, cons = [], []
    for rev in reviews:
        for sentence in rev.replace(".", ".|").replace(",", ",|").split("|"):
            s = sentence.strip()
            if len(s) < 10:
                continue
            pred = sentiment_pipeline(s[:512])[0]
            if pred["label"] == "POSITIVE" and pred["score"] >= 0.80:
                pros.append(s)
            elif pred["label"] == "NEGATIVE" and pred["score"] >= 0.80:
                cons.append(s)

    # Deduplicate and pick top_n
    seen = set()
    unique_pros = []
    for p in pros:
        key = p.lower()[:40]
        if key not in seen:
            seen.add(key)
            unique_pros.append(p)

    seen = set()
    unique_cons = []
    for c in cons:
        key = c.lower()[:40]
        if key not in seen:
            seen.add(key)
            unique_cons.append(c)

    return {
        "pros": unique_pros[:top_n],
        "cons": unique_cons[:top_n]
    }


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def home():
    return {"message": "Product Review Summarizer API is running", "version": "3.0"}


# ── Week 1 endpoints (enhanced) ──────────────────────────────────────────────

@app.post("/analyze/")
def analyze_review(review: str):
    """Analyze sentiment of a single review — now includes NEUTRAL."""
    if not review.strip():
        return {"error": "Empty review"}
    result = _classify(review)
    _log_history("analyze", review, sentiment=result["sentiment"], score=result["score"])
    return {"review": review, "sentiment": result["sentiment"], "score": result["score"]}


@app.post("/analyze-batch/")
async def analyze_batch(
    file: UploadFile = File(...),
    product: str = Query(default=None, description="Filter by product name")
):
    """
    Batch sentiment analysis with optional product filter
    and per-product breakdown in the response.
    """
    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception:
        return {"error": "Invalid CSV file"}

    if "review" not in df.columns:
        return {"error": "CSV must have a column named 'review'"}
    if "product" not in df.columns:
        df["product"] = "Unknown"
    df = df.fillna("")

    if product:
        df = df[df["product"].str.lower() == product.lower()]
        if df.empty:
            return {"error": f"No reviews found for product: {product}"}

    results = []
    skipped_rows = 0
    for _, row in df.iterrows():
        try:
            text = str(row["review"]).strip()
            if not text:
                skipped_rows += 1
                continue
            pred = _classify(text)
            if not pred.get("ok", True):
                skipped_rows += 1
                continue
            results.append({
                "product": str(row["product"]),
                "review": text,
                "sentiment": pred["sentiment"],
                "score": pred["score"]
            })
        except Exception:
            # A single malformed row must never crash the whole batch.
            skipped_rows += 1
            continue

    positive  = sum(1 for r in results if r["sentiment"] == "POSITIVE")
    negative  = sum(1 for r in results if r["sentiment"] == "NEGATIVE")
    neutral   = sum(1 for r in results if r["sentiment"] == "NEUTRAL")

    # Per-product breakdown
    breakdown: dict = {}
    for r in results:
        p = r["product"]
        if p not in breakdown:
            breakdown[p] = {"positive": 0, "negative": 0, "neutral": 0}
        breakdown[p][r["sentiment"].lower()] += 1

    return {
        "total_reviews": len(results),
        "positive_count": positive,
        "negative_count": negative,
        "neutral_count":  neutral,
        "skipped_rows": skipped_rows,
        "product_breakdown": breakdown,
        "results": results
    }


@app.post("/summarize/")
async def summarize_reviews(
    file: UploadFile = File(...),
    product: str = Query(default=None, description="Filter by product name")
):
    """
    Extractive pros/cons summary from a CSV file.
    Optionally filtered to a single product.
    """
    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception:
        return {"error": "Invalid CSV file"}

    if "review" not in df.columns:
        return {"error": "CSV must have a column named 'review'"}
    if "product" not in df.columns:
        df["product"] = "Unknown"
    df = df.fillna("")

    if product:
        df = df[df["product"].str.lower() == product.lower()]
        if df.empty:
            return {"error": f"No reviews found for product: {product}"}

    reviews = [str(r).strip() for r in df["review"].tolist() if str(r).strip()]
    pc = _extractive_pros_cons(reviews)

    return {
        "product_filter": product or "All",
        "total_reviews_analyzed": len(reviews),
        **pc
    }


# ── Week 2 new endpoints ─────────────────────────────────────────────────────

@app.get("/products/")
def list_products():
    """Return list of unique product names from the loaded dataset."""
    products = sorted(_dataset["product"].dropna().unique().tolist())
    return {"products": products, "count": len(products)}


@app.post("/summarize-text/")
def summarize_text(text: str):
    """
    Extractive summary of a long paragraph (top 3 key sentences).
    Uses sentence scoring — no extra model download required.
    Compatible with Transformers 5.x (summarization pipeline removed).
    """
    if not text.strip():
        return {"error": "Empty text"}
    if len(text.split()) < 20:
        return {"error": "Text too short to summarize (need at least 20 words)"}
    try:
        summary = _extractive_summary(text, num_sentences=3)
        sentiment = _classify(text)
        _log_history("summarize-text", text, sentiment=sentiment["sentiment"], score=sentiment["score"])
        return {
            "original_length": len(text.split()),
            "summary": summary,
            "sentiment": sentiment["sentiment"],
            "score": sentiment["score"]
        }
    except Exception as e:
        return {"error": str(e)}


def _compute_product_summary(product: str) -> dict:
    """
    Shared logic: verdict + top 5 pros + top 5 cons + sentiment counts
    for a specific product from the loaded dataset.
    Used by both /product-summary/ and /export-report/ (Week 3) so the
    two endpoints can never drift out of sync.
    """
    df = _dataset
    filtered = df[df["product"].str.lower() == product.lower()]
    if filtered.empty:
        return {"error": f"No reviews found for product: {product}"}

    reviews = [str(r).strip() for r in filtered["review"].tolist() if str(r).strip()]
    sentiments = [_classify(r) for r in reviews]

    positive = sum(1 for s in sentiments if s["sentiment"] == "POSITIVE")
    negative = sum(1 for s in sentiments if s["sentiment"] == "NEGATIVE")
    neutral  = sum(1 for s in sentiments if s["sentiment"] == "NEUTRAL")
    total    = len(sentiments)

    if total == 0:
        verdict = "No data"
    elif positive / total >= 0.65:
        verdict = "Recommended ✅"
    elif negative / total >= 0.65:
        verdict = "Not Recommended ❌"
    else:
        verdict = "Mixed Reviews ⚠️"

    pc = _extractive_pros_cons(reviews)

    return {
        "product": product,
        "total_reviews": total,
        "positive_count": positive,
        "negative_count": negative,
        "neutral_count":  neutral,
        "verdict": verdict,
        "pros": pc["pros"],
        "cons": pc["cons"]
    }


@app.get("/product-summary/")
def product_summary(product: str = Query(..., description="Product name")):
    """
    Returns verdict + top 5 pros + top 5 cons + sentiment counts
    for a specific product from the loaded dataset.
    """
    result = _compute_product_summary(product)
    if "error" in result:
        return result

    total = result["total_reviews"]
    positive = result["positive_count"]
    _log_history("product-summary", f"[{total} reviews]", sentiment=result["verdict"],
                 score=round(positive / total, 4) if total else None, product=product)

    return result


@app.post("/reload-dataset/")
async def reload_dataset(file: UploadFile = File(...)):
    """
    Replace the in-memory dataset with a newly uploaded CSV.
    Does NOT overwrite the file on disk.
    """
    global _dataset
    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception:
        return {"error": "Invalid CSV file"}

    if "review" not in df.columns:
        return {"error": "CSV must have a column named 'review'"}
    if "product" not in df.columns:
        df["product"] = "Unknown"

    _dataset = df.fillna("")
    return {
        "message": "Dataset reloaded successfully",
        "rows": len(_dataset),
        "products": sorted(_dataset["product"].dropna().unique().tolist())
    }


# ── Week 3 new endpoints ─────────────────────────────────────────────────────

@app.get("/history/")
def get_history(
    limit: int = Query(default=20, ge=1, le=500, description="Max records to return"),
    product: str = Query(default=None, description="Filter by product name"),
    sentiment: str = Query(default=None, description="Filter by sentiment label")
):
    """
    Return the most recent analysis history (newest first), optionally
    filtered by product and/or sentiment. Backed by data/history.db (SQLite),
    so history survives a server restart — unlike the in-memory dataset.
    """
    try:
        conn = _get_db()
        query = "SELECT id, timestamp, endpoint, input_text, product, sentiment, score FROM history"
        conditions = []
        params = []
        if product:
            conditions.append("LOWER(product) = LOWER(?)")
            params.append(product)
        if sentiment:
            conditions.append("LOWER(sentiment) = LOWER(?)")
            params.append(sentiment)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        conn.close()

        records = [dict(row) for row in rows]
        return {"count": len(records), "history": records}
    except Exception as e:
        return {"error": str(e)}


@app.delete("/history/")
def clear_history():
    """Clear all logged history — used to reset the demo before a viva/video."""
    try:
        conn = _get_db()
        conn.execute("DELETE FROM history")
        conn.commit()
        conn.close()
        return {"message": "History cleared successfully"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/export-report/")
def export_report(
    product: str = Query(..., description="Product name to build a report for"),
    format: str = Query(default="txt", pattern="^(txt|csv)$", description="Report format: txt or csv")
):
    """
    Download a pros/cons + verdict report for a product as a CSV or TXT file.
    Reuses _compute_product_summary — never drifts from /product-summary/.
    """
    summary = _compute_product_summary(product)
    if "error" in summary:
        return summary

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    if format == "csv":
        buffer = io.StringIO()
        buffer.write("field,value\n")
        buffer.write(f"product,{summary['product']}\n")
        buffer.write(f"generated_at,{generated_at}\n")
        buffer.write(f"total_reviews,{summary['total_reviews']}\n")
        buffer.write(f"positive_count,{summary['positive_count']}\n")
        buffer.write(f"negative_count,{summary['negative_count']}\n")
        buffer.write(f"neutral_count,{summary['neutral_count']}\n")
        buffer.write(f"verdict,{summary['verdict']}\n")
        for i, p in enumerate(summary["pros"], 1):
            buffer.write(f"pro_{i},\"{p.replace(chr(34), chr(39))}\"\n")
        for i, c in enumerate(summary["cons"], 1):
            buffer.write(f"con_{i},\"{c.replace(chr(34), chr(39))}\"\n")
        buffer.seek(0)
        filename = f"{summary['product'].replace(' ', '_')}_report.csv"
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    # default: txt
    pros_lines = [f"  + {p}" for p in summary["pros"]] if summary["pros"] else ["  (none found)"]
    cons_lines = [f"  - {c}" for c in summary["cons"]] if summary["cons"] else ["  (none found)"]
    lines = [
        "Product Review Summary Report",
        f"Product: {summary['product']}",
        f"Generated: {generated_at}",
        "-" * 40,
        f"Total reviews analyzed: {summary['total_reviews']}",
        f"Positive: {summary['positive_count']} | Negative: {summary['negative_count']} | Neutral: {summary['neutral_count']}",
        f"Verdict: {summary['verdict']}",
        "",
        "Top Pros:",
        *pros_lines,
        "",
        "Top Cons:",
        *cons_lines,
    ]
    text = "\n".join(lines)
    filename = f"{summary['product'].replace(' ', '_')}_report.txt"
    return StreamingResponse(
        iter([text]),
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/health/")
def health_check():
    """
    Status check for deployment/demo readiness.
    Confirms the sentiment model is loaded and the dataset is available.
    """
    try:
        _ = sentiment_pipeline("test")
        model_loaded = True
    except Exception:
        model_loaded = False

    return {
        "status": "ok",
        "model_loaded": model_loaded,
        "dataset_rows": len(_dataset)
    }
