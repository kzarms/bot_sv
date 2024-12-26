import csv
import json
import logging
import os
import random
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)

debug = os.getenv("DEBUG", "")
FILES = [
    "./db/supervisors.json",
    "./db/supervisors_qeue.json",
    "./db/registrations.json",
]
if debug:
    # Run in debug
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    logging.info("Starting DEBUG mode!")
    SUPERVISORS = {
        "6412574124": {
            "FullName": "Kot",
            "Sessions": 2,
            "Requests": [],
            "Total": 0,
        },
        "1706832328": {
            "FullName": "Konstantin",
            "Sessions": 0,
            "Requests": [],
            "Total": 0,
            "UserName": "knstp",
        },
        "1222374948": {
            "FullName": "Лена Зарудаева",
            "Sessions": 0,
            "Requests": [],
            "Total": 0,
            "UserName": "helencoachde",
        },
    }
    SUPERVISORS_QEUE = ["6412574124", "1706832328", "1222374948"]
else:
    # Normal start
    SUPERVISORS = {}
    SUPERVISORS_QEUE = []
    logging.basicConfig(
        filename="./log.txt",
        filemode="a",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
REGISTRATIONS = {}
# TIMEOUT_CONVERSATION = 1 * 60 * 1  # 10 min to complete conversation

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

# region messages
FEEDBACK_URL = "https://forms.yandex.ru/cloud/659e5ee4e010db88f63e4db0/"
REPORT_URL = "https://docs.google.com/spreadsheets/d/1BKFfQUo2pu-Ksg6L9EXibRuasIjYLU84BBW00GanoHg/edit?pli=1#gid=508014521"

FOOTER_SV = "\n\n/review показать запросы\n/stat показать статистику"
FOOTER_USER = "\n\n/session запросить супервизию\n/help общая информация"
MSG_NON_SV = (
    "Вы не явялетесь супервизором, попросите администратора добавить вас в систему."
)
MSG_HELP = """Этот бот 🤖 поможет вам найти супервизора и записаться на встречу с ним. 👥
<b>Запись на сессию</b>
1. Нажмите команду /session, чтобы запросить супервизию. 📋
2. Выберите одного из супервизоров. 🕵️‍♂️
3. Договоритесь с супервизором о конктретном вермени. 📅

Вы всегда можете отозвать свой запрос командой /cancel до того как супервизор подтвердил его и создать новый, если хотите.
В исключительных случаях супервизор может отклонить ваш запрос, о чем вы будете оповещены.

<b>Дополнительные возможности</b>
🤝 Если вам нужна супервизия в личных целях (например, для себя как для коуча или для любой своей профессиональной роли за пределами академии), вы всегда можете обратиться к нашим супервизорам, которые готовы работать с вами по специальной тарифной ставке - 3.000 рублей.
Актуальный список таких супервизоров вы можете получить у Лены Зарудаевой @helencoachde

<b>Справка по командам</b>
Помощь: /help
Запрос сессии: /session
Подготовка к сессии: /help_more
Процесс одобрения: /help_next
Отмена заявки: /cancel

Все пожелания по улучшению, вы можете направить Лене Зарудаевой @helencoachde
💛 Хорошего дня 💛
"""
MSG_HELP_MORE = f"""Что важно учесть и как лучше подготовиться к супервизии, чтобы она прошла для вас наилучшим образом?

✅ Подумайте над ситуацией, связанной с вашей работой в Академии, которую вы хотели бы обсудить с супервизором.

✅ Пожалуйста, приходите вовремя. Супервизор ждет вас <b>5 минут</b>, а затем завершает встречу.

✅ Обеспечьте тихую и спокойную обстановку, чтобы вам было комфортно рассказывать о себе.

✅ Длительность супервизии составляет <b>30 минут</b>.

💟 Наши супервизоры будут вам благодарны за оставленный <a href='{FEEDBACK_URL}'>отзыв</a> о работе супервизора. <a href='{FEEDBACK_URL}'>Отзыв</a> является добровольным и анонимным.
"""
MSG_HELP_NEXT = """❓Что дальше?

Супервизор получил ваш запрос, и если технические настройки <b>вашего</b> Телеграм позволят ему написать вам сообщение, он сделает это в течение <b>2-3 часов</b>.

Если в течение этого времени вы не получили ответа от супервизора, вы можете связаться с ним самостоятельно, нажав на его имя в сообщении, и договориться о времени встречи.

Вы также в любой момент можете отменить /cancel свой запрос к этому супервизору, пока он его не принял.

Общая информация: /help"""
MSG_HELP_CONFIRM = """

Как подготовиться: /help_more
Общая информация: /help
"""
MSG_HELP_REQUEST = """

Что дальше: /help_next
Отмена запроса: /cancel
"""

USER_SESSION_CONFIRMATIONS = [
    f"😀 Ваша заявка на консультацию с SUPERVISOR была успешно одобрена.\n\nМы ценим ваше доверие к нашей команде внутренних специалистов. Не забудьте поделиться вашим мнением о сессии через <a href='{FEEDBACK_URL}'>анонимный опрос</a> на нашем сайте.{MSG_HELP_CONFIRM}",
    f"🎉 Поздравляем, ваш запрос на встречу с супервизором SUPERVISOR получил одобрение.\n\nМы рады предоставить вам возможность работы с нашими профессионалами. Оставьте свой <a href='{FEEDBACK_URL}'>анонимный отзыв</a> о взаимодействии на указанной странице.{MSG_HELP_CONFIRM}",
    f"🌟 Ваше обращение за супервизией у SUPERVISOR принято.\n\nСпасибо за то, что выбрали нашу службу внутренних супервизоров. Ваше мнение важно для нас, пожалуйста, оставьте <a href='{FEEDBACK_URL}'>анонимный отзыв</a> после сессии.{MSG_HELP_CONFIRM}",
    f"😊 Заявка на сессию супервизии с SUPERVISOR одобрена.\n\nМы ценим ваш выбор наших услуг и стремимся предложить лучшее сопровождение. Не забывайте, что ваше мнение может быть <a href='{FEEDBACK_URL}'>анонимно</a> озвучено на нашем ресурсе.{MSG_HELP_CONFIRM}",
    f"👍 Ваш запрос на супервизорскую поддержку от SUPERVISOR утвержден.\n\nМы рады сопровождать вас в этом процессе и надеемся, что он будет плодотворным. Пожалуйста, поделитесь своими впечатлениями <a href='{FEEDBACK_URL}'>анонимно</a> на нашей платформе.{MSG_HELP_CONFIRM}",
    f"💖 Вам одобрена супервизия с SUPERVISOR.\n\nМы рады предоставить вам качественную поддержку наших специалистов. Ваш отзыв может быть оставлен <a href='{FEEDBACK_URL}'>анонимно</a> и будет очень ценен для нас.{MSG_HELP_CONFIRM}",
    f"🥳 Ваша заявка на работу с супервизором SUPERVISOR успешно одобрена.\n\nМы гордимся возможностью предложить вам профессиональную поддержку. Не забудьте оставить свой <a href='{FEEDBACK_URL}'>анонимный отзыв</a> на нашем сайте.{MSG_HELP_CONFIRM}",
    f"🎈 Поздравляем, ваш запрос на консультацию с супервизором SUPERVISOR одобрен.\n\nМы стремимся предоставить вам лучшую поддержку. Пожалуйста, оставьте ваш <a href='{FEEDBACK_URL}'>анонимный отзыв</a> о сессии, это поможет нам улучшить наши услуги.{MSG_HELP_CONFIRM}",
    f"✨ Ваша заявка на сессию супервизии с SUPERVISOR была утверждена.\n\nМы рады предложить вам помощь наших квалифицированных супервизоров. Ваше <a href='{FEEDBACK_URL}'>анонимное мнение</a> очень важно для нас, не забудьте его оставить.{MSG_HELP_CONFIRM}",
    f"🚀 Ваш запрос на встречу с супервизором SUPERVISOR получил зеленый свет.\n\nМы признательны за ваше доверие к нашим внутренним специалистам. Пожалуйста, поделитесь своими впечатлениями <a href='{FEEDBACK_URL}'>анонимно</a>, чтобы мы могли стать лучше.{MSG_HELP_CONFIRM}",
]

SV_SESSION_CONFIRMATIONS = [
    f"🌟 Дорогой супервизор, большое спасибо за твои усилия! 📝 Не забудь, пожалуйста, внести информацию о супервизиях в <a href='{REPORT_URL}'>отчет</a>. 🙏",
    f"🤗 Уважаемый супервизор, благодарим за твою великолепную работу! 📊 Мы были бы рады видеть данные супервизий в <a href='{REPORT_URL}'>отчет</a>. 📌",
    f"👋 Привет, дорогой супервизор! Огромное спасибо за твой вклад. 🗂️ Не мог бы ты добавить результаты супервизий в наш <a href='{REPORT_URL}'>отчет</a>? 📈",
    f"💼 Уважаемый супервизор, твоя работа восхитительна! 🌈 Пожалуйста, не забывай вносить данные о супервизиях в <a href='{REPORT_URL}'>отчет</a>. 📋",
    f"💌 Дорогой супервизор, ты делаешь отличную работу! 🎉 Будь так добр, включи, пожалуйста, информацию о супервизиях в наш <a href='{REPORT_URL}'>отчет</a>. 📚",
    f"👍 Приветствуем тебя, супервизор! Твои усилия неоценимы. 🌟 Пожалуйста, убедись, что данные супервизий отражены в <a href='{REPORT_URL}'>отчете</a>. ✅",
    f"🎖️ Уважаемый супервизор, твоя работа заслуживает похвалы! 📘 Не забудь, пожалуйста, внести соответствующие данные в <a href='{REPORT_URL}'>отчете</a>. 🖊️",
    f"🌺 Дорогой супервизор, твоя помощь бесценна! 💼 Ждем данных о супервизиях в нашем <a href='{REPORT_URL}'>отчете</a>. 📉",
    f"💫 Уважаемый супервизор, благодарим за твой вклад! 📖 Надеемся увидеть данные о супервизиях в <a href='{REPORT_URL}'>отчете</a> в ближайшее время. ⏳",
    f"🙌 Привет, замечательный супервизор! Твоя работа вдохновляет нас. 🌟 Пожалуйста, не забудь внести информацию о супервизиях в наш <a href='{REPORT_URL}'>отчет</a>. 📑",
]

REPORT_CONFIRMATIONS = [
    "Привет, Заяц! 😊 Твоя улыбка сегодня особенно сияет. Кстати, отчет готов, как и обещал. 📄✨",
    "Доброе утро, Ух! 🌞 Ты сегодня выглядишь просто великолепно. А еще у меня для тебя хорошие новости: отчет полностью готов. 📊🌟",
    "Приветик, 🐰 Ты всегда находишь способ заставить меня улыбаться. Спешу сообщить, что твой отчет готов. 📈💖",
    "Здравствуй, Ух! 👋 Твой стиль сегодня просто безупречен. И кстати, отчет уже на твоем столе. 📑🎉",
    "Привет, 🐇 ☀️ Ты сегодня как солнце - светишься изнутри. Отчет, кстати, уже готов. 📝✅",
    "🐰, ты как всегда очаровательна! 💫 И чтобы добавить тебе радости, отчет уже готов. 📚💌",
    "Привет, Заяц! 🌺 Твои идеи всегда такие оригинальные, как и ты сама. Отчет готов, ждет тебя. 📖🚀",
    "Ух, твой энтузиазм просто заразителен! 😃 Готова ли ты услышать, что отчет тоже заразительно готов? 📋🎈",
    "Здравствуй, 🐇! 💖 Ты сегодня просто сверкаешь. И я сверкаю от радости, сообщая, что отчет готов. 🌟📚",
    "Привет, Ух! 🤗 Ты всегда такая вдумчивая, это восхищает. Отчет готов, как и твои мысли, всегда на месте. 🧠📃",
    "Заяц, твое терпение и усердие вдохновляют. С радостью сообщаю, что отчет готов. 🐾💌",
    "Ух, твое чувство юмора - мое спасение в серые дни. Как и твой отчет, который уже готов. 😂📑",
    "Заяц, ты как всегда на высоте! И чтобы твой день был еще лучше, отчет уже готов. 🚀📊",
    "Привет, 🐇. 💐 Твоя интуиция просто поразительна, как и скорость, с которой был подготовлен этот отчет. Готово! 🌈📈",
    "Заяц, ты источник вдохновения для всех нас. 🌟 И вот твой отчет, подготовленный с такой же заботой. 📓💕",
    "Ух, ты превосходишь ожидания в каждом деле. 🌠 И твой отчет, конечно, не исключение - он уже готов. 🗂️💡",
    "🐰, твоя энергия освежает как утренний бриз. 🌬️ И радостное известие: отчет готов! 📁🌸",
]


# endregion
# region local functions
def get_tocken() -> str:
    try:
        with open("./token.txt", "r") as f:
            return f.readline()
    except:
        logging.error("Problem with token")
    return ""


def add_sv_request(id, user_id, user_name) -> bool:
    # Add request for supervisor
    SUPERVISORS[id]["Requests"].append({"id": user_id, "FullName": user_name})
    logging.info(f"Added request from {user_name} for {SUPERVISORS[id]['FullName']}")
    return True


def add_sv_session(supervisor) -> bool:
    # This function adds session to the supervisor
    SUPERVISORS[supervisor]["Total"] += 1
    if SUPERVISORS[supervisor]["Sessions"] >= 2:
        logging.info(
            f"This is the third session, put {SUPERVISORS[supervisor]['FullName']} in the end of the list."
        )
        SUPERVISORS[supervisor]["Sessions"] = 0
        return True
    else:
        logging.info(f"Adding session for {supervisor}")
        SUPERVISORS[supervisor]["Sessions"] += 1
    return False


def del_sv_request(id, user_id) -> bool:
    # Add request for supervisor
    temp_list = SUPERVISORS[id]["Requests"]
    for request in SUPERVISORS[id]["Requests"]:
        if request["id"] == user_id:
            temp_list.remove(request)
            break
    SUPERVISORS[id]["Requests"] = temp_list
    logging.info(f"Removed {user_id} request from {SUPERVISORS[id]['FullName']}")
    return True


def decline_sv_requests(id) -> bool:
    # Add request for supervisor
    temp_list = SUPERVISORS[id]["Requests"]
    SUPERVISORS[id]["Requests"] = []
    logging.info(
        f"Removed {len(temp_list)} requests from {SUPERVISORS[id]['FullName']}"
    )
    return temp_list


def update_sv_list(supervisor):
    """Update list of supervisors"""
    if supervisor in SUPERVISORS_QEUE:
        logging.info(f"User {supervisor} is in the list")
        SUPERVISORS_QEUE.remove(supervisor)
    SUPERVISORS_QEUE.append(supervisor)
    logging.info(f"Update user list of supervisors {SUPERVISORS_QEUE}")
    return SUPERVISORS_QEUE


def save_to_local():
    """Save data to local file"""
    for file in FILES:
        file.upper()
        var = file[5:-5].upper()
        with open(file, "w", encoding="utf-8") as f:
            json.dump(globals()[var], f, ensure_ascii=False, indent=4)
    logging.info(f"Saved to local files")


def load_from_local():
    """Save data to local file"""
    logging.info("Read from local files")
    for file in FILES:
        var = file[5:-5].upper()
        # If we have data in the vars, do not load them
        if len(globals()[var]) == 0:
            with open(file, "r", encoding="utf-8") as f:
                globals()[var] = json.load(f)
                logging.info(f"Loaded {len(globals()[var])} objects for {var}")
    logging.info(f"Active queue is:\n{SUPERVISORS_QEUE}")


def create_sv_list_from_db():
    """Create list of supervisors"""
    if len(SUPERVISORS_QEUE) == 0:
        for supervisor in SUPERVISORS:
            SUPERVISORS_QEUE.append(supervisor)
        logging.info(f"Found empty QEUE, load it!\n{SUPERVISORS_QEUE}")
    return SUPERVISORS_QEUE


def gen_report() -> str:
    # Generate csv file
    current_datetime = datetime.now()
    file_name = f"{current_datetime.strftime('%Y-%m-%d_%H:%M:%S')}_report.csv"
    with open(file_name, "w", encoding="utf-8", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["Супервизор", "Сессии", "Запросы", "Всего"])
        for supervisor in SUPERVISORS:
            csvwriter.writerow(
                [
                    SUPERVISORS[supervisor]["FullName"],
                    SUPERVISORS[supervisor]["Sessions"],
                    len(SUPERVISORS[supervisor]["Requests"]),
                    SUPERVISORS[supervisor]["Total"],
                ]
            )
    return file_name


# endregion
# region telegram functions
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """General help message about commands"""
    await update.message.reply_text(MSG_HELP, parse_mode=ParseMode.HTML)


async def help_more(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help message about more info"""
    await update.message.reply_text(MSG_HELP_MORE, parse_mode=ParseMode.HTML)


async def help_next(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help message about next"""
    await update.message.reply_text(MSG_HELP_NEXT, parse_mode=ParseMode.HTML)


async def reg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Register as Supervisor"""
    logging.info(f"Registration for {update.effective_user}")
    message = f"Ваша заявка на регистрацию принята."
    await update.message.reply_text(message)
    msg = f"Привет, Ух! В твой бот просится на регистрацию {update.effective_user.first_name}. Скажи мужу чтоб добавил {update.effective_user.id}. Чмок!"
    await context.bot.send_message(
        chat_id="1222374948", text=msg, parse_mode=ParseMode.HTML
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """First interruction with the user, keep in USER db"""
    user = update.effective_user.id
    message = f"Добро пожаловать {update.effective_user.full_name}!{FOOTER_USER}"
    if user in SUPERVISORS:
        message += FOOTER_SV
    await update.message.reply_text(message)


async def stat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get status for superuser"""
    supervisor = str(update.effective_user.id)
    if supervisor not in SUPERVISORS:
        await update.message.reply_text(MSG_NON_SV)
        return
    if supervisor == "1222374948":
        # Special report for Lena
        report_file = gen_report()
        message = random.choice(REPORT_CONFIRMATIONS)
        await update.message.reply_text(message)
        with open(report_file, "rb") as file:
            await context.bot.sendDocument(
                chat_id=update.effective_user.id, document=file, filename=report_file
            )
    else:
        # Common message
        message = f"У вас {SUPERVISORS[supervisor]['Sessions']} забронированных сессий и {len(SUPERVISORS[supervisor]['Requests'])} запросов в ожидании.{FOOTER_SV}"
        await update.message.reply_text(message)


async def session_sv_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sends a message with three inline buttons attached."""
    user_id = str(update.effective_user.id)
    if user_id in REGISTRATIONS:
        await update.message.reply_text(
            "У вас уже есть запрос на супервизию.\n\n/cancel отменить запрос"
        )
        return ConversationHandler.END
    keyboard = []
    # If we have less than 4 items, just add them to the keyboard,
    items = min(len(SUPERVISORS_QEUE), 4)
    for i in range(items):
        supervisor = SUPERVISORS_QEUE[i]
        keyboard.append(
            [InlineKeyboardButton(SUPERVISORS[supervisor]["FullName"], callback_data=i)]
        )
    keyboard.append([InlineKeyboardButton("Cancel", callback_data="99")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите супервизора:", reply_markup=reply_markup)
    return 0


async def session_sv_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    user_id = str(update.effective_user.id)
    await query.answer()
    answer = int(query.data)
    if answer == 99:
        await query.edit_message_text(text="Отменено")
        return ConversationHandler.END
    # Todo: Add check if the ID in the requests
    # Request session for the SV
    id = SUPERVISORS_QEUE[answer]
    # Add user request into DB
    REGISTRATIONS[user_id] = id
    add_sv_request(id, user_id, update.effective_user.full_name)
    # Notify SV
    logging.info(REGISTRATIONS)
    username = ""
    try:
        username = f" @{update.effective_user.username}"
    except:
        logging.info(f"{update.effective_user.first_name} does not have username")
    msg = f"У вас есть новый запрос на супервизию от {update.effective_user.mention_html()}{username}.{FOOTER_SV}"
    await context.bot.send_message(chat_id=id, text=msg, parse_mode=ParseMode.HTML)
    # Notify User
    sv_username = ""
    if "UserName" in SUPERVISORS[id]:
        sv_username = f' @{SUPERVISORS[id]["UserName"]}'
    message = f'Ваш запрос на супервизию отправлен <a href="tg://user?id={id}">{SUPERVISORS[id]["FullName"]}</a>.{sv_username}{MSG_HELP_REQUEST}'
    # Send message back to the user
    await query.edit_message_text(text=message, parse_mode=ParseMode.HTML)
    save_to_local()
    return ConversationHandler.END


async def supervisor_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sends a message with three inline buttons attached."""
    # If empty end conversation
    supervisor = str(update.effective_user.id)
    if supervisor not in SUPERVISORS:
        await update.message.reply_text(MSG_NON_SV)
        return ConversationHandler.END
    # If empty end conversation
    requests = SUPERVISORS[supervisor]["Requests"]
    if requests == []:
        await update.message.reply_text("У вас нет запросов на супервизию")
        return ConversationHandler.END
    keyboard = []
    # If not empty add buttons to the keyboard,
    for i in range(len(requests)):
        requestor = requests[i]
        keyboard.append(
            [InlineKeyboardButton(requestor["FullName"], callback_data=requestor["id"])]
        )
    keyboard.append([InlineKeyboardButton("Cancel", callback_data="99")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите запрос:", reply_markup=reply_markup)
    return 0


async def supervisor_review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    supervisor = str(update.effective_user.id)
    await query.answer()
    answer = query.data
    if answer == "99":
        await query.edit_message_text(text="Отменено")
        return ConversationHandler.END
    keyboard = [
        [
            InlineKeyboardButton("Принять", callback_data=f"accept {answer}"),
            InlineKeyboardButton("Отклонить", callback_data=f"decline {answer}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    for user in SUPERVISORS[supervisor]["Requests"]:
        if user["id"] == int(answer):
            break
    msg = f"Супервизия для {user['FullName']}"
    await query.edit_message_text(text=msg, reply_markup=reply_markup)
    return 1


async def supervisor_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    "Final processing"
    users_to_notify = []
    reset = False
    query = update.callback_query
    supervisor = str(update.effective_user.id)
    await query.answer()
    answer = query.data.split(" ")
    for user in SUPERVISORS[supervisor]["Requests"]:
        if user["id"] == answer[1]:
            break
    # Accept
    if answer[0] == "accept":
        sv_message = f"Запрос одобрен для {user['FullName']}"
        user_message = random.choice(USER_SESSION_CONFIRMATIONS)
        user_message = user_message.replace(
            "SUPERVISOR", SUPERVISORS[supervisor]["FullName"]
        )
        reset = add_sv_session(supervisor)
        if reset:
            # Reset couner
            update_sv_list(supervisor)
            sv_message += f"\n\n{random.choice(SV_SESSION_CONFIRMATIONS)}"
    # Decline
    else:
        sv_message = f"Запрос отклонен для {user['FullName']}"
        user_message = f"Ваш запрос на супервизию к {SUPERVISORS[supervisor]['FullName']} отклонен."
    # Remove user from request and waiting list
    REGISTRATIONS.pop(user["id"])
    del_sv_request(supervisor, user["id"])
    # Notify user
    await context.bot.send_message(
        chat_id=user["id"], text=user_message, parse_mode=ParseMode.HTML
    )
    if reset:
        # Cleanup requests
        users_to_notify = decline_sv_requests(supervisor)
        user_message_decline = (
            f"Слоты у супервизора {SUPERVISORS[supervisor]['FullName']} закончились. "
        )
        user_message_decline = "Обратитесь, пожалуйста, к другому свободному супервизору.\n\n/session запросить супервизию"
        for user in users_to_notify:
            await context.bot.send_message(
                chat_id=user["id"], text=user_message_decline
            )
    # Add session into DB
    await query.edit_message_text(text=sv_message, parse_mode=ParseMode.HTML)
    save_to_local()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel and end the conversation."""
    user_id = str(update.effective_user.id)
    if user_id in REGISTRATIONS:
        supervisor = REGISTRATIONS[user_id]
        REGISTRATIONS.pop(user_id)
        del_sv_request(supervisor, user_id)
        await update.message.reply_text(
            f"Ваш запрос на супервизию к {SUPERVISORS[supervisor]['FullName']} отменен."
        )
        msg = f"Запрос от {update.effective_user.full_name} отменен пользоветелем.{FOOTER_SV}"
        save_to_local()
        await context.bot.send_message(chat_id=supervisor, text=msg)
    else:
        await update.message.reply_text("Не вопрос, попробуйте в следующий раз.")
        user = update.message.from_user
        logging.info(f"User {user.full_name} canceled the conversation.")
        return ConversationHandler.END


# endregion


# main function
def main():
    # Load data in memory
    load_from_local()
    create_sv_list_from_db()
    # Get access
    token = get_tocken()
    if not token:
        return 1
    # Star the chat bot
    application = ApplicationBuilder().token(token).build()
    # Commands
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("help_more", help_more))
    application.add_handler(CommandHandler("help_next", help_next))
    application.add_handler(CommandHandler("reg", reg))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stat", stat))
    application.add_handler(CommandHandler("cancel", cancel))
    # Conversations
    conv_sesion_request = ConversationHandler(
        allow_reentry=True,
        entry_points=[CommandHandler("session", session_sv_select)],
        states={
            0: [CallbackQueryHandler(session_sv_request)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    conv_sesion_review = ConversationHandler(
        allow_reentry=True,
        entry_points=[CommandHandler("review", supervisor_select)],
        states={
            0: [CallbackQueryHandler(supervisor_review)],
            1: [CallbackQueryHandler(supervisor_answer)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_sesion_request)
    application.add_handler(conv_sesion_review)
    # App
    application.run_polling(allowed_updates=Update.ALL_TYPES)


# Local execution
if __name__ == "__main__":
    main()
