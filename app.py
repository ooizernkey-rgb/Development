"""BizGuard AI multi-view CSV business health dashboard."""
import streamlit as st
import pandas as pd
import numpy as np
import io
import os
from difflib import SequenceMatcher
from detect import detect, METRIC_LABELS, METRICS
from prioritize import prioritize
from explain import explain

st.set_page_config(page_title="BizGuard AI", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")
REQUIRED = ["date", *METRICS]

def get_openai_key():
    """Read the API key without displaying it; supports .env and PowerShell-style lines."""
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key.strip().strip('"').strip("'")
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    try:
        with open(env_path, "r", encoding="utf-8") as env_file:
            for line in env_file:
                text = line.strip()
                if text.startswith("$env:OPENAI_API_KEY=") or text.startswith("OPENAI_API_KEY="):
                    return text.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return None

def get_gemini_key():
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if key:
        return key.strip().strip('"').strip("'")
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    try:
        with open(env_path, "r", encoding="utf-8") as env_file:
            for line in env_file:
                text = line.strip()
                for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
                    if text.startswith(f"$env:{name}=") or text.startswith(f"{name}="):
                        return text.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return None

def ask_gemini(question, context):
    api_key = get_gemini_key()
    if not api_key:
        return None

def get_openrouter_key():
    key = os.getenv("OPENROUTER_API_KEY")
    if key:
        return key.strip().strip('"').strip("'")
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    try:
        with open(env_path, "r", encoding="utf-8") as env_file:
            for line in env_file:
                text = line.strip()
                if text.startswith("$env:OPENROUTER_API_KEY=") or text.startswith("OPENROUTER_API_KEY="):
                    return text.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return None

def ask_openrouter(question, context):
    api_key = get_openrouter_key()
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1", timeout=10.0)
        response = client.chat.completions.create(
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are BizGuard AI Advisor, a practical small-business coach. Give clear, actionable advice, state assumptions, and avoid claiming certainty for financial decisions."},
                {"role": "user", "content": f"Business context:\n{context}\n\nUser question:\n{question}"},
            ],
            temperature=0.3,
            max_tokens=512,
        )
        return response.choices[0].message.content
    except Exception as exc:
        st.session_state.advisor_error = str(exc)
        return None
    try:
        import google.genai as genai
        from google.genai import types
        client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=10000))
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        response = client.models.generate_content(
            model=model,
            contents=f"Business context:\n{context}\n\nUser question:\n{question}",
            config={
                "system_instruction": "You are BizGuard AI Advisor, a practical small-business coach. Give clear, actionable advice, state assumptions, and avoid claiming certainty for financial decisions.",
                "temperature": 0.3,
                "max_output_tokens": 512,
            },
        )
        return response.text
    except Exception as exc:
        st.session_state.advisor_error = str(exc)
        return None

