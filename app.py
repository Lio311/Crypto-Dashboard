import streamlit as st

st.set_page_config(
    page_title="Crypto Control Tower",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Welcome to your Crypto Control Tower")
st.header("An automated system for crypto market analysis")

st.markdown("""
This is your central hub for analysis and decision-making.
It combines several automated tools to give you a complete picture.

**What can you do here?**

* **📈 Deep Dive:**
    Select a specific coin (like BTC, ETH, SOL) and get a full technical analysis, including moving averages, RSI, and a Gemini AI analysis.

* **📡 Market Scanner:**
    Get a smart, fast summary table of the 12 scanned coins. Filter and sort by RSI, trend, and more.
    
* **🔬 Advanced Analysis:**
    View correlation analyses and cycle detection (FFT) for the leading coins.

---
**How does it work?**
An automated engine (`engine.py`) runs every 30 minutes via GitHub Actions,
performs all calculations, and saves them. This dashboard reads that prepared data.
""")

st.sidebar.success("Select an analysis page from the menu above.")
