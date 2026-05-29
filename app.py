import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# القائمة والتعريفات الأساسية
saudi_market = {
    "2310": "سبكيم العالمية", "3080": "أسمنت الشرقية", "4250": "جبل عمر", "4110": "باتك",
    "3010": "أسمنت العربية", "3020": "أسمنت اليمامة", "3030": "أسمنت السعودية", 
    "3040": "أسمنت القصيم", "3050": "أسمنت الجنوبية", "3060": "أسمنت ينبع", 
    "3090": "أسمنت تبوك", "1120": "الراجحي", "1180": "الأهلي", "1150": "الإنماء", 
    "2222": "أرامكو السعودية", "2010": "سابك", "2082": "معادن", "7010": "STC"
}

def calculate_wma(series, length):
    weights = np.arange(1, length + 1)
    return series.rolling(length).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

def calculate_hma(series, length):
    half_len = int(length / 2)
    sqrt_len = int(np.sqrt(length))
    diff = 2 * calculate_wma(series, half_len) - calculate_wma(series, length)
    return calculate_wma(diff, sqrt_len)

def calculate_slope(series, length=5):
    y = series.iloc[-length:].values
    x = np.arange(len(y))
    slope, _ = np.polyfit(x, y, 1)
    return slope

# واجهة التطبيق
st.set_page_config(layout="wide")
st.title("🎯 رادار القناص المتكامل (شارت + رادار)")

tab1, tab2 = st.tabs(["📊 عرض الشارت لأي سهم", "🔍 رادار زاوية الميل"])

# التبويب الأول: الشارت لأي سهم
with tab1:
    stock_input = st.text_input("أدخل رقم السهم (مثال 2310):", "2310")
    if st.button("عرض الشارت"):
        df = yf.Ticker(f"{stock_input}.SR").history(period="1y", interval="1d")
        if not df.empty:
            hma_series = calculate_hma(df['Close'], 21)
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']))
            fig.add_trace(go.Scatter(x=df.index, y=hma_series, name="HMA 21", line=dict(color='orange')))
            st.plotly_chart(fig, use_container_width=True)

# التبويب الثاني: الرادار
with tab2:
    if st.button("تفعيل الرادار"):
        results = []
        for code, name in saudi_market.items():
            try:
                df = yf.Ticker(f"{code}.SR").history(period="6mo", interval="1d")
                hma = calculate_hma(df['Close'], 21)
                slope = calculate_slope(hma, 5)
                status = "🟢 صاعد قوي" if slope > 0.05 else "🔴 هابط/عرضي"
                results.append({"السهم": name, "الحالة": status, "قوة الميل": round(slope, 4)})
            except: continue
        st.dataframe(pd.DataFrame(results))
