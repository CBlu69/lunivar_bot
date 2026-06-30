import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID_STR = os.environ.get("ADMIN_ID")

if not TOKEN or not ADMIN_ID_STR:
    raise ValueError("BOT_TOKEN and ADMIN_ID must be set")

ADMIN_ID = int(ADMIN_ID_STR)
print(f"✅ ADMIN_ID is set to: {ADMIN_ID}")

def escape_markdown(text):
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    print(f"🔔 /start from user: {user.id} - {user.first_name}")
    
    await update.message.reply_text(
        "🔒 *پیام ناشناس*\n\n"
        "پیامت رو اینجا بنویس تا ناشناس ارسال بشه.",
        parse_mode='Markdown'
    )
    
    if user.id == ADMIN_ID:
        await update.message.reply_text("👑 *خوش اومدی آرزو*", parse_mode='Markdown')

def get_user_info(user):
    """اطلاعات کاربر رو برای نمایش آماده می‌کنه"""
    safe_name = escape_markdown(user.first_name or '')
    safe_last = escape_markdown(user.last_name or '')
    safe_username = escape_markdown(user.username or 'ندارد')
    
    return (
        f"🆔: `{user.id}`\n"
        f"👤: {safe_name} {safe_last}\n"
        f"📎: @{safe_username}"
    )

