import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ============================================
# ⚙️ تنظیمات
# ============================================
TOKEN = "8774654907:AAGSnrwx9gRJQI4EZx1G1VGRDD0wavwzKrM"         
ADMIN_ID = 5406539706

# ⚙️ پروکسی رایگان MTProto (بدون نیاز به VPN)
# اگه این کار نکرد، آدرس‌های دیگه رو امتحان کن
PROXY_URL = "http://t.me/proxy?server=162.55.239.11&port=443&secret=ee662233ee662233ee662233ee662233"

# فعال‌سازی لاگ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# دیکشنری‌های ذخیره اطلاعات
user_messages = {}
user_ids = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔒 *پیام ناشناس*\n\n"
        "پیامت رو اینجا بنویس تا به صورت کاملاً ناشناس ارسال بشه.\n"
        "فرستنده پیام محرمانه میمونه! 🤫",
        parse_mode='Markdown'
    )

async def handle_anonymous_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message_text = update.message.text
    
    user_info = {
        'user_id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name
    }
    
    admin_text = (
        f"📨 *پیام ناشناس جدید*\n\n"
        f"👤 *اطلاعات فرستنده:*\n"
        f"🆔 آیدی: `{user.id}`\n"
        f"👤 نام: {user.first_name} {user.last_name or ''}\n"
        f"📎 یوزرنیم: @{user.username if user.username else 'ندارد'}\n\n"
        f"📝 *متن پیام:*\n{message_text}"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✍️ پاسخ", callback_data=f"reply_{user.id}"),
            InlineKeyboardButton("✅ خوندم", callback_data=f"read_{user.id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    admin_message = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    
    user_messages[admin_message.message_id] = user_info
    user_ids[user.id] = admin_message.message_id
    
    await update.message.reply_text("✅ پیامت ارسال شد! پاسخ رو همینجا دریافت می‌کنی.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    action, user_id = query.data.split('_')
    user_id = int(user_id)
    
    if action == "read":
        await query.edit_message_reply_markup(reply_markup=None)
        original_text = query.message.text
        await query.edit_message_text(
            f"{original_text}\n\n✅ *خوانده شد*",
            parse_mode='Markdown'
        )
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="📬 پیامت توسط ادمین خونده شد."
            )
        except:
            pass
    
    elif action == "reply":
        context.user_data['replying_to'] = user_id
        await query.edit_message_reply_markup(reply_markup=None)
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"✍️ پاسخ خودت رو به کاربر `{user_id}` بنویس:",
            parse_mode='Markdown'
        )

async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    if 'replying_to' in context.user_data:
        target_user_id = context.user_data['replying_to']
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"📩 *پاسخ ادمین:*\n\n{update.message.text}",
                parse_mode='Markdown'
            )
            await update.message.reply_text("✅ پاسخ با موفقیت ارسال شد!")
            del context.user_data['replying_to']
        except Exception as e:
            await update.message.reply_text(f"❌ خطا در ارسال پاسخ: {e}")

async def main():
    # راه‌اندازی بدون پروکسی - مستقیم وصل میشه
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.User(user_id=ADMIN_ID), handle_reply))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.User(user_id=ADMIN_ID), handle_anonymous_message))
    
    print("🤖 ربات ناشناس آماده به کاره...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == '__main__':
    asyncio.run(main())