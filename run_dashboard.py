"""
Dashboard launcher — adds the local lib folder to sys.path then starts Streamlit.
Run with: py -3.12 run_dashboard.py
"""

import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
LIB  = os.path.join(ROOT, "lib")

sys.path.insert(0, LIB)

from streamlit.web import cli as stcli

sys.argv = [
    "streamlit", "run",
    os.path.join(ROOT, "dashboard", "app.py"),
    "--browser.gatherUsageStats=false",
]

sys.exit(stcli.main())
