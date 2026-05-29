import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ==========================================
# 1. الدالات الفنية المتقدمة والمترجمة بدقة
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

def calculate_rsi(series, length=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
    rs = gain / (loss + 1e-10)
    return 100 - (100 / (1 + rs))

# ==========================================
# 2. إعدادات واجهة المستخدم والرادار
# ==========================================
st.set_page_config(page_title="The Ultimate Trinity Radar Pro", layout="wide")
st.title("🎯 رادار الاقتناص الاحترافي المتوافق مع الشارت (Trinity & KAMA Pro)")

st.sidebar.header("⚙️ إعدادات النمط والفلترة")
trading_style = st.sidebar.selectbox("اختر نمط التداول (Global Settings):", ["Balanced", "Scalping", "Swing"])

# تعيين الفترات الديناميكية بناءً على النمط المحدد في Pine Script
if trading_style == "Scalping":
    hma_src_len, rsi_fast_len, rsi_slow_len, vol_hma_len, cmf_len = 5, 7, 14, 5, 10
elif trading_style == "Swing":
    hma_src_len, rsi_fast_len, rsi_slow_len, vol_hma_len, cmf_len = 21, 21, 50, 21, 30
else:  # Balanced
    hma_src_len, rsi_fast_len, rsi_slow_len, vol_hma_len, cmf_len = 9, 14, 25, 9, 20

kama_length = st.sidebar.number_input("KAMA Length (Trend)", value=100)
hma_length = st.sidebar.number_input("HMA Length (Signal)", value=21)

tab1, tab2 = st.tabs(["📊 الشارت المتكامل المتعدد الفريمات", "🔍 رادار فحص وتصفية السوق المشروط"])

# ==========================================
# 3. سلة الأسهم (المجموعة كاملة لضمان الفحص الموحد)
# ==========================================
saudi_market = {
    "3080": "أسمنت الشرقية", "4250": "جبل عمر", "4110": "باتك",
    "3010": "أسمنت العربية", "3020": "أسمنت اليمامة", "3030": "أسمنت السعودية", 
    "3040": "أسمنت القصيم", "3050": "أسمنت الجنوبية", "3060": "أسمنت ينبع", 
    "3090": "أسمنت تبوك", "3001": "أسمنت حائل", "3002": "أسمنت نجران", 
    "3003": "أسمنت المدينة", "3004": "أسمنت الشمالية", "3005": "أسمنت أم القرى", "3092": "أسمنت الرياض",
    "1120": "الراجحي", "1180": "الأهلي", "1150": "الإنماء", "1140": "البلاد", "1010": "بنك الرياض",
    "2222": "أرامكو السعودية", "2010": "سابك", "2310": "سبكيم العالمية", "2082": "معادن", "7010": "STC"
}

# ==========================================
# التبويب الأول: محاكاة الشارت الاحترافي
# ==========================================
with tab1:
    st.header("📈 استعراض الإستراتيجية وفحص الخطوط")
    stock_number = st.text_input("اكتب رقم السهم للتحليل المتقدم:", "3080", key="chart_input")
    
    if st.button("تحليل ورسم الشارت المدمج"):
        with st.spinner("جاري جلب الفريمات المتعددة ومطابقة الألوان..."):
            ticker = f"{stock_number}.SR"
            df_1d = yf.Ticker(ticker).history(period="1y", interval="1d")
            
            if not df_1d.empty and len(df_1d) > 100:
                df_1d = df_1d.dropna(subset=['Close'])
                df_1d['KAMA'] = calculate_kama(df_1d['Close'], length=kama_length)
                df_1d['HMA_Signal'] = calculate_hma(df_1d['Close'], length=hma_length)
                
                # جلب فريم الـ 4 ساعات الحقيقي (تقريبياً عبر فريم الـ 90 دقيقة المتوفر لبيانات أدق)
                try:
                    df_4h = yf.Ticker(ticker).history(period="3mo", interval="90m")
                    if not df_4h.empty:
                        df_4h['HMA_50'] = calculate_hma(df_4h['Close'], 50)
                        df_4h_resampled = df_4h['HMA_50'].resample('D').last().reindex(df_1d.index, method='ffill')
                        df_1d['MTF_HMA'] = df_4h_resampled
                    else:
                        df_1d['MTF_HMA'] = calculate_hma(df_1d['Close'], 50)
                except:
                    df_1d['MTF_HMA'] = calculate_hma(df_1d['Close'], 50)
                
                # حساب الألوان بناءً على التغير الصارم المتوافق مع TradingView
                colors = []
                for i in range(len(df_1d)):
                    if i == 0 or pd.isna(df_1d['HMA_Signal'].iloc[i]) or pd.isna(df_1d['HMA_Signal'].iloc[i-1]):
                        colors.append('gray')
                    elif df_1d['HMA_Signal'].iloc[i] > df_1d['HMA_Signal'].iloc[i-1]:
                        colors.append('green')
                    else:
                        colors.append('red')
                
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df_1d.index, open=df_1d['Open'], high=df_1d['High'], low=df_1d['Low'], close=df_1d['Close'], name="السعر"))
                fig.add_trace(go.Scatter(x=df_1d.index, y=df_1d['KAMA'], name="KAMA Trend (Blue)", line=dict(color='blue', width=2)))
                fig.add_trace(go.Scatter(x=df_1d.index, y=df_1d['HMA_Signal'], name="HMA Signal (Dynamic)", line=dict(color='orange', width=2)))
                
                fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
                
                curr_color = "🟢 أخضر (صاعد)" if colors[-1] == 'green' else "🔴 أحمر (هابط)"
                st.subheader(f"🔍 فحص الحالة اللحظية للسهم: خط HMA يعتبر حالياً: **{curr_color}**")
            else:
                st.error("البيانات غير كافية أو رقم السهم غير صحيح.")

