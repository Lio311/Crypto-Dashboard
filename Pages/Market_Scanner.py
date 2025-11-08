import streamlit as st
import pandas as pd
import json

st.set_page_config(layout="wide", page_title="Market Scanner")
st.title("📡 Market Scanner")
st.markdown("This table is automatically updated every 30 minutes by the background engine.")

# --- SETTINGS ---
DATA_FILE = "market_scan.json"

# --- LOGIC ---
@st.cache_data(ttl=60) # Re-read from disk every 60 seconds
def load_data():
    try:
        # Read the JSON created by the engine
        df = pd.read_json(DATA_FILE)
        return df
    except FileNotFoundError:
        st.error(f"Data file '{DATA_FILE}' not found. Please wait for the first automated run or run `5_engine.py` manually.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# --- DISPLAY ---
scan_df = load_data()

if not scan_df.empty:
    st.subheader("Latest Scan Results")
    
    # --- FILTERS ---
    st.markdown("---")
    st.sidebar.header("Scanner Filters")
    
    rsi_range = st.sidebar.slider("Filter by RSI range:", 0.0, 100.0, (0.0, 100.0))
    filtered_df = scan_df[
        (scan_df['RSI (14)'] >= rsi_range[0]) & 
        (scan_df['RSI (14)'] <= rsi_range[1])
    ]
    
    rsi_signal_filter = st.sidebar.multiselect("Filter by RSI Signal:", 
                                     options=scan_df['סיגנל RSI'].unique(),
                                     default=scan_df['סיגנל RSI'].unique())
    filtered_df = filtered_df[filtered_df['סיגנל RSI'].isin(rsi_signal_filter)]
    
    # --- DISPLAY TABLE ---
    st.dataframe(
        filtered_df.style
            .format({
                "מחיר אחרון": "${:,.2f}",
                "שינוי יומי (%)": "{:,.2f}%",
                "RSI (14)": "{:.1f}",
                "מרחק מ-SMA200 (%)": "{:,.2f}%"
            })
            # Cell coloring
            .background_gradient(cmap='RdYlGn', subset=['RSI (14)'], vmin=30, vmax=70)
            .background_gradient(cmap='RdYlGn', subset=['שינוי יומי (%)'], vmin=-5, vmax=5)
    , use_container_width=True)
    
else:
    st.warning("No data loaded.")
