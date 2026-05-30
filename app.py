import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np

# ==========================================
# 1. إعدادات الصفحة الأساسية
# ==========================================
st.set_page_config(page_title="Dashboard Pro", layout="wide")
st.title("لوحة تحليل الأسهم المتقدمة 📊")

# ==========================================
# 2. قائمة الشركات (طاقة، بتروكيماويات، تجزئة) - بدون تأمين
# ==========================================
tickers_dict = {
    "أرامكو (طاقة)": "2222.SR",
    "سابك (بتروكيماويات)": "2010.SR",
    "ينساب (بتروكيماويات)": "2230.SR",
    "سبكيم العالمية (بتروكيماويات)": "2310.SR",
    "بترورابغ (طاقة)": "2380.SR",
    "المتقدمة (بتروكيماويات)": "2330.SR",
    "كيان السعودية (بتروكيماويات)": "2350.SR",
    "الدريس (طاقة)": "4200.SR",
    "البحري (طاقة)": "4030.SR",
    "جرير (تجزئة)": "4190.SR",
    "إكسترا (تجزئة)": "4003.SR",
    "أسواق العثيم (تجزئة)": "4001.SR",
    "سينومي ريتيل (تجزئة)": "4240.SR",
    "ساسكو (تجزئة)": "4050.SR"
}

# ==========================================
# 3. دالة حساب المؤشرات (Trinity Pro) - نمط Balanced
# ==========================================
def apply_trinity_pro(df):
    if len(df) < 100: # نحتاج بيانات كافية لحساب KAMA و HMA
        return None
        
    # إعدادات النمط Balanced
    hmaSrcLen, rsiFastLen, rsiSlowLen = 9, 14, 25
    volHmaLen, cmfLen = 9, 20
    kamaLength, hmaLength = 100, 21

    # حساب KAMA و HMA
    df['KAMA'] = ta.kama(df['Close'], length=kamaLength)
    df['HMA'] = ta.hma(df['Close'], length=hmaLength)
    
    # حساب RSI مبني على HMA
    df['Price_HMA'] = ta.hma(df['Close'], length=hmaSrcLen)
    df['RSI_Fast'] = ta.rsi(df['Price_HMA'], length=rsiFastLen)
    df['RSI_Slow'] = ta.rsi(df['Price_HMA'], length=rsiSlowLen)

    # حساب فوليوم HMA
    df['Vol_HMA'] = ta.hma(df['Volume'], length=volHmaLen)
    df['Is_High_Vol'] = df['Volume'] > df['Vol_HMA']

    # حساب سيولة CMF
    df['CMF'] = ta.cmf(df['High'], df['Low'], df['Close'], df['Volume'], length=cmfLen)
    df['CMF_Fast'] = ta.hma(df['CMF'].fillna(0), length=9)
    df['CMF_Slow'] = ta.hma(df['CMF'].fillna(0), length=21)
    df['Is_CMF_Bullish'] = df['CMF_Fast'] > df['CMF_Slow']

    # حساب Volume Delta
    high_low_diff = df['High'] - df['Low']
    high_low_diff = high_low_diff.replace(0, 0.0001) # لتجنب القسمة على صفر
    buy_vol = df['Volume'] * (df['Close'] - df['Low']) / high_low_diff
    sell_vol = df['Volume'] * (df['High'] - df['Close']) / high_low_diff
    df['Delta'] = buy_vol - sell_vol
    df['Delta_Filter'] = df['Delta'] > 0

    # فلاتر أخرى (RSI & MTF Proxy)
    df['RSI_Val'] = ta.rsi(df['Close'], length=14)
    df['RSI_Filter'] = df['RSI_Val'] < 70
    df['MTF_HMA'] = ta.hma(df['Close'], length=50)
    df['Is_MTF_Bullish'] = df['Close'] > df['MTF_HMA']

    # ==========================================
    # 4. شروط الدخول (Buy Signals)
    # ==========================================
    df['Uptrend'] = df['Close'] > df['KAMA']
    
    # تقاطع HMA للأعلى
    df['HMA_Prev'] = df['HMA'].shift(1)
    df['HMA_Prev2'] = df['HMA'].shift(2)
    df['HMA_Turns_Up'] = (df['HMA'] > df['HMA_Prev']) & (df['HMA_Prev'] < df['HMA_Prev2'])

    # شروط Trinity Buy
    df['RSI_Fast_Prev'] = df['RSI_Fast'].shift(1)
    df['RSI_Slow_Prev'] = df['RSI_Slow'].shift(1)
    df['RSI_Cross'] = (df['RSI_Fast'] > df['RSI_Slow']) & (df['RSI_Fast_Prev'] <= df['RSI_Slow_Prev'])
    
    df['Trinity_Buy'] = df['RSI_Cross'] & df['Is_High_Vol'] & df['Is_CMF_Bullish'] & df['Is_MTF_Bullish']
    df['Strong_Buy_Signal'] = df['Uptrend'] & df['HMA_Turns_Up'] & df['Delta_Filter'] & df['RSI_Filter'] & df['Trinity_Buy']

    return df

# ==========================================
# 5. بناء الواجهة - التبويبات (Tabs)
# ==========================================
tab1, tab2, tab3 = st.tabs(["🚀 HMA Trinity Scanner", "탭 2 (قريباً)", "탭 3 (قريباً)"])

with tab1:
    st.header("ماسح إشارات HMA Trinity Pro")
    st.markdown("يقوم هذا الماسح بالبحث عن الشركات التي حققت إشارة **Strong Buy** بناءً على تقاطع الزخم، السيولة الإيجابية، وحجم التداول الشري.")
    
    if st.button("بدء المسح (Scan)"):
        with st.spinner("جاري سحب البيانات وتحليل الأسهم..."):
            results = []
            
            for name, ticker in tickers_dict.items():
                try:
                    # سحب بيانات 6 أشهر لضمان دقة مؤشر KAMA (100)
                    df = yf.download(ticker, period="6mo", interval="1d", progress=False)
                    if df.empty:
                        continue
                        
                    # تسطيح الأعمدة إذا كانت MultiIndex (يحدث أحياناً في النسخ الجديدة من yfinance)
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                        
                    df_analyzed = apply_trinity_pro(df.copy())
                    
                    if df_analyzed is not None:
                        last_row = df_analyzed.iloc[-1]
                        
                        # إذا تحققت إشارة الشراء في آخر شمعة
                        if last_row['Strong_Buy_Signal']:
                            results.append({
                                "الشركة": name,
                                "الرمز": ticker,
                                "آخر إغلاق": round(last_row['Close'], 2),
                                "RSI": round(last_row['RSI_Val'], 2),
                                "حالة السيولة (CMF)": "إيجابية 🟢" if last_row['Is_CMF_Bullish'] else "سلبية 🔴",
                                "فوليوم دلتا": "إيجابي 🟢" if last_row['Delta_Filter'] else "سلبي 🔴"
                            })
                except Exception as e:
                    st.error(f"خطأ في تحليل {name}: {e}")
            
            if results:
                st.success("تم العثور على فرص توافق شروطك!")
                results_df = pd.DataFrame(results)
                st.dataframe(results_df, use_container_width=True)
            else:
                st.info("لم تحقق أي شركة شروط الدخول (Strong Buy) اليوم. السوق قد يحتاج إلى مزيد من الزخم.")
