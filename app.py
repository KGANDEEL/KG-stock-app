import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# دالة حساب ميل الخط (Slope) للتحقق من قوة الاتجاه
def calculate_slope(series, length=5):
    # نأخذ آخر 5 نقاط لنحسب زاوية الميل
    y = series.iloc[-length:].values
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)
    return slope

# (بقية الدوال كما هي: calculate_hma, calculate_kama, calculate_rsi)
# [ملاحظة: استخدم نفس الدوال السابقة لضمان الاستقرار]

# ==========================================
# الرادار الذكي بنظام "زاوية الميل" (Slope Radar)
# ==========================================
st.title("🎯 رادار القناص: نظام زاوية الميل (Slope-Based Trinity)")

if st.button("تفعيل الرادار القناص 🚀"):
    results = []
    # هنا يتم الفحص
    for code, name in saudi_market.items():
        try:
            df = yf.Ticker(f"{code}.SR").history(period="1y", interval="1d")
            close = df['Close']
            
            # حساب خط هال
            hma_series = calculate_hma(close, 21)
            
            # حساب قوة الميل (هذا هو السر!)
            current_slope = calculate_slope(hma_series, length=5)
            
            # شرط القناص: لا أخضر إلا إذا كان الميل إيجابياً وبقوة تفوق التذبذب
            is_strong_buy = current_slope > 0.05 
            
            if is_strong_buy:
                results.append({"السهم": name, "الحالة": "🟢 اتجاه صاعد قوي (مؤكد)"})
            else:
                results.append({"السهم": name, "الحالة": "🔴 اتجاه ضعيف أو هابط"})
        except:
            continue
    st.dataframe(pd.DataFrame(results))
