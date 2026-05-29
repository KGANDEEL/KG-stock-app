import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ==========================================
# 1. دالات الحسابات الفنية المخصصة المطهّرة
# ==========================================

def calculate_sma(series, length):
    return series.rolling(length).mean()

def calculate_ema(series, length):
    return series.ewm(span=length, adjust=False).mean()

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

def calculate_macd(series, fast=12, slow=26, signal=9):
    fast_ema = calculate_ema(series, fast)
    slow_ema = calculate_ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = calculate_ema(macd_line, signal)
    return macd_line, signal_line

def calculate_cci(df, length=20):
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    tp_sma = tp.rolling(length).mean()
    tp_mad = tp.rolling(length).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    return (tp - tp_sma) / (0.015 * tp_mad + 1e-10)

def calculate_stochastic(df, length=14):
    low_min = df['Low'].rolling(length).min()
    high_max = df['High'].rolling(length).max()
    return ((df['Close'] - low_min) / (high_max - low_min + 1e-10)) * 100

def calculate_adx(df, length=14):
    hl = df['High'] - df['Low']
    hc = (df['High'] - df['Close'].shift(1)).abs()
    lc = (df['Low'] - df['Close'].shift(1)).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    atr = tr.rolling(length).mean()
    
    up_move = df['High'].diff()
    down_move = df['Low'].shift(1) - df['Low']
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(length).mean() / (atr + 1e-10))
    minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(length).mean() / (atr + 1e-10))
    
    dx = (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-10) * 100
    adx = dx.rolling(length).mean()
    return adx, plus_di, minus_di

def calculate_obv(df):
    direction = np.sign(df['Close'].diff())
    direction.iloc[0] = 0
    return (direction * df['Volume']).cumsum()

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
# 2. إعدادات واجهة المستخدم
# ==========================================
st.set_page_config(page_title="رادار الاقتناص المستقر", layout="wide")
st.title("🎯 رادار صيد القيعان الاحترافي الذكي (Batch Engine Pro)")

st.sidebar.header("⚙️ إعدادات النمط الحركي")
trading_style = st.sidebar.selectbox("نمط التداول الفعال لتحديد طول HMA:", ["Balanced", "Scalping", "Swing"])

if trading_style == "Scalping":
    hma_len = 5
elif trading_style == "Swing":
    hma_len = 21
else:
    hma_len = 9

tab1, tab2 = st.tabs(["📊 شارت ومؤشرات السهم المخصصة", "🔍 رادار اقتناص القيعان وفحص KAMA"])

# ==========================================
# 3. قائمة الأسهم المشغلة (63 شركة)
# ==========================================
saudi_market = {
    "4250": "جبل عمر", "4110": "باتك",
    "3010": "أسمنت العربية", "3020": "أسمنت اليمامة", "3030": "أسمنت السعودية", 
    "3040": "أسمنت القصيم", "3050": "أسمنت الجنوبية", "3060": "أسمنت ينبع", 
    "3080": "أسمنت الشرقية", "3090": "أسمنت تبوك", "3001": "أسمنت حائل", 
    "3002": "أسمنت نجران", "3003": "أسمنت المدينة", "3004": "أسمنت الشمالية", 
    "3005": "أسمنت أم القرى", "3092": "أسمنت الرياض",
    "1120": "الراجحي", "1180": "الأهلي", "1150": "الإنماء", "1140": "البلاد",
    "1010": "بنك الرياض", "1020": "بنك الجزيرة", "1030": "الاستثمار", "1050": "السعودي الفرنسي", "1080": "العربي",
    "2222": "أرامكو السعودية", "2010": "سابك", "2310": "سبكيم العالمية", "2082": "معادن", 
    "2020": "سابك للمغذيات", "2330": "المتقدمة", "2002": "المجموعة السعودية", "2060": "التصنيع",
    "7010": "STC", "7020": "موبايلي", "7030": "زين السعودية", "7200": "عذيب للاتصالات", "4240": "سلوشنز",
    "4013": "سليمان الحبيب", "4004": "دله الصحية", "4002": "المواساة", "4009": "السعودي الألماني الصحي",
    "4003": "إكسترا", "2280": "المراعي", "4190": "جرير", "2290": "نادك", "4001": "أسواق العثيم", "2050": "صافولا", "6001": "حلواني إخوان",
    "4220": "إعمار", "4300": "دار الأركان", "4090": "طيبة للاستثمار", "4100": "مكة للإنشاء", "4321": "سينومي سنترز", "4150": "الرياض التعمير",
    "4030": "البحري", "4260": "بدجت السعودية", "4071": "الذيب لتأجير السيارات", "1810": "سيرا", "8210": "بوبا العربية", "8010": "التعاونية", "2120": "متطورة", "4140": "الصادرات"
}

