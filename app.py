import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

# 1. إعداد عنوان الموقع وشكله (عريض ومريح)
st.set_page_config(page_title="موقع الأسهم السعودي", layout="wide")

st.title("📊 منصة تحليل الأسهم السعودية المجانية")
st.write("مرحباً بك! اختر السهم والفترة من القائمة الجانبية لتحديث الشارت فوراً.")

# 2. إنشاء قائمة جانبية لخيارات المستخدم
st.sidebar.header("⚙️ لوحة التحكم")

# صندوق نصي يكتب فيه المستخدم رقم السهم
stock_number = st.sidebar.text_input("اكتب رقم السهم (مثال: 2222 لأرامكو):", "2222")

# قائمة خيارات لتحديد المدة الزمنية
period = st.sidebar.selectbox("اختر الفترة الزمنية:", ["1mo", "3mo", "6mo", "1y", "5y"])

# إضافة الرمز الخاص بالسوق السعودي تلقائياً خلف الكواليس
full_ticker = f"{stock_number}.SR"

# 3. زر لتشغيل جلب البيانات ورسم الشارت
if st.sidebar.button("عرض الشارت وتحديث البيانات"):
    with st.spinner("جاري سحب البيانات الآن..."):
        
        # سحب البيانات من ياهو فاينانس
        stock = yf.Ticker(full_ticker)
        df = stock.history(period=period)
        
        # التأكد أن السهم موجود وله بيانات
        if not df.empty:
            st.subheader(f"📈 حركة سعر السهم رقم ({stock_number})")
            
            # 4. رسم شارت الشموع اليابانية التفاعلي
            fig = go.Figure(data=[go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']
            )])
            
            fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=True)
            st.plotly_chart(fig, use_container_width=True)
            
            # 5. عرض جدول بآخر الأسعار تحت الشارت
            st.subheader("📋 جدول بآخر الأسعار الرقمية المُغلقة")
            st.dataframe(df.tail(10).sort_index(ascending=False), use_container_width=True)
            
        else:
            st.error("❌ خطأ: تأكد من كتابة رقم السهم بشكل صحيح (مثال: 1120 أو 2222).")
