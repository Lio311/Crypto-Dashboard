import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
from scipy.signal import find_peaks
import json
import os
import smtplib
import ssl
from email.message import EmailMessage

# --- SETTINGS ---
SCAN_LIST = [
    "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", 
    "XRP-USD", "ADA-USD", "DOGE-USD", "LINK-USD",
    "DOT-USD", "AVAX-USD", "SHIB-USD", "MATIC-USD"
]

OUTPUT_SCAN_FILE = "market_scan.json"
OUTPUT_ADVANCED_FILE = "advanced_analysis.json"

# --- FUNCTION 1: MARKET SCANNER ---
def run_market_scanner():
    print("Starting market scan...")
    df_list = []
    
    for ticker in SCAN_LIST:
        try:
            # --- FIX #1: Added group_by='column' to flatten the columns ---
            data = yf.download(ticker, period="1y", progress=False, group_by='column')
            if data.empty: continue
                
            data.ta.rsi(length=14, append=True)
            data.ta.sma(length=50, append=True)
            data.ta.sma(length=200, append=True)
            
            data = data.dropna()
            if data.empty: continue

            last = data.iloc[-1]
            daily_change = (last['Close'] / data.iloc[-2]['Close'] - 1) * 100
            
            if last['RSI_14'] > 70: rsi_signal = "Overbought"
            elif last['RSI_14'] < 30: rsi_signal = "Oversold"
            else: rsi_signal = "Neutral"
                
            if last['Close'] > last['SMA_50'] and last['Close'] > last['SMA_200']: trend = "Strong Bullish"
            elif last['Close'] > last['SMA_200']: trend = "Bullish"
            else: trend = "Bearish"
            
            df_list.append({
                "מטבע": ticker,
                "מחיר אחרון": last['Close'],
                "שינוי יומי (%)": daily_change,
                "RSI (14)": last['RSI_14'],
                "סיגנל RSI": rsi_signal,
                "מגמה": trend,
                "מרחק מ-SMA200 (%)": (last['Close'] / last['SMA_200'] - 1) * 100
            })
            print(f"... Successfully scanned {ticker}")
        except Exception as e:
            print(f"!!! Error scanning {ticker}: {e}")
            
    print("Market scan finished.")
    return pd.DataFrame(df_list)

# --- FUNCTION 2: SEND EMAIL ALERT ---
def send_email_alert(subject, body):
    email_sender = os.environ.get('EMAIL_SENDER')
    email_password = os.environ.get('EMAIL_PASSWORD')
    email_receiver = os.environ.get('EMAIL_RECEIVER')

    if not all([email_sender, email_password, email_receiver]):
        print("!!! Alert Error: Environment variables (EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER) not set.")
        print("!!! Make sure you have set up your GitHub Secrets.")
        return

    # Build the message object
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = email_sender
    msg['To'] = email_receiver

    print(f"Preparing to send email to {email_receiver}...")

    try:
        # Create a secure SSL context
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(email_sender, email_password)
            smtp.send_message(msg)
            print("--- Email alert sent successfully! ---")
    except Exception as e:
        print(f"!!! Critical error sending email: {e}")

# --- FUNCTION 3: CHECK FOR ALERTS ---
def check_for_alerts(df):
    print("\nChecking for alerts...")
    alerts = []
    
    try:
        # Specific alert for Bitcoin
        btc_data = df[df['מטבע'] == 'BTC-USD'].iloc[0]
        if btc_data['RSI_14'] < 30:
            alerts.append(f"🔴 BTC Alert: Oversold! RSI: {btc_data['RSI_14']:.2f}")
        if btc_data['RSI_14'] > 70:
            alerts.append(f"🟠 BTC Alert: Overbought! RSI: {btc_data['RSI_14']:.2f}")
    except Exception as e:
        print(f"Error checking BTC alert: {e}")

    # General alert for any oversold coin
    oversold = df[df['סיגנל RSI'] == "Oversold"]
    for _, row in oversold.iterrows():
        if row['מטבע'] != 'BTC-USD': # We already handled Bitcoin
            alerts.append(f"🟢 Opportunity Alert: {row['מטבע']} is Oversold. RSI: {row['RSI_14']:.2f}")

    if not alerts:
        print("No new alerts.")
    else:
        # If there are alerts, build an email
        print(f"Found {len(alerts)} new alerts. Sending email...")
        
        subject = f"🤖 Crypto Alert: {len(alerts)} New Events"
        body = "The monitoring system has detected the following alerts:\n\n"
        body += "\n".join(alerts)
        body += "\n\n-- End of message --"
        
        # Print to log and also send email
        print(body)
        send_email_alert(subject, body)