def ask_openai(question, context):
    """Return an AI answer when configured; otherwise return None for local fallback."""
    api_key = get_openai_key()
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model="gpt-5-mini",
            instructions=("You are BizGuard AI Advisor, a practical small-business coach. "
                          "Answer the user's question clearly and concisely. Give actionable advice, "
                          "state assumptions, and do not claim certainty for financial decisions. "
                          "Use the connected business context when present."),
            input=f"Business context:\n{context}\n\nUser question:\n{question}",
        )
        return response.output_text
    except Exception as exc:
        st.session_state.advisor_error = str(exc)
        return None

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--bg:#0b0d12;--panel:#141821;--line:#252c39;--muted:#8992a4;--text:#f4f6fb;--purple:#7767f7;--green:#28d27b;--orange:#ffb547;--red:#ff6575}.stApp{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif}[data-testid='stSidebar']{background:#10131a;border-right:1px solid var(--line)}[data-testid='stSidebar']>div:first-child{padding:1.3rem 1rem}h1,h2,h3{font-family:'Space Grotesk',sans-serif;letter-spacing:-.03em}.brand{font-family:'Space Grotesk';font-size:1.25rem;font-weight:700;padding:0 .5rem 1.5rem;border-bottom:1px solid var(--line)}.brand span{color:var(--purple)}.brand small{display:block;color:var(--muted);font:400 .72rem 'DM Sans';margin-top:.35rem}.eyebrow{color:var(--purple);text-transform:uppercase;letter-spacing:.12em;font-size:.7rem;font-weight:700}.subtle{color:var(--muted)}.hero{padding:1rem 0 1.1rem}.hero h1{margin:.3rem 0 .45rem;font-size:2.15rem}.hero p{color:var(--muted);margin:0}.card{background:var(--panel);border:1px solid var(--line);border-radius:15px;padding:1rem 1.1rem;height:100%}.metric-label{color:var(--muted);font-size:.78rem;text-transform:uppercase;letter-spacing:.05em}.metric-value{font:700 1.55rem 'Space Grotesk';margin-top:.35rem}.metric-note{font-size:.75rem;color:var(--muted);margin-top:.25rem}.green{color:var(--green)}.orange{color:var(--orange)}.red{color:var(--red)}.section-title{font:600 1rem 'Space Grotesk';margin:1.6rem 0 .7rem}.issue{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--red);border-radius:12px;padding:1rem 1.1rem;margin:.7rem 0}.issue-title{font-weight:700;margin-bottom:.35rem}.issue-copy{color:#c0c6d3;font-size:.86rem;line-height:1.45}.badge{display:inline-block;padding:.18rem .55rem;border-radius:99px;font-size:.68rem;font-weight:700;margin-right:.35rem}.upload-box{background:linear-gradient(135deg,#17172c,#151b27);border:1px dashed #6860da;border-radius:16px;padding:1.2rem}.footer-note{color:#687184;font-size:.72rem;text-align:center;margin-top:2rem}
</style>""", unsafe_allow_html=True)

def normalize_columns(data):
    """Map common export labels to the model's canonical column names."""
    aliases = {
        "date": ["date", "day", "transaction_date", "report_date"],
        "daily_sales": ["daily_sales", "sales", "revenue", "daily revenue", "total sales", "gross sales", "income", "turnover"],
        "daily_expenses": ["daily_expenses", "expenses", "costs", "operating costs", "daily costs", "opex", "spend", "outgoings"],
        "customer_count": ["customer_count", "customers", "customer count", "transactions", "orders", "visitors", "guests", "footfall"],
        "inventory_value": ["inventory_value", "inventory", "inventory value", "stock value", "stock", "assets"],
    }
    lookup = {str(col).strip().lower().replace("-", "_").replace(" ", "_"): col for col in data.columns}
    rename = {}
    for canonical, options in aliases.items():
        for option in options:
            key = option.lower().replace("-", "_").replace(" ", "_")
            if key in lookup:
                rename[lookup[key]] = canonical
                break
        if canonical not in rename.values():
            # Handle headers such as "Monthly Revenue (RM)" or "No. of Guests".
            candidates = [(SequenceMatcher(None, canonical, key).ratio(), col) for key, col in lookup.items()]
            if candidates:
                similarity, column = max(candidates)
                if similarity >= 0.62:
                    rename[column] = canonical
    return data.rename(columns=rename)

