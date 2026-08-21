import logging
import os
from datetime import time
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- НАСТРОЙКИ ---
# Берем из переменных окружения для безопасности
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_CHAT_ID = int(os.getenv("OWNER_CHAT_ID", 0))

# Московское время
MOSCOW_TZ = pytz.timezone('Europe/Moscow')

# Список пользователей (их chat_id), кому отправляем "ЖИВ?"
USERS = [
    1061521927,  # Эмиль
    434935789,   # Я
    946107650,   # Саня Кривцов
    227620276,   # Гладкий
    #281925706    # Агеев 2
]

# Словарь для отслеживания: кому мы уже отправили "ЖИВ?"
waiting_for_response = {}

# Включим логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- ОСНОВНАЯ ЛОГИКА ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие при запуске /start"""
    user_id = update.effective_user.id

    if user_id == OWNER_CHAT_ID:
        keyboard = [
            [
                InlineKeyboardButton("📤 Тестовая рассылка", callback_data="test"),
                InlineKeyboardButton("👥 Список пользователей", callback_data="users"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "Привет! Я буду проверять, жив ли ты. 😊\n"
            "Расписание:\n"
            "• Суббота в 19:40\n"
            "• Воскресенье в 7:40\n"
            "• Воскресенье в 19:40\n"
            "(по московскому времени)\n\n"
            "🔧 Панель управления:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "Привет! Я буду проверять, жив ли ты. 😊\n"
            "Расписание:\n"
            "• Суббота в 19:40\n"
            "• Воскресенье в 7:40\n"
            "• Воскресенье в 19:40\n"
            "(по московскому времени)"
            "ВНИМАНИЕ! Бот НИКОГДА не просит пароли, деньги или личные данные!\n"
            "Он только отправляет ЖИВ? и пересылает ответы владельцу.\n"
            "При подозрениях — пишите мне напрямую."
        )

async def send_alive_check(context: ContextTypes.DEFAULT_TYPE):
    """Отправляет 'ЖИВ?' всем пользователям из списка"""
    global waiting_for_response

    waiting_for_response = {}

    for user_id in USERS:
        try:
            await context.bot.send_message(chat_id=user_id, text="Браток, очко целое? Ставь +")
            waiting_for_response[user_id] = True
            logging.info(f"Отправлено 'ЖИВ?' пользователю {user_id}")
        except Exception as e:
            logging.error(f"Не удалось отправить пользователю {user_id}: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ВСЕ сообщения от пользователей и пересылает владельцу"""
    global waiting_for_response

    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "Пользователь"
    username = update.effective_user.username or "нет username"

    if user_id in USERS:
        if waiting_for_response.get(user_id, False):
            await update.message.forward(chat_id=OWNER_CHAT_ID)
            await context.bot.send_message(
                chat_id=OWNER_CHAT_ID,
                text=f"✅ Ответ от {user_name} (@{username}, ID: {user_id})"
            )
            waiting_for_response[user_id] = False
            logging.info(f"Ответ от {user_id} переслан владельцу")
            await update.message.reply_text("✅ Ваш ответ отправлен.")
        else:
            await update.message.reply_text(
                "Сейчас я не жду ответа. Следующая проверка будет в расписание."
            )

async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает сообщения от неизвестных пользователей"""
    user_id = update.effective_user.id
    if user_id not in USERS and user_id != OWNER_CHAT_ID:
        await update.message.reply_text("Извините, вы не в списке пользователей.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на инлайн-кнопки"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    if user_id != OWNER_CHAT_ID:
        await query.edit_message_text("❌ У вас нет прав для этой команды")
        return

    # Клавиатура для возврата в меню
    menu_keyboard = [
        [
            InlineKeyboardButton("📤 Тестовая рассылка", callback_data="test"),
            InlineKeyboardButton("👥 Список пользователей", callback_data="users"),
        ]
    ]
    menu_markup = InlineKeyboardMarkup(menu_keyboard)

    if query.data == "test":
        await send_alive_check(context)
        await query.edit_message_text(
            "✅ Тестовая рассылка выполнена!\n\n"
            "🔧 Вернуться в меню:",
            reply_markup=menu_markup  # ← Возвращаем меню
        )
        logging.info("🧪 Тестовая рассылка запущена через кнопку")

    elif query.data == "users":
        user_list = "\n".join([f"• {uid}" for uid in USERS])
        await query.edit_message_text(
            f"📋 Список пользователей:\n{user_list}\n\n"
            "🔧 Вернуться в меню:",
            reply_markup=menu_markup  # ← Возвращаем меню
        )

async def test_alive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовая рассылка 'ЖИВ?' всем пользователям (команда /test)"""
    if update.effective_user.id == OWNER_CHAT_ID:
        await send_alive_check(context)
        await update.message.reply_text("✅ Тестовая рассылка выполнена!")
        logging.info("🧪 Тестовая рассылка запущена владельцем")
    else:
        await update.message.reply_text("❌ У вас нет прав для этой команды")

async def show_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список пользователей (команда /users)"""
    if update.effective_user.id == OWNER_CHAT_ID:
        user_list = "\n".join([f"• {uid}" for uid in USERS])
        await update.message.reply_text(f"📋 Список пользователей:\n{user_list}")
    else:
        await update.message.reply_text("❌ У вас нет прав")

# --- НАСТРОЙКА ПЛАНИРОВЩИКА ---

async def setup_jobs(application):
    """Настройка периодических задач"""
    job_queue = application.job_queue
    if job_queue is None:
        logging.error("JobQueue не доступен")
        return

    global waiting_for_response
    waiting_for_response = {}

    # Суббота в 20:00
    job_queue.run_daily(
        send_alive_check,
        time=time(hour=19, minute=40, tzinfo=MOSCOW_TZ),
        days=(5,)
    )
    logging.info("Запланирована проверка на субботу 19:40 МСК")

    # Воскресенье в 8:00
    job_queue.run_daily(
        send_alive_check,
        time=time(hour=7, minute=40, tzinfo=MOSCOW_TZ),
        days=(6,)
    )
    logging.info("Запланирована проверка на воскресенье 7:40 МСК")

    # Воскресенье в 20:00
    job_queue.run_daily(
        send_alive_check,
        time=time(hour=19, minute=40, tzinfo=MOSCOW_TZ),
        days=(6,)
    )
    logging.info("Запланирована проверка на воскресенье 19:40 МСК")

# --- ЗАПУСК БОТА ---

def main():
    # Создаём приложение
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Регистрируем обработчики команд (ВСЕ ДО run_polling!)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test", test_alive))
    application.add_handler(CommandHandler("users", show_users))
    application.add_handler(CallbackQueryHandler(button_handler))  # ← ЭТО ВАЖНО!
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.ALL, handle_unknown), group=1)

    # Настраиваем планировщик
    setup_jobs(application)

    # Запускаем бота
    logging.info("Бот запущен!")
    logging.info("Расписание:")
    logging.info("  • Суббота 19:40 МСК")
    logging.info("  • Воскресенье 7:40 МСК")
    logging.info("  • Воскресенье 19:40 МСК")

    application.run_polling()  # ← ЭТО ПОСЛЕДНЯЯ КОМАНДА


if __name__ == '__main__':
    main()