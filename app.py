import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor

# قائمة موسعة للأسهم السعودية
def get_all_stocks():
    return {
        "1120":"الراجحي", "1180":"الأهلي", "1150":"الإنماء", "1140":"البلاد", "1010":"الرياض", "1030":"الاستثمار", "1060":"الفرنسي",
        "2222":"أرامكو", "2010":"سابك", "7010":"STC", "2310":"سبكيم", "2082":"معادن", "3080":"أسمنت الشرقية", "3010":"أسمنت العربية",
        "3020":"أسمنت اليمامة", "3030":"أسمنت السعودية", "3040":"أسمنت القصيم", "3050":"أسمنت الجنوبية", "3060":"أسمنت ينبع",
        "3090":"أسمنت تبوك", "4250":"جبل عمر", "4110":"باتك", "4071":"سليمان الحبيب", "2380":"المتقدمة", "8230":"إتحاد اتصالات",
        "7020":"زين", "2060":"تنمية", "4001":"سلوشنز", "4002":"علم", "2090":"دار الأركان", "4300":"الإنماء العقارية", "1210":"جرير",
        "4003":"أكوا باور", "2280":"المواساة", "4004":"سماسكو", "2020":"سابك للمغذيات", "2350":"كيمانول", "4040":"سابتكو",
        "2150":"سافكو", "2160":"صناعات كهربائية", "1080":"سامبا", "1150":"الإنماء", "4010":"شمس", "4020":"الحكير"
    }

# الدوال الفنية
def calculate_hma(series, length):
    weights = np.arange(1, length + 1)
    def wma(s, l): return s.rolling(l).apply(lambda x: np.dot(x, weights[:l]) / weights[:l].sum(), raw=True)
    return wma(2 * wma(series, int(length/2)) - wma(series, length), int(np.sqrt(length)))

def calculate_slope(series, length=5):
    y = series.iloc[-length:].values
    x = np.arange(len(y))
    slope, _ = np.polyfit(x, y, 1)
    return slope

# الفحص الموازي
def scan_stock(code, name):
    try:
        df = yf.Ticker(f"{code}.SR").history(period="3mo", interval="1d")
        if df.empty: return None
        hma = calculate_hma(df['Close'], 21)
        slope = calculate_slope(hma, 5)
        if slope > 0.05: status, color = "إيجابي", "🟢"
        elif slope > -0.02: status, color = "مراقبة", "🟡"
        else: status, color = "سلبي", "🔴"
        return {"السهم": name, "الحالة": f"{color} {status}", "ميل HMA": round(slope, 4)}
    except: return None

# الواجهة
st.set_page_config(layout="wide")
st.title("🛡️ رادار القناص: المسح الشامل")

stocks = get_all_stocks()
tab1, tab2 = st.tabs(["📊 التحليل الفردي", "🔍 رادار السوق"])

with tab1:
    s_code = st.text_input("أدخل رمز السهم (مثال: 4040 لسابتكو):", "2310")
    if st.button("تحليل"):
        df = yf.Ticker(f"{s_code}.SR").history(period="1y", interval="1d")
        if not df.empty:
            hma = calculate_hma(df['Close'], 21)
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="السعر"))
            fig.add_trace(go.Scatter(x=df.index, y=hma, name="HMA 21", line=dict(color='yellow')))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("لم يتم العثور على بيانات لهذا الرمز، تأكد من الرقم!")

with tab2:
    if st.button("ابدأ المسح الشامل لكل الأسهم"):
        with st.spinner("جاري فحص السوق..."):
            with ThreadPoolExecutor(max_workers=10) as executor:
                results = list(executor.map(lambda p: scan_stock(*p), stocks.items()))
            clean_results = [r for r in results if r is not None]
            st.dataframe(pd.DataFrame(clean_results), use_container_width=True)
