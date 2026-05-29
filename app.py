import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import time

# ==========================================
# 1. دالات الحسابات الفنية المخصصة (ترجمة Pine Script)
# ==========================================

# حساب المتوسط المتحرك الموزون (WMA)
def calculate_wma(series, length):
    if len(series) < length:
        return pd.Series(index=series.index, data=np.nan)
    weights = np.arange(1, length + 1)
    return series.rolling(length).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

# حساب متوسط هال المتحرك (HMA)
def calculate_hma(series, length):
    half_len = int(length / 2)
    sqrt_len = int(np.sqrt(length))
    wma_half = calculate_wma(series, half_len)
    wma_full = calculate_wma(series, length)
    diff = 2 * wma_half - wma_full
    return calculate_wma(diff, sqrt_len)

# حساب مؤشر القوة النسبية (RSI)
def calculate_rsi(series, length=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
    rs = gain / (loss + 1e-10)
    return 100 - (100 / (1 + rs))

# حساب مؤشر كوفمان التكيفي (KAMA)
def calculate_kama(series, length=100, fast=2, slow=30):
    mom = series.diff(length).abs()
    vol = series.diff().abs().rolling(length).sum()
    er = mom / (vol + 1e-10)
    
    fast_alpha = 2 / (fast + 1)
    slow_alpha = 2 / (slow + 1)
    sc = ((er * (fast_alpha - slow_alpha)) + slow_alpha) ** 2
    
    kama = np.zeros(len(series))
    start_idx = length
    if start_idx >= len(series):
        return pd.Series(index=series.index, data=np.nan)
    
    kama[:start_idx] = np.nan
    kama[start_idx] = series.iloc[start_idx]
    
    for i in range(start_idx + 1, len(series)):
        kama[i] = kama[i-1] + sc.iloc[i] * (series.iloc[i] - kama[i-1])
        
    return pd.Series(kama, index=series.index)

# ==========================================
# 2. إعدادات واجهة مستخدم Streamlit
# ==========================================
st.set_page_config(page_title="منصة Trinity & KAMA Pro", layout="wide")
st.title("🎯 منصة المسح الكمي الذكي - إستراتيجية HMA Trinity & KAMA Pro")

# شريط جانبي للإعدادات ليعطي طابع المنصات الاحترافية
st.sidebar.header("⚙️ إعدادات الإستراتيجية الخاصة بك")
trading_style = st.sidebar.selectbox("نمط التداول الفعال:", ["Balanced", "Scalping", "Swing"])

# تحديد أطوال المؤشرات بناءً على نمط التداول المختار (نفس منطق كودك تماماً)
if trading_style == "Scalping":
    hma_src_len, rsi_fast_len, rsi_slow_len, vol_hma_len, cmf_len = 5, 7, 14, 5, 10
elif trading_style == "Swing":
    hma_src_len, rsi_fast_len, rsi_slow_len, vol_hma_len, cmf_len = 21, 21, 50, 21, 30
else: # Balanced
    hma_src_len, rsi_fast_len, rsi_slow_len, vol_hma_len, cmf_len = 9, 14, 25, 9, 20

st.sidebar.write(f"ℹ️ تم تطبيق أوزان نمط **{trading_style}** تلقائياً على المحرك الفني.")

tab1, tab2 = st.tabs(["📊 شارت سهم محدد ومؤشراتك", "🔍 تصفية السوق الآلية الشاملة"])

# قائمة موسعة بـ 40 شركة كبرى في السوق السعودي تغطي أغلب القطاعات
saudi_market = {
    "2222": "أرامكو", "1120": "الراجحي", "2010": "سابك", "7010": "STC", "1180": "الأهلي", 
    "1150": "الإنماء", "2310": "سبكيم", "5110": "كهرباء السعودية", "2082": "معادن", "4220": "إعمار",
    "4003": "إكسترا", "2280": "المراعي", "4030": "البحري", "7020": "موبايلي", "7030": "زين",
    "4190": "جرير", "1020": "بنك الجزيرة", "1030": "استثمار", "1080": "العربي", "2290": "نادك", 
    "4004": "دله الصحية", "4013": "سليمان الحبيب", "2020": "سابك للمغذيات", "1140": "البلاد",
    "8210": "ببوبا العربية", "4090": "طيبه", "4250": "جبل عمر", "4100": "مكة الإنشاء",
    "2120": "متطورة", "2330": "المتقدمة", "1211": "معادن", "4260": "بدجت السعودية",
    "4071": "الذيب لتأجير السيارات", "4300": "دار الأركان", "6001": "حلواني إخوان", "2140": "أييان",
    "1304": "اليمامة للحديد", "1810": "سيرا", "4040": "القمة", "4140": "الصادرات"
}

# ==========================================
# التبويب الأول: شارت السهم مع خطوط المؤشرات الخاصة بك
# ==========================================
with tab1:
    st.header("📈 استعراض مؤشرات الإستراتيجية على الشارت")
    stock_number = st.text_input("اكتب رقم السهم:", "2222", key="one")
    
    with st.spinner("جاري تحليل الشارت ورسم الخطوط..."):
        # سحب بيانات سنة كاملة لكي يستقر حساب مؤشر KAMA (يحتاج 100 شمعة كحد أدنى)
        df = yf.Ticker(f"{stock_number}.SR").history(period="1y")
        
        if not df.empty and len(df) > 100:
            # حساب المؤشرات للشارت
            df['KAMA'] = calculate_kama(df['Close'], length=100)
            df['HMA_Signal'] = calculate_hma(df['Close'], length=21)
            
            fig = go.Figure()
            # رسم الشموع
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="السعر"))
            # رسم خط KAMA (الاتجاه)
            fig.add_trace(go.Scatter(x=df.index, y=df['KAMA'], name="KAMA (الاتجاه العام)", line=dict(color='blue', width=2)))
            # رسم خط HMA (الإشارة)
            fig.add_trace(go.Scatter(x=df.index, y=df['HMA_Signal'], name="HMA (خط الإشارة)", line=dict(color='orange', width=1.5)))
            
            fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("تأكد من رقم السهم أو وفر بيانات كافية.")

