# social_publisher.py

import requests
import logging
import json

LOG_FILENAME = "app_scraper.log" 
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=LOG_FILENAME, filemode='a')


def publish_to_social_media(message, platforms, api_tokens):
    """
    ينشر نفس المحتوى على منصات متعددة بضغطة زر.
    (يجب تعبئة حقول api_tokens في config.json للعمل الفعلي)
    """
    
    results = {}
    
    # 1. النشر على فيسبوك (Facebook Page)
    if 'facebook' in platforms:
        try:
            page_access_token = api_tokens.get('facebook_token')
            page_id = api_tokens.get('facebook_page_id')
            
            if page_access_token and page_id and page_access_token != "YOUR_FACEBOOK_PAGE_ACCESS_TOKEN":
                url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
                payload = {'message': message, 'access_token': page_access_token}
                response = requests.post(url, data=payload)
                
                if response.status_code == 200:
                    results['facebook'] = "✅ تم النشر بنجاح على فيسبوك!"
                    logging.info(f"Published to Facebook: {message[:50]}...")
                else:
                    results['facebook'] = f"❌ فشل فيسبوك: {response.json().get('error', 'غير معروف')}"
            else:
                 results['facebook'] = "⚠️ رموز الوصول لفيسبوك غير متوفرة أو غير صحيحة (تحتاج للتعديل في config.json)."
                 
        except Exception as e:
            results['facebook'] = f"❌ خطأ الاتصال بفيسبوك: {e}"

    # 2. النشر على تويتر (X) - (محاكاة)
    if 'twitter' in platforms:
        results['twitter'] = "⚠️ يتطلب توثيق OAuth معقد. (محاكاة: تم إرسال التغريدة!)"
        
    return results
