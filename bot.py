import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID_STR = os.environ.get("ADMIN_ID")

if not TOKEN or not ADMIN_ID_STR:
    raise ValueError("BOT_TOKEN and ADMIN_ID must be set")

ADMIN_ID = int(ADMIN_ID_STR)
print(f"✅ ADMIN_ID is set to: {ADMIN_ID}")  # برای debug

def escape_markdown(text):
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    print(f"🔔 /start from user: {user.id} - {user.first_name}")
    
    await update.message.reply_text(
        "🔒 *پیام ناشناس*\n\nپیامت رو اینجا بنویس تا ناشناس ارسال بشه.",
        parse_mode='Markdown'
    )
    
    # اگر خود ادمین باشه
    if user.id == ADMIN_ID:
        await update.message.reply_text("👑 *خوش اومدی ادمین!*", parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    
    print(f"📩 پیام از {user.id}: {text}")  # debug
    print(f"👑 ADMIN_ID: {ADMIN_ID}")  # debug
    print(f"🔍 Is admin? {user.id == ADMIN_ID}")  # debug
    
    # پاسخ ادمین
    if user.id == ADMIN_ID and 'reply_to' in context.user_data:
        try:
            await context.bot.send_message(
                chat_id=context.user_data['reply_to'],
                text=f"📩 *پاسخ:*\n\n{escape_markdown(text)}",
                parse_mode='Markdown'
            )
            await update.message.reply_text("✅ ارسال شد")
            del context.user_data['reply_to']
            print("✅ پاسخ ارسال شد")
        except Exception as e:
            await update.message.reply_text(f"❌ خطا: {e}")
            print(f"❌ خطا در پاسخ: {e}")
        return
    
    # پیام ناشناس از کاربر عادی
    safe_name = escape_markdown(user.first_name or '')
    safe_last = escape_markdown(user.last_name or '')
    safe_username = escape_markdown(user.username or 'ندارد')
    safe_text = escape_markdown(text)
    
    msg = (
        f"📨 *پیام جدید*\n\n"
        f"🆔: `{user.id}`\n"
        f"👤: {safe_name} {safe_last}\n"
        f"📎: @{safe_username}\n\n"
        f"💬: {safe_text}"
    )
    
    keyboard = [[
        InlineKeyboardButton("✍️ پاسخ", callback_data=f"reply_{user.id}"),
        InlineKeyboardButton("✅ خوندم", callback_data=f"read_{user.id}")
    ]]
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=msg,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        print(f"✅ پیام به ادمین ({ADMIN_ID}) ارسال شد")
        
        await update.message.reply_text("✅ پیامت ارسال شد")
    except Exception as e:
        print(f"❌ خطا در ارسال به ادمین: {e}")
        await update.message.reply_text("❌ خطا در ارسال پیام. لطفاً دوباره تلاش کن.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    action, uid = query.data.split('_')
    uid = int(uid)
    
    if action == "read":
        await query.edit_message_text(
            query.message.text_markdown + "\n\n✅ *خوانده شد*",
            parse_mode='Markdown'
        )
        try:
            await context.bot.send_message(uid, "📬 پیامت خونده شد")
        except:
            pass
    
    elif action == "reply":
        context.user_data['reply_to'] = uid
        await query.edit_message_text(
            query.message.text_markdown + "\n\n✍️ *در حال پاسخ...*",
            parse_mode='Markdown'
        )
        await context.bot.send_message(
            ADMIN_ID,
            f"✍️ پاسخ به کاربر `{uid}`:",
            parse_mode='Markdown'
        )

def main():
    print(f"🤖 Starting bot with ADMIN_ID: {ADMIN_ID}")
    print(f"🔑 Token starts with: {TOKEN[:10]}...")
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 ربات شروع به کار کرد...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
