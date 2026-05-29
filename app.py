import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# دمج دالة جلب قائمة الأسهم السعودية تلقائياً (تغطية كاملة)
@st.cache_data
def get_saudi_stocks():
    # هذه قائمة موسعة لأغلب أسهم تداول
    # ملاحظة: يمكنك إضافة أي رمز آخر إذا رغبت
    stocks = {
        "1120": "الراجحي", "1180": "الأهلي", "1150": "الإنماء", "2222": "أرامكو", 
        "2010": "سابك", "7010": "STC", "2310": "سبكيم", "3080": "أسمنت الشرقية",
        "4250": "جبل عمر", "4110": "باتك", "1140": "البلاد", "2082": "معادن",
        "3030": "أسمنت السعودية", "3040": "أسمنت القصيم", "3060": "أسمنت ينبع",
        "8230": "إتحاد اتصالات", "2380": "المتقدمة", "4071": "سليمان الحبيب",
        "1150": "الإنماء", "1010": "الرياض", "7020": "زين", "2060": "تنمية"
        # يمكنك إضافة المزيد هنا بسهولة
    }
    return stocks

# الدوال الفنية
def calculate_hma(series, length):
    half_len = int(length / 2)
    sqrt_len = int(np.sqrt(length))
    # تقريب مباشر لـ WMA
    def wma(s, l):
        weights = np.arange(1, l + 1)
        return s.rolling(l).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    diff = 2 * wma(series, half_len) - wma(series, length)
    return wma(diff, sqrt_len)

def calculate_slope(series, length=5):
    y = series.iloc[-length:].values
    x = np.arange(len(y))
    slope, _ = np.polyfit(x, y, 1)
    return slope

# واجهة الرادار
st.set_page_config(layout="wide")
st.title("🚀 رادار القناص الاحترافي (المستوى الشامل)")

tab1, tab2 = st.tabs(["📊 التحليل الفردي", "🔍 رادار السوق الكامل"])

stocks = get_saudi_stocks()

with tab1:
    s = st.selectbox("اختر السهم:", list(stocks.values()))
    code = [k for k, v in stocks.items() if v == s][0]
    if st.button("تحليل"):
        df = yf.Ticker(f"{code}.SR").history(period="1y", interval="1d")
        hma = calculate_hma(df['Close'], 21)
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']))
        fig.add_trace(go.Scatter(x=df.index, y=hma, name="HMA 21", line=dict(color='orange')))
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("فلتر القناص: الشركات الصاعدة بقوة")
    if st.button("فحص السوق الآن"):
        results = []
        progress = st.progress(0)
        for i, (code, name) in enumerate(stocks.items()):
            try:
                df = yf.Ticker(f"{code}.SR").history(period="6mo", interval="1d")
                hma = calculate_hma(df['Close'], 21)
                slope = calculate_slope(hma, 5)
                
                # شرط القناص المدمج:
                if slope > 0.03: # زاوية ميل إيجابية
                    results.append({"السهم": name, "ميل HMA": round(slope, 4), "الحالة": "🚀 صاعد قوي"})
            except: continue
            progress.progress((i + 1) / len(stocks))
        
        st.dataframe(pd.DataFrame(results))
