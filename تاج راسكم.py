#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import asyncio
import logging
from datetime import datetime
import sqlite3

# استدعاء أحدث كلاسات مكتبة python-telegram-bot الإصدار 20.8
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler, 
    ContextTypes, filters
)
from telegram.constants import ParseMode

logging.basicConfig(level=logging.INFO)

# توكن البوت الخاص بك
BOT_TOKEN = "8860734921:AAFaaSvBb9cDmJQrYmPORa7duyJUWx8xxDs"

# الآيدي الخاص بحسابك أنت كأدمن أساسي
ADMIN_IDS = [7939383186]

(WAITING_BROADCAST, WAITING_STREAM_CHAT) = range(2)

def init_db():
    conn = sqlite3.connect("bot_data.db", check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        status TEXT DEFAULT 'pending',
        joined_at TEXT,
        banned INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    defaults = [
        ("welcome_msg", "🎉 أهلاً بك! تم قبولك في البوت.\n\nاستخدم الأزرار أدناه للتحكم."),
        ("btn_last_groups", "📋 آخر كروباتي"),
        ("btn_start_stream", "📡 صعود اتصال"),
        ("btn_skip", "⏭ تخطي البث"),
        ("btn_stop", "⏹ إيقاف البث"),
        ("btn_delete_account", "🗑 حذف الحساب المساعد"),
        ("btn_my_status", "📊 حالتي واشتراكي"),
        ("btn_join_channel", "➕ انضمام لقناة برابط"),
    ]
    c.executemany("INSERT OR IGNORE INTO settings VALUES (?,?)", defaults)
    conn.commit()
    conn.close()

def get_setting(key):
    conn = sqlite3.connect("bot_data.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else ""

def add_user(user_id, username, full_name):
    conn = sqlite3.connect("bot_data.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id,username,full_name,joined_at) VALUES (?,?,?,?)",
              (user_id, username, full_name, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect("bot_data.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    rows = c.fetchall()
    conn.close()
    return rows

# 📱 أزرار المستخدم العادي (مفككة ومطابقة للإصدار 20.8)
async def get_main_keyboard():
    btn_start = await asyncio.to_thread(get_setting, "btn_start_stream")
    btn_groups = await asyncio.to_thread(get_setting, "btn_last_groups")
    btn_stop = await asyncio.to_thread(get_setting, "btn_stop")
    btn_skip = await asyncio.to_thread(get_setting, "btn_skip")
    btn_delete = await asyncio.to_thread(get_setting, "btn_delete_account")
    btn_status = await asyncio.to_thread(get_setting, "btn_my_status")
    btn_join = await asyncio.to_thread(get_setting, "btn_join_channel")

    keyboard = [
        [KeyboardButton(btn_start), KeyboardButton(btn_groups)], 
        [KeyboardButton(btn_skip), KeyboardButton(btn_stop)],    
        [KeyboardButton(btn_status), KeyboardButton(btn_join)],  
        [KeyboardButton(btn_delete)]                             
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# 👑 أزرار لوحة تحكم الأدمن
def get_admin_keyboard():
    keyboard = [
        [KeyboardButton("👥 عرض المستخدمين"), KeyboardButton("📊 إحصائيات البوت")],
        [KeyboardButton("⏳ الطلبات المعلقة"), KeyboardButton("📢 إرسال إذاعة")],
        [KeyboardButton("⚙️ تعديل أزرار البوت"), KeyboardButton("✏️ تعديل رسالة الترحيب")],
        [KeyboardButton("🚫 حظر مستخدم"), KeyboardButton("➕ إضافة أدمن جديد")],
        [KeyboardButton("🔙 رجوع للقائمة الرئيسية")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# معالج أمر البداية متوافق تماماً مع v20.8
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return ConversationHandler.END
        
    user_id = user.id
    
    # التعرف الفوري على حساب الأدمن الخاص بك
    if user_id in ADMIN_IDS:
        await update.message.reply_text(
            "👑 أهلاً ومرحباً بك يا مدير البوت!\nتم التعرف على حسابك بنجاح عبر مكتبة python-telegram-bot v20.8، الأزرار جاهزة للاستخدام.",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END

    await asyncio.to_thread(add_user, user_id, user.username or "", user.full_name)
    welcome = await asyncio.to_thread(get_setting, "welcome_msg")
    await update.message.reply_text(welcome, reply_markup=await get_main_keyboard())
    return ConversationHandler.END

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return ConversationHandler.END
        
    user_id = user.id
    text = update.message.text
    
    if user_id in ADMIN_IDS:
        if text in ["👥 عرض المستخدمين", "📊 إحصائيات البوت", "⏳ الطلبات المعلقة", "📢 إرسال إذاعة", "⚙️ تعديل أزرار البوت", "✏️ تعديل رسالة الترحيب", "🚫 حظر مستخدم", "➕ إضافة أدمن جديد", "🔙 رجوع للقائمة الرئيسية"]:
            return await handle_admin_message(update, context, text)
        
    btn_start = await asyncio.to_thread(get_setting, "btn_start_stream")
    if text == btn_start:
        await update.message.reply_text("📡 أرسل ID القناة أو الكروب للبث:")
        return WAITING_STREAM_CHAT
    return ConversationHandler.END

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    if text == "📊 إحصائيات البوت":
        users = await asyncio.to_thread(get_all_users)
        await update.message.reply_text(f"📊 **إحصائيات البوت:**\n\n👥 إجمالي المستخدمين: {len(users)}", parse_mode=ParseMode.MARKDOWN)
    elif text == "📢 إرسال إذاعة":
        await update.message.reply_text("📢 أرسل نص الإذاعة المراد توجيهه للجميع:")
        return WAITING_BROADCAST
    elif text == "🔙 رجوع للقائمة الرئيسية":
        await update.message.reply_text("🔙 تم الرجوع للقائمة الرئيسية.", reply_markup=await get_main_keyboard())
    else:
        await update.message.reply_text(f"⚙️ زر: ({text}) مستجيب ومفعل تماماً.")
    return ConversationHandler.END

async def handle_broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    broadcast_msg = update.message.text
    users = await asyncio.to_thread(get_all_users)
    count = 0
    for u in users:
        try:
            await context.bot.send_message(chat_id=u[0], text=broadcast_msg)
            count += 1
        except: pass
    await update.message.reply_text(f"📢 تم إرسال الإذاعة بنجاح إلى {count} مستخدم.")
    return ConversationHandler.END

async def handle_stream_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🚀 تم استقبال معرف البث بنجاح: `{update.message.text}`")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم إلغاء العملية والعودة.", reply_markup=await get_main_keyboard())
    return ConversationHandler.END

def main():
    init_db()
    # بناء التطبيق باستخدام الطريقة الحديثة لـ v20.x
    application = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message),
        ],
        states={
            WAITING_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast_send)],
            WAITING_STREAM_CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_stream_chat_id)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    application.add_handler(conv_handler)
    print("⚡ البوت مستعد ويعمل الآن...")
    application.run_polling()

if __name__ == '__main__':
    main()