def parse_uploaded_file(uploaded):
    try:
        suffix = uploaded.name.lower().rsplit(".", 1)[-1]
        raw = uploaded.getvalue()
        if suffix == "csv":
            data = pd.read_csv(io.BytesIO(raw))
        elif suffix in ("xlsx", "xls"):
            data = pd.read_excel(io.BytesIO(raw))
        elif suffix == "pdf":
            try:
                import pdfplumber
            except ImportError:
                st.error("PDF support needs the pdfplumber package. Install the project requirements and restart the app.")
                return None
            tables = []
            with pdfplumber.open(io.BytesIO(raw)) as pdf:
                for page in pdf.pages:
                    tables.extend(page.extract_tables() or [])
            if not tables:
                st.error("No table could be detected in this PDF. Export the report as a table or CSV and try again.")
                return None
            frames = []
            for table in tables:
                if len(table) > 1:
                    header = [str(x or "").strip() for x in table[0]]
                    frames.append(pd.DataFrame(table[1:], columns=header))
            if not frames:
                st.error("The PDF contained no readable data rows.")
                return None
            data = pd.concat(frames, ignore_index=True)
        else:
            st.error("Unsupported file type.")
            return None
        data = normalize_columns(data)
        missing = [c for c in REQUIRED if c not in data.columns]
        if missing:
            st.warning("Some columns could not be identified automatically. Map them below before analysis.")
            st.caption("This prevents the predictor from analyzing the wrong fields.")
            with st.form("column_mapping_form"):
                choices = ["-- not available --"] + list(data.columns)
                mappings = {}
                for canonical in missing:
                    label = {"date":"Date", "daily_sales":"Daily sales / revenue", "daily_expenses":"Daily expenses / costs", "customer_count":"Customer count / visitors", "inventory_value":"Inventory value / stock"}[canonical]
                    mappings[canonical] = st.selectbox(f"Which column is {label}?", choices, key=f"map_{canonical}")
                confirmed = st.form_submit_button("Confirm mapping and analyze", type="primary")
            if not confirmed or any(value == "-- not available --" for value in mappings.values()):
                st.info("Choose a source column for every required field to continue.")
                return None
            data = data.rename(columns={source: target for target, source in mappings.items()})
        data["date"] = pd.to_datetime(data["date"], errors="coerce")
        for col in METRICS:
            data[col] = pd.to_numeric(data[col].astype(str).str.replace(r"[^0-9.\-]", "", regex=True), errors="coerce")
        data = data.dropna(subset=REQUIRED).sort_values("date").reset_index(drop=True)
        if len(data) < 14: st.warning("Add at least 14 valid daily rows for reliable trends.")
        if len(data) < 7: st.error("At least 7 valid daily rows are required for analysis."); return None
        return data
    except Exception as exc:
        st.error(f"We could not read that CSV: {exc}")
        return None

def risk_score(items):
    return min(96, max(18, int(np.mean([x.get("score", 40) for x in items])))) if items else 12

def overview(df, ranked):
    risk = risk_score(ranked); level = "green" if risk < 35 else "orange" if risk < 65 else "red"; latest = df.iloc[-1]
    cash = float(df.tail(7)["daily_sales"].mean() - df.tail(7)["daily_expenses"].mean())
    st.markdown('<div class="hero"><div class="eyebrow">Business command center</div><h1>Good morning, operator.</h1><p>Your latest data has been translated into a clear view of cash health and business risk.</p></div>', unsafe_allow_html=True)
    cards = [("Overall risk", f"{risk}/100", "Low risk" if risk < 35 else "Needs attention", level), ("Weekly cash flow", f"RM {cash:,.0f}", "avg. sales less expenses", "green" if cash >= 0 else "red"), ("Daily sales", f"RM {latest['daily_sales']:,.0f}", "latest reported day", "green"), ("Open signals", str(len(ranked)), "detected from your data", "orange" if ranked else "green")]
    cols = st.columns(4)
    for col, (label, value, note, color) in zip(cols, cards):
        with col: st.markdown(f'<div class="card"><div class="metric-label">{label}</div><div class="metric-value {color}">{value}</div><div class="metric-note">{note}</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">12-month danger trajectory</div>', unsafe_allow_html=True)
    chart = pd.DataFrame({"Risk score": np.linspace(risk, max(8, risk - 5), 12)}, index=["Now"] + [f"M{i}" for i in range(1, 12)])
    st.line_chart(chart, height=230, color="#28d27b")
    left, right = st.columns([1.15, 1])
    with left:
        st.markdown('<div class="section-title">Recent activity</div>', unsafe_allow_html=True)
        if not ranked: st.success("No issues detected. Your business looks healthy!")
        for item in ranked[:4]:
            event = item["event"]; result = explain(event, item["category"], item["score"], item["financial_impact"], df); color = result["priority_color"]
            st.markdown(f'<div class="issue" style="border-left-color:{color}"><span class="badge" style="background:{color};color:#10131a">{result["priority"]}</span><span class="subtle">{result["category_label"]}</span><div class="issue-title">{result["metric_label"]} {event["direction"]} {event["deviation_pct"]}%</div><div class="issue-copy">{result["text"]}</div></div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="section-title">Cash health</div>', unsafe_allow_html=True)
        status = "Positive" if cash >= 0 else "At risk"; action = "Review your open signals and protect the current margin." if ranked else "Keep your data fresh and check back weekly."
        st.markdown(f'<div class="card"><div class="metric-label">Cash flow status</div><div class="metric-value green">{status}</div><div class="metric-note">Based on a 7-day rolling average</div><hr style="border-color:#252c39;border-width:1px 0 0;margin:1rem 0"><div class="metric-label">Next best action</div><p style="line-height:1.5">{action}</p></div>', unsafe_allow_html=True)

