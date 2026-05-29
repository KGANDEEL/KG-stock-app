import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import time

# ==========================================
# 1. دالات الحسابات الفنية المخصصة (ترجمة إستراتيجيتك)
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

def calculate_rsi(series, length=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
    rs = gain / (loss + 1e-10)
    return 100 - (100 / (1 + rs))

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
# 2. إعدادات واجهة المستخدم
# ==========================================
st.set_page_config(page_title="منصة Trinity & KAMA Pro الشاملة", layout="wide")
st.title("🎯 منصة المسح والفرز الذكي - إستراتيجية HMA Trinity & KAMA Pro")

# إعدادات الشريط الجانبي
st.sidebar.header("⚙️ إعدادات الإستراتيجية الخاصة بك")
trading_style = st.sidebar.selectbox("نمط التداول الفعال:", ["Balanced", "Scalping", "Swing"])

if trading_style == "Scalping":
    hma_src_len, rsi_fast_len, rsi_slow_len, vol_hma_len, cmf_len = 5, 7, 14, 5, 10
elif trading_style == "Swing":
    hma_src_len, rsi_fast_len, rsi_slow_len, vol_hma_len, cmf_len = 21, 21, 50, 21, 30
else: # Balanced
    hma_src_len, rsi_fast_len, rsi_slow_len, vol_hma_len, cmf_len = 9, 14, 25, 9, 20

st.sidebar.write(f"ℹ️ نمط الحساب الحالي: **{trading_style}**")

# التبويبات الرئيسية
tab1, tab2 = st.tabs(["📊 شارت سهم محدد ومؤشراتك", "🔍 تصفية وفحص السوق الذكي"])

# ==========================================
# 3. القائمة الشاملة والمليئة بالأسهم (63 شركة قيادية ونشطة)
# ==========================================
saudi_market = {
    # --- الأسهم المطلوبة حديثاً وقطاع الإسمنت بالكامل (16 شركة) ---
    "4250": "جبل عمر", "4110": "باتك",
    "3010": "أسمنت العربية", "3020": "أسمنت اليمامة", "3030": "أسمنت السعودية", 
    "3040": "أسمنت القصيم", "3050": "أسمنت الجنوبية", "3060": "أسمنت ينبع", 
    "3080": "أسمنت الشرقية", "3090": "أسمنت تبوك", "3001": "أسمنت حائل", 
    "3002": "أسمنت نجران", "3003": "أسمنت المدينة", "3004": "أسمنت الشمالية", 
    "3005": "أسمنت أم القرى", "3092": "أسمنت الرياض",
    
    # --- قطاع البنوك والخدمات المالية (9 شركات) ---
    "1120": "الراجحي", "1180": "الأهلي", "1150": "الإنماء", "1140": "البلاد",
    "1010": "بنك الرياض", "1020": "بنك الجزيرة", "1030": "الاستثمار", "1050": "السعودي الفرنسي",
    "1080": "العربي",
    
    # --- قطاع الطاقة والبتروكيماويات والمواد الأساسية (8 شركات) ---
    "2222": "أرامكو السعودية", "2010": "سابك", "2310": "سبكيم العالمية", "2082": "معادن", 
    "2020": "سابك للمغذيات", "2330": "المتقدمة", "2002": "المجموعة السعودية", "2060": "التصنيع",
    
    # --- قطاع الاتصالات وتقنية المعلومات (5 شركات) ---
    "7010": "STC", "7020": "موبايلي", "7030": "زين السعودية", "7200": "عذيب للاتصالات", "4240": "سلوشنز",
    
    # --- قطاع الرعاية الصحية والأدوية (4 شركات) ---
    "4013": "سليمان الحبيب", "4004": "دله الصحية", "4002": "المواساة", "4009": "السعودي الألماني الصحي",
    
    # --- قطاع التجزئة والسلع الاستهلاكية والأغذية (7 شركات) ---
    "4003": "إكسترا", "2280": "المراعي", "4190": "جرير", "2290": "نادك", 
    "4001": "أسواق العثيم", "2050": "صافولا", "6001": "حلواني إخوان",
    
    # --- قطاع العقارات والإنشاءات (6 شركات) ---
    "4220": "إعمار", "4300": "دار الأركان", "4090": "طيبة للاستثمار", "4100": "مكة للإنشاء",
    "4321": "سينومي سنترز", "4150": "الرياض التعمير",
    
    # --- قطاع النقل والخدمات المتنوعة والتأمين (8 شركات) ---
    "4030": "البحري", "4260": "بدجت السعودية", "4071": "الذيب لتأجير السيارات", "1810": "سيرا",
    "8210": "بوبا العربية", "8010": "التعاونية", "2120": "متطورة", "4140": "الصادرات"
}

# ==========================================
# التبويب الأول: الشارت التفاعلي ومؤشراتك الخاصه
# ==========================================
with tab1:
    st.header("📈 استعراض مؤشرات الإستراتيجية على الشارت")
    stock_number = st.text_input("اكتب رقم السهم للي تبي تحلله:", "2222", key="chart_input")
    
    if st.button("عرض وتحليل الشارت"):
        with st.spinner("جاري تحليل البيانات ورسم الخطوط..."):
            df = yf.Ticker(f"{stock_number}.SR").history(period="1y")
            
            if not df.empty and len(df) > 100:
                df['KAMA'] = calculate_kama(df['Close'], length=100)
                df['HMA_Signal'] = calculate_hma(df['Close'], length=21)
                
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="السعر"))
                fig.add_trace(go.Scatter(x=df.index, y=df['KAMA'], name="KAMA (الاتجاه)", line=dict(color='cyan', width=2)))
                fig.add_trace(go.Scatter(x=df.index, y=df['HMA_Signal'], name="HMA (الإشارة)", line=dict(color='orange', width=1.5)))
                
                fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("تأكد من كتابة رقم سهم صحيح وتوفر بيانات كافية.")

