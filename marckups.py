import aiogram
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

menu_cd = CallbackData("menu", "action")

async def help_keyboard():
    keyboard = InlineKeyboardMarkup()
    # keywords_button = InlineKeyboardButton("Ключевики", callback_data=menu_cd.new(action="keywords"))
    keywords_button = InlineKeyboardButton("Шаблоны", callback_data=menu_cd.new(action="templates"))
    # blacklistkeywords_button = InlineKeyboardButton("Стоп слова", callback_data=menu_cd.new(action="blacklistkeywords"))
    # groups_button = InlineKeyboardButton("Группы", callback_data=menu_cd.new(action="groups"))
    scan_button = InlineKeyboardButton("Сканирование", callback_data=menu_cd.new(action="scan"))
    # users_button = InlineKeyboardButton("Пользователи", callback_data=menu_cd.new(action="users"))
    messages_button = InlineKeyboardButton("Выгрузка сообщений", callback_data=menu_cd.new(action="messages"))
    keyboard.add(keywords_button, scan_button)
    keyboard.row(messages_button)
    return keyboard

async def keywords_keyboard():
    keyboard = InlineKeyboardMarkup()
    list_button = InlineKeyboardButton("Список", callback_data=menu_cd.new(action="list_keywords"))
    add_button = InlineKeyboardButton("Добавить", callback_data=menu_cd.new(action="add_keywords"))
    delete_button = InlineKeyboardButton("Удалить", callback_data=menu_cd.new(action="remove_keywords"))
    keyboard.add(list_button, add_button, delete_button)
    keyboard.add(back_button())
    return keyboard

async def templates_keyboard():
    keyboard = InlineKeyboardMarkup()
    list_button = InlineKeyboardButton("Список", callback_data=menu_cd.new(action="show_templates_button"))
    add_button = InlineKeyboardButton("Добавить", callback_data=menu_cd.new(action="add_template"))
    delete_button = InlineKeyboardButton("Удалить", callback_data=menu_cd.new(action="remove_template"))
    keyboard.add(list_button, add_button, delete_button)
    keyboard.add(back_button())
    return keyboard

async def blacklistkeywords_keyboard():
    keyboard = InlineKeyboardMarkup()
    list_button = InlineKeyboardButton("Список", callback_data=menu_cd.new(action="list_blacklistkeywords"))
    add_button = InlineKeyboardButton("Добавить", callback_data=menu_cd.new(action="add_blacklistkeywords"))
    delete_button = InlineKeyboardButton("Удалить", callback_data=menu_cd.new(action="remove_blacklistkeywords"))
    keyboard.add(list_button, add_button, delete_button)
    keyboard.add(back_button())
    return keyboard

async def groups_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    list_button = InlineKeyboardButton("Список", callback_data=menu_cd.new(action="list_groups"))
    search_button = InlineKeyboardButton("Поиск новой", callback_data=menu_cd.new(action="join_group_by_search"))
    join_button = InlineKeyboardButton("Присоединиться по ссылке", callback_data=menu_cd.new(action="join_group_by_link"))
    remove_button = InlineKeyboardButton("Удалить", callback_data=menu_cd.new(action="remove_groups"))
    back_btn = back_button()
    keyboard.add(list_button, search_button, join_button, remove_button)
    keyboard.row(back_btn)
    return keyboard

async def scan_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    # selective_button = InlineKeyboardButton("Запустить", callback_data=menu_cd.new(action="selective_scan"))
    # stop_selective_button = InlineKeyboardButton("Остановить", callback_data=menu_cd.new(action="selective_stop"))
    selective_button_template = InlineKeyboardButton("Запустить шаблон", callback_data=menu_cd.new(action="selective_scan_template"))
    stop_selective_button_template = InlineKeyboardButton("Остановить шаблон", callback_data=menu_cd.new(action="selective_stop_template"))
    keyboard.add(selective_button_template, stop_selective_button_template)
    keyboard.add(back_button())
    return keyboard

async def users_keyboard():
    keyboard = InlineKeyboardMarkup()
    create_user_button = InlineKeyboardButton("Создать пользователя", callback_data=menu_cd.new(action="create_user"))
    keyboard.add(create_user_button)
    keyboard.add(back_button())
    return keyboard

async def messages_keyboard():
    keyboard = InlineKeyboardMarkup()
    month_button = InlineKeyboardButton("За месяц", callback_data=menu_cd.new(action="month_messages"))
    week_button = InlineKeyboardButton("За 7 дней", callback_data=menu_cd.new(action="week_messages"))
    day_button = InlineKeyboardButton("За сутки", callback_data=menu_cd.new(action="day_messages"))
    keyboard.add(day_button, week_button, month_button)
    keyboard.add(back_button())
    return keyboard


async def back_keyboard():
    return InlineKeyboardMarkup().add(back_button())

def back_button():
    return InlineKeyboardButton("Назад", callback_data=menu_cd.new(action="back"))
