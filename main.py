#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Instagram Repost Bot - لأغراض تعليمية فقط
⚠️ استخدام هذا البوت قد يؤدي إلى حظر حسابك
"""

import os
import json
import time
import random
import schedule
import instaloader
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import warnings
warnings.filterwarnings("ignore")

class InstagramRepostBot:
    def __init__(self, config_file="config.json"):
        """تهيئة البوت مع تحميل الإعدادات"""
        
        # تحميل الإعدادات
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.username = self.config['instagram_username']
        self.password = self.config['instagram_password']
        self.target_pages = self.config['target_pages']
        self.headless = self.config.get('headless_mode', False)
        self.max_videos = self.config.get('max_videos_per_run', 3)
        
        # إنشاء المجلدات المطلوبة
        self.download_dir = "downloaded_videos"
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        
        # تهيئة Instaloader للتحميل
        self.loader = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            filename_pattern='{date}',
            dirname_pattern=self.download_dir
        )
        
        print(f"✅ تم تهيئة البوت للحساب: {self.username}")
    
    def login_instaloader(self):
        """تسجيل الدخول باستخدام Instaloader للتحميل"""
        try:
            # محاولة تحميل الجلسة المحفوظة
            session_file = f"{self.username}.session"
            if os.path.exists(session_file):
                self.loader.load_session_from_file(self.username, session_file)
                print("✅ تم تحميل الجلسة المحفوظة")
            else:
                # تسجيل دخول جديد
                self.loader.login(self.username, self.password)
                self.loader.save_session_to_file(session_file)
                print("✅ تم تسجيل الدخول وحفظ الجلسة")
            return True
        except Exception as e:
            print(f"❌ فشل تسجيل الدخول بواسطة Instaloader: {e}")
            return False
    
    def download_random_videos(self, page_name, count=2):
        """تحميل فيديوهات عشوائية من صفحة محددة"""
        try:
            print(f"📥 جاري تحميل {count} فيديوهات من {page_name}...")
            
            # تحميل معلومات الصفحة
            profile = instaloader.Profile.from_username(self.loader.context, page_name)
            
            # جمع روابط الفيديوهات
            video_posts = []
            for post in profile.get_posts():
                if post.is_video:
                    video_posts.append({
                        'url': f"https://www.instagram.com/p/{post.shortcode}/",
                        'caption': post.caption if post.caption else "",
                        'shortcode': post.shortcode
                    })
                    if len(video_posts) >= 10:  # نجمع 10 فيديوهات عشان نختار عشوائياً
                        break
            
            if not video_posts:
                print(f"⚠️ لا توجد فيديوهات في صفحة {page_name}")
                return []
            
            # اختيار فيديوهات عشوائية
            selected = random.sample(video_posts, min(count, len(video_posts)))
            downloaded = []
            
            for video in selected:
                try:
                    # تحميل الفيديو
                    post = instaloader.Post.from_shortcode(self.loader.context, video['shortcode'])
                    self.loader.download_post(post, target=f"{self.download_dir}/{page_name}")
                    
                    # البحث عن ملف الفيديو المحمل
                    video_file = None
                    for file in os.listdir(f"{self.download_dir}/{page_name}"):
                        if file.endswith('.mp4'):
                            video_file = os.path.abspath(f"{self.download_dir}/{page_name}/{file}")
                            break
                    
                    if video_file:
                        downloaded.append({
                            'file': video_file,
                            'caption': video['caption'][:2200],  # حد الكابشن
                            'source': page_name
                        })
                        print(f"✅ تم تحميل: {video_file}")
                    
                    # تأخير بين التحميلات
                    time.sleep(random.uniform(5, 10))
                    
                except Exception as e:
                    print(f"❌ فشل تحميل فيديو: {e}")
                    continue
            
            return downloaded
            
        except Exception as e:
            print(f"❌ خطأ في تحميل الفيديوهات من {page_name}: {e}")
            return []
    
    def setup_selenium_driver(self):
        """إعداد متصفح Selenium"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # إعدادات لتجنب الكشف
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # مجلد تحميل مخصص
        prefs = {
            "download.default_directory": os.path.abspath(self.download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def login_instagram_selenium(self, driver):
        """تسجيل الدخول إلى إنستغرام باستخدام Selenium للنشر"""
        try:
            print("🔑 جاري تسجيل الدخول إلى إنستغرام...")
            driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(3)
            
            # إدخال اسم المستخدم
            username_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_input.send_keys(self.username)
            
            # إدخال كلمة المرور
            password_input = driver.find_element(By.NAME, "password")
            password_input.send_keys(self.password)
            password_input.send_keys(Keys.RETURN)
            
            # انتظار تسجيل الدخول
            time.sleep(5)
            
            # تخطي النوافذ المنبثقة
            try:
                not_now = driver.find_element(By.XPATH, "//div[contains(text(), 'Not Now')]")
                not_now.click()
            except:
                pass
            
            print("✅ تم تسجيل الدخول بنجاح")
            return True
            
        except Exception as e:
            print(f"❌ فشل تسجيل الدخول: {e}")
            return False
    
    def upload_video(self, driver, video_path, caption):
        """رفع فيديو إلى إنستغرام"""
        try:
            print(f"📤 جاري رفع: {os.path.basename(video_path)}")
            
            # الضغط على زر الإضافة
            create_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @aria-label='Create']"))
            )
            create_btn.click()
            time.sleep(2)
            
            # اختيار فيديو
            file_input = driver.find_element(By.XPATH, "//input[@type='file']")
            file_input.send_keys(os.path.abspath(video_path))
            time.sleep(3)
            
            # الضغط على التالي
            next_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Next')]"))
            )
            next_btn.click()
            time.sleep(2)
            
            # الضغط على التالي مرة أخرى للوصول للكابشن
            next_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Next')]"))
            )
            next_btn.click()
            time.sleep(2)
            
            # إضافة الكابشن
            caption_input = driver.find_element(By.XPATH, "//textarea[@aria-label='Write a caption...']")
            
            # إضافة إشارة للمصدر + الهاشتاغات
            full_caption = f"{caption}\n\n📌 Source: @{self.target_pages[0]}\n#repost #instagram #viral"
            caption_input.send_keys(full_caption)
            time.sleep(2)
            
            # الضغط على مشاركة
            share_btn = driver.find_element(By.XPATH, "//div[contains(text(), 'Share')]")
            share_btn.click()
            
            # انتظار اكتمال الرفع
            time.sleep(10)
            print(f"✅ تم رفع الفيديو بنجاح")
            return True
            
        except Exception as e:
            print(f"❌ فشل رفع الفيديو: {e}")
            return False
    
    def cleanup_old_videos(self):
        """تنظيف الفيديوهات القديمة"""
        try:
            for folder in os.listdir(self.download_dir):
                folder_path = os.path.join(self.download_dir, folder)
                if os.path.isdir(folder_path):
                    for file in os.listdir(folder_path):
                        file_path = os.path.join(folder_path, file)
                        try:
                            os.remove(file_path)
                        except:
                            pass
                    try:
                        os.rmdir(folder_path)
                    except:
                        pass
            print("🧹 تم تنظيف الملفات القديمة")
        except Exception as e:
            print(f"⚠️ خطأ في التنظيف: {e}")
    
    def run_once(self):
        """تشغيل دورة واحدة من البوت"""
        print(f"\n🔄 بدء دورة جديدة في {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # تنظيف الملفات القديمة
        self.cleanup_old_videos()
        
        # تسجيل الدخول للتحميل
        if not self.login_instaloader():
            print("❌ لا يمكن الاستمرار بدون تسجيل دخول Instaloader")
            return
        
        # اختيار صفحة عشوائية
        target_page = random.choice(self.target_pages)
        print(f"🎯 الصفحة المستهدفة: {target_page}")
        
        # تحميل فيديوهات عشوائية
        videos = self.download_random_videos(target_page, self.max_videos)
        
        if not videos:
            print("⚠️ لا توجد فيديوهات للرفع")
            return
        
        # إعداد Selenium للنشر
        driver = self.setup_selenium_driver()
        
        try:
            # تسجيل الدخول للنشر
            if not self.login_instagram_selenium(driver):
                return
            
            # رفع الفيديوهات
            success_count = 0
            for video in videos:
                if self.upload_video(driver, video['file'], video['caption']):
                    success_count += 1
                    # تأخير بين الرفع
                    time.sleep(random.uniform(30, 60))
            
            print(f"✅ تم رفع {success_count} من أصل {len(videos)} فيديو بنجاح")
            
        finally:
            driver.quit()
            print("🏁 انتهت الدورة")
    
    def run_schedule(self):
        """تشغيل البوت بشكل مجدول كل ساعة"""
        print("⏰ بدء جدولة البوت...")
        
        # تشغيل دورة فورية للاختبار
        self.run_once()
        
        # جدولة التشغيل كل ساعة
        schedule.every().hour.do(self.run_once)
        
        # حلقة التشغيل المستمر
        while True:
            schedule.run_pending()
            time.sleep(60)  # نفحص كل دقيقة

def main():
    """الدالة الرئيسية"""
    print("=" * 50)
    print("Instagram Repost Bot - للأغراض التعليمية فقط")
    print("⚠️ استخدام هذا البوت قد يؤدي إلى حظر حسابك")
    print("=" * 50)
    
    # التأكد من وجود ملف الإعدادات
    if not os.path.exists("config.json"):
        print("❌ ملف config.json غير موجود!")
        print("قم بإنشاء الملف بالشكل التالي:")
        print("""
{
    "instagram_username": "your_username",
    "instagram_password": "your_password",
    "target_pages": ["page1", "page2"],
    "headless_mode": false,
    "max_videos_per_run": 2
}
        """)
        return
    
    # إنشاء وتشغيل البوت
    bot = InstagramRepostBot("config.json")
    
    # اختيار وضع التشغيل
    print("\nاختر وضع التشغيل:")
    print("1. تشغيل دورة واحدة فقط")
    print("2. تشغيل مجدول (كل ساعة)")
    
    choice = input("اختيارك (1 أو 2): ").strip()
    
    if choice == "1":
        bot.run_once()
    else:
        try:
            bot.run_schedule()
        except KeyboardInterrupt:
            print("\n👋 تم إيقاف البوت بواسطة المستخدم")
            # إضافة خادم ويب بسيط لإبقاء البوت نشطاً على Koyeb
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Bot is running!')
    
    def log_message(self, format, *args):
        # إلغاء التسجيل لتجنب الإزعاج
        pass

def run_health_server():
    server = HTTPServer(('0.0.0.0', 8080), HealthCheckHandler)
    server.serve_forever()

# تشغيل خادم الصحة في خيط منفصل
health_thread = threading.Thread(target=run_health_server, daemon=True)
health_thread.start()
print("🌐 Health check server started on port 8080")

if __name__ == "__main__":
    main()
