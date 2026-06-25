from pyrogram import Client
from pytgcalls import PyTgCalls
from pytgcalls.types import VideoPiped
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler, 
                          MessageHandler, filters, ContextTypes, ConversationHandler)

# الإعدادات
BOT_TOKEN = "8860734921:AAFaaSvBb9cDmJQrYmPORa7duyJUWx8xxDs"
API_ID = 39828165
API_HASH = "fa68cdfdb1b0d29af276bb158b8adad3"

# الحالات
PHONE, CODE, PASSWORD, ADD_CHANNEL, UPLOAD_VIDEO = range(5)
channels_list = []
videos_list = []
# كائن الاتصال
pytg = None

def main_menu(context):
    phone = context.bot_data.get('saved_phone', 'لا يوجد حساب')
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"👤 {phone}", callback_data="none")],
        # تم تعديل النص هنا فقط ليصبح أوضح
        [InlineKeyboardButton("🚀 صعود (للقناة)", callback_data="connect"), InlineKeyboardButton("🔴 نزول", callback_data="disconnect")],
        [InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings")],
        [InlineKeyboardButton("➕ إضافة حساب", callback_data="add_account"), InlineKeyboardButton("➕ إضافة قناة", callback_data="add_channel")],
        [InlineKeyboardButton("🎬 رفع فيديو", callback_data="upload_video")],
        [InlineKeyboardButton("📢 القنوات", callback_data="channels")],
        [InlineKeyboardButton("📂 الفيديوهات", callback_data="videos")]
    ])

async def start(update, context):
    await update.message.reply_text("القائمة الرئيسية:", reply_markup=main_menu(context))

async def button_handler(update, context):
    global pytg
    query = update.callback_query
    await query.answer()
    
    if query.data == "connect":
        client = context.user_data.get('app')
        if not client:
            await query.message.reply_text("⚠️ سجل الدخول أولاً!")
            return ConversationHandler.END
        
        # تحقق من وجود القناة في القائمة
        if not channels_list:
            await query.message.reply_text("⚠️ لم تقم بإضافة قناة بعد!")
            return ConversationHandler.END
            
        target_channel = channels_list[0] # البث في أول قناة مضافة
        await query.message.reply_text(f"🚀 جاري الصعود للقناة: {target_channel}")
        
        if not pytg:
            pytg = PyTgCalls(client)
            await pytg.start()
            
        await pytg.join_group_call(target_channel, VideoPiped("video.mp4"))
        await query.message.reply_text(f"✅ تم البث في {target_channel}")
        
    elif query.data == "disconnect":
        if pytg and channels_list:
            await pytg.leave_group_call(channels_list[0])
            await query.message.reply_text("🔴 تم إنهاء الاتصال.")
    
    # بقية الأزرار كما هي تماماً
    elif query.data == "add_account":
        await query.message.reply_text("أرسل رقم الهاتف:")
        return PHONE
    elif query.data == "add_channel":
        await query.message.reply_text("أرسل معرف القناة:")
        return ADD_CHANNEL
    elif query.data == "upload_video":
        await query.message.reply_text("أرسل ملف الفيديو:")
        return UPLOAD_VIDEO
    elif query.data == "channels":
        text = "\n".join(channels_list) if channels_list else "لا توجد قنوات."
        await query.message.reply_text(f"📢 القنوات:\n{text}")
    elif query.data == "videos":
        await query.message.reply_text(f"📂 الفيديوهات: {len(videos_list)}")
    return ConversationHandler.END

# [بقية الدوال الأصلية (handle_phone, handle_code, إلخ) تبقى كما هي دون أي تغيير]
# تأكد من إضافتها هنا كما كانت في كودك السابق ليعمل البوت بشكل كامل.
