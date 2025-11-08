import streamlit as st
import json
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(layout="wide", page_title="Advanced Analysis")
st.title("🔬 Advanced Analysis")
st.markdown("This analysis is updated automatically by the engine.")

# --- SETTINGS ---
DATA_FILE = "advanced_analysis.json"

# --- LOGIC ---
@st.cache_data(ttl=600) # Re-read from disk every 10 minutes
def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        st.error(f"Data file '{DATA_FILE}' not found. Please wait for the first automated run or run `5_engine.py` manually.")
        return None
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# --- DISPLAY ---
advanced_data = load_data()

if advanced_data:
    if 'error' in advanced_data:
        st.error(f"An error occurred during the advanced analysis calculation: {advanced_data['error']}")
    
    # --- 1. Display Correlation Analysis ---
    st.subheader("Correlation Analysis - Last 30 Days")
    if 'correlation' in advanced_data:
        col1, col2 = st.columns(2)
        try:
            col1.metric(
                label="Bitcoin <-> Ethereum Correlation", 
                value=f"{advanced_data['correlation']['btc_eth_30d']:.3f}"
            )
            col2.metric(
                label="Bitcoin <-> Solana Correlation", 
                value=f"{advanced_data['correlation']['btc_sol_30d']:.3f}"
            )
        except KeyError:
            st.warning("Correlation data missing.")
    else:
        st.warning("No correlation data found.")

    st.markdown("---")

    # --- 2. Display Cyclical Analysis (FFT) ---
    st.subheader("Cyclical Analysis (FFT) - Bitcoin (based on 2 years)")
    st.markdown("The chart shows the 'power' of each cycle (in days). High peaks represent statistically dominant cycles.")
    
    if 'fft_analysis' in advanced_data:
        try:
            # Load data for the graph from JSON
            periods = advanced_data['fft_analysis']['fft_periods']
            power = advanced_data['fft_analysis']['fft_power']
            dominant_periods = advanced_data['fft_analysis']['dominant_periods_days']

            if not periods or not power:
                st.info("No spectrum data to display.")
            else:
                # Create Plotly figure
                fig = go.Figure()
                
                # Add spectrum line trace
                fig.add_trace(go.Scatter(
                    x=periods,
                    y=power,
                    mode='lines',
                    name='Spectrum Power'
                ))
                
                # Add markers for the dominant peaks we found
                if dominant_periods:
                    st.write("Dominant cycles identified (in days):")
                    st.code(f"{[round(p, 1) for p in dominant_periods]}")
                    
                    # Build data to display peaks
                    peak_df = pd.DataFrame({'period': periods, 'power': power})
                    peak_df = peak_df[peak_df['period'].isin(dominant_periods)]
                    
                    fig.add_trace(go.Scatter(
                        x=peak_df['period'],
                        y=peak_df['power'],
                        mode='markers',
                        name='Dominant Peaks',
                        marker=dict(color='red', size=10, symbol='x')
                    ))
                else:
                    st.info("No strong dominant cycles were identified.")

                # Update graph layout
                fig.update_layout(
                    title="Bitcoin Cycle Periodogram",
                    xaxis_title="Period (Days) - Logarithmic Scale",
                    yaxis_title="Power (Amplitude)",
                    xaxis_type="log", # Use log scale for X-axis - critical for this type of graph
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)

        except KeyError:
            st.warning("FFT data is missing or in an incorrect format.")
        except Exception as e:
            st.error(f"Error creating FFT chart: {e}")
    else:
        st.warning("No FFT data found.")
        
    st.markdown("---")
    # Raw Data (JSON)
    st.subheader("Raw Data (JSON)")
    st.json(advanced_data)

else:
    st.warning("No data loaded.")
