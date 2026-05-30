import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor

# دالة قراءة البيانات
@st.cache_data
def get_full_saudi_market():
    try:
        df = pd.read_csv('stocks.csv')
        return dict(zip(df['Symbol'].astype(str), df['Name']))
    except Exception as e:
        st.error(f"خطأ في قراءة الملف: {e}")
        return {}

def calculate_hma(series, length):
    weights = np.arange(1, length + 1)
    def wma(s, l): return s.rolling(l).apply(lambda x: np.dot(x, weights[:l]) / weights[:l].sum(), raw=True)
    return wma(2 * wma(series, int(length/2)) - wma(series, length), int(np.sqrt(length)))

def calculate_slope(series, length=5):
    y = series.iloc[-length:].values
    x = np.arange(len(y))
    slope, _ = np.polyfit(x, y, 1)
    return slope

def scan_stock(code, name):
    try:
        df = yf.Ticker(f"{code}.SR").history(period="3mo", interval="1d")
        if df.empty or len(df) < 21: return None
        hma = calculate_hma(df['Close'], 21)
        slope = calculate_slope(hma, 5)
        if slope > 0.05: status = "إيجابي"
        elif slope > -0.02: status = "مراقبة"
        else: status = "سلبي"
        return {"السهم": name, "الرمز": code, "الحالة": status, "ميل HMA": round(slope, 4)}
    except: return None

# الواجهة
st.set_page_config(layout="wide")
st.title("🛡️ رادار القناص الاحترافي")

stocks = get_full_saudi_market()
tab1, tab2 = st.tabs(["📊 التحليل الفردي", "🔍 رادار السوق"])

with tab1:
    s_code = st.text_input("أدخل رمز السهم:", "2310")
    if st.button("تحليل"):
        df = yf.Ticker(f"{s_code}.SR").history(period="1y", interval="1d")
        if not df.empty:
            hma = calculate_hma(df['Close'], 21)
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']))
            fig.add_trace(go.Scatter(x=df.index, y=hma, name="HMA 21", line=dict(color='yellow')))
            # تم التعديل حسب طلبك: width='stretch'
            st.plotly_chart(fig, width='stretch')
        else:
            st.warning("رمز غير صحيح أو لا توجد بيانات!")

with tab2:
    filter_choice = st.selectbox("اختر الحالة:", ["الكل", "إيجابي", "مراقبة", "سلبي"])
    if st.button(f"ابدأ المسح لـ {len(stocks)} شركة 🚀"):
        with st.spinner("جاري المسح..."):
            with ThreadPoolExecutor(max_workers=30) as executor:
                results = list(executor.map(lambda p: scan_stock(*p), stocks.items()))
            clean_results = [r for r in results if r is not None]
            df_results = pd.DataFrame(clean_results)
            if filter_choice != "الكل":
                df_results = df_results[df_results['الحالة'] == filter_choice]
            # تم التعديل حسب طلبك: width='stretch'
            st.dataframe(df_results, width='stretch')
