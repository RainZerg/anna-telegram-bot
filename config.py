"""
Bot Configuration
Created by RainZerg on 2025-03-07 17:14:36 UTC
"""

import os
from pathlib import Path

# Bot tokens and IDs
TOKEN = os.getenv("BOT_TOKEN")
PROVIDER_TOKEN = os.getenv("YOOMONEY_PROVIDER_TOKEN")
STUDENTS_CHAT_ID = os.getenv("STUDENTS_CHAT_ID")

# Course information
COURSE_TITLE = "Курс по бытовой дрессировке для инструкторов"
COURSE_PRICE = 1000000  # Price in kopeks (10000 RUB)
CURRENCY = "RUB"

# Tax system configuration
TAX_SYSTEM_CODE = 6  # Common tax system
VAT_CODE = 1  # VAT 20%

# Media files configuration
MEDIA_DIR = Path("/app/media")
COVER_IMAGE_PATH = MEDIA_DIR / "cover_image.jpg"
LECTURER_IMAGE_PATH = MEDIA_DIR / "lecturer_image.jpg"

# Database configuration
DB_DIR = Path("/app/data")
DB_FILE = DB_DIR / "course_bot.db"

# Ensure directories exist
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)
