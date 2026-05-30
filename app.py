import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor

# 1. قراءة البيانات
@st.cache_data
def get_full_saudi_market():
    try:
        df = pd.read_csv('stocks.csv')
        # التأكد من أن الرمز نص (String) ليحافظ على الأصفار في البداية
        df['Symbol'] = df['Symbol'].astype(str).str.zfill(4)
        return dict(zip(df['Symbol'], df['Name']))
    except Exception as e:
        st.error(f"خطأ في قراءة ملف CSV: {e}")
        return {}

# 2. الدوال الحسابية
def calculate_hma(series, length):
    weights = np.arange(1, length + 1)
    def wma(s, l): return s.rolling(l).apply(lambda x: np.dot(x, weights[:l]) / weights[:l].sum(), raw=True)
    return wma(2 * wma(series, int(length/2)) - wma(series, length), int(np.sqrt(length)))

def calculate_slope(series, length=5):
    y = series.iloc[-length:].values
    x = np.arange(len(y))
    slope, _ = np.polyfit(x, y, 1)
    return slope

# 3. محرك المسح (النسخة الذكية التي تكشف الأخطاء)
def scan_stock(code, name):
    try:
        ticker = yf.Ticker(f"{code}.SR")
        df = ticker.history(period="3mo", interval="1d")
        
        if df.empty:
            return {"السهم": name, "الرمز": code, "الحالة": "فشل (لا بيانات)", "ميل HMA": 0}
        
        if len(df) < 21:
            return {"السهم": name, "الرمز": code, "الحالة": "فشل (بيانات قليلة)", "ميل HMA": 0}
            
        hma = calculate_hma(df['Close'], 21)
        slope = calculate_slope(hma, 5)
        
        if slope > 0.05: status = "إيجابي"
        elif slope > -0.02: status = "مراقبة"
        else: status = "سلبي"
        
        return {"السهم": name, "الرمز": code, "الحالة": status, "ميل HMA": round(slope, 4)}
    except:
        return {"السهم": name, "الرمز": code, "الحالة": "خطأ تقني", "ميل HMA": 0}

# 4. الواجهة
st.set_page_config(layout="wide")
st.title("🛡️ رادار القناص: المسح الشامل")

stocks = get_full_saudi_market()
st.sidebar.write(f"إجمالي الشركات في الملف: {len(stocks)}")

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
            st.plotly_chart(fig, width='stretch')
        else:
            st.warning("رمز غير صحيح أو لا توجد بيانات!")

with tab2:
    filter_choice = st.selectbox("اختر الحالة:", ["الكل", "إيجابي", "مراقبة", "سلبي", "فشل (لا بيانات)"])
    if st.button(f"ابدأ المسح لـ {len(stocks)} شركة 🚀"):
        with st.spinner("جاري المسح..."):
            with ThreadPoolExecutor(max_workers=30) as executor:
                results = list(executor.map(lambda p: scan_stock(*p), stocks.items()))
            
            df_results = pd.DataFrame(results)
            
            if filter_choice != "الكل":
                df_results = df_results[df_results['الحالة'] == filter_choice]
            
            st.dataframe(df_results, width='stretch')