# ==========================================
# التبويب الثاني: محرك الرادار الذكي المصحح بالكامل
# ==========================================
with tab2:
    st.header("🔍 رادار التصفية واقتناص الفريمات المتعددة")
    
    filter_choice = st.selectbox(
        "اختر شرط التصفية الصارم المترجم من Pine Script:",
        [
            "عرض الأسهم ذات خط HMA صاعد (أخضر على الشارت)",
            "🚀 إشارة دخول Trinity مكتملة الشروط (شراء قوي)",
            "🔥 توافق تام: سعر فوق KAMA وخط HMA أخضر"
        ]
    )
    
    if st.button("تشغيل رادار الاقتناص المطور 🚀"):
        results = []
        progress_bar = st.progress(0)
        total_stocks = len(saudi_market)
        
        # حلقة فحص فردية عميقة لكل سهم لضمان دقة حساب الفريمات المتعددة والتزامن
        for index, (code, name) in enumerate(saudi_market.items()):
            ticker_key = f"{code}.SR"
            try:
                # جلب البيانات بشكل منفرد ومباشر لضمان التطهير التام للتواريخ الفارغة
                ticker_obj = yf.Ticker(ticker_key)
                df = ticker_obj.history(period="1y", interval="1d").dropna(subset=['Close'])
                
                if len(df) < 100:
                    continue
                
                close = df['Close']
                c_price = close.iloc[-1]
                
                # 1. حساب المتوسطات الأساسية للشمعة الحالية والسابقة لضبط اللون
                hma_series = calculate_hma(close, length=hma_length)
                kama_series = calculate_kama(close, length=kama_length)
                
                hma_curr = hma_series.iloc[-1]
                hma_prev = hma_series.iloc[-2]
                
                # الشرط الحاسم للون المتوافق مع شاشتك تماماً
                is_hma_green = hma_curr > hma_prev
                hma_status_str = "🟢 أخضر (صاعد)" if is_hma_green else "🔴 أحمر (هابط)"
                
                # 2. جلب حساب الـ MTF الحقيقي لفريم الـ 4 ساعات
                df_4h = ticker_obj.history(period="3mo", interval="90m")
                if not df_4h.empty:
                    df_4h['HMA_50'] = calculate_hma(df_4h['Close'], 50)
                    mtf_val = df_4h['HMA_50'].iloc[-1]
                else:
                    mtf_val = calculate_hma(close, 50).iloc[-1]
                
                is_mtf_bullish = c_price > mtf_val
                
                # 3. حساب مؤشرات Trinity المخصصة للسيولة والزخم
                price_hma_trinity = calculate_hma(close, hma_src_len)
                rsi_fast = calculate_rsi(price_hma_trinity, rsi_fast_len).iloc[-1]
                rsi_slow = calculate_rsi(price_hma_trinity, rsi_slow_len).iloc[-1]
                
                vol_hma = calculate_hma(df['Volume'], vol_hma_len).iloc[-1]
                is_high_vol = df['Volume'].iloc[-1] > vol_hma
                
                # حساب السيولة المخصصة CMF
                high, low, vol = df['High'], df['Low'], df['Volume']
                ad = np.where(high == low, 0, ((2 * close - low - high) / (high - low + 1e-10)) * vol)
                ad_series = pd.Series(ad, index=df.index)
                mf = ad_series.rolling(cmf_len).sum() / (vol.rolling(cmf_len).sum() + 1e-10)
                
                cmf_fast = calculate_hma(mf, 9).iloc[-1]
                cmf_slow = calculate_hma(mf, 21).iloc[-1]
                is_cmf_bullish = cmf_fast > cmf_slow
                
                # كشف تقاطع الـ RSI المخصص للإشارة الشرائية
                trinity_buy_active = (rsi_fast > rsi_slow) and is_high_vol and is_cmf_bullish and is_mtf_bullish
                
                # فرز بناء على اختيارك الفني المتطابق
                if filter_choice.startswith("عرض الأسهم") and not is_hma_green:
                    continue
                elif filter_choice.startswith("🚀") and not (is_hma_green and trinity_buy_active):
                    continue
                elif filter_choice.startswith("🔥") and not (c_price > kama_series.iloc[-1] and is_hma_green):
                    continue
                
                results.append({
                    "رقم السهم": code,
                    "اسم الشركة": name,
                    "السعر الحالي": round(float(c_price), 2),
                    "خط HMA (اللون)": hma_status_str,
                    "الاتجاه فوق KAMA": "🟢 نعم" if c_price > kama_series.iloc[-1] else "🔴 لا",
                    "تدفق السيولة CMF": "✅ إيجابي" if is_cmf_bullish else "❌ سلبي",
                    "حجم التداول (Vol)": "🔥 عالٍ" if is_high_vol else "💤 طبيعي",
                    "توافق الفريم الأكبر MTF": "🔝 إيجابي" if is_mtf_bullish else "⚠️ سلبي"
                })
            except:
                continue
            progress_bar.progress((index + 1) / total_stocks)
            
        progress_bar.empty()
        
        if results:
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.warning("لا توجد أسهم تطابق الشروط الفنية الصارمة المحددة حالياً في السوق.")
