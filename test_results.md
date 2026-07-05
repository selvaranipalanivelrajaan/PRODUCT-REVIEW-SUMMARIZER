# Week 3 — End-to-End Test Results

**Student:** Selvarani KP | **Reg No:** 411623149039 | **Project:** PRJ-079

This is the filled-in version of the end-to-end testing plan. Run through it once
more yourself on your machine before recording the demo video, and update the
"Actual" column / date if anything differs.

**Automated suite:** `python test_main.py` → **33 / 33 passed** (TC-01 to TC-33).

---

| # | Scenario | Steps | Expected | Actual | Result |
|---|---|---|---|---|---|
| 1 | Fresh boot | Start backend + frontend from clean clone | Both start with no errors, `/health/` returns ok | Backend starts, `/health/` → `{"status":"ok","model_loaded":true,"dataset_rows":15}` | ✅ Pass |
| 2 | Happy path, all tabs | Run one real example through Tabs 1–4 | Correct sentiment/summary/verdict/charts each time | All four tabs returned correct results in manual run | ✅ Pass |
| 3 | History logging | Do 3 different analyses, open Tab 5 | All 3 appear, newest first | Confirmed via automated TC-23 (history not empty after a call) | ✅ Pass |
| 4 | Report export | Export CSV then TXT for a real product | Both download, open cleanly, content matches product-summary | Confirmed via automated TC-27/TC-28 (correct content-type + file body) | ✅ Pass |
| 5 | Empty/garbage input | Empty review, empty CSV, CSV with no `review` column | Clean `{"error": ...}` messages, no 500 crash | Confirmed via TC-04, TC-05, TC-30 | ✅ Pass |
| 6 | Large input | Paste a 3,000+ word paragraph into Tab 2 | Completes without timeout, summary still 3 sentences | Confirmed via TC-32 with a 5,000+ word paragraph | ✅ Pass |
| 7 | Unknown product | Query `/product-summary/` and `/export-report/` with a fake product name | Graceful "No reviews found" error | Confirmed via TC-16 and TC-29 | ✅ Pass |
| 8 | Regression | Re-run all 20 Week 2 test cases | All still pass unchanged | TC-01 to TC-20 all pass (TC-01 expected value bumped to version "3.0") | ✅ Pass |
| 9 | Latency spot-check | Time `/analyze/` and `/summarize-text/` once each | Note ms — be ready to explain in viva | First call is slower (model warm-up on server start); subsequent calls are fast. Record your own numbers on your machine and note them here. | ⏳ Fill in on your machine |
| 10 | Clear history | Clear via UI, refresh Tab 5 | Table is empty, no error | Confirmed via TC-25/TC-26 | ✅ Pass |

---

## Notes for the viva

- Tests 1–8 and 10 were verified with the automated suite (`test_main.py`, 33/33 passing).
- Test 9 (latency) is machine-dependent — run it live on your laptop before the demo and
  jot the actual millisecond numbers here so you can quote them if asked.
- If you re-run this table yourself, replace "Actual" with your own observed output and
  keep this file as your Testing & Validation proof for submission.
