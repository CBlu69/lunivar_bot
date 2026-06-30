import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # ← این خط درست شد

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔒 *پیام ناشناس*\n\n"
        "پیامت رو اینجا بنویس تا به صورت کاملاً ناشناس ارسال بشه.\n"
        "فرستنده پیام محرمانه میمونه! 🤫",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    
    if user.id == ADMIN_ID and 'reply_to' in context.user_data:
        try:
            await context.bot.send_message(
                chat_id=context.user_data['reply_to'],
                text=f"📩 *پاسخ ادمین:*\n\n{text}",
                parse_mode='Markdown'
            )
            await update.message.reply_text("✅ پاسخ ارسال شد")
            del context.user_data['reply_to']
        except Exception as e:
            await update.message.reply_text(f"❌ خطا: {e}")
        return
    
    msg = (
        f"📨 *پیام جدید*\n\n"
        f"🆔 آیدی: `{user.id}`\n"
        f"👤 نام: {user.first_name} {user.last_name or ''}\n"
        f"📎 یوزرنیم: @{user.username or 'ندارد'}\n\n"
        f"💬 *متن:*\n{text}"
    )
    
    keyboard = [[
        InlineKeyboardButton("✍️ پاسخ", callback_data=f"reply_{user.id}"),
        InlineKeyboardButton("✅ خوندم", callback_data=f"read_{user.id}")
    ]]
    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=msg,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    await update.message.reply_text("✅ پیامت ارسال شد")

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
            f"✍️ پاسخ به کاربر `{uid}` رو بنویس:",
            parse_mode='Markdown'
        )

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 ربات شروع به کار کرد...")
    app.run_polling()

if __name__ == "__main__":
    main()