def upload_view():
    st.markdown('<div class="hero"><div class="eyebrow">Step 01 · Connect your data</div><h1>Upload your business data</h1><p>Start with a CSV export from your accounting or sales system. We will turn it into a plain-English health check.</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="upload-box">', unsafe_allow_html=True)
    uploaded = st.file_uploader("Drop your file here or browse files", type=["csv", "xlsx", "xls", "pdf"], help="Supported: CSV, Excel, and table-based PDF files. Required fields are date, sales, expenses, customers, and inventory.")
    st.markdown('</div>', unsafe_allow_html=True)
    st.write(""); c1, c2 = st.columns(2)
    with c1: st.markdown('<div class="card"><div class="metric-label">Recommended format</div><p>One row per day with five columns:</p><p class="subtle">date · daily_sales · daily_expenses · customer_count · inventory_value</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card"><div class="metric-label">Want to explore first?</div><p>Use a realistic cafe dataset with planted issues.</p>', unsafe_allow_html=True)
        if st.button("Load demo cafe data", use_container_width=True):
            from data_generator import generate_cafe_data
            st.session_state.df = generate_cafe_data(); st.session_state.view = "Overview"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    if uploaded is not None:
        parsed = parse_uploaded_file(uploaded)
        if parsed is not None:
            st.session_state.df = parsed; st.session_state.view = "Overview"; st.success(f"{uploaded.name} is ready — {len(parsed):,} days loaded."); st.rerun()

def insights_view(df, ranked):
    st.markdown('<div class="hero"><div class="eyebrow">Step 03 · Understand the why</div><h1>Business insights</h1><p>Signals ranked by likely impact, with a suggested next move for each one.</p></div>', unsafe_allow_html=True)
    if not ranked: st.success("No issues detected. Your business looks healthy!")
    for item in ranked:
        event = item["event"]; result = explain(event, item["category"], item["score"], item["financial_impact"], df); color = result["priority_color"]
        st.markdown(f'<div class="issue" style="border-left-color:{color}"><span class="badge" style="background:{color};color:#10131a">{result["priority"]}</span><span class="subtle">{result["category_label"]} · score {item["score"]}/100</span><div class="issue-title">{result["metric_label"]} {event["direction"]} {event["deviation_pct"]}%</div><div class="issue-copy">{result["text"]}</div><p class="green"><b>Try this:</b> {result["action"]}</p></div>', unsafe_allow_html=True)

