# BizGuard AI

BizGuard AI is a small-business health advisor that turns everyday operating data into practical decisions. It helps a business owner understand what is happening now, model what could happen next, and ask questions in plain language.

## What we built

### 1. Upload data workspace

Users can upload business data and move through three focused views:

- **Overview** - risk score, cash-flow health, open signals, and a 12-month danger trajectory.
- **Insights** - detected business issues ranked by priority, with explanations and recommended actions.
- **Data explorer** - metric charts and a raw data table for transparency.

Supported files:

- CSV
- Excel (`.xlsx`, `.xls`)
- Table-based PDF

The importer accepts common column variations such as `revenue`, `sales`, `income`, `opex`, `costs`, `customers`, `visitors`, `stock`, and `inventory`. If a column cannot be identified confidently, the user can map it manually before analysis continues.

### 2. Future predictor

The Future predictor works independently from file upload. A user can enter:

- Current cash in bank
- Monthly revenue
- Monthly operating costs
- Existing debt or loans
- Expected sales growth or decline
- Expense inflation
- Loan interest rate

The app then estimates cash runway, monthly cash change, ending cash, a 12-month risk score, and a month-by-month forecast.

### 3. AI Advisor

The AI Advisor answers general business questions even when no data has been uploaded. When available, it also receives context from:

- Uploaded business data and detected signals
- Future predictor assumptions and results

This allows users to ask questions such as:

- “How can I reduce my monthly costs?”
- “What should I investigate first?”
- “Is my business likely to run out of cash?”
- “What is the difference between a small business and a company?”

The advisor uses OpenRouter through its OpenAI-compatible API. If the external AI service is unavailable, BizGuard keeps a local fallback advisor for common business topics.

## Analysis approach

The uploaded-data analysis combines:

- Rolling anomaly detection
- Recent trend detection
- Short-term threshold forecasting
- Issue categorization and priority scoring
- Plain-language explanations and suggested actions

The system validates dates and numeric fields, removes invalid rows, requires a minimum amount of data for analysis, and shows the data mapping before continuing when the input format is ambiguous.

## Quick start

From the `bizguard` folder:

```powershell
..\bizguard-venv\Scripts\python.exe -m pip install -r requirements.txt
.\run.bat
```

The app opens on port `8600`:

```text
http://localhost:8600
```

## AI configuration

Create a `.env` file in the `bizguard` folder. Never commit this file or share its contents.

```env
OPENROUTER_API_KEY=your-private-key
OPENROUTER_MODEL=openai/gpt-4o-mini
```

The model can be changed through `OPENROUTER_MODEL` without editing the application code. The app limits response length and applies a request timeout to control cost and avoid a frozen interface.

## Demo files

The `sample_uploads` folder contains ready-to-test examples:

- `bizguard_sample.csv`
- `bizguard_sample.xlsx`
- `bizguard_sample.pdf`

The demo data contains 90 days of daily business activity with planted sales, expense, customer, and inventory signals so the analysis views have meaningful results.

## Project structure

```text
app.py              Streamlit UI, navigation, upload flow, predictor, and advisor
detect.py           Anomaly, trend, and forecast detection
categorize.py       Business issue categorization
prioritize.py       Priority and financial-impact scoring
explain.py          Plain-language explanations and actions
data_generator.py   Demo dataset generator
sample_uploads/     CSV, Excel, and PDF upload examples
requirements.txt    Python dependencies
run.bat             Windows launcher
```

## Important limitations

- Forecasts are planning estimates, not accounting, investment, tax, or legal advice.
- PDF support expects a readable table. Scanned image-only PDFs may need OCR before upload.
- Predictive accuracy improves with longer, cleaner, and consistently dated history.
- OpenRouter usage depends on the selected model, account credits, and provider availability.
