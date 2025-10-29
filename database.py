# database.py - إعدادات قاعدة البيانات

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# الحصول على DATABASE_URL من متغيرات البيئة أو استخدام SQLite
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    # استخدام SQLite كبديل محلي
    DATABASE_URL = 'sqlite:///./app_database.db'
    logger.warning(
        "⚠️ DATABASE_URL غير محدد. استخدام SQLite محلي: app_database.db. "
        "للإنتاج، قم بتكوين PostgreSQL في بيئة Replit."
    )

# إنشاء المحرك مع إعدادات مناسبة لكل نوع
if DATABASE_URL.startswith('postgres'):
    engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True, pool_recycle=3600)
else:
    # SQLite لا يحتاج إلى pool settings
    engine = create_engine(DATABASE_URL, echo=False)

# إنشاء فئة الجلسة
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# القاعدة التصريحية للنماذج
Base = declarative_base()

def get_db():
    """الحصول على جلسة قاعدة بيانات."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """تهيئة قاعدة البيانات وإنشاء جميع الجداول."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ تم إنشاء جميع جداول قاعدة البيانات بنجاح!")
    except Exception as e:
        logger.error(f"❌ فشل إنشاء الجداول: {e}")
        raise
