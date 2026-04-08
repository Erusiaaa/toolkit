import logging
import random
from html import escape
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from app.config import settings
from app.crud import get_designs_by_tag, get_or_create_user, get_public_alias, get_random_design, save_design_for_user
from app.database import SessionLocal
from app.seed import seed_db
from app.seed_data import TAG_LABELS

logging.basicConfig(level=logging.INFO)
LAST_DESIGN: dict[int, int] = {}
BASE_DIR = Path(__file__).resolve().parents[1] / "static" / "images"


def gallery_url(user_id: int, username: str | None):
    if username:
        return f"{settings.public_base_url}/u/{username.lstrip('@')}"
    return f"{settings.public_base_url}/gallery/{user_id}"


def keyboard_for_design(user_id: int, username: str | None, design_id: int):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Save", callback_data=f"save:{design_id}")],
            [InlineKeyboardButton("Open gallery", url=gallery_url(user_id, username))],
        ]
    )


def caption_for_design(design) -> str:
    labels = " · ".join(TAG_LABELS.get(tag, tag.title()) for tag in design.tag_list)
    return f"<b>{escape(design.title)}</b>\n{escape(design.description)}\n\n<i>{escape(labels)}</i>"


async def send_design(update: Update, design):
    image_path = BASE_DIR / design.image_filename
    LAST_DESIGN[update.effective_user.id] = design.id
    with image_path.open("rb") as image_file:
        await update.message.reply_photo(
            photo=InputFile(image_file, filename=image_path.name),
            caption=caption_for_design(design),
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard_for_design(update.effective_user.id, update.effective_user.username, design.id),
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    try:
        user = update.effective_user
        created = get_or_create_user(db, str(user.id), user.username, user.first_name)
        alias = get_public_alias(created)
    finally:
        db.close()
    await update.message.reply_text(
        f"Use /random, /long, /short, /solid, /creative, /save, and /my.\nYour alias: {alias}"
    )


async def random_design(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    try:
        design = get_random_design(db)
    finally:
        db.close()
    if not design:
        await update.message.reply_text("No designs found yet.")
        return
    await send_design(update, design)


async def tag_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tag = update.message.text.lstrip("/").split("@")[0].lower()
    db = SessionLocal()
    try:
        designs = get_designs_by_tag(db, tag)
    finally:
        db.close()
    if not designs:
        await update.message.reply_text(f"No designs found for {tag}.")
        return
    await send_design(update, random.choice(designs))


async def save_current(update: Update, context: ContextTypes.DEFAULT_TYPE):
    design_id = LAST_DESIGN.get(update.effective_user.id)
    if not design_id:
        await update.message.reply_text("Open a design first with /random or a tag command.")
        return
    db = SessionLocal()
    try:
        user = update.effective_user
        saved = save_design_for_user(db, str(user.id), design_id, user.username, user.first_name)
    finally:
        db.close()
    await update.message.reply_text("Saved to your gallery." if saved else "Already in your gallery.")


async def my_gallery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(gallery_url(update.effective_user.id, update.effective_user.username))


async def save_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, design_id = query.data.split(":")
    db = SessionLocal()
    try:
        user = query.from_user
        saved = save_design_for_user(db, str(user.id), int(design_id), user.username, user.first_name)
    finally:
        db.close()
    await query.message.reply_text("Saved to your gallery." if saved else "Already in your gallery.")


def main():
    seed_db()
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("random", random_design))
    for tag in TAG_LABELS.keys():
        app.add_handler(CommandHandler(tag, tag_command))
    app.add_handler(CommandHandler("save", save_current))
    app.add_handler(CommandHandler("my", my_gallery))
    app.add_handler(CallbackQueryHandler(save_callback, pattern=r"^save:"))
    app.run_polling()


if __name__ == "__main__":
    main()
