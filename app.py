"""
Phase 6: Streamlit App - BizGuard AI
Upload a CSV of daily business data and get a ranked alert list.
Or click "Generate demo data" to try it instantly with synthetic cafe data.

Run:  streamlit run app.py
"""
import streamlit as st
import pandas as pd

from detect import detect, METRIC_LABELS
from categorize import categorize, CATEGORY_LABELS
from prioritize import prioritize
from explain import explain


st.set_page_config(page_title="BizGuard AI", page_icon=None, layout="centered")

# Initialize session state
if "df" not in st.session_state:
    st.session_state.df = None

# --- Header ---
st.markdown(
    "<h2 style='margin-bottom:0;'>BizGuard AI</h2>"
    "<p style='color:gray;margin-top:4px;'>"
    "Upload your daily business data and get a ranked watch list."
    "</p>",
    unsafe_allow_html=True,
)

# --- Two ways to load data ---
col1, col2 = st.columns([2, 1])

with col1:
    uploaded = st.file_uploader("Upload your CSV file", type=["csv"])

with col2:
    st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
    demo_clicked = st.button("Use demo cafe data")

# --- Load data into session ---
if uploaded is not None:
    st.session_state.df = pd.read_csv(uploaded)
    st.success(f"Loaded {len(st.session_state.df)} rows from {uploaded.name}")

if demo_clicked:
    from data_generator import generate_cafe_data
    # Generate in memory - returns a DataFrame, no file needed
    st.session_state.df = generate_cafe_data()
    st.success("Demo data loaded: 90 days of cafe data with 4 planted problems.")

# --- Process and display ---
if st.session_state.df is not None:
    df = st.session_state.df

    with st.spinner("Analyzing your data..."):
        events = detect(df)
        ranked = prioritize(events, df)

    if not ranked:
        st.info("No issues detected. Your business looks healthy!")
    else:
        st.subheader(f"Today's watch list ({len(ranked)} issues found)")

        for i, item in enumerate(ranked, 1):
            event = item["event"]
            result = explain(
                event, item["category"], item["score"],
                item["financial_impact"], df
            )

            color = result["priority_color"]
            st.markdown(
                f"""
                <div style="border-left:4px solid {color};
                            padding:12px 16px;margin-bottom:12px;
                            background:#1a1a1a;border-radius:0 8px 8px 0;">
                  <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                    <span style="font-size:11px;font-weight:600;padding:2px 10px;
                                 border-radius:10px;color:white;background:{color};">
                      {result['priority']}
                    </span>
                    <span style="font-size:12px;color:gray;">
                      {result['category_label']} - score {item['score']}/100
                    </span>
                  </div>
                  <p style="font-size:14px;font-weight:600;margin:0 0 6px;color:white;">
                    {result['metric_label']} {event['direction']} {event['deviation_pct']}%
                  </p>
                  <p style="font-size:13px;color:#ccc;margin:0 0 6px;line-height:1.5;">
                    {result['text']}
                  </p>
                  <p style="font-size:12px;color:#5DCAA5;margin:0;">
                    <b>Try this:</b> {result['action']}
                  </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # --- Data preview ---
    with st.expander("View raw data (last 14 days)"):
        st.dataframe(df.tail(14), use_container_width=True)

    # --- Simple chart ---
    st.subheader("30-day trend")
    chart_metric = st.selectbox(
        "Select metric to chart",
        list(METRIC_LABELS.keys()),
        format_func=lambda x: METRIC_LABELS[x],
    )
    chart_data = df.tail(30)[["date", chart_metric]].set_index("date")
    st.line_chart(chart_data, height=250)
else:
    st.markdown("---")
    st.info("Upload a CSV file above, or click **Use demo cafe data** to try it instantly.")
