"""
Product Review Summarizer — Week 3 Frontend (app.py)
PRJ-079 | Student: Selvarani KP

Five tabs:
  Tab 1 — Single review sentiment (Week 1, improved badge + NEUTRAL)
  Tab 2 — Summarize long text (Week 2)
  Tab 3 — Product dashboard (Week 2)
  Tab 4 — Batch CSV analysis (Week 1/2, extended)
  Tab 5 — History & Reports (NEW, Week 3)

Week 3 also adds a sidebar backend/model status indicator and a
consistent toast/error style across all tabs.
"""

import streamlit as st
import requests
import pandas as pd
import os

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Product Review Summarizer",
    page_icon="🛍️",
    layout="centered"
)

st.title("🛍️ Product Review Sentiment Analyzer")
st.markdown("Analyze customer reviews using AI — type a review, paste a paragraph, explore by product, or upload a CSV file.")


# ── SIDEBAR: backend/model status (Week 3) ───────────────────────────────────
with st.sidebar:
    st.header("⚙️ System Status")
    try:
        health = requests.get(f"{API_URL}/health/", timeout=5).json()
        if health.get("status") == "ok":
            st.success("Backend: Connected ✅")
        else:
            st.warning("Backend: Responding, but not healthy ⚠️")
        if health.get("model_loaded"):
            st.success("Model: Loaded ✅")
        else:
            st.error("Model: Not loaded ❌")
        st.caption(f"Dataset rows: {health.get('dataset_rows', 'N/A')}")
    except Exception:
        st.error("Backend: Not reachable ❌")
        st.caption(f"Expected at: {API_URL}")
    st.divider()
    st.caption("PRJ-079 · Selvarani KP · 411623149039")


def show_error(prefix: str, err: Exception):
    """Consistent error style: short message + details in an expander."""
    st.error(f"{prefix} Make sure the backend is running.")
    with st.expander("Show technical details"):
        st.exception(err)


# ── TAB LAYOUT ───────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Single Review",
    "Summarize Text",
    "Product Dashboard",
    "Batch Upload (CSV)",
    "History & Reports"
])


# ── TAB 1: SINGLE REVIEW (Week 1 style, now handles NEUTRAL) ─────────────────
with tab1:
    st.subheader("Analyze a Single Review")
    review = st.text_area(
        "Enter your product review here:",
        height=120,
        placeholder="e.g. The battery life is amazing and the camera is clear!"
    )

    if st.button("Analyze", key="single"):
        if review.strip() == "":
            st.warning("Please enter a review before clicking Analyze.")
        else:
            with st.spinner("Analyzing..."):
                try:
                    response = requests.post(f"{API_URL}/analyze/", params={"review": review})
                    result = response.json()

                    if "error" in result:
                        st.error(result["error"])
                    else:
                        sentiment = result["sentiment"]
                        score = result["score"]

                        if sentiment == "POSITIVE":
                            st.success("Sentiment: ✅ POSITIVE")
                        elif sentiment == "NEGATIVE":
                            st.error("Sentiment: ❌ NEGATIVE")
                        else:
                            st.info("Sentiment: ⚠️ NEUTRAL")

                        st.metric(label="Confidence Score", value=f"{score:.2%}")
                        st.json(result)
                        st.toast("Analysis complete", icon="✅")
                except Exception as e:
                    show_error("Could not connect to API.", e)


# ── TAB 2: SUMMARIZE TEXT (Week 2) ───────────────────────────────────────────
with tab2:
    st.subheader("Summarize a Long Review or Paragraph")
    st.info("Paste a long customer review (at least 20 words) and get an AI-generated summary with sentiment.")

    long_text = st.text_area(
        "Paste your review or paragraph here:",
        height=200,
        placeholder="e.g. I bought this laptop three months ago and have been using it daily for work and gaming. "
                    "The performance is excellent — it handles multitasking without any lag. "
                    "The display is sharp and bright, making video calls look professional. "
                    "However, the battery life is disappointing, lasting only 4 hours under load. "
                    "The keyboard is comfortable but the trackpad sometimes misregisters clicks. "
                    "Overall I am satisfied with the purchase despite the battery issue."
    )

    if st.button("Summarize", key="summarize_text"):
        if long_text.strip() == "":
            st.warning("Please paste some text before clicking Summarize.")
        elif len(long_text.split()) < 20:
            st.warning("Text is too short. Please enter at least 20 words.")
        else:
            with st.spinner("Generating summary... this may take a moment."):
                try:
                    response = requests.post(
                        f"{API_URL}/summarize-text/",
                        params={"text": long_text}
                    )
                    result = response.json()

                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.subheader("📝 AI Summary")
                        st.write(result["summary"])

                        sentiment = result["sentiment"]
                        score = result["score"]

                        if sentiment == "POSITIVE":
                            st.success(f"Overall Sentiment: ✅ POSITIVE")
                        elif sentiment == "NEGATIVE":
                            st.error(f"Overall Sentiment: ❌ NEGATIVE")
                        else:
                            st.info(f"Overall Sentiment: ⚠️ NEUTRAL")

                        col1, col2 = st.columns(2)
                        col1.metric("Confidence Score", f"{score:.2%}")
                        col2.metric("Original Word Count", result["original_length"])

                        st.json(result)
                        st.toast("Summary generated", icon="✅")
                except Exception as e:
                    show_error("Could not connect to API.", e)