async def send_media_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, media_type: str):
    """ارسال مدیا به ادمین"""
    user = update.effective_user
    
    # اگر ادمین باشه و در حال پاسخ دادن
    if user.id == ADMIN_ID and 'reply_to' in context.user_data:
        await handle_admin_reply(update, context)
        return
    
    user_info = get_user_info(user)
    caption = update.message.caption or ""
    safe_caption = escape_markdown(caption) if caption else ""
    
    msg = f"📨 *پیام جدید ({media_type})*\n\n{user_info}"
    if safe_caption:
        msg += f"\n\n💬: {safe_caption}"
    
    keyboard = [[
        InlineKeyboardButton("✍️ پاسخ", callback_data=f"reply_{user.id}"),
        InlineKeyboardButton("✅ خوندم", callback_data=f"read_{user.id}")
    ]]
    
    try:
        # ارسال بر اساس نوع مدیا
        if media_type == "عکس" and update.message.photo:
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=update.message.photo[-1].file_id,
                caption=msg,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif media_type == "فیلم" and update.message.video:
            await context.bot.send_video(
                chat_id=ADMIN_ID,
                video=update.message.video.file_id,
                caption=msg,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif media_type == "گیف" and update.message.animation:
            await context.bot.send_animation(
                chat_id=ADMIN_ID,
                animation=update.message.animation.file_id,
                caption=msg,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif media_type == "استیکر" and update.message.sticker:
            # اول پیام رو بفرستیم
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=msg,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            # بعد استیکر رو
            await context.bot.send_sticker(
                chat_id=ADMIN_ID,
                sticker=update.message.sticker.file_id
            )
        elif media_type == "ویس" and update.message.voice:
            await context.bot.send_voice(
                chat_id=ADMIN_ID,
                voice=update.message.voice.file_id,
                caption=msg,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif media_type == "سند" and update.message.document:
            await context.bot.send_document(
                chat_id=ADMIN_ID,
                document=update.message.document.file_id,
                caption=msg,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        print(f"✅ {media_type} به ادمین ({ADMIN_ID}) ارسال شد")
        await update.message.reply_text(f"✅ {media_type}ات ارسال شد")
        
    except Exception as e:
        print(f"❌ خطا در ارسال {media_type} به ادمین: {e}")
        await update.message.reply_text("❌ خطا در ارسال پیام. لطفاً دوباره تلاش کن.")

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت پاسخ ادمین (متن یا مدیا)"""
    user_id = context.user_data['reply_to']
    
    try:
        # پاسخ متنی
        if update.message.text:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📩 *پاسخ:*\n\n{escape_markdown(update.message.text)}",
                parse_mode='Markdown'
            )
        
        # پاسخ با عکس
        elif update.message.photo:
            caption = update.message.caption or ""
            await context.bot.send_photo(
                chat_id=user_id,
                photo=update.message.photo[-1].file_id,
                caption=f"📩 *پاسخ:*\n\n{escape_markdown(caption)}" if caption else "📩 *پاسخ*",
                parse_mode='Markdown' if caption else None
            )
        
        # پاسخ با فیلم
        elif update.message.video:
            caption = update.message.caption or ""
            await context.bot.send_video(
                chat_id=user_id,
                video=update.message.video.file_id,
                caption=f"📩 *پاسخ:*\n\n{escape_markdown(caption)}" if caption else "📩 *پاسخ*",
                parse_mode='Markdown' if caption else None
            )
        
        # پاسخ با گیف
        elif update.message.animation:
            caption = update.message.caption or ""
            await context.bot.send_animation(
                chat_id=user_id,
                animation=update.message.animation.file_id,
                caption=f"📩 *پاسخ:*\n\n{escape_markdown(caption)}" if caption else "📩 *پاسخ*",
                parse_mode='Markdown' if caption else None
            )
        
        # پاسخ با استیکر
        elif update.message.sticker:
            await context.bot.send_message(
                chat_id=user_id,
                text="📩 *پاسخ:*",
                parse_mode='Markdown'
            )
            await context.bot.send_sticker(
                chat_id=user_id,
                sticker=update.message.sticker.file_id
            )
        
        # پاسخ با ویس
        elif update.message.voice:
            caption = update.message.caption or ""
            await context.bot.send_voice(
                chat_id=user_id,
                voice=update.message.voice.file_id,
                caption=f"📩 *پاسخ:*\n\n{escape_markdown(caption)}" if caption else "📩 *پاسخ (ویس)*",
                parse_mode='Markdown' if caption else None
            )
        
        await update.message.reply_text("✅ پاسخ ارسال شد")
        del context.user_data['reply_to']
        print("✅ پاسخ ارسال شد")
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")
        print(f"❌ خطا در پاسخ: {e}")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت پیام‌های متنی"""
    user = update.effective_user
    
    # اگر ادمین باشه و در حال پاسخ دادن
    if user.id == ADMIN_ID and 'reply_to' in context.user_data:
        await handle_admin_reply(update, context)
        return
    
    text = update.message.text
    
    print(f"📩 پیام متنی از {user.id}: {text}")
    
    user_info = get_user_info(user)
    safe_text = escape_markdown(text)
    
    msg = (
        f"📨 *پیام جدید (متن)*\n\n"
        f"{user_info}\n\n"
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
        # اضافه کردن ✅ خونده شد به پیام
        current_text = query.message.text or query.message.caption or ""
        if current_text:
            try:
                if query.message.text:
                    await query.edit_message_text(
                        current_text + "\n\n✅ *خوانده شد*",
                        parse_mode='Markdown'
                    )
                elif query.message.caption:
                    await query.edit_message_caption(
                        caption=current_text + "\n\n✅ *خوانده شد*",
                        parse_mode='Markdown'
                    )
            except:
                pass
        
        try:
            await context.bot.send_message(uid, "📬 پیامت خونده شد")
        except:
            pass
    
    elif action == "reply":
        context.user_data['reply_to'] = uid
        
        # آپدیت پیام اصلی
        current_text = query.message.text or query.message.caption or ""
        if current_text:
            try:
                if query.message.text:
                    await query.edit_message_text(
                        current_text + "\n\n✍️ *در حال پاسخ...*",
                        parse_mode='Markdown'
                    )
                elif query.message.caption:
                    await query.edit_message_caption(
                        caption=current_text + "\n\n✍️ *در حال پاسخ...*",
                        parse_mode='Markdown'
                    )
            except:
                pass
        
        await context.bot.send_message(
            ADMIN_ID,
            f"✍️ پاسخ به کاربر `{uid}`\n"
            "حالا می‌تونی متن، عکس، فیلم، گیف، استیکر یا ویس بفرستی:",
            parse_mode='Markdown'
        )

def main():
    print(f"🤖 Starting bot with ADMIN_ID: {ADMIN_ID}")
    print(f"🔑 Token starts with: {TOKEN[:10]}...")
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # هندلر برای پیام‌های متنی
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # هندلر برای عکس
    app.add_handler(MessageHandler(filters.PHOTO, lambda u, c: send_media_to_admin(u, c, "عکس")))
    
    # هندلر برای فیلم
    app.add_handler(MessageHandler(filters.VIDEO, lambda u, c: send_media_to_admin(u, c, "فیلم")))
    
    # هندلر برای گیف
    app.add_handler(MessageHandler(filters.ANIMATION, lambda u, c: send_media_to_admin(u, c, "گیف")))
    
    # هندلر برای استیکر
    app.add_handler(MessageHandler(filters.Sticker.ALL, lambda u, c: send_media_to_admin(u, c, "استیکر")))
    
    # هندلر برای ویس
    app.add_handler(MessageHandler(filters.VOICE, lambda u, c: send_media_to_admin(u, c, "ویس")))
    
    # هندلر برای فایل/سند
    app.add_handler(MessageHandler(filters.Document.ALL, lambda u, c: send_media_to_admin(u, c, "سند")))
    
    print("🤖 ربات شروع به کار کرد...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
