import itertools
import os
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
)

# ВАЖНО: ЗАМЕНИТЕ ЭТОТ ТОКЕН НА СВОЙ ПОСЛЕ РЕГИСТРАЦИИ НОВОГО БОТА!
TOKEN = "ВАШ_НОВЫЙ_ТОКЕН_ТУТ"

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== ВАШИ ДАННЫЕ ИЗ ЗАПРОСА =====
# Если вам нужны именно эти данные, оставьте их
# Если нужны другие - замените

products = ["Подушка", "Комплект подушек"]
qualities = [
    "Серый", "Черный", "Модные", "Меmоry Fоаm", "мягкая", "средяя жнсткость",
    "с инновационной пеной", "с фиксации к креслу", "для сидения",
    "с эффектом памяти", "для спины"
]
for_who = [
    "для офиса", "для стула", "для дома", "для авто", "для кресла",
    "для игрового кресла", "для офисного кресла", "для автомобиля", "для путешествия"
]
utp = [
    "Тренд", "Топ", "Хит", "хит зимы", "топ сезона", "тренд сезона",
    "Высокoe качествo", "Новинка", "Новая коллекция", "premium"
]
extras = [
    "2025", "NEW 2025", "при болях в спине", "для долгой работы",
    "отправка по всей России", "Быстрая доставка",
    "для комфортного путешествия", "разгрузи спину"
]

# Список разрешенных брендов (можно расширить)
ALLOWED_BRANDS = ["Mvita", "mvita", "Celine", "Bottega", "ExampleBrand"]

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

    # Генерация для пар (2 элемента)
    for schema in itertools.permutations(["Бренд", "Товар"], 2):
        lists = [all_vars[v] for v in schema]
        for combo in itertools.product(*lists):
            phrase = " ".join(combo)
            unique_results.add(phrase)
    
    # Генерация для троек (3 элемента)
    for schema in itertools.permutations(["Бренд", "Товар", "Какие"], 3):
        lists = [all_vars[v] for v in schema]
        for combo in itertools.product(*lists):
            phrase = " ".join(combo)
            unique_results.add(phrase)
    
    # Генерация для троек (Бренд, Товар, Для кого)
    for schema in itertools.permutations(["Бренд", "Товар", "Для кого"], 3):
        lists = [all_vars[v] for v in schema]
        for combo in itertools.product(*lists):
            phrase = " ".join(combo)
            unique_results.add(phrase)
    
    # Генерация для троек (Бренд, Товар, УТП)
    for schema in itertools.permutations(["Бренд", "Товар", "УТП"], 3):
        lists = [all_vars[v] for v in schema]
        for combo in itertools.product(*lists):
            phrase = " ".join(combo)
            unique_results.add(phrase)
    
    # Генерация для троек (Бренд, Товар, Добавка)
    for schema in itertools.permutations(["Бренд", "Товар", "Добавка"], 3):
        lists = [all_vars[v] for v in schema]
        for combo in itertools.product(*lists):
            phrase = " ".join(combo)
            unique_results.add(phrase)

    # Генерация для четверок (4 элемента) - добавляем четвертый элемент к Бренд+Товар
    base_vars = ["Бренд", "Товар"]
    additional_vars = ["Какие", "Для кого", "УТП", "Добавка"]
    
    for additional in additional_vars:
        for schema in itertools.permutations(base_vars + [additional], 3):
            lists = [all_vars[v] for v in schema]
            for combo in itertools.product(*lists):
                phrase = " ".join(combo)
                unique_results.add(phrase)
    
    # Ограничение по максимальному количеству
    results = list(unique_results)
    if len(results) > MAX_PHRASES:
        results = results[:MAX_PHRASES]
        logger.info(f"Ограничено до {MAX_PHRASES} фраз")
    
    return sorted(results)