def advisor_view(df):
    st.markdown('<div class="hero"><div class="eyebrow">Connected business guidance</div><h1>AI advisor</h1><p>Ask a practical business question. Advice is grounded in your uploaded data and future predictor assumptions when available.</p></div>', unsafe_allow_html=True)
    forecast = st.session_state.get("forecast_context", {})
    if df is not None:
        recent_sales = float(df["daily_sales"].tail(7).mean())
        recent_costs = float(df["daily_expenses"].tail(7).mean())
        open_signals = prioritize(detect(df), df)
        context_line = f"Recent 7-day average sales are RM {recent_sales:,.0f}/day and costs are RM {recent_costs:,.0f}/day, with {len(open_signals)} open signal(s)."
    else:
        open_signals = []
        context_line = "No uploaded dataset is connected yet."
    if forecast:
        context_line += f" The predictor currently estimates a {forecast['risk']}/100 risk, {forecast['runway'] or '12+'}-month runway, and RM {forecast['monthly_change']:,.0f} monthly cash change at month 12."
    if st.session_state.get("advisor_error"):
        st.warning(f"Gemini is currently unavailable: {st.session_state.advisor_error}")
    st.info(context_line)
    if "advisor_messages" not in st.session_state:
        st.session_state.advisor_messages = []
    for message in st.session_state.advisor_messages:
        with st.chat_message(message["role"]): st.markdown(message["content"])
    question = st.chat_input("Ask about cash flow, costs, growth, runway, or your business plan...")
    if question:
        st.session_state.advisor_messages.append({"role": "user", "content": question})
        q = question.lower()
        with st.spinner("Advisor is thinking..."):
            ai_answer = ask_openrouter(question, context_line)
        if ai_answer:
            st.session_state.advisor_messages.append({"role": "assistant", "content": ai_answer})
            st.rerun()
        advice = []
        if df is None and not forecast:
            advice.append("This is a general business question, so the answer below uses standard small-business principles rather than your company data.")
        if any(word in q for word in ["cash", "runway", "survive", "money"]):
            if forecast and forecast["monthly_change"] < 0:
                advice.append(f"Your forecast shows cash falling by about RM {abs(forecast['monthly_change']):,.0f} per month by month 12. Focus first on protecting cash: pause non-essential spending, shorten invoice collection time, and test a small price or sales improvement.")
            elif forecast:
                advice.append(f"Your forecast remains cash-positive with about RM {forecast['monthly_change']:,.0f} monthly change at month 12. Keep a buffer rather than treating the full surplus as spendable.")
            elif df is not None:
                advice.append(f"Your recent daily operating buffer is about RM {recent_sales - recent_costs:,.0f}. Track this weekly and keep enough cash to cover at least one slower month.")
        if any(word in q for word in ["cost", "expense", "spend", "budget"]):
            advice.append("Separate essential operating costs from discretionary spend, then set a monthly ceiling for each category. Review variances weekly instead of waiting until month-end.")
        if any(word in q for word in ["sales", "revenue", "growth", "customer"]):
            advice.append("Test one measurable growth action at a time: improve repeat purchases, raise average order value, or recover inactive customers. Compare the result against your baseline before scaling it.")
        if any(word in q for word in ["marketing", "advertis", "social media", "brand", "promote"]):
            advice.append("Start with one clearly defined customer segment and one measurable offer. Use a small test budget, track leads and conversions, then scale only the channel that produces profitable customers.")
        if any(word in q for word in ["price", "pricing", "charge", "margin"]):
            advice.append("Set price from your costs, target margin, and customer value rather than copying competitors alone. Test a small price change and watch conversion, average order value, and gross margin together.")
        if any(word in q for word in ["break even", "break-even", "profit"]):
            advice.append("Break-even sales equals fixed costs divided by contribution margin. List fixed costs, estimate variable cost per sale, and model a conservative, expected, and optimistic sales case.")
        if any(word in q for word in ["business plan", "plan", "strategy", "goal"]):
            advice.append("A useful business plan should state the target customer, problem, offer, acquisition channel, pricing, operating costs, and three measurable goals for the next 90 days.")
        if any(word in q for word in ["hire", "hiring", "employee", "staff", "team"]):
            advice.append("Hire against a specific bottleneck or revenue opportunity. Define the expected output, fully loaded monthly cost, and a 30/60/90-day success measure before committing.")
        if any(word in q for word in ["kpi", "metric", "measure", "track"]):
            advice.append("Begin with a small weekly scorecard: revenue, gross margin, cash balance, customer count, repeat rate, and one operational quality metric. A metric is useful only when it changes a decision.")
        if open_signals:
            top = open_signals[0]["event"]
            advice.append(f"Your highest-priority uploaded-data signal is {METRIC_LABELS.get(top['metric'], top['metric'])} moving {top['direction']} by {top['deviation_pct']}%. Investigate that before making a large new commitment.")
        if not advice:
            advice.append("A good next step is to define the decision you are making, its budget limit, and one success metric. I can then help you compare the trade-offs using your connected numbers.")
        answer = "\n\n".join(advice)
        st.session_state.advisor_messages.append({"role": "assistant", "content": answer})
        st.rerun()