# ==========================================
# التبويب الثاني: المسح الآلي مع التصفية الذكية
# ==========================================
with tab2:
    st.header("🕵️ لوحة التصفية والمسح الشامل للسوق")
    st.write(f"اللوحة مهيأة الآن لفحص **{len(saudi_market)} شركة** بناءً على معادلاتك الكمية المخصصة.")
    
    # إضافة الفلتر الذكي في الواجهة قبل البدء بالفحص
    st.markdown("### 🎛️ أدوات الفرز والتصفية الذكية")
    filter_choice = st.selectbox(
        "اختر الإشارات التي تريد عرضها في الجدول النهائي:",
        ["عرض كل الشركات بدون استثناء", "🟢 إشارات الشراء القوية فقط", "🟡 مناطق الانتظار والحياد فقط", "🔴 مناطق الخروج والاتجاه الهابط فقط"]
    )
    
    if st.button("تشغيل الفحص الذكي الفوري 🚀"):
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_stocks = len(saudi_market)
        
        for index, (code, name) in enumerate(saudi_market.items()):
            status_text.text(f"🔄 جاري معالجة وفحص {index + 1}/{total_stocks}: {name} ({code})...")
            
            try:
                stock_df = yf.Ticker(f"{code}.SR").history(period="1y")
                
                if not stock_df.empty and len(stock_df) >= 100:
                    # حساب المعادلات الفنية بدقة
                    stock_df['KAMA'] = calculate_kama(stock_df['Close'], length=100)
                    stock_df['HMA_Signal'] = calculate_hma(stock_df['Close'], length=21)
                    
                    price_hma = calculate_hma(stock_df['Close'], hma_src_len)
                    rsi_fast = calculate_rsi(price_hma, rsi_fast_len)
                    rsi_slow = calculate_rsi(price_hma, rsi_slow_len)
                    
                    vol_hma = calculate_hma(stock_df['Volume'], vol_hma_len)
                    
                    high, low, close, volume = stock_df['High'], stock_df['Low'], stock_df['Close'], stock_df['Volume']
                    ad = np.where(high == low, 0, ((2 * close - low - high) / (high - low)) * volume)
                    ad_series = pd.Series(ad, index=stock_df.index)
                    
                    mf = ad_series.rolling(cmf_len).sum() / (volume.rolling(cmf_len).sum() + 1e-10)
                    cmf_fast = calculate_hma(mf, 9)
                    cmf_slow = calculate_hma(mf, 21)
                    
                    # التقاط القيم الحالية
                    c_close, c_kama, c_hma, p_hma = close.iloc[-1], stock_df['KAMA'].iloc[-1], stock_df['HMA_Signal'].iloc[-1], stock_df['HMA_Signal'].iloc[-2]
                    c_rsi_f, c_rsi_s, p_rsi_f, p_rsi_s = rsi_fast.iloc[-1], rsi_slow.iloc[-1], rsi_fast.iloc[-2], rsi_slow.iloc[-2]
                    c_vol, c_v_hma, c_rsi_val = volume.iloc[-1], vol_hma.iloc[-1], calculate_rsi(close, 14).iloc[-1]
                    
                    # التحقق من الشروط
                    uptrend = c_close > c_kama
                    hma_turns_up = c_hma > p_hma
                    delta_filter = ad[-1] > 0
                    rsi_filter = c_rsi_val < 70
                    trinity_buy = (c_rsi_f > c_rsi_s) and (p_rsi_f <= p_rsi_s) and (c_vol > c_v_hma) and (cmf_fast.iloc[-1] > cmf_slow.iloc[-1])
                    
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
            time.sleep(0.01)  # الفحص سريع ومحمي
            
        status_text.empty()
        progress_bar.empty()
        
        if results:
            res_df = pd.DataFrame(results)
            
            # تطبيق الفلتر الذكي برمجياً على الجدول بناءً على اختيار المستخدم
            if filter_choice == "🟢 إشارات الشراء القوية فقط":
                res_df = res_df[res_df["الحالة الفنية بحسب مؤشرك"] == "🟢 إشارة شراء قوية (Trinity Buy)"]
            elif filter_choice == "🟡 مناطق الانتظار والحياد فقط":
                res_df = res_df[res_df["الحالة الفنية بحسب مؤشرك"] == "🟡 انتظار (منطقة حيادية)"]
            elif filter_choice == "🔴 مناطق الخروج والاتجاه الهابط فقط":
                res_df = res_df[res_df["الحالة الفنية بحسب مؤشرك"] == "🔴 خروج / اتجاه هابط"]
            
            # عرض النتائج المصفاة
            st.success(f"✅ تم الفحص بنجاح! تم العثور على {len(res_df)} شركة تطابق خيار التصفية الحالي.")
            if not res_df.empty:
                st.dataframe(res_df, use_container_width=True)
            else:
                st.warning("لا توجد شركات تطابق هذا الفلتر حالياً في السوق.")
        else:
            st.error("فشل جلب البيانات، يرجى المحاولة لاحقاً.")
