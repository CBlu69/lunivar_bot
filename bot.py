import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID_STR = os.environ.get("ADMIN_ID")

if not TOKEN or not ADMIN_ID_STR:
    raise ValueError("BOT_TOKEN and ADMIN_ID must be set")

ADMIN_IDS = [int(id.strip()) for id in ADMIN_ID_STR.split(',')]
print(f"✅ ADMIN_IDs: {ADMIN_IDS}")
print(f"👥 Count: {len(ADMIN_IDS)}")

def escape_markdown(text):
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text("🔒 *پیام ناشناس*\n\nپیامت رو اینجا بنویس تا ناشناس ارسال بشه.", parse_mode='Markdown')
    if user.id in ADMIN_IDS:
        await update.message.reply_text("👑 *خوش اومدی ادمین*", parse_mode='Markdown')

def get_user_info(user):
    safe_name = escape_markdown(user.first_name or '')
    safe_last = escape_markdown(user.last_name or '')
    safe_username = escape_markdown(user.username or 'ندارد')
    return f"🆔: `{user.id}`\n👤: {safe_name} {safe_last}\n📎: @{safe_username}"

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get('reply_to')
    if not user_id:
        await update.message.reply_text("❌ خطا")
        return
    try:
        if update.message.text:
            await context.bot.send_message(chat_id=user_id, text=f"📩 *پاسخ ادمین:*\n\n{escape_markdown(update.message.text)}", parse_mode='Markdown')
        elif update.message.photo:
            caption = update.message.caption or ""
            await context.bot.send_photo(chat_id=user_id, photo=update.message.photo[-1].file_id, caption=f"📩 *پاسخ ادمین:*\n\n{escape_markdown(caption)}" if caption else "📩 *پاسخ ادمین*", parse_mode='Markdown' if caption else None)
        elif update.message.video:
            caption = update.message.caption or ""
            await context.bot.send_video(chat_id=user_id, video=update.message.video.file_id, caption=f"📩 *پاسخ ادمین:*\n\n{escape_markdown(caption)}" if caption else "📩 *پاسخ ادمین*", parse_mode='Markdown' if caption else None)
        elif update.message.animation:
            caption = update.message.caption or ""
            await context.bot.send_animation(chat_id=user_id, animation=update.message.animation.file_id, caption=f"📩 *پاسخ ادمین:*\n\n{escape_markdown(caption)}" if caption else "📩 *پاسخ ادمین*", parse_mode='Markdown' if caption else None)
        elif update.message.sticker:
            await context.bot.send_message(chat_id=user_id, text="📩 *پاسخ ادمین:*", parse_mode='Markdown')
            await context.bot.send_sticker(chat_id=user_id, sticker=update.message.sticker.file_id)
        elif update.message.voice:
            caption = update.message.caption or ""
            await context.bot.send_voice(chat_id=user_id, voice=update.message.voice.file_id, caption=f"📩 *پاسخ ادمین:*\n\n{escape_markdown(caption)}" if caption else "📩 *پاسخ ادمین (ویس)*", parse_mode='Markdown' if caption else None)
        elif update.message.document:
            caption = update.message.caption or ""
            await context.bot.send_document(chat_id=user_id, document=update.message.document.file_id, caption=f"📩 *پاسخ ادمین:*\n\n{escape_markdown(caption)}" if caption else "📩 *پاسخ ادمین*", parse_mode='Markdown' if caption else None)
        await update.message.reply_text("✅ پاسخ ارسال شد")
        context.user_data['reply_to'] = None
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

def make_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✍️ پاسخ", callback_data=f"reply_{user_id}"),
         InlineKeyboardButton("✅ خوندم", callback_data=f"read_{user_id}")]
    ])

