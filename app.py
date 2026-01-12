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
    /* تحسين شكل صندوق الرفع */
    section[data-testid="stFileUploader"] {
        direction: RTL;
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🇸🇦 مساعد تبسيط الخطابات الرسمية")
st.subheader("ارفع صورة الخطاب وسأشرحه لك ببساطة")

# 3. اختيار الملف
uploaded_file = st.file_uploader("اختر صورة الخطاب أو التعميم (JPG, PNG)", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    # عرض الصورة المرفوعة
    st.image(uploaded_file, caption='الخطاب المرفوع', use_container_width=True)
    
    if st.button("تحليل وتبسيط الخطاب"):
        with st.spinner('جاري الاتصال بـ AWS وتحليل الخطاب...'):
            try:
                # أ. إعداد العملاء (يقرأ المفاتيح من Secrets تلقائياً)
                s3 = boto3.client('s3', region_name='us-west-2')
                lambda_client = boto3.client('lambda', region_name='us-west-2')
                
                # ب. أسماء الموارد (تم التحديث للاسم الصحيح)
                bucket_name = "smart-gov-docs-261371110842" 
                lambda_func = "Musser"
                
                # ج. رفع الملف إلى S3
                file_name = uploaded_file.name
                s3.upload_fileobj(uploaded_file, bucket_name, file_name)
                
                # د. تجهيز البيانات للـ Lambda (تنسيق S3 Trigger)
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
                
                # التحقق من وجود محتوى في الرد
                if 'body' in response_payload:
                    body = response_payload['body']
                    # إذا كان الـ body نصاً مشفراً بصيغة JSON، نقوم بفكه
                    if isinstance(body, str):
                        body = json.loads(body)
                    
                    st.success("تم التحليل بنجاح!")
                    
                    # عرض النص المبسط
                    st.markdown("---")
                    st.markdown("### 📝 الشرح المبسط:")
                    st.info(body.get('simplified_text', 'لم يتم العثور على نص مبسط في الرد.'))
                    
                    # عرض الملف الصوتي إن وجد
                    if body.get('audio_url'):
                        st.markdown("### 🔊 الاستماع للشرح (صوتياً):")
                        st.audio(body['audio_url'])

                    st.balloons() # احتفال بالنجاح!
                else:
                    st.error("فشل التحليل: لم تصل بيانات صالحة من خدمة Lambda.")

            except Exception as e:
                # عرض الخطأ بشكل واضح لاستكشاف المشاكل
                st.error(f"حدث خطأ تقني: {str(e)}")
                if "NoSuchBucket" in str(e):
                    st.warning("تنبيه: يبدو أن اسم الـ Bucket غير صحيح في AWS.")