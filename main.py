import streamlit as st
import psycopg2
import pandas as pd # Import pandas for data handling
import plotly.express as px # Import plotly for plotting
from db_helpers import save_analysis_result, get_recent_analysis_data, create_analysis_table
from ai_assistant import initialize_gemini_client, generate_ai_advice
from scraper_core import run_scraper_and_analysis # Import the scraper function

# --- CSS للتجميل (إضافة خلفية) ---
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://www.transparenttextures.com/patterns/cubes.png"); /* يمكنك تغيير الرابط لصورة من اختيارك */
        background-size: cover;
        background-attachment: fixed;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F0F2F6;
        border-radius: 4px 4px 0 0;
        gap: 4px;
        padding-top: 10px;
        padding-bottom: 10px;
        padding-left: 16px;
        padding-right: 16px;
    }

    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- عنوان التطبيق ---
st.title("🚀 مدير الأداء الذكي")

# --- تهيئة حالة الجلسة (Session State) ---
if 'GEMINI_API_KEY' not in st.session_state:
    st.session_state['GEMINI_API_KEY'] = ''
if 'POSTGRES_URL' not in st.session_state:
    st.session_state['POSTGRES_URL'] = ''
if 'db_connected' not in st.session_state:
    st.session_state['db_connected'] = False
if 'gemini_client' not in st.session_state:
     st.session_state['gemini_client'] = None


# --- محاكاة حالة المستخدم (مجاني / Premium) ---
# في التطبيق الحقيقي، سيعتمد هذا على تسجيل الدخول/الاشتراك
user_is_premium = st.checkbox("تفعيل وضع Premium (للاختبار)") # زر تبديل للاختبار

# --- واجهة التبويبات ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([ # Added tab6
    "🔍 التحكم والاستخلاص",
    "📈 التحليلات السابقة",
    "🧠 العقل المدبر",
    "📊 تحليل المشاعر", # تبويب افتراضي لم يتم تفصيله في الملخصات، يمكن تخصيصه لاحقاً
    "⚙️ الإعدادات المتقدمة",
    "💡 Support & Help" # Added tab6 title in English
])

