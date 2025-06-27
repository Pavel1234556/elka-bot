import itertools
import os
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
)

# Токен бота (не публикуй в открытом доступе!)
TOKEN = "7713828114:AAExMZAdoCscjzQYqyiHDI0Z7PXOAIs4u3E"

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы и данные
products = ["Очки", "Солнцезащитные очки"]
qualities = [
    "Трендовые", "Имиджевые", "Модные", "Новые", "Поляризационные",
    "брендовые", "полароид", "polaroid", "Стильные", "фирменные",
    "хамелеон", "Polarized"
]
for_who = [
    "женские", "мужские", "унисекс", "для женщин", "для мужчин",
    "для уверенных", "для модных", "для стильных"
]
utp = [
    "Тренд", "Топ", "Хит", "хит сезона", "топ сезона", "тренд сезона", "с гарантией",
    "Высокoe качествo", "Новинка", "Новая коллекция", "premium"
]
extras = [
    "2025", "NEW 2025", "защита UV400", "поликарбонат", "отправка по всей России",
    "Быстрая доставка", "защита от УФ-лучей", "Полимерные линзы", "Защита от солнца UV"
]

MAX_PHRASES = 30000

# Путь к общей папке на рабочем столе
BASE_FOLDER = os.path.expanduser("~/Desktop/elka_phrases")

def generate_combinations(brand: str) -> list[str]:
    """
    Генерируем уникальные фразы по шаблонам из словарей.
    Ограничиваем по максимальному количеству.
    """
    all_vars = {
        "Бренд": [brand],
        "Товар": products,
        "Какие": qualities,
        "Для кого": for_who,
        "УТП": utp,
        "Добавка": extras
    }

    var_names = list(all_vars.keys())
    unique_results = set()

    for r in range(2, 5):  # пары, тройки, четвёрки
        for schema in itertools.permutations(var_names, r):
            if "Бренд" not in schema or "Товар" not in schema:
                continue
            lists = [all_vars[v] for v in schema]
            for combo in itertools.product(*lists):
                phrase = " ".join(combo)
                unique_results.add(phrase)

                if len(unique_results) >= MAX_PHRASES:
                    logger.info(f"Достигнуто максимальное количество фраз: {MAX_PHRASES}")
                    return sorted(unique_results)

    return sorted(unique_results)

async def generate_and_send(update: Update, brand: str):
    chat_id = update.effective_chat.id
    bot = update.get_bot()

    try:
        await bot.send_message(chat_id, f"🔄 Начинаю генерацию фраз для бренда: {brand}...")
        logger.info(f"Начата генерация фраз для бренда {brand}")

        variants = generate_combinations(brand)

        await bot.send_message(chat_id, f"✅ Сгенерировано {len(variants)} фраз. Сохраняю в файлы...")

        # Гарантируем создание папки перед записью файлов
        os.makedirs(BASE_FOLDER, exist_ok=True)

        chunk_size = 5000
        total_chunks = (len(variants) + chunk_size - 1) // chunk_size

        filenames = []
        for i in range(total_chunks):
            chunk = variants[i * chunk_size : (i + 1) * chunk_size]
            filename = os.path.join(BASE_FOLDER, f"{brand}_variants_{i + 1}.txt")
            filenames.append(filename)
            logger.info(f"Записываю файл: {filename}")
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write("\n".join(chunk))
            except Exception as e:
                logger.error(f"Ошибка при записи файла {filename}: {e}")
                await bot.send_message(chat_id, f"❌ Ошибка при записи файла {filename}: {e}")
                return  # Прекращаем дальнейшую работу, т.к. критично

        await bot.send_message(chat_id, f"📤 Начинаю отправку {total_chunks} файлов...")

        for i, filename in enumerate(filenames, start=1):
            try:
                with open(filename, "rb") as f:
                    await bot.send_document(chat_id, document=f)
                await bot.send_message(chat_id, f"✅ Отправлен файл {i} из {total_chunks}")
                # os.remove(filename)  # Закомментировано, чтобы файлы не удалялись
                logger.info(f"Файл {filename} отправлен")
                await asyncio.sleep(1)  # Чтобы не перегружать Telegram API
            except Exception as e:
                logger.error(f"Ошибка при отправке файла {filename}: {e}")
                await bot.send_message(chat_id, f"❌ Ошибка при отправке файла {filename}: {e}")

        await bot.send_message(chat_id,
                               f"✅ Все файлы отправлены.\n"
                               f"📁 Папка сохранена: {BASE_FOLDER}")

    except Exception as e:
        logger.error(f"Общая ошибка в generate_and_send: {e}")
        await bot.send_message(chat_id, f"❌ Ошибка: {e}")

async def handle_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    brand = update.message.text.strip()
    if not brand:
        await update.message.reply_text("⚠️ Пожалуйста, введи корректное название бренда.")
        return
    logger.info(f"Получен бренд от пользователя: {brand}")
    await update.message.reply_text(f"👀 Принял бренд: {brand}. Генерация начнётся вскоре...")
    asyncio.create_task(generate_and_send(update, brand))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Напиши мне бренд (например: Celine), и я сгенерирую для тебя фразы."
    )

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_brand))
    logger.info("Бот запущен...")
    app.run_polling()
