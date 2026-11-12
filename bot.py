
import os
import re
from datetime import time, datetime
from zoneinfo import ZoneInfo

from telegram import Update, ChatPermissions
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ["BOT_TOKEN"]
TZ = ZoneInfo("Europe/Copenhagen")
last_message_time = {}
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! من Avat Group Manager هستم. برای مدیریت گروه آماده‌ام."
    )

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        await update.message.reply_text(
            f"خوش آمدی {member.first_name}! 🌹"
        )

async def is_admin(update, context):
    member = await context.bot.get_chat_member(
        update.effective_chat.id,
        update.effective_user.id
    )
    return member.status in ("administrator", "creator")

async def protect_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message or not message.from_user:
        return

    if message.from_user.is_bot:
        return

    if await is_admin(update, context):
        return
    if (
    message.photo
    or message.video
    or message.video_note
    or message.voice
    or message.audio
    or message.document
    or message.sticker
    or message.animation
):
            await message.delete()
            await message.chat.send_message(
                f"⚠️ {message.from_user.first_name} ارسال ویدیو و پیام صوتی مجاز نیست."
            )
            return
    if not message.text:
        await message.delete()
        return
    text = message.text or message.caption or ""
    entities = list(message.entities or []) + list(message.caption_entities or [])
    entities += list(message.caption_entities or [])
    has_link = (
        bool(re.search(r"https?://|www\.|t\.me/", text, re.I))
        or any(e.type in ("url", "text_link") for e in entities)
    )

    if has_link:
        try:
            await message.delete()
            await message.chat.send_message(
                f"⚠️ {message.from_user.first_name} ارسال لینک مجاز نیست."
            )
        except Exception:
            pass
    user_id = message.from_user.id
    now = datetime.now().timestamp()
    last = last_message_time.get(user_id, 0)

    if now - last < 20:
        await message.delete()
        return

    last_message_time[user_id] = now
async def quiet_start(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    await context.bot.set_chat_permissions(
        chat_id,
        ChatPermissions(
    can_send_messages=False,
    can_send_audios=False,
    can_send_documents=False,
    can_send_photos=False,
    can_send_videos=False,
    can_send_video_notes=False,
    can_send_voice_notes=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False
)
    )

async def quiet_end(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    await context.bot.set_chat_permissions(
        chat_id,
        ChatPermissions(
            can_send_messages=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
    )

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("فقط مدیران می‌توانند این دستور را اجرا کنند.")
        return

    chat_id = update.effective_chat.id
    job_queue = context.application.job_queue

    for name in (f"quiet_start_{chat_id}", f"quiet_end_{chat_id}"):
        for job in job_queue.get_jobs_by_name(name):
            job.schedule_removal()

    job_queue.run_daily(
        quiet_start,
        time=time(23, 0, tzinfo=TZ),
        chat_id=chat_id,
        name=f"quiet_start_{chat_id}"
    )

    job_queue.run_daily(
        quiet_end,
        time=time(7, 0, tzinfo=TZ),
        chat_id=chat_id,
        name=f"quiet_end_{chat_id}"
    )
    now_local = datetime.now(TZ).time()

    if now_local >= time(23, 0) or now_local < time(7, 0):
    await context.bot.set_chat_permissions(
    chat_id,
    ChatPermissions(can_send_messages=False)
            )
    await update.message.reply_text(
        "✅ تنظیمات فعال شد.\n"
        "🌙 سکوت گروه: 23:00 تا 07:00\n"
        "🕒 منطقه زمانی: Copenhagen"
    )

async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("این دستور فقط برای مدیران است.")
        return

    try:
        link = await context.bot.create_chat_invite_link(
            update.effective_chat.id,
            member_limit=1
        )
        await context.bot.send_message(
            update.effective_user.id,
            f"لینک دعوت یک‌بارمصرف شما:\n{link.invite_link}"
        )
        await update.message.reply_text("✅ لینک دعوت به پیام خصوصی شما ارسال شد.")
    except Exception:
        await update.message.reply_text(
            "ابتدا ربات را در خصوصی Start کنید و دسترسی ساخت لینک دعوت بدهید."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "دستورات ربات:\n"
        "/start شروع\n"
        "/settings تنظیم سکوت شبانه\n"
        "/invite ساخت لینک دعوت خصوصی\n"
        "/help راهنما"
    )

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(CommandHandler("invite", invite))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome)
    )
    app.add_handler(
        MessageHandler(
            (filters.ALL) & ~filters.COMMAND,
            protect_group
        )
    )

    print("Avat Group Manager is running!")
    app.run_polling()

if __name__ == "__main__":
    main()
