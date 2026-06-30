import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID_STR = os.environ.get("ADMIN_ID")

if not TOKEN or not ADMIN_ID_STR:
    raise ValueError("BOT_TOKEN and ADMIN_ID must be set")

ADMIN_ID = int(ADMIN_ID_STR)

# دیکشنری چت‌ها
chat_sessions = {}

def escape_markdown(text):
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if user.id == ADMIN_ID:
        await update.message.reply_text(
            "👑 *پنل ادمین*\n\nپیام‌های کاربران اینجا میاد.\nبرای پاسخ روی ✍️ کلیک کن.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "🔒 *پیام ناشناس*\n\nپیامت رو بنویس تا ناشناس ارسال بشه.",
            parse_mode='Markdown'
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    
    # ==============================
    # ادمین در حال چت با کاربر
    # ==============================
    if user.id == ADMIN_ID:
        if user.id in chat_sessions:
            target_user_id = chat_sessions[user.id]
            
            # دکمه پایان چت
            keyboard = [[
                InlineKeyboardButton("🚫 پایان چت", callback_data=f"endchat_{target_user_id}")
            ]]
            
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"📩 *پاسخ ادمین:*\n\n{escape_markdown(text)}",
                    parse_mode='Markdown'
                )
                await update.message.reply_text(
                    f"✅ پیام به `{target_user_id}` ارسال شد.",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e:
                await update.message.reply_text(f"❌ خطا: {e}")
                # پایان خودکار چت
                if user.id in chat_sessions:
                    del chat_sessions[user.id]
                if target_user_id in chat_sessions:
                    del chat_sessions[target_user_id]
            return
        
        # ادمین در حال چت نیست
        await update.message.reply_text("⚠️ روی دکمه ✍️ *پاسخ* کلیک کن تا چت شروع بشه.", parse_mode='Markdown')
        return
    
    # ==============================
    # کاربر ناشناس
    # ==============================
    safe_name = escape_markdown(user.first_name or '')
    safe_last = escape_markdown(user.last_name or '')
    safe_username = escape_markdown(user.username or 'ندارد')
    safe_text = escape_markdown(text)
    
    status = "💬 *در حال چت*" if user.id in chat_sessions else "📨 *پیام جدید*"
    
    msg = (
        f"{status}\n\n"
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
        await update.message.reply_text("✅ پیامت ارسال شد")
    except Exception as e:
        print(f"❌ خطا: {e}")
        await update.message.reply_text("❌ خطا در ارسال.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    action = data[0]
    uid = int(data[1]) if len(data) > 1 else None
    
    # ==============================
    # پایان چت
    # ==============================
    if action == "endchat":
        target_user_id = uid
        admin_id = query.from_user.id
        
        if admin_id in chat_sessions:
            del chat_sessions[admin_id]
        if target_user_id in chat_sessions:
            del chat_sessions[target_user_id]
        
        await query.edit_message_text(
            query.message.text_markdown + "\n\n🚫 *چت پایان یافت*",
            parse_mode='Markdown'
        )
        
        try:
            await context.bot.send_message(
                target_user_id,
                "🚫 *چت با ادمین پایان یافت.*\n\nبرای شروع دوباره، پیام جدید بفرست.",
                parse_mode='Markdown'
            )
        except:
            pass
        return
    
    # ==============================
    # خوانده شد
    # ==============================
    if action == "read":
        await query.edit_message_text(
            query.message.text_markdown + "\n\n✅ *خوانده شد*",
            parse_mode='Markdown'
        )
        try:
            await context.bot.send_message(uid, "📬 پیامت خونده شد.")
        except:
            pass
        return
    
    # ==============================
    # شروع چت (پاسخ)
    # ==============================
    if action == "reply":
        admin_id = query.from_user.id
        
        # فعال کردن چت دو طرفه
        chat_sessions[admin_id] = uid
        chat_sessions[uid] = True
        
        # ادیت پیام قبلی
        await query.edit_message_text(
            query.message.text_markdown + "\n\n✍️ *در حال چت...*",
            parse_mode='Markdown'
        )
        
        # پیام به ادمین با دکمه پایان
        keyboard = [[
            InlineKeyboardButton("🚫 پایان چت", callback_data=f"endchat_{uid}")
        ]]
        
        await context.bot.send_message(
            chat_id=admin_id,
            text=f"✍️ *چت با کاربر* `{uid}` *فعال شد.*\n\nهر پیامی بدی میره به کاربر.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # اطلاع به کاربر
        try:
            await context.bot.send_message(
                chat_id=uid,
                text="💬 *ادمین بهت پاسخ داد!*\n\nهر پیامی بدی مستقیم میره به ادمین.\nمنتظر پاسخ باش...",
                parse_mode='Markdown'
            )
        except:
            pass

def main():
    print(f"🤖 Starting bot with ADMIN_ID: {ADMIN_ID}")
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 ربات شروع به کار کرد...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