async def send_to_all_admins(context, admin_ids, send_func, *args, **kwargs):
    for admin_id in admin_ids:
        try:
            await send_func(chat_id=admin_id, *args, **kwargs)
            print(f"✅ ارسال شد به {admin_id}")
        except Exception as e:
            print(f"❌ خطا برای {admin_id}: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg_type = "متن"
    
    if user.id in ADMIN_IDS and context.user_data.get('reply_to'):
        await handle_admin_reply(update, context)
        return
    
    user_info = get_user_info(user)
    caption = update.message.caption or ""
    safe_caption = escape_markdown(caption) if caption else ""
    keyboard = make_keyboard(user.id)
    
    if update.message.text:
        msg = f"📨 *پیام جدید (متن)*\n\n{user_info}\n\n💬: {escape_markdown(update.message.text)}"
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(chat_id=admin_id, text=msg, parse_mode='Markdown', reply_markup=keyboard)
                print(f"✅ متن به {admin_id}")
            except Exception as e:
                print(f"❌ خطا: {e}")
                
    elif update.message.photo:
        msg = f"📨 *پیام جدید (عکس)*\n\n{user_info}"
        if safe_caption: msg += f"\n\n💬: {safe_caption}"
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_photo(chat_id=admin_id, photo=update.message.photo[-1].file_id, caption=msg, parse_mode='Markdown', reply_markup=keyboard)
                print(f"✅ عکس به {admin_id}")
            except Exception as e:
                print(f"❌ خطا: {e}")
        msg_type = "عکس"
        
    elif update.message.video:
        msg = f"📨 *پیام جدید (فیلم)*\n\n{user_info}"
        if safe_caption: msg += f"\n\n💬: {safe_caption}"
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_video(chat_id=admin_id, video=update.message.video.file_id, caption=msg, parse_mode='Markdown', reply_markup=keyboard)
                print(f"✅ فیلم به {admin_id}")
            except Exception as e:
                print(f"❌ خطا: {e}")
        msg_type = "فیلم"
        
    elif update.message.animation:
        msg = f"📨 *پیام جدید (گیف)*\n\n{user_info}"
        if safe_caption: msg += f"\n\n💬: {safe_caption}"
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_animation(chat_id=admin_id, animation=update.message.animation.file_id, caption=msg, parse_mode='Markdown', reply_markup=keyboard)
                print(f"✅ گیف به {admin_id}")
            except Exception as e:
                print(f"❌ خطا: {e}")
        msg_type = "گیف"
        
    elif update.message.sticker:
        msg = f"📨 *پیام جدید (استیکر)*\n\n{user_info}"
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(chat_id=admin_id, text=msg, parse_mode='Markdown', reply_markup=keyboard)
                await context.bot.send_sticker(chat_id=admin_id, sticker=update.message.sticker.file_id)
                print(f"✅ استیکر به {admin_id}")
            except Exception as e:
                print(f"❌ خطا: {e}")
        msg_type = "استیکر"
        
    elif update.message.voice:
        msg = f"📨 *پیام جدید (ویس)*\n\n{user_info}"
        if safe_caption: msg += f"\n\n💬: {safe_caption}"
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_voice(chat_id=admin_id, voice=update.message.voice.file_id, caption=msg, parse_mode='Markdown', reply_markup=keyboard)
                print(f"✅ ویس به {admin_id}")
            except Exception as e:
                print(f"❌ خطا: {e}")
        msg_type = "ویس"
        
    elif update.message.document:
        msg = f"📨 *پیام جدید (سند)*\n\n{user_info}"
        if safe_caption: msg += f"\n\n💬: {safe_caption}"
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_document(chat_id=admin_id, document=update.message.document.file_id, caption=msg, parse_mode='Markdown', reply_markup=keyboard)
                print(f"✅ سند به {admin_id}")
            except Exception as e:
                print(f"❌ خطا: {e}")
        msg_type = "سند"
    
    await update.message.reply_text(f"✅ {msg_type}ات ارسال شد")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, uid = query.data.split('_')
    uid = int(uid)
    
    if query.from_user.id not in ADMIN_IDS:
        await query.answer("⛔ فقط ادمین", show_alert=True)
        return
    
    if action == "read":
        try:
            await context.bot.send_message(uid, "📬 پیامت خونده شد")
        except:
            pass
    elif action == "reply":
        context.user_data['reply_to'] = uid
        await context.bot.send_message(query.from_user.id, f"✍️ پاسخ به کاربر `{uid}`\nحالا پیامت رو بفرست:", parse_mode='Markdown')

def main():
    print(f"🤖 Bot starting...")
    print(f"👥 Admins: {ADMIN_IDS}")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))
    app.add_handler(MessageHandler(filters.VIDEO, handle_message))
    app.add_handler(MessageHandler(filters.ANIMATION, handle_message))
    app.add_handler(MessageHandler(filters.Sticker.ALL, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_message))
    print("🤖 Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