# ── TAB 3: PRODUCT DASHBOARD (Week 2) ────────────────────────────────────────
with tab3:
    st.subheader("Product Dashboard — Pros, Cons & Verdict")
    st.info("Select a product to see its overall verdict, sentiment breakdown, and top pros/cons extracted from reviews.")

    # Fetch product list from API
    try:
        prod_response = requests.get(f"{API_URL}/products/")
        products_data = prod_response.json()
        product_list = products_data.get("products", [])
    except Exception:
        product_list = []

    if not product_list:
        st.warning("Could not fetch product list. Make sure the backend is running.")
    else:
        selected_product = st.selectbox("Choose a product:", product_list)

        if st.button("Get Product Summary", key="product_summary"):
            with st.spinner(f"Fetching summary for {selected_product}..."):
                try:
                    response = requests.get(
                        f"{API_URL}/product-summary/",
                        params={"product": selected_product}
                    )
                    result = response.json()

                    if "error" in result:
                        st.error(result["error"])
                    else:
                        # Verdict banner
                        verdict = result["verdict"]
                        if "Recommended ✅" in verdict:
                            st.success(f"Verdict: {verdict}")
                        elif "Not Recommended ❌" in verdict:
                            st.error(f"Verdict: {verdict}")
                        else:
                            st.warning(f"Verdict: {verdict}")

                        # Sentiment counts
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Total Reviews", result["total_reviews"])
                        col2.metric("Positive ✅", result["positive_count"])
                        col3.metric("Negative ❌", result["negative_count"])
                        col4.metric("Neutral ⚠️", result["neutral_count"])

                        # Donut chart using st.bar_chart (same style as Week 1 chart)
                        chart_data = pd.DataFrame({
                            "Sentiment": ["POSITIVE", "NEGATIVE", "NEUTRAL"],
                            "Count": [
                                result["positive_count"],
                                result["negative_count"],
                                result["neutral_count"]
                            ]
                        })
                        st.bar_chart(chart_data.set_index("Sentiment"))

                        # Pros and Cons side by side
                        st.subheader("Top Pros & Cons")
                        col_pros, col_cons = st.columns(2)

                        with col_pros:
                            st.markdown("**👍 Top Pros**")
                            pros = result.get("pros", [])
                            if pros:
                                for p in pros:
                                    st.markdown(f"- {p}")
                            else:
                                st.write("No strong pros found.")

                        with col_cons:
                            st.markdown("**👎 Top Cons**")
                            cons = result.get("cons", [])
                            if cons:
                                for c in cons:
                                    st.markdown(f"- {c}")
                            else:
                                st.write("No strong cons found.")

                        st.json(result)
                        st.toast("Product summary loaded", icon="✅")
                except Exception as e:
                    show_error("Could not connect to API.", e)


# ── TAB 4: BATCH CSV (Week 1/2 extended — filter + breakdown) ────────────────
with tab4:
    st.subheader("Batch Analyze from CSV File")
    st.info(
        "Upload a CSV with a review text column such as **'review'**, **'tweet_text'**, "
        "**'full_text'**, **'text'**, **'content'**, **'comment'**, or **'message'** "
        "(and optionally **'product'**)."
    )

    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

    product_filter = st.text_input(
        "Filter by product name (optional):",
        placeholder="e.g. Laptop Pro 15"
    )

    if uploaded_file is not None:
        df_preview = pd.read_csv(uploaded_file)
        st.write("Preview of uploaded file:")
        st.dataframe(df_preview.head())

        uploaded_file.seek(0)  # reset pointer for sending to API

        if st.button("Analyze All Reviews", key="batch"):
            with st.spinner("Analyzing all reviews... this may take a moment."):
                try:
                    params = {}
                    if product_filter.strip():
                        params["product"] = product_filter.strip()

                    response = requests.post(
                        f"{API_URL}/analyze-batch/",
                        files={"file": ("reviews.csv", uploaded_file, "text/csv")},
                        params=params
                    )
                    result = response.json()

                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.success(f"Analysis complete! {result['total_reviews']} reviews processed.")
                        detected_review_column = result.get("detected_review_column")
                        if detected_review_column:
                            st.caption(f"Detected review column: {detected_review_column}")
                        skipped = result.get("skipped_rows", 0)
                        if skipped:
                            st.warning(f"⚠️ {skipped} row(s) were skipped (empty or malformed) and did not affect the results.")

                        # Sentiment summary metrics
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Total Reviews", result["total_reviews"])
                        col2.metric("Positive ✅", result["positive_count"])
                        col3.metric("Negative ❌", result["negative_count"])
                        col4.metric("Neutral ⚠️", result.get("neutral_count", 0))

                        # Overall sentiment bar chart (same as Week 1)
                        st.subheader("Sentiment Distribution")
                        chart_data = pd.DataFrame({
                            "Sentiment": ["POSITIVE", "NEGATIVE", "NEUTRAL"],
                            "Count": [
                                result["positive_count"],
                                result["negative_count"],
                                result.get("neutral_count", 0)
                            ]
                        })
                        st.bar_chart(chart_data.set_index("Sentiment"))

                        # Per-product breakdown chart
                        breakdown = result.get("product_breakdown", {})
                        if breakdown and len(breakdown) > 1:
                            st.subheader("Per-Product Breakdown")
                            bd_df = pd.DataFrame(breakdown).T.fillna(0).astype(int)
                            bd_df.index.name = "Product"
                            st.bar_chart(bd_df)

                        # Results table
                        st.subheader("Detailed Results")
                        results_df = pd.DataFrame(result["results"])
                        st.dataframe(results_df)
                        st.toast("Batch analysis complete", icon="✅")

                except Exception as e:
                    show_error("Could not connect to API.", e)