def explorer_view(df):
    st.markdown('<div class="hero"><div class="eyebrow">Step 04 · Inspect the source</div><h1>Data explorer</h1><p>Check the rows behind your signals and inspect each operating metric.</p></div>', unsafe_allow_html=True)
    metric = st.selectbox("Metric to chart", METRICS, format_func=lambda x: METRIC_LABELS[x]); st.line_chart(df.set_index("date")[[metric]], height=300, color="#7767f7"); st.dataframe(df.tail(30), use_container_width=True, hide_index=True)

def predictor_view(df):
    """Interactive 12-month cash runway simulator based on user assumptions."""
    st.markdown('<div class="hero"><div class="eyebrow">Step 02 · Model the future</div><h1>Future risk & cash runway predictor</h1><p>Adjust the assumptions to see how your cash position and financial risk may change over the next 12 months.</p></div>', unsafe_allow_html=True)
    # The predictor is intentionally independent from the CSV workflow. If a
    # dataset exists, use it as a convenience starting point; otherwise use
    # editable example values so the user can model a business from scratch.
    defaults = {
        "cash": float(df["daily_sales"].tail(30).mean() * 30) if df is not None else 100000.0,
        "revenue": float(df["daily_sales"].tail(30).mean() * 30) if df is not None else 76000.0,
        "expenses": float(df["daily_expenses"].tail(30).mean() * 30) if df is not None else 54000.0,
    }
    left, right = st.columns([1.05, 1.35])
    with left:
        st.markdown('<div class="section-title">Core business numbers</div>', unsafe_allow_html=True)
        cash = st.number_input("Current cash in bank (RM)", min_value=0.0, value=round(defaults["cash"], 0), step=1000.0)
        revenue = st.number_input("Monthly revenue / sales (RM)", min_value=0.0, value=round(defaults["revenue"], 0), step=1000.0)
        expenses = st.number_input("Monthly operating costs (RM)", min_value=0.0, value=round(defaults["expenses"], 0), step=1000.0)
        debt = st.number_input("Existing debts / loans (RM)", min_value=0.0, value=0.0, step=1000.0)
        st.markdown('<div class="section-title">Future changes & market pressures</div>', unsafe_allow_html=True)
        sales_growth = st.slider("Expected sales growth / drop (%)", -50, 100, 0, 1)
        expense_inflation = st.slider("Expense inflation / price rise (%)", 0, 50, 3, 1)
        interest = st.slider("Interest rate on loans (%)", 0.0, 25.0, 6.0, 0.5)
    months = np.arange(1, 13)
    monthly_revenue = revenue * ((1 + sales_growth / 100) ** (months / 12))
    monthly_costs = expenses * ((1 + expense_inflation / 100) ** (months / 12))
    interest_cost = (debt * interest / 100) / 12
    net_cash = monthly_revenue - monthly_costs - interest_cost
    cash_balance = cash + np.cumsum(net_cash)
    risk_curve = np.clip(100 - (cash_balance / max(cash, 1) * 100), 5, 100)
    runway = next((int(months[i]) for i, value in enumerate(cash_balance) if value <= 0), None)
    overall = int(np.clip(np.mean(risk_curve), 5, 99))
    st.session_state.forecast_context = {
        "cash": cash, "revenue": revenue, "expenses": expenses, "debt": debt,
        "sales_growth": sales_growth, "expense_inflation": expense_inflation,
        "interest": interest, "runway": runway, "risk": overall,
        "ending_cash": float(cash_balance[-1]), "monthly_change": float(net_cash[-1]),
    }
    with right:
        st.markdown('<div class="section-title">Your forecast</div>', unsafe_allow_html=True)
        cards = [("Cash runway", f"{runway}-month" if runway else "12+ months", "until cash reaches zero", "red" if runway else "green"), ("12-month risk", f"{overall}/100", "Low risk" if overall < 35 else "Watch closely", "green" if overall < 35 else "orange"), ("Monthly cash change", f"RM {net_cash[-1]:,.0f}", "at month 12", "green" if net_cash[-1] >= 0 else "red")]
        cols = st.columns(3)
        for col, (label, value, note, color) in zip(cols, cards):
            with col: st.markdown(f'<div class="card"><div class="metric-label">{label}</div><div class="metric-value {color}">{value}</div><div class="metric-note">{note}</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Cash balance trajectory</div>', unsafe_allow_html=True)
        cash_chart = pd.DataFrame({"Cash balance": cash_balance, "Risk score": risk_curve}, index=[f"M{i}" for i in months])
        st.line_chart(cash_chart, height=310)
        if runway:
            st.error(f"Cash is projected to run out around month {runway}. Consider increasing revenue, reducing costs, or adding a funding buffer.")
        elif net_cash[-1] >= 0:
            st.success("Cash flowing: your assumptions keep the business cash-positive across the forecast.")
        else:
            st.warning("Your business remains above zero, but monthly cash flow is negative. Review the cost and growth assumptions.")
    with st.expander("View monthly forecast details"):
        detail = pd.DataFrame({"Month": months, "Revenue (RM)": monthly_revenue.round(0), "Costs + interest (RM)": (monthly_costs + interest_cost).round(0), "Net cash change (RM)": net_cash.round(0), "Ending cash (RM)": cash_balance.round(0), "Risk score": risk_curve.round(0)})
        st.dataframe(detail, use_container_width=True, hide_index=True)