# --- تبويب: التحكم والاستخلاص ---
with tab1:
    st.header("🔍 التحكم والاستخلاص")

    if not user_is_premium:
        # محاكاة كود الإعلانات للمستخدمين المجانيين
        st.markdown(
            """
            <div style='background-color: #FFFACD; padding: 10px; border-left: 5px solid #FFA500; margin-bottom: 15px;'>
                <h4>📢 إعلان: للوصول إلى التحليلات الكاملة ومساعد الذكاء الاصطناعي، اشترك في باقة Premium!</h4>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.write("أدخل رابط الصفحة التي تريد تحليل أدائها واستخلاص البيانات منها.")

    url = st.text_input("رابط الصفحة:", "")
    pages_to_scrape = st.number_input("الحد الأقصى لعدد الصفحات للكشط:", min_value=1, value=5)
    concurrency = st.number_input("مستوى التزامن:", min_value=1, value=2)

    if st.button("بدء التحليل والاستخلاص"):
        if not url:
            st.warning("الرجاء إدخال رابط الصفحة للتحليل.")
        else:
            # استدعاء دالة الكاشط الرئيسية من scraper_core.py
            # الدالة run_scraper_and_analysis ستقوم بالكشط وتحليل المشاعر وحفظ النتائج في DB
            # نحتاج إلى تمرير db_url إلى دالة run_scraper_and_analysis
            db_url = st.session_state.get('POSTGRES_URL')
            if db_url:
                run_scraper_and_analysis(db_url, url, pages_to_scrape, concurrency)
            else:
                 st.warning("⚠️ يرجى إدخال رابط اتصال PostgreSQL في تبويب الإعدادات أولاً لحفظ نتائج الكشط.")


# --- تبويب: التحليلات السابقة (ميزة Premium) ---
with tab2:
    st.header("📈 التحليلات السابقة")
    if user_is_premium:
        st.write("هنا يمكنك عرض الرسوم البيانية للتحليلات السابقة والمقارنات.")

        # جلب البيانات التاريخية من قاعدة البيانات
        db_url = st.session_state.get('POSTGRES_URL')
        if db_url:
            try:
                historical_data_df = get_recent_analysis_data(db_url, limit=50) # جلب آخر 50 نتيجة

                if not historical_data_df.empty:
                    st.subheader("آخر نتائج التحليل المحفوظة:")
                    # Display data in a table
                    st.dataframe(historical_data_df)

                    # Example: Plot sentiment score over time
                    st.subheader("اتجاه المشاعر عبر الزمن:")
                    fig_time = px.line(historical_data_df, x='analysis_time', y='sentiment_score', title='اتجاه المشاعر عبر الزمن')
                    st.plotly_chart(fig_time)

                    st.subheader("متوسط المشاعر حسب الرابط:")
                    avg_sentiment_by_url = historical_data_df.groupby('url')['sentiment_score'].mean().reset_index()
                    fig_url = px.bar(avg_sentiment_by_url, x='url', y='sentiment_score', title='متوسط المشاعر حسب الرابط')
                    st.plotly_chart(fig_url)

                else:
                    st.info("لا توجد تحليلات سابقة محفوظة بعد.")

            except Exception as e:
                 st.error(f"⚠️ خطأ أثناء جلب البيانات التاريخية: {{e}}")
        else:
            st.warning("⚠️ يرجى إدخال رابط اتصال PostgreSQL في تبويب الإعدادات لعرض التحليلات السابقة.")


    else:
        st.warning("🔒 هذا التبويب متاح فقط لمستخدمي باقة Premium.")
        st.markdown(
            """
            <div style='background-color: #FFFACD; padding: 10px; border-left: 5px solid #FFA500; margin-top: 15px;'>
                <h4>💎 ترقية إلى Premium لفتح هذه الميزة!</h4>
            </div>
            """,
            unsafe_allow_html=True
        )


# --- تبويب: العقل المدبر (ميزة Premium) ---
with tab3:
    st.header("🧠 العقل المدبر (مساعد الذكاء الاصطناعي)")
    if user_is_premium:
        st.write("استخدم مساعد الذكاء الاصطناعي للحصول على رؤى وتحليلات معمقة بناءً على بياناتك.")

        # تهيئة عميل Gemini عند الحاجة
        if st.session_state.get('gemini_client') is None and st.session_state.get('GEMINI_API_KEY'):
             st.session_state['gemini_client'] = initialize_gemini_client()

        if st.session_state.get('gemini_client'):
            ai_query = st.text_area("اطرح سؤالك على العقل المدبر:", "")
            # جلب البيانات التاريخية لتمريرها للعقل المدبر عند الحاجة
            db_url = st.session_state.get('POSTGRES_URL')
            historical_data_for_ai = pd.DataFrame() # Initialize empty DataFrame
            if db_url:
                 try:
                     # جلب كل البيانات التاريخية المتوفرة أو مجموعة أكبر
                     historical_data_for_ai = get_recent_analysis_data(db_url, limit=1000) # يمكن تعديل الحد حسب الحاجة
                 except Exception as e:
                     st.warning(f"⚠️ لم يتمكن العقل المدبر من الوصول إلى البيانات التاريخية: {{e}}")


            if st.button("احصل على تحليل من العقل المدبر"):
                with st.spinner("جاري استشارة العقل المدبر..."):
                    # استدعاء دالة توليد النصيحة من ai_assistant.py وتمرير البيانات التاريخية
                    advice = generate_ai_advice(ai_query, st.session_state['gemini_client'], historical_data=historical_data_for_ai)
                    if advice:
                        st.subheader("نصيحة العقل المدبر:")
                        st.write(advice)
        else:
            st.warning("⚠️ يرجى تهيئة مفتاح Gemini API في تبويب الإعدادات أولاً.")


    else:
        st.warning("🔒 هذا التبويب متاح فقط لمستخدمي باقة Premium.")
        st.markdown(
            """
            <div style='background-color: #FFFACD; padding: 10px; border-left: 5px solid #FFA500; margin-top: 15px;'>
                <h4>💎 ترقية إلى Premium لفتح هذه الميزة!</h4>
            </div>
            """,
            unsafe_allow_html=True
        )

# --- تبويب: تحليل المشاعر (يمكن تخصيصه لاحقاً) ---
with tab4:
    st.header("📊 تحليل المشاعر (تفصيلي)")
    st.write("عرض تفاصيل تحليل المشاعر من آخر تحليل تم إجراؤه.")

    # Fetch the most recent analysis result to display details
    db_url = st.session_state.get('POSTGRES_URL')
    if db_url:
        try:
            # Get the single most recent analysis result (including text_content if available)
            # NOTE: get_recent_analysis_data needs to be updated to fetch text_content
            # or a new function like get_latest_analysis_details is needed.
            # Assuming for now that get_recent_analysis_data might return text_content
            # or that we will update db_helpers later.
            # For now, just show score and URL as in the previous attempt.
            recent_analysis_df = get_recent_analysis_data(db_url, limit=1)

            if not recent_analysis_df.empty:
                latest_result = recent_analysis_df.iloc[0]
                st.subheader(f"تفاصيل آخر تحليل للرابط: {{latest_result.get('url', 'N/A')}}") # Use .get for safety
                st.write(f"وقت التحليل: {{latest_result.get('analysis_time', 'N/A')}}") # Use .get for safety
                # Check if sentiment_score exists and is not None before formatting
                sentiment_score_display = "N/A"
                if latest_result.get('sentiment_score') is not None:
                     sentiment_score_display = f"**{{latest_result['sentiment_score']:.2f}}**"
                st.write(f"نتيجة المشاعر (Sentiment Score): {sentiment_score_display}")

                # Attempt to display text_content if available in the DataFrame
                if 'text_content' in latest_result and latest_result['text_content'] is not None:
                    st.subheader("محتوى النص:")
                    st.text_area("Content:", value=latest_result['text_content'], height=300, disabled=True)
                else:
                     st.info("محتوى النص الكامل لهذا التحليل غير متاح في النتائج الأخيرة.")


            else:
                st.info("لا توجد نتائج تحليل متاحة لعرض التفاصيل. يرجى إجراء تحليل أولاً.")

        except Exception as e:
             st.error(f"⚠️ خطأ أثناء جلب تفاصيل التحليل: {{e}}")
    else:
         st.warning("⚠️ يرجى إدخال رابط اتصال PostgreSQL في تبويب الإعدادات لعرض تفاصيل التحليل.")


# --- تبويب: الإعدادات المتقدمة ---
with tab5:
    st.header("⚙️ الإعدادات المتقدمة")
    st.write("قم بتكوين إعدادات الاتصال بقاعدة البيانات ومفاتيح API للخدمات الخارجية.")

    # إعدادات قاعدة بيانات PostgreSQL
    st.subheader("إعدادات قاعدة بيانات PostgreSQL")
    postgres_url_input = st.text_input("رابط اتصال PostgreSQL:", value=st.session_state.get('POSTGRES_URL', ''))

    # إعدادات Gemini API
    st.subheader("إعدادات Gemini API")
    gemini_api_key_input = st.text_input("مفتاح Gemini API Key:", type="password", value=st.session_state.get('GEMINI_API_KEY', ''))

    if st.button("حفظ الإعدادات والتأكد من الجداول"):
        # حفظ الإعدادات في حالة الجلسة
        st.session_state['POSTGRES_URL'] = postgres_url_input
        st.session_state['GEMINI_API_KEY'] = gemini_api_key_input

        st.success("✅ تم حفظ الإعدادات.")

        # محاولة الاتصال بقاعدة البيانات وإنشاء الجداول
        if st.session_state.get('POSTGRES_URL'):
            try:
                st.info("جاري محاولة الاتصال بقاعدة البيانات وإنشاء الجداول...")
                # استدعاء دالة إنشاء الجدول من db_helpers.py
                create_analysis_table(st.session_state['POSTGRES_URL'])
                st.session_state['db_connected'] = True
                st.success("✅ تم الاتصال بقاعدة البيانات بنجاح وتم التأكد من وجود الجداول.")
            except Exception as e:
                st.session_state['db_connected'] = False
                st.error(f"⚠️ فشل الاتصال بقاعدة البيانات أو إنشاء الجداول: {e}")
        else:
            st.warning("⚠️ لم يتم إدخال رابط اتصال PostgreSQL.")

        # تهيئة عميل Gemini بعد حفظ المفتاح
        if st.session_state.get('GEMINI_API_KEY'):
             st.session_state['gemini_client'] = initialize_gemini_client()
             if st.session_state.get('gemini_client'):
                 st.success("✅ تم تهيئة عميل Gemini بنجاح.")
             # initialize_gemini_client already shows error if failed
        else:
             st.warning("⚠️ لم يتم إدخال مفتاح Gemini API.")


# --- Tab: Support & Help ---
with tab6:
    st.header("💡 Support & Help")
    st.write("Welcome to the Support & Help section. Here you can find information on how to use the Smart Performance Manager and get assistance.")

    st.subheader("Contact Us")
    st.write("If you encounter any issues or have questions, please contact our support team:")
    st.markdown("- **Email:** support@yourcompany.com")
    st.markdown("- **Phone:** +123 456 7890 (Available Monday-Friday, 9 AM - 5 PM)")

    st.subheader("How to Use")
    st.write("Follow these basic steps to use the application:")
    st.markdown("1. Navigate to the 'Control & Extraction' tab.")
    st.markdown("2. Enter the URL of the page you want to analyze.")
    st.markdown("3. Specify the number of pages to scrape and concurrency level.")
    st.markdown("4. Click 'Start Analysis & Extraction'.")
    st.write("Results will be displayed in the 'Historical Analysis' and 'Sentiment Analysis' tabs.")

    st.subheader("FAQ")
    st.write("Frequently Asked Questions:")
    st.markdown("**Q: How do I get a Gemini API key?**")
    st.markdown("A: You can obtain a Gemini API key from the Google AI Studio website.")
    st.markdown("**Q: What is the difference between free and premium modes?**")
    st.markdown("A: Premium mode unlocks the 'Historical Analysis' and 'Mastermind (AI)' features.")
    st.markdown("**Q: How can I report a bug?**")
    st.markdown("A: Please contact our support team via email.")
