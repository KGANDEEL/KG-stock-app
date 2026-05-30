import streamlit as st
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor

# دالة لقراءة القائمة من ملف CSV مباشرة
@st.cache_data
def get_full_saudi_market():
    # سيقرأ الملف ويحول البيانات لقاموس
    df = pd.read_csv('stocks.csv')
    return dict(zip(df['Symbol'].astype(str), df['Name']))

# باقي الدوال (calculate_hma, calculate_slope, scan_stock) تبقى كما هي

# عند بدء الرادار في التاب الثاني:
# سيعتمد الآن على القائمة القادمة من الملف مباشرة
# stocks = get_full_saudi_market()
