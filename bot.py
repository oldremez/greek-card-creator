import io
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from claude_client import FlashCard, extract_greek_cards
from config import ALLOWED_USER_ID, TELEGRAM_BOT_TOKEN
from text_client import compare_greek, explain_greek, script, translate_russian

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


async def _handle_explain_greek(update: Update, word: str) -> None:
    status = await update.message.reply_text("🔍 Разбираю слово...")
    try:
        result = explain_greek(word)
    except Exception as e:
        logger.exception("explain_greek failed")
        await status.edit_text(f"❌ Ошибка: {e}")
        return
    await status.edit_text(result.explanation)
    card_line = f"{result.card_normalized}::{result.card_translation}"
    await update.message.reply_text(card_line)


async def _handle_translate_russian(update: Update, word: str) -> None:
    status = await update.message.reply_text("🔍 Перевожу...")
    try:
        result = translate_russian(word)
    except Exception as e:
        logger.exception("translate_russian failed")
        await status.edit_text(f"❌ Ошибка: {e}")
        return
    await status.edit_text(result.overview)
    for option in result.options:
        card_line = f"{option.greek}::{option.translation}"
        await update.message.reply_text(card_line)


async def _handle_compare(update: Update, words: list[str]) -> None:
    status = await update.message.reply_text("🔍 Сравниваю слова...")
    try:
        comparison = compare_greek(words)
    except Exception as e:
        logger.exception("compare_greek failed")
        await status.edit_text(f"❌ Ошибка: {e}")
        return
    await status.edit_text(comparison)


async def handle_text(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update):
        return
    text = update.message.text.strip()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    if not lines:
        return

    if len(lines) >= 2:
        if all(script(ln) == "greek" for ln in lines[:3]):
            await _handle_compare(update, lines[:3])
            return
        await update.message.reply_text(
            "Отправь 2–3 греческих слова (по одному на строку) для сравнения, "
            "одно греческое слово/фразу для разбора, или одно русское слово/фразу для перевода."
        )
        return

    word = lines[0]
    detected = script(word)
    if detected == "greek":
        await _handle_explain_greek(update, word)
    elif detected == "cyrillic":
        await _handle_translate_russian(update, word)
    else:
        await update.message.reply_text(
            "Отправь греческое или русское слово/фразу."
        )


def main() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("Bot is running…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
