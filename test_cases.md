# Week 3 Test Cases — Product Review Summarizer (PRJ-079)

**Student:** Selvarani KP  
**Reg No:** 411623149039  
**Week 2 Testing Plan:** Check output quality on varied texts, boundary cases, and sample latency.  
**Week 3 Testing Plan:** Run end-to-end tests, fix failure cases, and prepare presentation-ready examples.

This file documents all 33 automated test cases (TC-01 to TC-33). TC-01 to TC-20 are
Week 1/2 regression tests (still required to pass). TC-21 to TC-33 are new Week 3 tests
for history, report export, health check, and hardened error handling. See also
`test_results_week3.md` for the manually-run end-to-end scenario table.

---

## How to Run

```bash
# Terminal 1 — Start backend
uvicorn main:app --reload

# Terminal 2 — Run tests
python test_main.py
```

---

## Test Cases

| TC   | Endpoint            | Input / Condition                       | Expected Output                        | Category         |
|------|---------------------|-----------------------------------------|----------------------------------------|------------------|
| TC-01 | GET /              | Health check                            | version = "2.0"                        | Regression       |
| TC-02 | POST /analyze/     | Positive review text                    | sentiment = POSITIVE                   | Regression       |
| TC-03 | POST /analyze/     | Negative review text                    | sentiment = NEGATIVE                   | Regression       |
| TC-04 | POST /analyze/     | Empty string                            | error field in response                | Boundary         |
| TC-05 | POST /analyze/     | Whitespace only                         | error field in response                | Boundary         |
| TC-06 | POST /analyze/     | Any review                              | 0.0 ≤ score ≤ 1.0                     | Data Validation  |
| TC-07 | POST /analyze/     | Neutral text                            | sentiment field present                | Regression       |
| TC-08 | GET /products/     | No params                               | products is a list                     | Week 2 — New     |
| TC-09 | GET /products/     | No params                               | count > 0                              | Week 2 — New     |
| TC-10 | POST /summarize-text/ | Text with < 20 words               | error field in response                | Boundary         |
| TC-11 | POST /summarize-text/ | Empty string                        | error field in response                | Boundary         |
| TC-12 | POST /summarize-text/ | Long paragraph (≥ 20 words)        | summary field present                  | Week 2 — New     |
| TC-13 | POST /summarize-text/ | Long paragraph                     | original_length field present          | Week 2 — New     |
| TC-14 | GET /product-summary/ | product = "Smartphone X"          | verdict field present                  | Week 2 — New     |
| TC-15 | GET /product-summary/ | product = "Smartphone X"          | pros list returned                     | Week 2 — New     |
| TC-16 | GET /product-summary/ | Non-existent product              | error field in response                | Boundary         |
| TC-17 | POST /analyze-batch/  | Upload data/reviews.csv           | total_reviews = 15                     | Regression       |
| TC-18 | POST /analyze-batch/  | Upload data/reviews.csv           | product_breakdown present              | Week 2 — New     |
| TC-19 | POST /analyze-batch/  | product filter = "Laptop Pro 15"  | total_reviews = 3                      | Week 2 — New     |
| TC-20 | POST /analyze-batch/  | Upload data/reviews.csv           | neutral_count present                  | Week 2 — New     |
| TC-21 | GET /health/        | No params                               | status = "ok"                          | Week 3 — New     |
| TC-22 | GET /health/        | No params                               | dataset_rows field present             | Week 3 — New     |
| TC-23 | GET /history/       | After 1 analyze call                    | history not empty                      | Week 3 — New     |
| TC-24 | GET /history/       | Filter by non-existent product          | empty list, no error                   | Boundary         |
| TC-25 | DELETE /history/    | Clear all history                       | message field present                  | Week 3 — New     |
| TC-26 | GET /history/       | After clearing history                  | count = 0                              | Week 3 — New     |
| TC-27 | GET /export-report/ | product="Smartphone X", format=txt      | file response (text/plain)             | Week 3 — New     |
| TC-28 | GET /export-report/ | product="Smartphone X", format=csv      | file response (text/csv)               | Week 3 — New     |
| TC-29 | GET /export-report/ | Non-existent product                    | error field in response                | Boundary         |
| TC-30 | POST /analyze-batch/| CSV missing 'review' column             | error, not a 500 crash                 | Boundary         |
| TC-31 | POST /analyze-batch/| CSV with 1 empty review row (of 3)      | skipped_rows ≥ 1                       | Boundary         |
| TC-32 | POST /summarize-text/| 5000+ word paragraph                   | summary still returned                 | Boundary         |
| TC-33 | POST /analyze/      | Review is only emojis/numbers           | no crash, sentiment field present      | Boundary         |

---

## Expected Results Summary

- **Regression tests (TC-01 to TC-07, TC-17):** All Week 1 behaviour preserved.
- **Boundary tests (TC-04, TC-05, TC-10, TC-11, TC-16, TC-24, TC-29 to TC-33):** All return a clear `error` key or a graceful fallback — never a raw 500 crash.
- **Week 2 tests (TC-08 to TC-09, TC-12 to TC-15, TC-18 to TC-20):** Summarization, product filtering, and batch breakdown work correctly.
- **Week 3 tests (TC-21 to TC-33):** History logging/filtering/clearing, report export (CSV + TXT), health check, and hardened batch/text processing all work correctly.

---

## Manual Testing Checklist

- [ ] Tab 1 — Single review: positive → green badge, negative → red badge, neutral → blue badge
- [ ] Tab 2 — Summarize text: paste 6+ sentence review → AI summary appears, word count shown
- [ ] Tab 3 — Product Dashboard: select product from dropdown → verdict banner, bar chart, pros/cons
- [ ] Tab 4 — Batch CSV: upload `data/reviews.csv` → 15 results, bar chart, per-product breakdown
- [ ] Tab 4 — Batch filter: enter "Laptop Pro 15" → only 3 rows in results table
- [ ] Tab 5 — History: run a few analyses in other tabs, confirm they appear newest-first
- [ ] Tab 5 — History filters: filter by product and by sentiment, confirm results narrow correctly
- [ ] Tab 5 — Clear History: checkbox + button clears the table, confirmed empty on refresh
- [ ] Tab 5 — Reports: download a TXT and a CSV report for a product, open both, confirm content matches Tab 3
- [ ] Sidebar: shows "Backend: Connected" and "Model: Loaded" when servers are running
- [ ] Sidebar: shows "Backend: Not reachable" when the FastAPI server is stopped
- [ ] Backend `/products/` endpoint: returns 5 unique products from the default dataset
- [ ] Backend `/health/` endpoint: returns `status: ok` and the correct dataset row count
