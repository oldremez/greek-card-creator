import io
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from claude_client import FlashCard, extract_greek_cards
from config import ALLOWED_USER_ID, TELEGRAM_BOT_TOKEN

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

_MIME_TO_CLAUDE: dict[str, str] = {
    "image/jpeg": "image/jpeg",
    "image/jpg": "image/jpeg",
    "image/png": "image/png",
    "image/gif": "image/gif",
    "image/webp": "image/webp",
}


def _is_allowed(update: Update) -> bool:
    return update.effective_user is not None and update.effective_user.id == ALLOWED_USER_ID


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update):
        return
    await update.message.reply_text(
        "Привет! 🇬🇷\n\n"
        "Отправь фото с греческим текстом — получишь карточки в формате front::back."
    )


async def _process_image(
    update: Update,
    image_bytes: bytes,
    media_type: str = "image/jpeg",
) -> None:
    status = await update.message.reply_text("🔍 Анализирую изображение...")

    try:
        cards: list[FlashCard] = extract_greek_cards(image_bytes, media_type)
    except Exception as e:
        logger.exception("Claude extraction failed")
        await status.edit_text(f"❌ Ошибка при анализе: {e}")
        return

    if not cards:
        await status.edit_text("❌ Греческий текст не найден.")
        return

    lines = [f"{card.normalized}::{card.translation}" for card in cards]
    await status.edit_text("\n".join(lines))


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update):
        return
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    buf = io.BytesIO()
    await file.download_to_memory(buf)
    await _process_image(update, buf.getvalue(), "image/jpeg")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update):
        return
    doc = update.message.document
    mime = (doc.mime_type or "").lower()
    claude_mime = _MIME_TO_CLAUDE.get(mime)
    if claude_mime is None:
        await update.message.reply_text("Пожалуйста, отправь изображение (JPEG, PNG, GIF или WebP).")
        return
    file = await context.bot.get_file(doc.file_id)
    buf = io.BytesIO()
    await file.download_to_memory(buf)
    await _process_image(update, buf.getvalue(), claude_mime)


def main() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))
    logger.info("Bot is running…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