# ==========================================
# التبويب الثاني: الفحص والمسح الآلي الفوري بناءً على الكود الخاص بك
# ==========================================
with tab2:
    st.header("🕵️ لوحة التصفية الرقمية لـ 40 شركة قيادية")
    st.write(f"سيقوم النظام الآن بفحص {len(saudi_market)} شركة بناءً على شروط دخول صفقة الشراء المعقدة في إستراتيجيتك.")
    
    if st.button("بدء المسح المتقدم للسوق 🚀"):
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_stocks = len(saudi_market)
        
        for index, (code, name) in enumerate(saudi_market.items()):
            status_text.text(f"🔄 جاري تطبيق خوارزمية Trinity Pro على: {name}...")
            
            try:
                # جلب البيانات
                stock_df = yf.Ticker(f"{code}.SR").history(period="1y")
                
                if not stock_df.empty and len(stock_df) >= 100:
                    # 1. الحسابات الفنية الأساسية من كودك
                    stock_df['KAMA'] = calculate_kama(stock_df['Close'], length=100)
                    stock_df['HMA_Signal'] = calculate_hma(stock_df['Close'], length=21)
                    
                    # 2. مكونات Trinity
                    price_hma = calculate_hma(stock_df['Close'], hma_src_len)
                    rsi_fast = calculate_rsi(price_hma, rsi_fast_len)
                    rsi_slow = calculate_rsi(price_hma, rsi_slow_len)
                    
                    vol_hma = calculate_hma(stock_df['Volume'], vol_hma_len)
                    
                    # 3. حساب سيولة CMF وبصمة الفوليوم
                    high, low, close, volume = stock_df['High'], stock_df['Low'], stock_df['Close'], stock_df['Volume']
                    ad = np.where(high == low, 0, ((2 * close - low - high) / (high - low)) * volume)
                    ad_series = pd.Series(ad, index=stock_df.index)
                    
                    mf = ad_series.rolling(cmf_len).sum() / (volume.rolling(cmf_len).sum() + 1e-10)
                    cmf_fast = calculate_hma(mf, 9)
                    cmf_slow = calculate_hma(mf, 21)
                    
                    # قيم الشمعة الأخيرة (الحالية) والقبل الأخيرة للحسابات التوجيهية
                    c_close, c_kama, c_hma, p_hma = close.iloc[-1], stock_df['KAMA'].iloc[-1], stock_df['HMA_Signal'].iloc[-1], stock_df['HMA_Signal'].iloc[-2]
                    c_rsi_f, c_rsi_s, p_rsi_f, p_rsi_s = rsi_fast.iloc[-1], rsi_slow.iloc[-1], rsi_fast.iloc[-2], rsi_slow.iloc[-2]
                    c_vol, c_v_hma, c_rsi_val = volume.iloc[-1], vol_hma.iloc[-1], calculate_rsi(close, 14).iloc[-1]
                    
                    # 4. التحقق من الشروط البرمجية الخاصة بك (Buy Conditions)
                    uptrend = c_close > c_kama
                    hma_turns_up = c_hma > p_hma
                    delta_filter = ad[-1] > 0
                    rsi_filter = c_rsi_val < 70
                    
                    # تقاطع الـ RSI المطور مع فوليوم وسيولة صاعدة
                    trinity_buy = (c_rsi_f > c_rsi_s) and (p_rsi_f <= p_rsi_s) and (c_vol > c_v_hma) and (cmf_fast.iloc[-1] > cmf_slow.iloc[-1])
                    
                    # القرار النهائي
                    if uptrend and hma_turns_up and delta_filter and rsi_filter and trinity_buy:
                        decision = "🟢 إشارة شراء قوية (Trinity Buy)"
                    elif c_close < c_kama:
                        decision = "🔴 خروج / اتجاه هابط"
                    else:
                        decision = "🟡 انتظار (منطقة حيادية)"
                        
                    results.append({
                        "رقم السهم": code,
                        "اسم الشركة": name,
                        "السعر الحالي": round(float(c_close), 2),
                        "الحالة الفنية بحسب مؤشرك": decision
                    })
            except Exception as e:
                continue
                
            progress_bar.progress((index + 1) / total_stocks)
            time.sleep(0.05)
            
        status_text.empty()
        progress_bar.empty()
        
        if results:
            res_df = pd.DataFrame(results)
            st.success("✅ اكتمل الفحص الكمي بنجاح!")
            # عرض البيانات بجدول تفاعلي رائع
            st.dataframe(res_df, use_container_width=True)
        else:
            st.error("فشل جلب البيانات.")
