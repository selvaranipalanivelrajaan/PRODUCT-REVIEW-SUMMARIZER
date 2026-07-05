"""
Week 3 - Automated Test Script
Product Review Summarizer (PRJ-079)
Student: Selvarani KP

Includes all Week 1/2 regression tests (TC-01 to TC-20) plus new
Week 3 tests (TC-21 to TC-30) for history, report export, health check,
and boundary/garbage-input hardening.

Run this after starting the backend:
    uvicorn main:app --reload
Then in another terminal:
    python test_main.py
"""

import requests
import io

API = "http://127.0.0.1:8000"
passed = 0
failed = 0


def check(test_id, description, condition, actual):
    global passed, failed
    status = "PASS ✅" if condition else "FAIL ❌"
    if condition:
        passed += 1
    else:
        failed += 1
    print(f"[{status}] {test_id}: {description}")
    if not condition:
        print(f"         Got: {actual}")


print("=" * 60)
print("  Product Review Summarizer — Week 3 Test Suite")
print("=" * 60)

# ── Week 1 endpoint tests (regression) ───────────────────────────

# TC-01: Health check (version 3.0 — bumped in Week 3)
r = requests.get(f"{API}/")
d = r.json()
check("TC-01", "GET / → version 3.0", d.get("version") == "3.0", d)

# TC-02: Positive review
r = requests.post(f"{API}/analyze/", params={"review": "Battery life is excellent, lasts all day easily"})
d = r.json()
check("TC-02", "Positive review → POSITIVE", d.get("sentiment") == "POSITIVE", d)

# TC-03: Negative review
r = requests.post(f"{API}/analyze/", params={"review": "Worst product I have ever bought, total waste of money"})
d = r.json()
check("TC-03", "Negative review → NEGATIVE", d.get("sentiment") == "NEGATIVE", d)

# TC-04: Empty review
r = requests.post(f"{API}/analyze/", params={"review": ""})
d = r.json()
check("TC-04", "Empty review → error message", "error" in d, d)

# TC-05: Whitespace only
r = requests.post(f"{API}/analyze/", params={"review": "   "})
d = r.json()
check("TC-05", "Whitespace only → error message", "error" in d, d)

# TC-06: Score range
r = requests.post(f"{API}/analyze/", params={"review": "This is a great product"})
d = r.json()
score = d.get("score", -1)
check("TC-06", "Score is between 0.0 and 1.0", 0.0 <= score <= 1.0, d)

# TC-07: Sentiment field present
r = requests.post(f"{API}/analyze/", params={"review": "Okay product, nothing special"})
d = r.json()
check("TC-07", "Sentiment field present in response", "sentiment" in d, d)

# ── Week 2: /products/ ────────────────────────────────────────────

# TC-08: Products list returns list
r = requests.get(f"{API}/products/")
d = r.json()
check("TC-08", "GET /products/ → returns list", isinstance(d.get("products"), list), d)

# TC-09: Products count > 0
check("TC-09", "GET /products/ → at least 1 product", d.get("count", 0) > 0, d)

# ── Week 2: /summarize-text/ ──────────────────────────────────────

# TC-10: Short text → error
r = requests.post(f"{API}/summarize-text/", params={"text": "This is short."})
d = r.json()
check("TC-10", "Short text (< 20 words) → error", "error" in d, d)

# TC-11: Empty text → error
r = requests.post(f"{API}/summarize-text/", params={"text": ""})
d = r.json()
check("TC-11", "Empty text → error", "error" in d, d)

# TC-12: Long text returns summary
long_text = (
    "I bought this laptop three months ago and have been using it daily for work and gaming. "
    "The performance is excellent — it handles multitasking without any lag. "
    "The display is sharp and bright, making video calls look professional. "
    "However, the battery life is disappointing, lasting only four hours under load. "
    "The keyboard is comfortable but the trackpad sometimes misregisters clicks. "
    "Overall I am satisfied with the purchase despite the battery issue."
)
r = requests.post(f"{API}/summarize-text/", params={"text": long_text})
d = r.json()
check("TC-12", "Long text → summary field present", "summary" in d, d)

# TC-13: Summarize-text returns original_length
check("TC-13", "Summarize-text returns original_length", "original_length" in d, d)

# ── Week 2: /product-summary/ ────────────────────────────────────

# TC-14: Valid product → verdict present
r = requests.get(f"{API}/product-summary/", params={"product": "Smartphone X"})
d = r.json()
check("TC-14", "Valid product → verdict present", "verdict" in d, d)

# TC-15: Valid product → pros and cons present
check("TC-15", "Valid product → pros list returned", "pros" in d, d)

# TC-16: Invalid product → error
r = requests.get(f"{API}/product-summary/", params={"product": "Nonexistent Product 999"})
d = r.json()
check("TC-16", "Invalid product → error message", "error" in d, d)

# ── Week 2: /analyze-batch/ with product filter ───────────────────

# TC-17: Batch upload with reviews.csv
try:
    with open("data/reviews.csv", "rb") as f:
        r = requests.post(f"{API}/analyze-batch/", files={"file": ("reviews.csv", f, "text/csv")})
    d = r.json()
    check("TC-17", "Batch CSV → 15 results returned", d.get("total_reviews") == 15, d)
except FileNotFoundError:
    print("[SKIP ⚠️] TC-17: data/reviews.csv not found — run from project root")

