import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import google.generativeai as genai 

st.set_page_config(layout="wide", page_title="Deep Dive Analysis")
st.title("ניתוח טכני מעמיק")

# --- Configure Gemini API Key ---
try:
    # The app will read the key from Streamlit Secrets
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    GEMINI_ENABLED = True
except Exception as e:
    st.sidebar.error("Gemini API Key not set.")
    st.sidebar.caption("To enable AI analysis, add 'GEMINI_API_KEY' to your Streamlit Cloud app Secrets.")
    GEMINI_ENABLED = False

# --- Settings and User Input ---
st.sidebar.header("בקרת ניתוח")
COIN_LIST = {
    "Bitcoin (BTC)": "BTC-USD",
    "Ethereum (ETH)": "ETH-USD",
    "Solana (SOL)": "SOL-USD",
    "Cardano (ADA)": "ADA-USD"
}
selected_coin_name = st.sidebar.selectbox("בחר מטבע:", list(COIN_LIST.keys()))
ticker = COIN_LIST[selected_coin_name]
timeframe = st.sidebar.selectbox("בחר טווח זמן:", ["שנה (1y)", "6 חודשים (6mo)", "3 חודשים (3mo)", "חודש (1mo)"], index=0)
period_map = {"שנה (1y)": "1y", "6 חודשים (6mo)": "6mo", "3 חודשים (3mo)": "3mo", "חודש (1mo)": "1mo"}
selected_period = period_map[timeframe]

# --- Data Processing Logic ---
@st.cache_data(ttl=300) # Cache for 5 minutes
def get_data(ticker, period):
    # --- FIX #4: Added group_by='column' to flatten the columns ---
    df = yf.download(ticker, period=period, group_by='column')
    
    if df.empty: return None
    df.ta.sma(length=50, append=True)
    df.ta.sma(length=200, append=True)
    df.ta.rsi(length=14, append=True)
    df.ta.bbands(length=20, std=2, append=True)
    df = df.dropna()
    return df

# --- Function to call Gemini ---
@st.cache_data(ttl=600) # Cache analysis for 10 minutes
def get_gemini_analysis(prompt):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating analysis: {e}"

# --- Run and Collect Data ---
data_df = get_data(ticker, selected_period)

if data_df is None or data_df.empty:
    st.error("לא הצלחתי להוריד נתונים. נסה מטבע או טווח זמן אחר.")
else:
    # --- Collect Data for Gemini ---
    st.header(f"ניתוח עבור {selected_coin_name}")
    
    last_row = data_df.iloc[-1]
    last_price = last_row['Close']
    last_rsi = last_row['RSI_14']
    ma_50 = last_row['SMA_50']
    ma_200 = last_row['SMA_200']
    bb_high = last_row['BBU_20_2.0']
    bb_low = last_row['BBL_20_2.0']

    if last_rsi > 70: rsi_status = "Overbought"
    elif last_rsi < 30: rsi_status = "Oversold"
    else: rsi_status = "Neutral"

    status_vs_50 = "above" if last_price > ma_50 else "below"
    status_vs_200 = "above" if last_price > ma_200 else "below"
    
    if last_price > bb_high: bb_status = "breaking the upper band"
    elif last_price < bb_low: bb_status = "touching the lower band"
    else: bb_status = "within the bands"

    # --- Display Metrics ---
    col1, col2, col3 = st.columns(3)
    col1.metric("מחיר אחרון (USD)", f"${last_price:,.2f}")
    col2.metric("RSI (14)", f"{last_rsi:.1f}", rsi_status)
    trend_status = "Bullish" if status_vs_200 == "above" else "Bearish"
    trend_delta = "▲" if trend_status == "Bullish" else "▼"
    col3.metric(f"מגמה (מול SMA 200)", trend_status, trend_delta)
    
    # --- Display Graphs ---
    st.subheader("גרפים (אינטראקטיביים - ניתן לבצע זום)")
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        vertical_spacing=0.05,
                        row_heights=[0.6, 0.2, 0.2],
                        subplot_titles=(f"גרף מחיר, ממוצעים נעים, ורצועות בולינגר", "RSI (מדד חוזק יחסי)", "נפח מסחר (Volume)"))
    fig.add_trace(go.Candlestick(x=data_df.index, open=data_df['Open'], high=data_df['High'], low=data_df['Low'], close=data_df['Close'], name='מחיר'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data_df.index, y=data_df['SMA_50'], mode='lines', name='SMA 50', line=dict(color='orange')), row=1, col=1)
    fig.add_trace(go.Scatter(x=data_df.index, y=data_df['SMA_200'], mode='lines', name='SMA 200', line=dict(color='blue', dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=data_df.index, y=data_df['BBL_20_2.0'], mode='lines', name='רצועה תחתונה', line=dict(color='gray', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=data_df.index, y=data_df['BBU_20_2.0'], mode='lines', name='רצועה עליונה', line=dict(color='gray', width=1), fill='tonexty', fillcolor='rgba(128,128,128,0.1)'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data_df.index, y=data_df['RSI_14'], mode='lines', name='RSI', line=dict(color='purple')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    fig.add_trace(go.Bar(x=data_df.index, y=data_df['Volume'], name='Volume', marker_color='teal'), row=3, col=1)
    fig.update_layout(height=800, showlegend=True, xaxis_rangeslider_visible=False, xaxis3_rangeslider_visible=True, title_text=f"ניתוח טכני עבור {selected_coin_name} ({ticker})")
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
    st.plotly_chart(fig, use_container_width=True)

    # --- Gemini Analysis Area ---
    st.markdown("---")
    st.subheader(f"🤖 ניתוח אוטומטי (מבוסס Gemini) - {selected_coin_name}")
    
    if not GEMINI_ENABLED:
        st.warning("To enable this analysis, set the `GEMINI_API_KEY` in your app's Secrets.")
    else:
        # Button to trigger analysis
        if st.button(f"בקש מ-Gemini לנתח את {selected_coin_name}"):
            with st.spinner("חושב... Gemini מנתח את הנתונים..."):
                
                # Build the Prompt
                prompt = f"""
                You are an objective technical crypto market analyst (not a financial advisor).
                Your job is to interpret cold technical data.
                
                Analyze the following data for {selected_coin_name} ({ticker}):

                * **Current Price:** ${last_price:,.2f}
                * **RSI (14):** {last_rsi:.1f} (Meaning: {rsi_status})
                * **Relation to SMA 50:** {status_vs_50}
                * **Relation to SMA 200:** {status_vs_200} (This is a long-term trend indicator)
                * **Relation to Bollinger Bands:** {bb_status}

                **Your Task:**
                1. Provide a brief summary (2-3 sentences) of the current technical situation.
                2. Provide 2-3 bullet points highlighting the strongest Bearish or Bullish signals you see.
                3. Conclude with a sentence about the expected Volatility (e.g., based on Bollinger Bands).
                
                Important: Do not give an explicit Buy/Sell/Hold recommendation. Focus only on interpreting the data.
                Write the response in Hebrew.
                """
                
                # Call the API
                analysis = get_gemini_analysis(prompt)
                
                # Display the result
                st.markdown(analysis)

    # --- Raw Data ---
    st.subheader("נתונים גולמיים")
    st.dataframe(data_df.tail(10))
