import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# 1. إعدادات الصفحة
st.set_page_config(page_title="منصة تداول الاحترافية", layout="wide")
st.title("📊 منصة المسح الفني الشامل للسوق السعودي (تداول)")

# إنشاء التبويبات
tab1, tab2 = st.tabs(["📊 شارت سهم محدد", "🔍 لوحة التصفية الفورية المعتمدة"])

# ==========================================
# التبويب الأول: شارت سهم محدد
# ==========================================
with tab1:
    st.header("استعراض شارت سهم تفاعلي")
    stock_number = st.text_input("اكتب رقم السهم (مثال: 2222، 1120):", "2222")
    period = st.selectbox("اختر الفترة الزمنية للشارت:", ["1mo", "3mo", "6mo", "1y"])
    
    if st.button("عرض الشارت"):
        with st.spinner("جاري جلب الشارت..."):
            df = yf.Ticker(f"{stock_number}.SR").history(period=period)
            if not df.empty:
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("❌ تأكد من رقم السهم الصحيح.")

# ==========================================
# التبويب الثاني: لوحة التصفية الشاملة لجميع الأسهم الكبرى
# ==========================================
with tab2:
    st.header("🕵️ المسح الآلي السريع لأسهم السوق الرئيسية")
    st.write("اضغط على الزر بالأسفل لفحص أكبر شركات السوق بناءً على متوسط (SMA 20) في ثوانٍ معدودة.")
    
    # قاموس ضخم يحتوي على أهم وأغلب الشركات المؤثرة في السوق السعودي لحفظ المساحة والسرعة
    saudi_market = {
        "2222": "أرامكو", "1120": "الراجحي", "2010": "سابك", "7010": "STC", "1180": "الأهلي", 
        "1150": "الإنماء", "2310": "سبكيم", "5110": "كهرباء السعودية", "2082": "معادن", "4220": "إعمار",
        "4003": "إكسترا", "2280": "المراعي", "4030": "البحري", "7020": "موبايلي", "7030": "زين",
        "4190": "جرير", "1020": "بنك الجزيرة", "1030": "استثمار", "1060": "ساب", "1080": "العربي",
        "2020": "سافكو/سابك للمغذيات", "2290": "نادك", "4004": "دله الصحية", "4013": "سليمان الحبيب"
    }
    
    if st.button("تشغيل الفحص السريع للسوق 🚀"):
        results = []
        
        with st.spinner("⚡ جاري جلب وتحليل بيانات جميع الأسهم دفعة واحدة..."):
            # تحويل الرموز لصيغة ياهو فاينانس وربطها بمسافات للتحميل الجماعي
            tickers_list = [f"{code}.SR" for code in saudi_market.keys()]
            tickers_string = " ".join(tickers_list)
            
            # سحر بايثون: تحميل بيانات كل الشركات بطلب واحد فقط!
            all_data = yf.download(tickers_string, period="3mo", group_by='ticker', verbose=False)
            
            for code, name in saudi_market.items():
                ticker_symbol = f"{code}.SR"
                
                # استخراج بيانات السهم المحدده من الملف الضخم
                if ticker_symbol in all_data.columns.levels[0]:
                    df_scan = all_data[ticker_symbol].dropna()
                    
                    if len(df_scan) >= 20:
                        # حساب المؤشر الفني
                        df_scan['SMA20'] = df_scan['Close'].rolling(window=20).mean()
                        
                        latest_close = round(float(df_scan['Close'].iloc[-1]), 2)
                        latest_sma20 = round(float(df_scan['SMA20'].iloc[-1]), 2)
                        
                        if latest_close > latest_sma20:
                            signal = "🟢 شراء (اتجاه صاعد)"
                        else:
                            signal = "🔴 بيع (اتجاه هابط)"
                            
                        results.append({
                            "رقم السهم": code,
                            "اسم الشركة": name,
                            "السعر الحالي": latest_close,
                            "متوسط 20 يوم": latest_sma20,
                            "الحالة الفنية": signal
                        })
            
            # عرض النتيجة
            if results:
                st.success(f"✅ تم تحليل {len(results)} شركة قيادية بنجاح!")
                st.dataframe(pd.DataFrame(results), use_container_width=True)
            else:
                st.error("لم نتمكن من جلب البيانات، جرب مرة أخرى.")