# ── TAB 5: HISTORY & REPORTS (NEW — Week 3) ──────────────────────────────────
with tab5:
    st.subheader("📜 History & Reports")
    st.info("Review everything analyzed so far, and download a pros/cons report for any product.")

    st.markdown("#### Recent Activity")

    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    with col_f1:
        try:
            prod_resp = requests.get(f"{API_URL}/products/", timeout=5)
            hist_product_list = ["All"] + prod_resp.json().get("products", [])
        except Exception:
            hist_product_list = ["All"]
        history_product_filter = st.selectbox("Filter by product:", hist_product_list, key="hist_product_filter")
    with col_f2:
        history_sentiment_filter = st.selectbox(
            "Filter by sentiment:",
            ["All", "POSITIVE", "NEGATIVE", "NEUTRAL"],
            key="hist_sentiment_filter"
        )
    with col_f3:
        history_limit = st.number_input("Show last N", min_value=5, max_value=200, value=20, step=5)

    if st.button("Refresh History", key="refresh_history"):
        st.session_state["_refresh_history_clicked"] = True

    try:
        params = {"limit": int(history_limit)}
        if history_product_filter != "All":
            params["product"] = history_product_filter
        if history_sentiment_filter != "All":
            params["sentiment"] = history_sentiment_filter

        hist_resp = requests.get(f"{API_URL}/history/", params=params, timeout=10)
        hist_data = hist_resp.json()

        if "error" in hist_data:
            st.error(hist_data["error"])
        else:
            records = hist_data.get("history", [])
            st.caption(f"Showing {len(records)} record(s).")
            if records:
                hist_df = pd.DataFrame(records)
                st.dataframe(hist_df, use_container_width=True)
            else:
                st.write("No history yet — run an analysis in one of the other tabs first.")
    except Exception as e:
        show_error("Could not load history.", e)

    st.divider()

    # ── Clear history ─────────────────────────────────────────────────────
    st.markdown("#### Reset")
    confirm_clear = st.checkbox("I understand this will permanently delete all logged history.")
    if st.button("🗑️ Clear History", key="clear_history", disabled=not confirm_clear):
        try:
            clear_resp = requests.delete(f"{API_URL}/history/", timeout=5)
            clear_result = clear_resp.json()
            if "error" in clear_result:
                st.error(clear_result["error"])
            else:
                st.success(clear_result.get("message", "History cleared."))
                st.toast("History cleared", icon="🗑️")
        except Exception as e:
            show_error("Could not clear history.", e)

    st.divider()

    # ── Download report ───────────────────────────────────────────────────
    st.markdown("#### Download a Product Report")
    try:
        prod_resp2 = requests.get(f"{API_URL}/products/", timeout=5)
        report_product_list = prod_resp2.json().get("products", [])
    except Exception:
        report_product_list = []

    if not report_product_list:
        st.warning("Could not fetch product list. Make sure the backend is running.")
    else:
        col_r1, col_r2 = st.columns([3, 1])
        with col_r1:
            report_product = st.selectbox("Choose a product:", report_product_list, key="report_product")
        with col_r2:
            report_format = st.radio("Format", ["txt", "csv"], key="report_format", horizontal=True)

        if st.button("Generate Report", key="generate_report"):
            with st.spinner("Building report..."):
                try:
                    report_resp = requests.get(
                        f"{API_URL}/export-report/",
                        params={"product": report_product, "format": report_format},
                        timeout=10
                    )
                    if report_resp.headers.get("content-type", "").startswith("application/json"):
                        # An error was returned as JSON instead of a file
                        err = report_resp.json()
                        st.error(err.get("error", "Could not generate report."))
                    else:
                        mime = "text/csv" if report_format == "csv" else "text/plain"
                        filename = f"{report_product.replace(' ', '_')}_report.{report_format}"
                        st.download_button(
                            label=f"⬇️ Download {filename}",
                            data=report_resp.content,
                            file_name=filename,
                            mime=mime,
                            key="download_report_btn"
                        )
                        st.success("Report ready — click above to download.")
                        st.toast("Report generated", icon="📄")
                except Exception as e:
                    show_error("Could not generate report.", e)
