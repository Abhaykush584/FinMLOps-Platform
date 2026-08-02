# File: dashboard/app.py
# Enterprise-Grade Streamlit Dashboard — Financial MLOps Signal Monitor
# Reads API_URL from environment (Docker) or falls back to localhost for local runs.

import os
import time
import json
import requests
import pandas as pd
import streamlit as st


# Read API_URL from Streamlit secrets, environment variable, or fallback to local Docker
API_URL = st.secrets.get("API_URL", os.getenv("API_URL", "http://localhost:5000"))
# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QuantSignal · AI Trading Monitor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── API URL Resolution (Docker network vs localhost) ─────────────────────────
API_URL = os.getenv("API_URL", "http://localhost:5000")

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

  html, body, [class*="css"] {
      font-family: 'Inter', sans-serif;
  }

  /* ── dark glass background ── */
  .stApp {
      background: linear-gradient(135deg, #0a0e1a 0%, #0d1829 40%, #0a1520 100%);
  }

  /* ── Main card wrapper ── */
  .glass-card {
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 16px;
      padding: 28px 32px;
      margin-bottom: 20px;
      backdrop-filter: blur(12px);
  }

  /* ── BUY signal banner ── */
  .signal-buy {
      background: linear-gradient(135deg, #00d46a 0%, #00a854 100%);
      border-radius: 14px;
      padding: 28px 36px;
      text-align: center;
      box-shadow: 0 0 40px rgba(0,212,106,0.35), 0 8px 32px rgba(0,0,0,0.4);
      animation: pulse-green 2s ease-in-out infinite;
  }
  .signal-buy h1 { font-size: 3.2rem; font-weight: 800; color: #fff; margin: 0; letter-spacing: 3px; }
  .signal-buy p  { color: rgba(255,255,255,0.85); font-size: 1rem; margin: 6px 0 0; }

  /* ── SELL signal banner ── */
  .signal-sell {
      background: linear-gradient(135deg, #ff3b5c 0%, #c9143b 100%);
      border-radius: 14px;
      padding: 28px 36px;
      text-align: center;
      box-shadow: 0 0 40px rgba(255,59,92,0.35), 0 8px 32px rgba(0,0,0,0.4);
      animation: pulse-red 2s ease-in-out infinite;
  }
  .signal-sell h1 { font-size: 3.2rem; font-weight: 800; color: #fff; margin: 0; letter-spacing: 3px; }
  .signal-sell p  { color: rgba(255,255,255,0.85); font-size: 1rem; margin: 6px 0 0; }

  @keyframes pulse-green {
      0%,100% { box-shadow: 0 0 40px rgba(0,212,106,0.35), 0 8px 32px rgba(0,0,0,0.4); }
      50%      { box-shadow: 0 0 60px rgba(0,212,106,0.6),  0 8px 32px rgba(0,0,0,0.4); }
  }
  @keyframes pulse-red {
      0%,100% { box-shadow: 0 0 40px rgba(255,59,92,0.35), 0 8px 32px rgba(0,0,0,0.4); }
      50%      { box-shadow: 0 0 60px rgba(255,59,92,0.6),  0 8px 32px rgba(0,0,0,0.4); }
  }

  /* ── Metric tiles ── */
  .metric-tile {
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.10);
      border-radius: 12px;
      padding: 20px 24px;
      text-align: center;
  }
  .metric-tile .label { color: rgba(255,255,255,0.5); font-size: 0.75rem; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; }
  .metric-tile .value { color: #fff; font-size: 2rem; font-weight: 700; margin-top: 4px; }

  /* ── Status dot ── */
  .status-online  { color: #00d46a; font-weight: 700; }
  .status-offline { color: #ff3b5c; font-weight: 700; }

  /* ── Section headers ── */
  .section-header {
      color: rgba(255,255,255,0.4);
      font-size: 0.7rem;
      font-weight: 700;
      letter-spacing: 2px;
      text-transform: uppercase;
      margin-bottom: 12px;
      border-bottom: 1px solid rgba(255,255,255,0.07);
      padding-bottom: 8px;
  }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
      background: rgba(10,14,26,0.95) !important;
      border-right: 1px solid rgba(255,255,255,0.07);
  }

  /* ── Input styling ── */
  [data-testid="stNumberInput"] input {
      background: rgba(255,255,255,0.06) !important;
      border: 1px solid rgba(255,255,255,0.12) !important;
      border-radius: 8px !important;
      color: #fff !important;
  }

  /* ── Divider ── */
  hr { border-color: rgba(255,255,255,0.06) !important; }

  /* ── JSON viewer ── */
  .json-block {
      background: rgba(0,0,0,0.4);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 10px;
      padding: 16px;
      font-family: 'Courier New', monospace;
      font-size: 0.8rem;
      color: #a8d8a8;
      white-space: pre-wrap;
  }
</style>
""", unsafe_allow_html=True)


# ── Helper: API ping ──────────────────────────────────────────────────────────
@st.cache_data(ttl=5)  # refresh every 5 seconds
def ping_api():
    try:
        r = requests.get(f"{API_URL}/", timeout=4)
        data = r.json()
        return True, data
    except Exception as e:
        return False, {"error": str(e)}


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📡 System Telemetry")
    st.caption(f"API endpoint: `{API_URL}`")

    online, health = ping_api()
    if online and health.get("model_loaded"):
        st.markdown('<p class="status-online">🟢 &nbsp; API Online · Model Ready</p>', unsafe_allow_html=True)
    elif online:
        st.markdown('<p class="status-offline">🟡 &nbsp; API Online · Model NOT Loaded</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="status-offline">🔴 &nbsp; API Offline</p>', unsafe_allow_html=True)
        st.error(f"Cannot reach {API_URL}")

    st.markdown("---")
    st.markdown("### 🏗️ Architecture")
    st.markdown("""
    ```
    Alpha Vantage API
          ↓
    GCP BigQuery (raw)
          ↓
    dbt Feature Store
          ↓  (daily via Airflow)
    XGBoost Classifier
          ↓
    Flask REST API  ←──── this dashboard
          ↓
    Streamlit UI
    ```
    """)

    st.markdown("---")
    st.markdown("### 🔧 Live Health Response")
    if online:
        with st.expander("View raw /health JSON"):
            st.json(health)
    else:
        st.warning("No response from API server.")

    st.markdown("---")
    st.caption("© 2026 QuantSignal · Financial MLOps")


# ── Main Header ───────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([0.07, 0.93])
with col_logo:
    st.markdown("# 📈")
with col_title:
    st.markdown("# QuantSignal · AI Trading Monitor")
    st.markdown('<p style="color:rgba(255,255,255,0.4);margin-top:-8px;font-size:0.9rem;">Real-time XGBoost stock signal inference · Powered by financial-pipeline-ml</p>', unsafe_allow_html=True)

st.markdown("---")

# ── Input Panel ───────────────────────────────────────────────────────────────
st.markdown('<p class="section-header">📊 Technical Indicator Inputs</p>', unsafe_allow_html=True)
st.markdown('<div class="glass-card">', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    close_price = st.number_input(
        "Close Price ($)", min_value=0.0, value=178.50, step=0.5,
        format="%.2f", help="Latest closing price of the stock"
    )
    volume = st.number_input(
        "Volume (M shares)", min_value=0.0, value=62.5, step=0.5,
        format="%.2f", help="Daily trading volume in millions"
    )

with col2:
    daily_return = st.number_input(
        "Daily Return (%)", value=0.82, step=0.01, format="%.4f",
        help="Percentage return for the current trading day"
    )
    ma_5 = st.number_input(
        "MA-5 ($)", min_value=0.0, value=176.40, step=0.5,
        format="%.2f", help="5-day moving average"
    )

with col3:
    ma_20 = st.number_input(
        "MA-20 ($)", min_value=0.0, value=174.10, step=0.5,
        format="%.2f", help="20-day moving average"
    )
    return_lag_1 = st.number_input(
        "Return Lag-1 (%)", value=0.45, step=0.01, format="%.4f",
        help="Previous day's daily return"
    )

with col4:
    return_lag_2 = st.number_input(
        "Return Lag-2 (%)", value=-0.22, step=0.01, format="%.4f",
        help="Two days ago daily return"
    )
    st.markdown("<br/>", unsafe_allow_html=True)
    run_inference = st.button(
        "🚀 &nbsp; Run Inference", use_container_width=True,
        type="primary"
    )

st.markdown('</div>', unsafe_allow_html=True)

# ── Construct payload ─────────────────────────────────────────────────────────
payload = {
    "close_price":   close_price,
    "volume":        volume,
    "daily_return":  daily_return,
    "ma_5":          ma_5,
    "ma_20":         ma_20,
    "return_lag_1":  return_lag_1,
    "return_lag_2":  return_lag_2,
}

# ── Results Section ───────────────────────────────────────────────────────────
st.markdown('<p class="section-header">🎯 Model Inference Results</p>', unsafe_allow_html=True)

if run_inference:
    if not online:
        st.error("❌ Cannot run inference — Flask API is offline. Start it with `docker compose up`.")
    else:
        with st.spinner("Sending request to Flask API…"):
            try:
                response = requests.post(
                    f"{API_URL}/predict",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                result = response.json()
            except Exception as e:
                result = {"error": str(e)}

        if "error" in result:
            st.error(f"❌ API Error: {result['error']}")
        else:
            signal     = result.get("signal", "?")
            confidence = result.get("confidence_score", 0)
            prediction = result.get("prediction", -1)
            probs      = result.get("probabilities", {})
            buy_prob   = probs.get("buy_prob", 0)
            sell_prob  = probs.get("sell_prob", 0)

            # ── Signal Banner ─────────────────────────────────────────────────
            css_class = "signal-buy" if signal == "BUY" else "signal-sell"
            emoji     = "🟢 " if signal == "BUY" else "🔴 "
            subtext   = "Model recommends entering a LONG position." if signal == "BUY" \
                        else "Model recommends staying out or going SHORT."

            st.markdown(f"""
            <div class="{css_class}">
                <h1>{emoji}{signal}</h1>
                <p>{subtext}</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<br/>", unsafe_allow_html=True)

            # ── Metric Tiles ──────────────────────────────────────────────────
            m1, m2, m3, m4 = st.columns(4)

            with m1:
                st.markdown(f"""<div class="metric-tile">
                    <div class="label">Confidence Score</div>
                    <div class="value">{confidence*100:.1f}%</div>
                </div>""", unsafe_allow_html=True)

            with m2:
                st.markdown(f"""<div class="metric-tile">
                    <div class="label">Raw Prediction Class</div>
                    <div class="value">{'1 (BUY)' if prediction==1 else '0 (SELL)'}</div>
                </div>""", unsafe_allow_html=True)

            with m3:
                st.markdown(f"""<div class="metric-tile">
                    <div class="label">BUY Probability</div>
                    <div class="value" style="color:#00d46a;">{buy_prob*100:.1f}%</div>
                </div>""", unsafe_allow_html=True)

            with m4:
                st.markdown(f"""<div class="metric-tile">
                    <div class="label">SELL Probability</div>
                    <div class="value" style="color:#ff3b5c;">{sell_prob*100:.1f}%</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("<br/>", unsafe_allow_html=True)

            # ── Confidence Progress Bar ───────────────────────────────────────
            st.markdown('<p class="section-header">📶 Model Probability Strength</p>', unsafe_allow_html=True)
            bar_col1, bar_col2 = st.columns([0.7, 0.3])
            with bar_col1:
                st.markdown(f"**SELL** &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **BUY**")
                bar_color = "#00d46a" if signal == "BUY" else "#ff3b5c"
                st.progress(float(buy_prob))
            with bar_col2:
                st.metric("BUY Probability", f"{buy_prob*100:.2f}%",
                          delta=f"{(buy_prob - 0.5)*100:+.1f}% vs random")

            st.markdown("---")

            # ── Raw payload / response viewer ─────────────────────────────────
            jcol1, jcol2 = st.columns(2)
            with jcol1:
                st.markdown('<p class="section-header">📤 Request Payload Sent to API</p>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="json-block">{json.dumps(payload, indent=2)}</div>',
                    unsafe_allow_html=True
                )
            with jcol2:
                st.markdown('<p class="section-header">📥 Raw API Response</p>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="json-block">{json.dumps(result, indent=2)}</div>',
                    unsafe_allow_html=True
                )

else:
    # ── Idle state ────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="glass-card" style="text-align:center; padding: 60px;">
        <p style="font-size:3rem; margin:0;">🤖</p>
        <h3 style="color:rgba(255,255,255,0.6); margin: 12px 0 4px;">Ready for Inference</h3>
        <p style="color:rgba(255,255,255,0.35); font-size:0.9rem;">
            Adjust the technical indicators above and click <b>Run Inference</b><br/>
            to get a real-time BUY / SELL signal from the XGBoost model.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
fcol1, fcol2, fcol3 = st.columns(3)
with fcol1:
    st.caption(f"🔌 API: `{API_URL}`")
with fcol2:
    st.caption("⚙️ Model: XGBoost Classifier · Scikit-Learn Pipeline")
with fcol3:
    status_txt = "🟢 Online" if online else "🔴 Offline"
    st.caption(f"Status: {status_txt}")