# --- FUNCTION 4: ADVANCED ANALYSIS (WITH FFT GRAPH) ---
def run_advanced_analysis():
    print("\nStarting advanced analysis...")
    results = {}

    try:
        # 1. Correlation Analysis
        print("... Calculating correlation...")
        # --- FIX #2: Added group_by='column' to flatten the columns ---
        df_corr = yf.download(["BTC-USD", "ETH-USD", "SOL-USD"], period="3mo", progress=False, group_by='column')['Close']
        returns = df_corr.pct_change().dropna()
        corr_btc_eth = returns['BTC-USD'].rolling(30).corr(returns['ETH-USD']).iloc[-1]
        corr_btc_sol = returns['BTC-USD'].rolling(30).corr(returns['SOL-USD']).iloc[-1]
        results['correlation'] = {
            "btc_eth_30d": corr_btc_eth,
            "btc_sol_30d": corr_btc_sol
        }

        # 2. Cyclical Analysis (FFT) on Bitcoin
        print("... Calculating FFT...")
         # --- FIX #3: Added group_by='column' to flatten the columns ---
        df_btc = yf.download("BTC-USD", period="2y", progress=False, group_by='column')['Close']
        data = df_btc.values
        
        N = len(data)
        if N < 100: # Ensure there is enough data
            raise ValueError("Not enough data for FFT analysis (minimum 100 days)")

        # Remove DC component
        yf = np.fft.fft(data - np.mean(data))
        # Calculate Amplitude
        yf = 2.0/N * np.abs(yf[:N//2])
        
        # xf = frequency (cycles per day), 1 = 1 day
        xf = np.fft.fftfreq(N, 1)[:N//2] 
        
        # Convert from frequencies to periods (days)
        # Ignore frequency 0 (remaining DC component)
        periods = 1.0 / xf[1:] 
        power = yf[1:]

        # Focus on relevant periods (e.g., 1 week to 1 year)
        min_period_days = 7
        max_period_days = 365
        
        # Create a boolean mask for filtering
        mask = (periods >= min_period_days) & (periods <= max_period_days)
        
        filtered_periods = periods[mask]
        filtered_power = power[mask]
        
        # Find peaks (like before, but on the filtered data)
        peaks, _ = find_peaks(filtered_power, height=np.mean(filtered_power) + np.std(filtered_power))
        dominant_periods = filtered_periods[peaks]

        results['fft_analysis'] = {
            # Raw data for the graph
            "fft_periods": filtered_periods.tolist(), # X-axis
            "fft_power": filtered_power.tolist(),     # Y-axis
            # Summarized result (as before)
            "dominant_periods_days": sorted(dominant_periods, reverse=True)
        }
        print("Advanced analysis finished.")
        
    except Exception as e:
        print(f"!!! Error in advanced analysis: {e}")
        results['error'] = str(e)
        
    return results

# --- MAIN EXECUTION FUNCTION ---
if __name__ == "__main__":
    
    scan_df = run_market_scanner()
    if not scan_df.empty:
        scan_df.to_json(OUTPUT_SCAN_FILE, orient="records", indent=4, force_ascii=False)
        print(f"\nScan results saved to {OUTPUT_SCAN_FILE}")
        check_for_alerts(scan_df)
    else:
        print("No scan data was generated.")

    advanced_data = run_advanced_analysis()
    
    with open(OUTPUT_ADVANCED_FILE, 'w', encoding='utf-8') as f:
        json.dump(advanced_data, f, indent=4, ensure_ascii=False)
    print(f"Advanced analysis results saved to {OUTPUT_ADVANCED_FILE}")
    
    print("\n--- Engine run finished ---")
