#main.py
import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, JobQueue,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from alerts_manager import save_alert, load_alerts
import asyncio
from binance_api import get_current_price
from alerts_manager import load_alerts, save_alerts, save_alert
import uuid
import json


# === Загрузка .env ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# === Логирование ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === Константы состояний ===
MAIN_MENU, SELECT_PAIR, SET_VALUE, CONFIRM = range(4)

# === Текст и кнопки главного меню ===
MAIN_MENU_BTNS = [
    "➕ Новый алерт",
    "📋 Мои алерты",
    "💹 Цены"
]


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE, text="Привет! Выберите действие:"):
    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"main_menu|{i}")]
        for i, name in enumerate(MAIN_MENU_BTNS)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, reply_markup=reply_markup)
    return MAIN_MENU

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📖 <b>Помощь по боту</b>

<b>Команды:</b>
/start - Главное меню
/show_alerts - Показать мои алерты
/help - Эта справка

<b>Типы алертов:</b>
💰 Цена выше - уведомление, когда цена достигнет указанного значения
💰 Цена ниже - уведомление, когда цена упадёт до указанного значения
📊 Изменение % (рост) - уведомление при росте на N%
📊 Изменение % (падение) - уведомление при падении на N%

<b>Примеры:</b>
- BTC выше $70,000
- ETH ниже $3,000
- SOL рост на +5%
- BNB падение на -3%
"""
    await update.message.reply_text(help_text, parse_mode="HTML")

SELECT_PAIR_STATE = 1

async def back_to_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"main_menu|{i}")]
        for i, name in enumerate(MAIN_MENU_BTNS)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Выберите действие:", reply_markup=reply_markup)
    return MAIN_MENU

async def select_pair(update: Update, context: ContextTypes.DEFAULT_TYPE, text="Выберите пару для отслеживания:"):
    pairs = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "Введите свою пару"]

    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"pair|{name}")]
        for name in pairs
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)

    return SELECT_PAIR_STATE

async def set_value_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value_text = update.message.text.strip()

    try:
        value = float(value_text)
    except ValueError:
        await update.message.reply_text("❌ Введите число, например: 68000")
        return SET_VALUE

    alert_type = context.user_data.get("alert_type")
    if not alert_type:
        await update.message.reply_text(
            "⚠️ Сначала выберите тип алерта: 💰 Цена выше, 💰 Цена ниже или 📊 Изменение %"
        )
        return MAIN_MENU

    # Для процентных алертов
    if alert_type in ("percent_up", "percent_down"):
        if value <= 0 or value > 100:
            await update.message.reply_text("❌ Процент должен быть от 0 до 100")
            return SET_VALUE

    # Для ценовых алертов
    if alert_type in ("above", "below"):
        if value <= 0:
            await update.message.reply_text("❌ Цена должна быть больше 0")
            return SET_VALUE

    pair = context.user_data.get("pair")
    current_price = context.user_data.get("current_price")

    alert_data = {
        "id": str(uuid.uuid4()),
        "user_id": update.effective_user.id,
        "pair": pair,
        "alert_type": alert_type,
        "target_value": value,
        "initial_price": current_price
    }

    try:
        save_alert(alert_data)
        logger.info(f"Алерт создан: user={update.effective_user.id}, pair={pair}, type={alert_type}")

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")
        ]])

        await update.message.reply_text(
            f"✅ Алерт сохранён!\n\n"
            f"Пара: {pair}\n"
            f"Тип: {alert_type}\n"
            f"Цель: {value}",
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Ошибка сохранения алерта: {e}")

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")
        ]])

        await update.message.reply_text(
            "❌ Ошибка сохранения алерта. Попробуйте позже.",
            reply_markup=keyboard
        )

    return MAIN_MENU

async def pair_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    pair = query.data.split("|")[1]

    if pair == "Введите свою пару":
        await query.edit_message_text("✏️ Введите символ пары (например: ADAUSDT, DOGEUSDT):\n\n"
            "Для отмены: /cancel")
        return SELECT_PAIR

    else:
        from binance_api import get_current_price
        price_data = get_current_price(pair)
        if not price_data["success"]:
            await query.edit_message_text("❌ Ошибка получения цены. Попробуй позже.")
            return SELECT_PAIR
        info = price_data["data"]
        context.user_data["pair"] = pair
        context.user_data["current_price"] = float(info["last_price"])
        price = float(info["last_price"])
        change_24h = float(info["price_change_percent"])
        sign = "+" if change_24h >= 0 else ""
        change_text = f"{sign}{change_24h:.2f}%"

        keyboard = [
            [InlineKeyboardButton("💰 Цена выше", callback_data="alert_type|above")],
            [InlineKeyboardButton("💰 Цена ниже", callback_data="alert_type|below")],
            [InlineKeyboardButton("📊 Изменение % (рост)", callback_data="alert_type|percent_up")],
            [InlineKeyboardButton("📊 Изменение % (падение)", callback_data="alert_type|percent_down")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        text = (
            f"Вы выбрали: {pair}\n\n"
            f"💰 Текущая цена: ${price:,.2f}\n"
            f"📊 Изменение 24ч: {change_24h:+.2f}%\n\n"
            f"Выберите тип алерта:"
        )
        await query.edit_message_text(text, reply_markup=reply_markup)
        return SET_VALUE

async def custom_pair_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pair = update.message.text.strip().upper()
    from binance_api import get_current_price
    price_data = get_current_price(pair)
    if not price_data["success"]:
        await update.message.reply_text("❌ Такой пары не существует. Попробуй ещё раз:")
        return SELECT_PAIR

    info = price_data["data"]
    context.user_data["pair"] = pair
    context.user_data["current_price"] = float(info["last_price"])
    price = float(info["last_price"])
    change_24h = float(info["price_change_percent"])
    sign = "+" if change_24h >= 0 else ""
    change_text = f"{sign}{change_24h:.2f}%"

    keyboard = [
        [InlineKeyboardButton("💰 Цена выше", callback_data="alert_type|above")],
        [InlineKeyboardButton("💰 Цена ниже", callback_data="alert_type|below")],
        [InlineKeyboardButton("📊 Изменение % (рост)", callback_data="alert_type|percent_up")],
        [InlineKeyboardButton("📊 Изменение % (падение)", callback_data="alert_type|percent_down")],

    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"Вы выбрали: {pair}\n\n"
        f"💰 Текущая цена: ${price:,.2f}\n"
        f"📊 Изменение 24ч: {change_24h:+.2f}%\n\n"
        f"Выберите тип алерта:"
    )
    await update.message.reply_text(text, reply_markup=reply_markup)
    return SET_VALUE

async def alert_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    logger.info("ALERT_TYPE_HANDLER called, data=%s", query.data)

    alert_type = query.data.split("|")[1]
    context.user_data["alert_type"] = alert_type

    # 🎯 Если изменение в процентах — другой текст запроса
    if alert_type in ("percent_up", "percent_down"):
        await query.message.reply_text(
            "Введите процент изменения, например: 3.5"
        )
        return SET_VALUE

    # 💰 Если алерт по цене — как было раньше
    await query.message.reply_text(
        "Введите цену для алерта (например: 70000):"
    )
    return SET_VALUE

async def delete_alert_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    index = int(query.data.split("|")[1])

    alerts = load_alerts()
    user_id = update.effective_user.id
    user_alerts = [a for a in alerts if a["user_id"] == user_id]

    if index < 0 or index >= len(user_alerts):
        await query.edit_message_text("❌ Ошибка — такого алерта нет.")
        return

    alert_to_remove = user_alerts[index]
    alerts.remove(alert_to_remove)
    save_alerts(alerts)

    await query.edit_message_text("✅ Алерт удалён!")

def format_alert_text(alert):
    pair = alert.get("pair", "???")
    atype = alert.get("alert_type", "unknown")
    value = alert.get("target_value", "")

    if atype == "below":
        condition = f"📉 Цена ниже: {value}"
    elif atype == "above":
        condition = f"🚀 Цена выше: {value}"
    elif atype == "percent_up":
        condition = f"📈 Рост: +{value}%"
    elif atype == "percent_down":
        condition = f"📉 Падение: -{value}%"
    else:
        condition = f"🧐 Неизвестный тип: {value}"

    return f"🔔 {pair}\n{condition}"

async def show_alerts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    alerts = load_alerts()

    if not alerts:
        await update.message.reply_text("У вас нет активных алертов 🙂")
        return

    for alert in alerts:
        text = format_alert_text(alert)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Удалить", callback_data=f"del_{alert['id']}")]
        ])
        await update.message.reply_text(text, reply_markup=keyboard)

async def delete_alert_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    alert_id = query.data.replace("del_", "")

    alerts = load_alerts()
    alerts = [a for a in alerts if a.get("id") != alert_id]
    save_alerts(alerts)

    await query.edit_message_text("✅ Алерт удалён")

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    choice = int(data.split("|")[1])

    if choice == 0:
        return await select_pair(update, context)

    elif choice == 1:
        alerts = load_alerts()
        user_alerts = [a for a in alerts if a["user_id"] == update.effective_user.id]
        if not user_alerts:
            await query.edit_message_text("У вас пока нет алертов 😌")
            return ConversationHandler.END
        await query.edit_message_text("📋 <b>Ваши алерты:</b>", parse_mode="HTML")
        for i, alert in enumerate(user_alerts):
            pair = alert["pair"]
            alert_type = alert.get("alert_type", "")
            value = alert.get("target_value", "?")
            if alert_type == "above":
                alert_title = "🚀 Цена выше"
            elif alert_type == "below":
                alert_title = "📉 Цена ниже"
            elif alert_type == "percent_up":
                alert_title = "📈 Рост"
                value = f"+{value}%"
            elif alert_type == "percent_down":
                alert_title = "📉 Падение"
                value = f"-{value}%"
            else:
                alert_title = "🧐 Неизвестный тип"
            text = f"🔔 <b>{pair}</b>\n{alert_title}: <b>{value}</b>"
            keyboard_single = InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Удалить", callback_data=f"del_{alert['id']}")
            ]])
            await query.message.reply_text(text, reply_markup=keyboard_single, parse_mode="HTML")
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")
        ]])
        await query.message.reply_text("Выберите действие:", reply_markup=keyboard)
        return ConversationHandler.END

    elif choice == 2:
        pairs = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
        await query.edit_message_text("⏳ Загружаю цены...")
        text_lines = ["💹 <b>Текущие цены:</b>\n"]
        for pair in pairs:
            price_data = get_current_price(pair)
            if price_data["success"]:
                info = price_data["data"]
                price = float(info["last_price"])
                change_24h = float(info["price_change_percent"])
                emoji = "🟢" if change_24h >= 0 else "🔴"
                sign = "+" if change_24h >= 0 else ""
                text_lines.append(
                    f"{emoji} <b>{pair.replace('USDT', '')}</b>: ${price:,.2f} "
                    f"({sign}{change_24h:.2f}%)"
                )

        await query.message.reply_text("\n".join(text_lines), parse_mode="HTML")
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")
        ]])
        await query.message.reply_text("Выберите действие:", reply_markup=keyboard)
        return ConversationHandler.END

logger = logging.getLogger(__name__)
async def check_single_alert(alert, app):
    pair = alert["pair"]
    alert_type = alert["alert_type"]
    target_value = float(alert["target_value"])
    user_id = alert["user_id"]

    price_data = get_current_price(pair)
    if not price_data["success"]:
        logger.warning(f"Ошибка получения цены для {pair}")
        return

    current_price = float(price_data["data"]["last_price"])

    # Проверка условий срабатывания
    triggered = False
    if alert_type == "above" and current_price >= target_value:
        message = f"🚀 {pair} достиг цены {current_price:.2f} (выше {target_value})"
        triggered = True
    elif alert_type == "below" and current_price <= target_value:
        message = f"📉 {pair} упал до {current_price:.2f} (ниже {target_value})"
        triggered = True
    elif alert_type in ("percent_up", "percent_down"):
        initial = float(alert["initial_price"])
        percent_target = float(alert["target_value"])
        change_now = (current_price - initial) / initial * 100

        if alert_type == "percent_up" and change_now >= percent_target:
            message = f"📈 {pair} вырос на {change_now:.2f}%!"
            triggered = True
        elif alert_type == "percent_down" and change_now <= -percent_target:
            message = f"📉 {pair} упал на {change_now:.2f}%!"
            triggered = True

    if not triggered:
        return

    try:
        await app.bot.send_message(chat_id=user_id, text=message)

        alerts = load_alerts()
        alerts = [a for a in alerts if not (
            a["user_id"] == user_id and
            a["pair"] == pair and
            a["alert_type"] == alert_type and
            float(a["target_value"]) == target_value and
            float(a.get("initial_price", initial)) == initial
        )]
        save_alerts(alerts)

        logger.info(f"Алерт удалён: {pair} {alert_type} {target_value}")
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")

async def check_alerts_task(app):
    logger.info("Фоновая проверка алертов запущена")

    alerts = load_alerts()

    alerts = [a for a in alerts if a.get("alert_type") in ("above", "below", "percent_up", "percent_down")]

    for alert in alerts:
        asyncio.create_task(check_single_alert(alert, app))

def main():
    async def post_init(app):
        logger.info("⏳ Инициализация фоновой задачи check_alerts_task...")
        if app.job_queue is None:
            app.job_queue = JobQueue()
        app.job_queue.set_application(app)

        # Запуск фоновой задачи
        app.job_queue.run_repeating(
            lambda _: asyncio.create_task(check_alerts_task(app)),
            interval=300,
            first=10
        )
        logger.info("✅ Фоновая задача check_alerts_task запущена")

    app = Application.builder().token(BOT_TOKEN).build()
    app.post_init = post_init

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            MAIN_MENU: [CallbackQueryHandler(menu_handler, pattern="^main_menu")],
            SELECT_PAIR: [
                CallbackQueryHandler(pair_handler, pattern="^pair"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, custom_pair_handler),
            ],
            SET_VALUE: [
                CallbackQueryHandler(alert_type_handler, pattern="^alert_type\\|"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_value_handler),
            ],
        },
        fallbacks=[],
        allow_reentry=True
    )
    # ✅ Глобальная команда — всегда доступна
    app.add_handler(CallbackQueryHandler(back_to_menu_handler, pattern="^back_to_menu$"))

    app.add_handler(CommandHandler("show_alerts", show_alerts_handler))

    app.add_handler(CommandHandler("help", help_command))

    # ✅ Callback удаления — срабатывает в любом состоянии
    app.add_handler(CallbackQueryHandler(delete_alert_callback, pattern="^del_"))

    app.add_handler(conv_handler)
    logger.info("🚀 Bot started!")
    app.run_polling()




if __name__ == "__main__":
    main()




