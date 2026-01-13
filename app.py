import streamlit as st
import boto3
import json 

# 1. إعدادات الصفحة
st.set_page_config(page_title="مساعدك الحكومي الذكي", page_icon="🇸🇦", layout="centered")

# 2. تنسيق CSS لدعم العربية وتجميل الواجهة
st.markdown("""
    <style>
    .main { direction: RTL; text-align: right; }
    div.stButton > button { 
        width: 100%; 
        border-radius: 10px; 
        background-color: #0073BB; 
        color: white; 
        height: 3em; 
        font-size: 1.2em;
        font-weight: bold;
    }
    .stMarkdown, .stSubheader, .stTitle { text-align: right; }
    section[data-testid="stFileUploader"] {
        direction: RTL;
        text-align: right;
    }
    /* تحسين عرض صناديق المعلومات */
    .stAlert { direction: RTL; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

st.title("🇸🇦 مساعد تبسيط الخطابات الرسمية")
st.subheader("ارفع صورة الخطاب وسأشرحه لك ببساطة")

# 3. اختيار الملف
uploaded_file = st.file_uploader("اختر صورة الخطاب أو التعميم (JPG, PNG)", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    # عرض الصورة المرفوعة مع التحديث الجديد للمتصفحات
    st.image(uploaded_file, caption='الخطاب المرفوع', use_column_width="always")
    
    if st.button("تحليل وتبسيط الخطاب"):
        with st.spinner('جاري الاتصال بـ AWS وتحليل الخطاب...'):
            try:
                # أ. إعداد العملاء (يقرأ المفاتيح من Streamlit Secrets)
                s3 = boto3.client('s3', region_name='us-west-2')
                lambda_client = boto3.client('lambda', region_name='us-west-2')
                
                # ب. أسماء الموارد
                bucket_name = "smart-gov-docs-261371110842" 
                lambda_func = "Musser"
                
                # ج. رفع الملف إلى S3
                file_name = uploaded_file.name
                s3.upload_fileobj(uploaded_file, bucket_name, file_name)
                
                # د. تجهيز البيانات للـ Lambda
                payload = {
                    "Records": [{
                        "s3": {
                            "bucket": {"name": bucket_name},
                            "object": {"key": file_name}
                        }
                    }]
                }
                
                # هـ. استدعاء Lambda وانتظار النتيجة
                response = lambda_client.invoke(
                    FunctionName=lambda_func,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )
                
                # و. معالجة الرد القادم من Lambda
                response_payload = json.loads(response['Payload'].read().decode("utf-8"))
                
                # إظهار صندوق تشخيص في حال وجود مشكلة (DEBUG)
                with st.expander("🔍 فحص الرد التقني (Debug)"):
                    st.json(response_payload)

                # ز. استخراج النتائج من الرد
                if 'body' in response_payload:
                    body = response_payload['body']
                    
                    # فك تشفير JSON إذا كان الـ body نصاً مشفراً
                    if isinstance(body, str):
                        try:
                            body = json.loads(body)
                        except:
                            pass
                    
                    # البحث عن النص بعدة مفاتيح محتملة (لضمان التوافق مع أي تعديل في Lambda)
                    simplified_text = body.get('simplified_text') or body.get('explanation') or body.get('result') or body.get('text')
                    
                    if simplified_text:
                        st.success("تم التحليل بنجاح!")
                        st.markdown("---")
                        st.markdown("### 📝 الشرح المبسط:")
                        st.info(simplified_text)
                        
                        # عرض الملف الصوتي إن وجد
                        if body.get('audio_url'):
                            st.markdown("### 🔊 الاستماع للشرح (صوتياً):")
                            st.audio(body['audio_url'])

                        st.balloons()
                    else:
                        st.warning("تمت المعالجة ولكن لم نجد نصاً مشرحاً داخل رد Lambda. يرجى فحص صندوق الـ Debug أعلاه.")
                else:
                    st.error("رد غير مكتمل من Lambda (مفتاح Body مفقود).")

            except Exception as e:
                st.error(f"حدث خطأ تقني: {str(e)}")
                if "NoSuchBucket" in str(e):
                    st.warning("تنبيه: اسم الـ Bucket غير موجود في حسابك.")