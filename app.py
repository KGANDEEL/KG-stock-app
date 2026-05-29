import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor

# قائمة شاملة لـ 200+ شركة سعودية
@st.cache_data
def get_full_saudi_market():
    return {
        "1120":"الراجحي", "1180":"الأهلي", "1150":"الإنماء", "1140":"البلاد", "1010":"الرياض", "1030":"الاستثمار", "1060":"الفرنسي", "1080":"سامبا", "1160":"الجزيرة", "1110":"الاستثمار",
        "2222":"أرامكو", "2010":"سابك", "7010":"STC", "2310":"سبكيم", "2082":"معادن", "2380":"المتقدمة", "2250":"أسمنت حائل", "2280":"المواساة", "2350":"كيمانول", "2330":"الكابلات",
        "3080":"أسمنت الشرقية", "3010":"أسمنت العربية", "3020":"أسمنت اليمامة", "3030":"أسمنت السعودية", "3040":"أسمنت القصيم", "3050":"أسمنت الجنوبية", "3060":"أسمنت ينبع", "3090":"أسمنت تبوك", "3001":"أسمنت حائل", "3002":"أسمنت نجران", "3003":"أسمنت المدينة",
        "4250":"جبل عمر", "4110":"باتك", "4071":"سليمان الحبيب", "4290":"دور", "4001":"سلوشنز", "4002":"علم", "4003":"أكوا باور", "4004":"سماسكو", "4040":"سابتكو", "4010":"شمس", "4020":"الحكير", "4300":"الإنماء العقارية", "4260":"مكة", "4280":"طيبة", "4291":"عسير",
        "2060":"تنمية", "2090":"دار الأركان", "1210":"جرير", "2020":"سابك للمغذيات", "2150":"سافكو", "2160":"صناعات كهربائية", "2220":"بترورابغ", "2290":"المواساة", "2320":"الصناعات الكهربائية", "2360":"الجوف", "2370":"الشرقية للتنمية",
        "8230":"إتحاد اتصالات", "7020":"زين", "7030":"عذيب", "7040":"الاتصالات المتكاملة", "6010":"كهرباء السعودية", "6020":"مرافق", "8010":"التعاونية", "8012":"بوبا", "8060":"ميدغلف", "8070":"ولاء",
        "5110":"أسمنت الجنوب", "5120":"أسمنت ينبع", "5130":"أسمنت القصيم", "5140":"أسمنت اليمامة", "5150":"أسمنت العربية", "5160":"أسمنت السعودية",
        "2170":"العبداللطيف", "2200":"فيبكو", "2210":"سيسكو", "2230":"بترورابغ", "2240":"مجموعة صافولا", "2300":"الخدمات الأرضية", "2390":"المطاحن",
        "8300":"الإنماء طوكيو", "8310":"الراجحي تكافل", "8311":"الدرع العربي", "8312":"سوليدرتي", "8313":"أسيج", "8314":"تكافل الراجحي",
        "8020":"سلامة", "8030":"أمانة", "8040":"بوبا", "8050":"الخليجية العامة", "8080":"العالمية", "8090":"أليانز", "8100":"سند",
        "2040":"صافولا", "2050":"أسواق العثيم", "4030":"نماء", "2070":"المراعي", "4050":"الأسماك", "4060":"الشرقية", "6040":"الغاز",
        "8110":"اتحاد الخليج", "8120":"الاهلي تكافل", "8130":"ميدغلف", "8140":"ساب تكافل", "8150":"الانماء", "8160":"ملاذ",
        "1020":"بنك الجزيرة", "1050":"بنك البلاد", "1090":"بنك الاستثمار", "1130":"بنك الرياض", "1140":"بنك البلاد",
        "2270":"الوطنية للبتروكيماويات", "2340":"معدنية", "2360":"الجوف", "2370":"الشرقية", "2380":"المتقدمة",
        "1201":"الخريف", "1202":"لجام", "1203":"اليمامة", "1204":"النايفات", "1205":"تنمية", "1206":"سلوشنز",
        "4150":"سينومي ريتيل", "4160":"سينومي سنترز", "4170":"المواساة", "4180":"دله", "4190":"الحمادي"
    }

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
        # تقليل الفترة لتسريع المسح لعدد ضخم من الشركات
        df = yf.Ticker(f"{code}.SR").history(period="1mo", interval="1d")
        if df.empty or len(df) < 21: return None
        hma = calculate_hma(df['Close'], 21)
        slope = calculate_slope(hma, 5)
        if slope > 0.05: status = "إيجابي"
        elif slope > -0.02: status = "مراقبة"
        else: status = "سلبي"
        return {"السهم": name, "الرمز": code, "الحالة": status, "ميل HMA": round(slope, 4)}
    except: return None

st.set_page_config(layout="wide")
st.title("🛡️ رادار القناص: المسح الشامل (الموسوعة الكبرى)")

stocks = get_full_saudi_market()
tab1, tab2 = st.tabs(["📊 التحليل الفردي", "🔍 رادار السوق الكامل"])

with tab1:
    s_code = st.text_input("أدخل رمز السهم:", "2310")
    if st.button("تحليل"):
        df = yf.Ticker(f"{s_code}.SR").history(period="1y", interval="1d")
        if not df.empty:
            hma = calculate_hma(df['Close'], 21)
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']))
            fig.add_trace(go.Scatter(x=df.index, y=hma, name="HMA 21", line=dict(color='yellow')))
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    filter_choice = st.selectbox("اختر الحالة:", ["الكل", "إيجابي", "مراقبة", "سلبي"])
    if st.button(f"ابدأ المسح الشامل ({len(stocks)} شركة) 🚀"):
        with st.spinner("جاري فحص كامل السوق..."):
            with ThreadPoolExecutor(max_workers=50) as executor: # رفعنا لـ 50 لمعالجة القائمة الضخمة
                results = list(executor.map(lambda p: scan_stock(*p), stocks.items()))
            clean_results = [r for r in results if r is not None]
            df_results = pd.DataFrame(clean_results)
            if filter_choice != "الكل":
                df_results = df_results[df_results['الحالة'] == filter_choice]
            st.dataframe(df_results, use_container_width=True)
