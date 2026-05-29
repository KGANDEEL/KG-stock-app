import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import time

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
# التبويب الثاني: لوحة التصفية الفردية الآمنة
# ==========================================
with tab2:
    st.header("🕵️ المسح الآلي الذكي لأسهم السوق الرئيسية")
    st.write("تقوم اللوحة بفحص الشركات القيادية الكبرى سهمًا بسهم للتأكد من استقرار البيانات.")
    
    # قائمة الشركات القيادية
    saudi_market = {
        "2222": "أرامكو", "1120": "الراجحي", "2010": "سابك", "7010": "STC", "1180": "الأهلي", 
        "1150": "الإنماء", "2310": "سبكيم", "5110": "كهرباء السعودية", "2082": "معادن", "4220": "إعمار",
        "4003": "إكسترا", "2280": "المراعي", "4030": "البحري", "7020": "موبايلي", "7030": "زين",
        "4190": "جرير", "1020": "بنك الجزيرة", "1030": "استثمار", "1080": "العربي"
    }
    
    if st.button("تشغيل الفحص الآلي الآن 🚀"):
        results = []
        
        # إنشاء شريط تقدم نصي وبصري في الواجهة
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_stocks = len(saudi_market)
        
        # حلقة ذكية تمر على الأسهم واحداً تلو الآخر
        for index, (code, name) in enumerate(saudi_market.items()):
            # تحديث النص للمستخدم ليعرف أين وصلنا
            status_text.text(f"🔄 جاري فحص شركة: {name} ({code})...")
            
            ticker_symbol = f"{code}.SR"
            
            try:
                # جلب بيانات السهم الفردي (طريقة مستقرة جداً ومحمية)
                stock = yf.Ticker(ticker_symbol)
                df_scan = stock.history(period="3mo")
                
                if not df_scan.empty and len(df_scan) >= 20:
                    # حساب المتوسط الفني
                    df_scan['SMA20'] = df_scan['Close'].rolling(window=20).mean()
                    
                    latest_close = round(float(df_scan['Close'].iloc[-1]), 2)
                    latest_sma20 = round(float(df_scan['SMA20'].iloc[-1]), 2)
                    
                    # تحديد الإشارة
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
            except Exception as e:
                # إذا فشل سهم واحد لأي سبب، يتخطاه البربرنامج ولا ينهار الموقع كاملاً
                continue
            
            # تحديث شارت التقدم
            progress_bar.progress((index + 1) / total_stocks)
            time.sleep(0.1) # تهدئة الطلبات لتجنب الحظر من ياهو
            
        # تنظيف شاشة التحميل بعد الانتهاء
        status_text.empty()
        progress_bar.empty()
        
        # عرض النتائج النهائية للمستخدم
        if results:
            st.success(f"✅ تم الانتهاء! تم فحص وتحليل {len(results)} شركة بنجاح.")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.error("❌ واجه السيرفر مشكلة في الاتصال بالبورصة، يرجى المحاولة مرة أخرى.")