# TC-18: Batch upload → product_breakdown present
try:
    with open("data/reviews.csv", "rb") as f:
        r = requests.post(f"{API}/analyze-batch/", files={"file": ("reviews.csv", f, "text/csv")})
    d = r.json()
    check("TC-18", "Batch result → product_breakdown present", "product_breakdown" in d, d)
except FileNotFoundError:
    print("[SKIP ⚠️] TC-18: data/reviews.csv not found — run from project root")

# TC-19: Batch upload with product filter
try:
    with open("data/reviews.csv", "rb") as f:
        r = requests.post(
            f"{API}/analyze-batch/",
            files={"file": ("reviews.csv", f, "text/csv")},
            params={"product": "Laptop Pro 15"}
        )
    d = r.json()
    check("TC-19", "Batch with product filter → 3 results (Laptop Pro 15)", d.get("total_reviews") == 3, d)
except FileNotFoundError:
    print("[SKIP ⚠️] TC-19: data/reviews.csv not found — run from project root")

# TC-20: neutral_count present in batch response
try:
    with open("data/reviews.csv", "rb") as f:
        r = requests.post(f"{API}/analyze-batch/", files={"file": ("reviews.csv", f, "text/csv")})
    d = r.json()
    check("TC-20", "Batch result → neutral_count present", "neutral_count" in d, d)
except FileNotFoundError:
    print("[SKIP ⚠️] TC-20: data/reviews.csv not found — run from project root")

# ── Week 3: /health/ ──────────────────────────────────────────────

# TC-21: Health check returns status ok
r = requests.get(f"{API}/health/")
d = r.json()
check("TC-21", "GET /health/ → status ok", d.get("status") == "ok", d)

# TC-22: Health check reports dataset_rows
check("TC-22", "GET /health/ → dataset_rows present", "dataset_rows" in d, d)

# ── Week 3: /history/ ────────────────────────────────────────────

# TC-23: Log an analysis, then confirm it shows up in history
requests.post(f"{API}/analyze/", params={"review": "The screen quality is amazing on this device"})
r = requests.get(f"{API}/history/", params={"limit": 5})
d = r.json()
check("TC-23", "POST /analyze/ then GET /history/ → history not empty", d.get("count", 0) > 0, d)

# TC-24: History filter by an unused sentiment/product returns empty, not an error
r = requests.get(f"{API}/history/", params={"product": "Nonexistent Product 999"})
d = r.json()
check("TC-24", "GET /history/ with unmatched filter → empty list, no error", d.get("count") == 0 and "error" not in d, d)

# TC-25: Clear history, then confirm it's empty
r = requests.delete(f"{API}/history/")
d = r.json()
check("TC-25", "DELETE /history/ → success message", "message" in d, d)

r = requests.get(f"{API}/history/")
d = r.json()
check("TC-26", "GET /history/ after clear → count is 0", d.get("count") == 0, d)

# ── Week 3: /export-report/ ──────────────────────────────────────

# TC-27: Export report (txt) for a valid product
r = requests.get(f"{API}/export-report/", params={"product": "Smartphone X", "format": "txt"})
is_file = r.headers.get("content-type", "").startswith("text/plain")
check("TC-27", "GET /export-report/ txt → file response", is_file, r.headers.get("content-type"))

# TC-28: Export report (csv) for a valid product
r = requests.get(f"{API}/export-report/", params={"product": "Smartphone X", "format": "csv"})
is_csv = r.headers.get("content-type", "").startswith("text/csv")
check("TC-28", "GET /export-report/ csv → file response", is_csv, r.headers.get("content-type"))

# TC-29: Export report for a non-existent product → JSON error, not a crash
r = requests.get(f"{API}/export-report/", params={"product": "Nonexistent Product 999"})
d = r.json()
check("TC-29", "GET /export-report/ invalid product → error", "error" in d, d)

# ── Week 3: boundary / garbage input hardening ────────────────────

# TC-30: CSV missing the 'review' column → clean error, no 500
bad_csv = io.BytesIO(b"product,comment\nSmartphone X,Great phone\n")
r = requests.post(f"{API}/analyze-batch/", files={"file": ("bad.csv", bad_csv, "text/csv")})
d = r.json()
check("TC-30", "Batch CSV missing 'review' column → error, not a crash", "error" in d, d)

# TC-31: CSV with an empty review row mixed with valid rows → skipped_rows reported
mixed_csv = io.BytesIO(
    b"product,review\nSmartphone X,\"Excellent camera and battery\"\nSmartphone X,\"\"\nSmartphone X,\"Worst screen ever\"\n"
)
r = requests.post(f"{API}/analyze-batch/", files={"file": ("mixed.csv", mixed_csv, "text/csv")})
d = r.json()
check("TC-31", "Batch CSV with 1 empty row → skipped_rows >= 1", d.get("skipped_rows", 0) >= 1, d)

# TC-32: Very long paragraph (5000+ words) still returns a 3-sentence summary
long_paragraph = ("This product works well and I am happy with it overall. " * 700)
r = requests.post(f"{API}/summarize-text/", params={"text": long_paragraph})
d = r.json()
check("TC-32", "5000+ word paragraph → summary still returned", "summary" in d, {"original_length": d.get("original_length")})

# TC-33: Review text that is only emojis/numbers → still returns a sentiment, no crash
r = requests.post(f"{API}/analyze/", params={"review": "12345 😀😀😀 !!! 000"})
d = r.json()
check("TC-33", "Emoji/number-only review → no crash, sentiment present", "sentiment" in d, d)

print()
print("=" * 60)
print(f"  Results: {passed} passed | {failed} failed | {passed + failed} total")
print("=" * 60)
