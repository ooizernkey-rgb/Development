# SME-Pulse: Early-Warning Financial Runway & Risk Engine

AI-powered dashboard that detects, categorises, prioritises, and explains
financial risk for small/medium businesses — before costly failures occur.

---

## Project Structure

```
sme-pulse/
├── data/
│   ├── sme_pulse.db        # SQLite database (auto-created)
│   └── xgb_model.pkl       # Trained XGBoost model
├── pipeline/
│   ├── db.py               # DB setup & connection helpers
│   ├── fetch_fred.py       # FRED macroeconomic data fetcher
│   ├── fetch_trends.py     # Google Trends fetcher
│   ├── generate_synthetic_financials.py  # Prototype financial data
│   ├── feature_engineering.py            # Merge + composite features
│   ├── train_model.py      # XGBoost + SMOTE + SHAP training
│   └── run_pipeline.py     # Master pipeline runner
├── dashboard/
│   └── app.py              # Streamlit dashboard (4 pages)
├── lib/                    # Local Python packages
├── run_dashboard.py        # Dashboard launcher
├── requirements.txt
└── README.md
```

---

## Setup & Run

### 1. Run the full data + training pipeline
```powershell
cd pipeline
py -3.12 run_pipeline.py
```

### 2. Launch the dashboard
```powershell
cd c:\Development\sme-pulse
py -3.12 run_dashboard.py
```
Then open: **http://localhost:8501**

---

## Dashboard Pages

| Page | What it shows |
|---|---|
| 📊 Portfolio Overview | Risk tier breakdown, top at-risk companies, global SHAP importance |
| 🔍 Company Deep-Dive  | Risk gauge, score timeline, SHAP drivers, downloadable action plan |
| 🎛️ What-If Simulator  | Live sliders for financial + macro inputs → instant risk score update |
| 📈 Macro Trends       | FRED indicator charts + Google Trends demand signals |

---

## Model Details

- **Algorithm**: XGBoost (gradient boosting on tabular data)
- **Class imbalance**: SMOTE (8% bankruptcy rate → balanced training set)
- **Explainability**: SHAP (SHapley Additive exPlanations)
- **Split strategy**: Time-based (2017–2021 train, 2022–2023 test)
- **Key metrics**: ROC-AUC, PR-AUC, Recall

---

## Next Steps

- Replace synthetic data with real Kaggle datasets (Taiwanese + Polish bankruptcy)
- Add PDF report export
- Deploy to Streamlit Cloud or HuggingFace Spaces