async def generate_and_send(update: Update, brand: str):
    chat_id = update.effective_chat.id
    bot = update.get_bot()

    try:
        await bot.send_message(chat_id, f"🔄 Начинаю генерацию фраз для бренда: {brand}...")
        logger.info(f"Начата генерация фраз для бренда {brand}")

        variants = generate_combinations(brand)

        if not variants:
            await bot.send_message(chat_id, "❌ Не удалось сгенерировать фразы. Проверьте настройки.")
            return

        await bot.send_message(chat_id, f"✅ Сгенерировано {len(variants)} фраз. Сохраняю в файлы...")

        # Создаем папку, если её нет
        try:
            os.makedirs(BASE_FOLDER, exist_ok=True)
            logger.info(f"Папка создана/проверена: {BASE_FOLDER}")
        except Exception as e:
            logger.error(f"Ошибка при создании папки: {e}")
            await bot.send_message(chat_id, f"❌ Ошибка при создании папки: {e}")
            return

        chunk_size = 5000
        total_chunks = (len(variants) + chunk_size - 1) // chunk_size

        filenames = []
        for i in range(total_chunks):
            chunk = variants[i * chunk_size : (i + 1) * chunk_size]
            # Создаем безопасное имя файла
            safe_brand = "".join(c for c in brand if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = os.path.join(BASE_FOLDER, f"{safe_brand}_variants_{i + 1:03d}.txt")
            filenames.append(filename)
            
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write("\n".join(chunk))
                logger.info(f"Записан файл: {filename}")
            except Exception as e:
                logger.error(f"Ошибка при записи файла {filename}: {e}")
                await bot.send_message(chat_id, f"❌ Ошибка при записи файла: {e}")
                return

        await bot.send_message(chat_id, f"📤 Начинаю отправку {total_chunks} файлов...")

        for i, filename in enumerate(filenames, start=1):
            try:
                with open(filename, "rb") as f:
                    await bot.send_document(
                        chat_id, 
                        document=f,
                        caption=f"Файл {i} из {total_chunks} для бренда {brand}"
                    )
                logger.info(f"Файл {filename} отправлен")
                await asyncio.sleep(0.5)  # Задержка, чтобы не превысить лимиты Telegram
                
            except Exception as e:
                logger.error(f"Ошибка при отправке файла {filename}: {e}")
                await bot.send_message(chat_id, f"❌ Ошибка при отправке файла {i}: {e}")
                # Продолжаем отправку остальных файлов

        await bot.send_message(
            chat_id,
            f"✅ Все файлы отправлены!\n"
            f"📁 Папка с файлами: {BASE_FOLDER}\n"
            f"📊 Всего фраз: {len(variants)}\n"
            f"📦 Файлов: {total_chunks}"
        )

    except Exception as e:
        logger.error(f"Общая ошибка в generate_and_send: {e}")
        await bot.send_message(chat_id, f"❌ Критическая ошибка: {e}")

async def handle_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    brand = update.message.text.strip()
    
    if not brand or len(brand) > 50:
        await update.message.reply_text("⚠️ Пожалуйста, введите корректное название бренда (не более 50 символов).")
        return
    
    # Проверяем бренд (опционально)
    # if brand not in ALLOWED_BRANDS:
    #     await update.message.reply_text("⚠️ Этот бренд не поддерживается. Используйте один из: " + ", ".join(ALLOWED_BRANDS))
    #     return
    
    logger.info(f"Получен бренд от пользователя {update.effective_user.id}: {brand}")
    await update.message.reply_text(f"👀 Принял бренд: {brand}. Генерация началась...")
    
    # Запускаем генерацию в фоне
    asyncio.create_task(generate_and_send(update, brand))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "📝 Напиши мне название бренда (например: Mvita или mvita),\n"
        "и я сгенерирую для тебя фразы для Авито.\n\n"
        "⚠️ Предупреждение: генерация может занять некоторое время."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Доступные команды:\n"
        "/start - начать работу\n"
        "/help - эта справка\n\n"
        "Просто отправьте название бренда, и бот начнет генерацию фраз."
    )

if __name__ == "__main__":
    # Проверяем токен
    if TOKEN == "ВАШ_НОВЫЙ_ТОКЕН_ТУТ":
        logger.error("❌ Токен не установлен! Замените TOKEN на свой токен от @BotFather")
        exit(1)
    
    # Проверяем доступность папки
    try:
        os.makedirs(BASE_FOLDER, exist_ok=True)
        logger.info(f"Папка для файлов: {BASE_FOLDER}")
    except Exception as e:
        logger.error(f"Не могу создать папку {BASE_FOLDER}: {e}")
        exit(1)
    
    # Создаем и запускаем бота
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_brand))
    
    logger.info("Бот запущен и готов к работе...")
    app.run_polling()