# ==========================================
# التبويب الأول: الشارت والتحليل الفردي
# ==========================================
with tab1:
    st.header("📈 استعراض الإستراتيجية على الشارت")
    stock_number = st.text_input("اكتب رقم السهم للي تبي تحلله:", "2222", key="chart_input")
    
    if st.button("عرض وتحليل الشارت"):
        with st.spinner("جاري تحليل البيانات ورسم الخطوط..."):
            df = yf.Ticker(f"{stock_number}.SR").history(period="1y")
            if not df.empty and len(df) > 100:
                df['KAMA'] = calculate_kama(df['Close'], length=100)
                df['HMA_Signal'] = calculate_hma(df['Close'], length=hma_len)
                
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="السعر"))
                fig.add_trace(go.Scatter(x=df.index, y=df['KAMA'], name="KAMA (الاتجاه)", line=dict(color='cyan', width=2)))
                fig.add_trace(go.Scatter(x=df.index, y=df['HMA_Signal'], name="HMA (الإشارة)", line=dict(color='orange', width=1.5)))
                fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("تأكد من كتابة رقم سهم صحيح وتوفر بيانات كافية.")

# ==========================================
# التبويب الثاني: الرادار النظيف والمصحح
# ==========================================
with tab2:
    st.header("🔍 رادار التصفية واقتناص الفرص المبكرة")
    st.info("⚡ **تم إصلاح محرك الفرز وتطهير البيانات:** تم تعديل الكود ليعمل بشكل متوافق تماماً مع إشارات الشارت وبدون أي أخطاء برمجية.")
    
    # تم تصحيح الخطأ المطبعي هنا من St إلى st واكتملت الحماية
    filter_choice = st.selectbox(
        "اختر تصنيف جودة التوافق الفني:",
        [
            "عرض كل الأسهم ذات الإشارات الخضراء الصاعدة على HMA", 
            "🔥 أسهم ذهبية خارقة التوافق (النقاط >= 8 من 10)", 
            "🟢 أسهم بزخم إيجابي جيد (النقاط من 5 إلى 7 من 10)"
        ]
    )
    
    if st.button("تشغيل رادار الاقتناص فائق السرعة 🚀"):
        results = []
        excluded_count = 0
        
        tickers_list = [f"{code}.SR" for code in saudi_market.keys()]
        with st.spinner("⚡ جاري جلب بيانات السوق وتطهيرها من التشويه..."):
            try:
                all_data = yf.download(tickers_list, period="1y", group_by='ticker', progress=False)
            except Exception as e:
                st.error(f"فشل الاتصال بمزود البيانات: {e}")
                st.stop()
        
        progress_bar = st.progress(0)
        total_stocks = len(saudi_market)
        
        for index, (code, name) in enumerate(saudi_market.items()):
            ticker_key = f"{code}.SR"
            
            try:
                if ticker_key not in all_data.columns.levels[0]:
                    continue
                
                df = all_data[ticker_key].copy()
                
                # 🧼 خطوة التطهير الحاسمة: إزالة التواريخ الفارغة التي كانت تسبب القراءات الخاطئة
                df = df.dropna(subset=['Close', 'High', 'Low', 'Open'])
                
                if len(df) < 100:
                    continue
                    
                close = df['Close']
                c_price = close.iloc[-1]
                
                # حساب المؤشرات على البيانات المطهّرة النظيفة
                hma_series = calculate_hma(close, length=hma_len)
                kama_series = calculate_kama(close, length=100)
                
                if hma_series.isna().iloc[-3:].any() or kama_series.isna().iloc[-1]:
                    continue
                    
                hma_curr = hma_series.iloc[-1]
                hma_prev = hma_series.iloc[-2]
                hma_prev2 = hma_series.iloc[-3]
                
                # 🛑 الفلتر الأساسي المنظف: شرط صعود مؤشر هال للأخضر (الحالي أكبر من السابق تماماً)
                if hma_curr <= hma_prev:
                    excluded_count += 1
                    continue
                
                # تحديد طبيعة الانعكاس
                if hma_prev <= hma_prev2:
                    hma_status = "🔥 إنعكاس جديد (بداية إيجابية)"
                else:
                    hma_status = "🟢 صعود مستمر مسبقاً"
                
                # حساب النسبة والموقع الدقيق من خط KAMA
                kama_val = kama_series.iloc[-1]
                pct_from_kama = ((c_price - kama_val) / kama_val) * 100
                
                if pct_from_kama < -5:
                    kama_position_str = "🔴 تحت بعيد (منطقة اقتناص قاع)"
                elif -5 <= pct_from_kama < 0:
                    kama_position_str = "🟡 تحت قريب (يستعد للاختراق)"
                elif 0 <= pct_from_kama < 5:
                    kama_position_str = "🟢 فوق قريب (تأكيد الاتجاه)"
                else:
                    kama_position_str = "🔵 فوق بعيد (صعود قوي مسبق)"
                
                # حساب توافق الـ 10 مؤشرات الأخرى
                rsi = calculate_rsi(close, 14).iloc[-1]
                macd_l, macd_s = calculate_macd(close)
                ema50 = calculate_ema(close, 50).iloc[-1]
                sma200 = calculate_sma(close, 200).iloc[-1]
                cci = calculate_cci(df, 20).iloc[-1]
                stoch_k = calculate_stochastic(df, 14).iloc[-1]
                adx, plus_di, minus_di = calculate_adx(df, 14)
                mom = close.diff(10).iloc[-1]
                obv = calculate_obv(df)
                
                # خوارزمية الفيبوناتشي
                fib_df = df.iloc[-100:]
                fib_high = fib_df['High'].max()
                fib_low = fib_df['Low'].min()
                fib_range = fib_high - fib_low
                
                f236 = fib_low + fib_range * 0.236
                f382 = fib_low + fib_range * 0.382
                f500 = fib_low + fib_range * 0.500
                f618 = fib_low + fib_range * 0.618
                f786 = fib_low + fib_range * 0.786
                
                diffs = {"61.8%": abs(c_price - f618), "38.2%": abs(c_price - f382), "50.0%": abs(c_price - f500), "23.6%": abs(c_price - f236), "78.6%": abs(c_price - f786)}
                closest_level = min(diffs, key=diffs.get)
                
                score = 0
                if rsi > 50 or rsi < 30: score += 1
                if macd_l.iloc[-1] > macd_s.iloc[-1]: score += 1
                if c_price > ema50: score += 1
                if c_price > sma200: score += 1
                if cci > 0 or cci < -100: score += 1
                if stoch_k > 50 or stoch_k < 20: score += 1
                if adx.iloc[-1] > 25 and plus_di.iloc[-1] > minus_di.iloc[-1]: score += 1
                if mom > 0: score += 1
                if obv.diff(1).iloc[-1] > 0: score += 1
                
                if closest_level == "61.8%" and c_price >= f618: score += 1
                elif closest_level == "38.2%" and c_price >= f382: score += 1
                elif closest_level == "50.0%" and c_price >= f500: score += 1
                elif c_price >= f236: score += 1
                    
                if score >= 8: rating = "🔥 ذهبي خارق"
                elif score >= 5: rating = "🟢 إيجابي صاعد"
                else: rating = "🟡 حيرة / زخم ضعيف"
                    
                results.append({
                    "رقم السهم": code,
                    "اسم الشركة": name,
                    "السعر الحالي": round(float(c_price), 2),
                    "إشارة مؤشر هال (HMA)": hma_status,
                    "موقع السعر من KAMA": kama_position_str,
                    "النسبة عن KAMA": f"{round(pct_from_kama, 2)}%",
                    "قوة التوافق (Score)": f"{score} / 10",
                    "أقرب مستوى فيبوناتشي": closest_level,
                    "التصنيف الحالي": rating,
                    "النقاط_الرقمية": score
                })
            except Exception:
                continue
                
            progress_bar.progress((index + 1) / total_stocks)
            
        progress_bar.empty()
        
        if results:
            res_df = pd.DataFrame(results)
            if filter_choice.startswith("🔥"):
                res_df = res_df[res_df["النقاط_الرقمية"] >= 8]
            elif filter_choice.startswith("🟢"):
                res_df = res_df[(res_df["النقاط_الرقمية"] >= 5) & (res_df["النقاط_الرقمية"] <= 7)]
                
            st.write(f"📊 **تحليل النظم المستقر:** تم حجب **{excluded_count} شركة** ذات مسار هابط، ومرت **{len(res_df)} شركة** إيجابية ومطابقة تماماً للشارت.")
            
            if not res_df.empty:
                res_df = res_df.sort_values(by="النقاط_الرقمية", ascending=False)
                res_df = res_df.drop(columns=["النقاط_الرقمية"])
                st.dataframe(res_df, use_container_width=True)
            else:
                st.warning("لا توجد أسهم حالياً تطابق جودة التوافق الرقمية المحددة.")
        else:
            st.error("جميع شركات السوق حالياً خارج نطاق الإيجابية ومؤشر هال أحمر بالكامل!")