if "df" not in st.session_state: st.session_state.df = None
if "view" not in st.session_state: st.session_state.view = "Upload data"
if "upload_view" not in st.session_state: st.session_state.upload_view = "Overview"
if "forecast_context" not in st.session_state: st.session_state.forecast_context = {}
with st.sidebar:
    st.markdown('<div class="brand">🛡️ <span>BizGuard</span> AI<small>Business health advisor</small></div>', unsafe_allow_html=True)
    view = st.radio("WORKSPACE", ["AI Advisor", "Upload data", "Future predictor"], index=["AI Advisor", "Upload data", "Future predictor"].index(st.session_state.view if st.session_state.view in ["AI Advisor", "Upload data", "Future predictor"] else "Upload data")); st.session_state.view = view
    if view == "Upload data":
        selected_upload_view = st.radio("UPLOAD DATA", ["Overview", "Insights", "Data explorer"], index=["Overview", "Insights", "Data explorer"].index(st.session_state.upload_view))
        st.session_state.upload_view = selected_upload_view
    st.markdown('<div style="height:2rem"></div>', unsafe_allow_html=True)
    if st.session_state.df is not None:
        st.success(f"Data connected · {len(st.session_state.df):,} rows")
        if st.button("Replace dataset", use_container_width=True): st.session_state.df = None; st.session_state.view = "Upload data"; st.rerun()
    st.markdown('<div class="footer-note">Private by design · Your CSV stays in this session</div>', unsafe_allow_html=True)
df = st.session_state.df
if view == "AI Advisor":
    advisor_view(df)
elif view == "Future predictor":
    predictor_view(df)
elif df is None:
    upload_view()
elif st.session_state.upload_view == "Overview":
    with st.spinner("Refreshing your business health..."): ranked = prioritize(detect(df), df)
    overview(df, ranked)
elif st.session_state.upload_view == "Insights":
    with st.spinner("Refreshing your business health..."): ranked = prioritize(detect(df), df)
    insights_view(df, ranked)
else:
    explorer_view(df)
