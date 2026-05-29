import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ==========================================
# 1. الدالات الفنية الدقيقة الحساب والمطابقة
# ==========================================

def calculate_wma(series, length):
    if len(series) < length:
        return pd.Series(index=series.index, data=np.nan)
    weights = np.arange(1, length + 1)
    return series.rolling(length).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

def calculate_hma(series, length):
    half_len = int(length / 2)
    sqrt_len = int(np.sqrt(length))
    wma_half = calculate_wma(series, half_len)
    wma_full = calculate_wma(series, length)
    diff = 2 * wma_half - wma_full
    return calculate_wma(diff, sqrt_len)

def calculate_kama(series, length=100, fast=2, slow=30):
    if len(series) <= length:
        return pd.Series(index=series.index, data=np.nan)
    mom = series.diff(length).abs()
    vol = series.diff().abs().rolling(length).sum()
    er = mom / (vol + 1e-10)
    fast_alpha = 2 / (fast + 1)
    slow_alpha = 2 / (slow + 1)
    sc = ((er * (fast_alpha - slow_alpha)) + slow_alpha) ** 2
    
    kama = np.zeros(len(series))
    kama[:] = np.nan
    kama[length] = series.iloc[length]
    for i in range(length + 1, len(series)):
        kama[i] = kama[i-1] + sc.iloc[i] * (series.iloc[i] - kama[i-1])
    return pd.Series(kama, index=series.index)

# ==========================================
# 2. واجهة المستخدم وإعدادات الرادار
# ==========================================
st.set_page_config(page_title="The Ultimate Trinity Radar Pro", layout="wide")
st.title("🎯 رادار الاقتناص الاحترافي المتوافق مع الشارت (Trinity & KAMA Pro)")

st.sidebar.header("⚙️ التحكم بحساسية التوافق")
# إضافة نسبة تسامح لمنع تقلبات البيانات الخاطئة بين المنصات
tolerance = st.sidebar.slider("نسبة فلتر التسامح لحركة HMA:", 0.0000, 0.0050, 0.0008, step=0.0001, 
                              help="زيادة النسبة تجعل الرادار أكثر صرامة في اختيار اللون الأخضر وتمنع إشارات ياهو فاينانس الوهمية")

kama_length = st.sidebar.number_input("KAMA Length (Trend)", value=100)
hma_length = st.sidebar.number_input("HMA Length (Signal)", value=21)

tab1, tab2 = st.tabs(["📊 الشارت وفحص الخطوط اللحظي", "🔍 رادار فحص وتصفية السوق"])

saudi_market = {
    "2310": "سبكيم العالمية", "3080": "أسمنت الشرقية", "4250": "جبل عمر", "4110": "باتك",
    "3010": "أسمنت العربية", "3020": "أسمنت اليمامة", "3030": "أسمنت السعودية", 
    "3040": "أسمنت القصيم", "3050": "أسمنت الجنوبية", "3060": "أسمنت ينبع", 
    "3090": "أسمنت تبوك", "1120": "الراجحي", "1180": "الأهلي", "1150": "الإنماء", 
    "2222": "أرامكو السعودية", "2010": "سابك", "2082": "معادن", "7010": "STC"
}

# ==========================================
# التبويب الأول: الشارت والتحقق
# ==========================================
with tab1:
    st.header("📈 استعراض دقة الإستراتيجية وفحص الخطوط")
    stock_number = st.text_input("اكتب رقم السهم لتبين حالته الحالية:", "2310", key="chart_input")
    
    if st.button("تحليل ورسم الشارت"):
        with st.spinner("جاري جلب البيانات وفحص التغير الحركي..."):
            ticker = f"{stock_number}.SR"
            df_1d = yf.Ticker(ticker).history(period="1y", interval="1d").dropna(subset=['Close'])
            
            if not df_1d.empty and len(df_1d) > 100:
                df_1d['KAMA'] = calculate_kama(df_1d['Close'], length=kama_length)
                df_1d['HMA_Signal'] = calculate_hma(df_1d['Close'], length=hma_length)
                
                hma_c = df_1d['HMA_Signal'].iloc[-1]
                hma_p = df_1d['HMA_Signal'].iloc[-2]
                
                # تطبيق شرط التسامح في الشارت أيضاً
                is_green = (hma_c - hma_p) > (hma_p * tolerance)
                curr_color = "🟢 أخضر (صاعد)" if is_green else "🔴 أحمر (هابط / تذبذب ضعيف)"
                
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df_1d.index, open=df_1d['Open'], high=df_1d['High'], low=df_1d['Low'], close=df_1d['Close'], name="السعر"))
                fig.add_trace(go.Scatter(x=df_1d.index, y=df_1d['KAMA'], name="KAMA (Blue)", line=dict(color='blue', width=2)))
                fig.add_trace(go.Scatter(x=df_1d.index, y=df_1d['HMA_Signal'], name="HMA Signal", line=dict(color='orange', width=2)))
                
                fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader(f"📊 قراءة الرادار الحالية للسهم رقم {stock_number}: خط HMA يعطي إشارة: **{curr_color}**")

# ==========================================
# التبويب الثاني: الرادار الذكي الحذر
# ==========================================
with tab2:
    st.header("🔍 تصفية السوق بناءً على تلوين خط HMA الفعلي")
    
    filter_choice = st.selectbox(
        "اختر تصفية الرادار الصارمة:",
        [
            "عرض الأسهم ذات خط HMA صاعد (أخضر على الشارت فقط)",
            "🔥 توافق ممتاز: السعر فوق KAMA و خط HMA أخضر صاعد"
        ]
    )
    
    if st.button("تشغيل تصفية الرادار الفورية 🚀"):
        results = []
        progress_bar = st.progress(0)
        total_stocks = len(saudi_market)
        
        for index, (code, name) in enumerate(saudi_market.items()):
            ticker_key = f"{code}.SR"
            try:
                df = yf.Ticker(ticker_key).history(period="1y", interval="1d").dropna(subset=['Close'])
                if len(df) < 100:
                    continue
                
                close = df['Close']
                c_price = close.iloc[-1]
                
                hma_series = calculate_hma(close, length=hma_length)
                kama_series = calculate_kama(close, length=kama_length)
                
                hma_curr = hma_series.iloc[-1]
                hma_prev = hma_series.iloc[-2]
                
                # إجبار الكود على اشتراط صعود حقيقي يتخطى نسبة التسامح المحددة في الشريط الجانبي
                is_hma_green = (hma_curr - hma_prev) > (hma_prev * tolerance)
                hma_status_str = "🟢 أخضر (صاعد)" if is_hma_green else "🔴 أحمر (هابط)"
                
                if filter_choice.startswith("عرض الأسهم") and not is_hma_green:
                    continue
                elif filter_choice.startswith("🔥") and not (c_price > kama_series.iloc[-1] and is_hma_green):
                    continue
                
                results.append({
                    "رقم السهم": code,
                    "اسم الشركة": name,
                    "السعر الحالي": round(float(c_price), 2),
                    "حالة مؤشر هال HMA": hma_status_str,
                    "موقع السعر من خط KAMA": "🟢 فوق الاتجاه" if c_price > kama_series.iloc[-1] else "🔴 تحت الاتجاه"
                })
            except:
                continue
            progress_bar.progress((index + 1) / total_stocks)
            
        progress_bar.empty()
        
        if results:
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.warning("لا توجد أسهم تطابق الشروط بدقة في الوقت الحالي.")
