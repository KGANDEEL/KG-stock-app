import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# 1. تعريف القائمة أولاً لتجنب خطأ الـ NameError
saudi_market = {
    "2310": "سبكيم العالمية", "3080": "أسمنت الشرقية", "4250": "جبل عمر", "4110": "باتك",
    "3010": "أسمنت العربية", "3020": "أسمنت اليمامة", "3030": "أسمنت السعودية", 
    "3040": "أسمنت القصيم", "3050": "أسمنت الجنوبية", "3060": "أسمنت ينبع", 
    "3090": "أسمنت تبوك", "1120": "الراجحي", "1180": "الأهلي", "1150": "الإنماء", 
    "2222": "أرامكو السعودية", "2010": "سابك", "2082": "معادن", "7010": "STC"
}

# 2. الدوال الفنية
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

# 3. واجهة المستخدم
st.title("🎯 رادار القناص: نظام زاوية الميل")

if st.button("تفعيل الرادار القناص 🚀"):
    results = []
    # الآن الكود سيعرف saudi_market بدون مشاكل
    for code, name in saudi_market.items():
        try:
            df = yf.Ticker(f"{code}.SR").history(period="1y", interval="1d")
            if df.empty: continue
            
            close = df['Close']
            hma_series = calculate_hma(close, 21)
            
            # حساب الميل (الزخم)
            current_slope = calculate_slope(hma_series, length=5)
            
            # شرط الصعود القوي
            if current_slope > 0.05:
                results.append({"السهم": name, "الحالة": "🟢 اتجاه صاعد قوي (مؤكد)"})
            else:
                results.append({"السهم": name, "الحالة": "🔴 اتجاه ضعيف أو هابط"})
        except:
            continue
    st.dataframe(pd.DataFrame(results))
