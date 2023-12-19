# Вспомогательные импорты
from dotenv import load_dotenv
import os
import asyncio
import traceback

# Импорты thelethon парсера
from telethon import TelegramClient

# Импорты aiogram бота
import aiogram
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery
from aiogram.dispatcher.filters import Command
from aiogram.utils.callback_data import CallbackData
import logging

# Организационные функции
from dbtools import *
from parser_funcs import *
from aditional_functions import *
from marckups import *

import pandas as pd
import os

# Импорт функций для хэндлеров
from templates_handlers import *

# Загрузка переменных окружения
load_dotenv()

# Переменные парсера
api_id = os.environ.get('API_ID')
api_hash = os.environ.get('API_HASH')
phone = os.environ.get('PHONE')

# api_id = '27998566'
# api_hash = '0dbe1ae10bde5203291929e066783cdc'
# phone = '+995555377197'

current_client = TelegramClient(phone, api_id, api_hash)

# client = TelegramClient("+79029858141")

# Переменные бота
bot_token = os.environ.get('BOT_TOKEN')
bot = Bot(token=bot_token)
dp = Dispatcher(bot)
print(dp)


# Глобальные переменные
going_tasks = {}
user_data = {}

# Список доступных команд
available_commands = [
    # Команды бота
    {'command': 'start', 'description': 'Приветственное сообщение'},
    {'command': 'help', 'description': 'Получить список доступных команд'},
    {'command': 'create_user', 'description': 'Добавить себя в список пользователей'},

    # Команды ключевых слов
    {'command': 'list_keywords',
        'description': 'Отобразить список текущих кллючевых слов'},
    {'command': 'add_keywords',
        'description': 'Добавить ключевые слова для отслеживания конкретных сообщений'},
    {'command': 'remove_keyword', 'description': 'Удалить ключевое слово'},

    # Команды групп
    {'command': 'list_groups',
        'description': 'Отобразить список текущих добавленных вами групп'},
    {'command': 'add_group_search',
        'description': 'Добавить группу в список при помощи поиска'},
    {'command': 'add_group_link',
        'description': 'Добавить группу в список при помощи ссылки'},
    {'command': 'remove_group',
        'description': 'Удалить добавленную ранее группу из списка'},

    # Команды сканирования
    {'command': 'start_scan',
        'description': 'Выбрать добавленную группу и начать сканирование по добавленным ключевым словам'},
    {'command': 'stop_scan', 'description': 'Остановить запущенное сканирование группы'},

]

# Обработчик команды запуска бота


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply("""Привет! Я бот для отселживания сообщений в телеграм-чатах.
    \nЯ могу сканировать добавленные вами групповые чаты и искать в них сообщения, в которых есть добавленные вами ключевые слова.
    \nНапиши /menu, чтобы попасть в меню взаимодействия.
    \nv.1.19.12""")

# Обработчик команды для получения списка команд
menu_cd = CallbackData("menu", "action")


@dp.callback_query_handler(menu_cd.filter(action="keywords"))
async def show_keywords_menu(query: CallbackQuery):
    text = "Меню взаимодействия с ключевыми словами"
    keyboard = await keywords_keyboard()
    await query.message.edit_text(text, reply_markup=keyboard)
    await query.answer()


@dp.callback_query_handler(menu_cd.filter(action="templates"))
async def show_templates_menu(query: CallbackQuery):
    text = "Меню взаимодействия с шаблонами"
    keyboard = await templates_keyboard()
    await query.message.edit_text(text, reply_markup=keyboard)
    await query.answer()


@dp.callback_query_handler(menu_cd.filter(action="messages"))
async def show_keywords_menu(query: CallbackQuery):
    text = "Выберите необходимый временной интервал"
    keyboard = await messages_keyboard()
    await query.message.edit_text(text, reply_markup=keyboard)
    await query.answer()


@dp.callback_query_handler(menu_cd.filter(action="blacklistkeywords"))
async def show_blacklistkeywords_menu(query: CallbackQuery):
    text = "Меню взаимодействия с стоп словами"
    keyboard = await blacklistkeywords_keyboard()
    await query.message.edit_text(text, reply_markup=keyboard)
    await query.answer()


@dp.callback_query_handler(menu_cd.filter(action="groups"))
async def show_groups_menu(query: CallbackQuery):
    text = "Меню взаимодействия с группами"
    keyboard = await groups_keyboard()
    await query.message.edit_text(text, reply_markup=keyboard)
    await query.answer()


@dp.callback_query_handler(menu_cd.filter(action="scan"))
async def show_scan_menu(query: CallbackQuery):
    text = "Сканирование"
    keyboard = await scan_keyboard()
    await query.message.edit_text(text, reply_markup=keyboard)
    await query.answer()


@dp.callback_query_handler(menu_cd.filter(action="users"))
async def show_users_menu(query: CallbackQuery):
    text = "Меню взаимодействия с пользователями"
    keyboard = await users_keyboard()
    await query.message.edit_text(text, reply_markup=keyboard)
    await query.answer()


@dp.callback_query_handler(menu_cd.filter(action="back"))
async def back_to_main_menu(query: CallbackQuery):
    user_id = query.from_user.id
    if user_id in user_data:
        del user_data[user_id]

    text = "Меню взаимодействия"
    keyboard = await help_keyboard()
    await query.message.edit_text(text, reply_markup=keyboard)
    await query.answer()


@dp.message_handler(Command('menu'))
async def cmd_help(message: types.Message):
    help_text = "Меню взаимодействия"
    keyboard = await help_keyboard()
    await bot.send_message(chat_id=message.chat.id, text=help_text, reply_markup=keyboard)

# Обработчик команды создания нового пользователя


async def user_exists(user_id, user_chat_id):
    users_list = await get_users_list()
    for user in users_list:
        if user[0] == user_id and user[2] == user_chat_id:
            return True
    return False


@dp.message_handler(commands=['create_user'])
async def process_start_command(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if await user_exists(user_id, chat_id):
        await bot.send_message(chat_id, "Вы уже добавлены в список пользователей.")
        return

    keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("Да", callback_data="add_user")
                                          ).add(InlineKeyboardButton("Нет", callback_data="cancel_add_user"))
    await bot.send_message(chat_id, "Хотите добавить себя в список пользователей?", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data in ['add_user', 'cancel_add_user'])
async def process_inline_answer(callback_query: aiogram.types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    user_name = callback_query.from_user.full_name

    if callback_query.data == 'add_user':
        await add_user(user_id, user_name, user_id)
        await bot.send_message(chat_id, "Отлично! Вы добавлены")
    else:
        await bot.send_message(chat_id, "Вы отказались от добавления в список оповещаемых.")

    await bot.answer_callback_query(callback_query.id)


template_event_handler = GroupsEventHandler(current_client, bot)

# Обработчик команды запуска сканирования шаблона


@dp.callback_query_handler(menu_cd.filter(action="selective_scan_template"))
async def add_start_scan__handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    markup = aiogram.types.InlineKeyboardMarkup(row_width=1)
    markup.add(back_button())

    selected_teplate_id = await find_selected_template(user_id)
    templateGroupList = await get_template_group_list(selected_teplate_id[0])
    # userGroupList = await get_user_group_list(user_id)

    groupArr = []
    groupIdArr = []

    for group in templateGroupList:
        groupArr.append({'chat_id': group[0], 'chat_name': group[1]})
        groupIdArr.append(int(group[0]))

    if (len(groupArr) > 0):

        print(template_event_handler.stop_listening)
        logging.info(template_event_handler.stop_listening)
        if (template_event_handler.stop_listening == True):
            template_event_handler.start_handler()
            msg_text = "Запущенно сканирование следующих групп: \n"
            await callback_query.message.edit_text("Ожидайте....")
            logging.info(groupIdArr)
            print(groupIdArr)
            for id in groupIdArr:
                logging.info("get_group_by_id")
                selected_group = await get_group_by_id(int(id), current_client)
                if (selected_group == 'Это приватный чат, или бота прогнали'):
                    await bot.send_message(chat_id=chat_id, text=f"Возможно бота прогнали из группы {id}")
                    groupIdArr.remove(id)
                    continue
            try:
                print("Попытка создать Экземпляр")
                logging.info("Попытка создать Экземпляр")
                await template_event_handler.create_template_groups_event_handler(groupIdArr, chat_id, selected_teplate_id[0])
                for group in groupArr:
                    msg_text += f"{group['chat_name']} id: {group['chat_id']}\n"
                await callback_query.message.edit_text(msg_text, reply_markup=markup)
            except Exception as e:
                print("Произошла ошибка:")
                logging.info("Произошла ошибка:")
                logging.info(e)
                print(e)
                traceback.print_exc()
                await callback_query.message.edit_text('Ошибка запуска сканирования', reply_markup=markup)
        else:
            await callback_query.message.edit_text('Сканирование уже запущенно', reply_markup=markup)

    else:
        await callback_query.message.edit_text(f"У вас нет добавленных групп в шаблоне", reply_markup=markup)

# Обработчик команды остановки сканирования


@dp.callback_query_handler(menu_cd.filter(action="selective_stop_template"))
async def add_stop_scan__handler(query: CallbackQuery):
    markup = aiogram.types.InlineKeyboardMarkup(row_width=1)
    markup.add(back_button())
    try:
        if (template_event_handler.stop_listening == False):
            template_event_handler.stop_handler()
            await query.message.edit_text(text="Все задачи сканирования остановленны", reply_markup=await back_keyboard())
        else:
            await query.message.edit_text(text="Нет активных задач для остановки", reply_markup=await back_keyboard())
    except Exception as e:
        print("Произошла ошибка:")
        print(str(e))
        logging.info("Произошла ошибка:")
        logging.info(str(e))
        traceback.print_exc()
        await query.message.edit_text(text="Ошибка остановки сканирования", reply_markup=await back_keyboard())

template_cd = CallbackData("template", "template_id", "action")

# Обработчик получения команды без обработчика


@dp.message_handler(commands=['unknown_command'], commands_prefix='/', regexp='^/')
async def cmd_unknown(message: types.Message):
    await message.reply("К сожалению, я не знаю такой команды. Попробуйте /help для списка доступных команд.")


@dp.callback_query_handler(menu_cd.filter(action="add_template"))
async def process_add_templates_handler(query: CallbackQuery, **kwargs):
    await add_templates_handler(query, user_data, bot, **kwargs)


@dp.message_handler(lambda message: message.text and message.from_user.id in user_data and user_data[message.from_user.id] == "add_template")
async def process_add_templatesr(msg: types.Message, **kwargs):
    await add_templates(msg, user_data, **kwargs)


@dp.callback_query_handler(menu_cd.filter(action="show_templates_button"))
async def process_show_templates(query: CallbackQuery, **kwargs):
    await show_templates_handler(query, bot, **kwargs)


@dp.callback_query_handler(menu_cd.filter(action="remove_template"))
async def process_delete_templates_handler(query: CallbackQuery, **kwargs):
    await delete_templates_handler(query, bot, **kwargs)


@dp.callback_query_handler(template_cd.filter(action="delete_template_button"))
async def process_delete_template_handler(query: CallbackQuery, callback_data: dict, **kwargs):
    await delete_template_handler(query, callback_data, user_data, bot, **kwargs)


@dp.callback_query_handler(template_cd.filter(action="edit_template_button"))
async def process_edit_template_handler(query: CallbackQuery, callback_data: dict, **kwargs):
    await edit_template_handler(query, callback_data, user_data, bot, **kwargs)

# Выбор шаблона


@dp.callback_query_handler(template_cd.filter(action="select_template"))
async def process_select_template_handler(query: CallbackQuery, callback_data: dict, **kwargs):
    await select_template_handler(query, callback_data, bot, **kwargs)

# Меню управления группами


@dp.callback_query_handler(template_cd.filter(action="groups_from_tamplate"))
async def process_groups_from_tamplate(query: CallbackQuery, callback_data: dict, **kwargs):
    await groups_from_tamplate(query, callback_data,  user_data, bot, **kwargs)

# Список групп шаблона


@dp.callback_query_handler(template_cd.filter(action="list_groups_template"))
async def process_list_groups_templater(query: CallbackQuery, callback_data: dict, **kwargs):
    await list_groups_template(query, callback_data, **kwargs)

# Экспорт групп шаблона


@dp.callback_query_handler(template_cd.filter(action="export_groups_template"))
async def process_export_groups_templater(query: CallbackQuery, callback_data: dict, **kwargs):
    await export_groups_template(current_client, query, callback_data, **kwargs)

# Обработчик удаления групп по id из шаблона


@dp.callback_query_handler(template_cd.filter(action="remove_group"))
async def process_remove_group_template(query: CallbackQuery, callback_data: dict, **kwargs):
    await remove_group_template(query, callback_data, user_data, **kwargs)


@dp.message_handler(lambda message: message.from_user.id in user_data and user_data[message.from_user.id] == "remove_group")
async def process_group_ids_to_remove_template(message: types.Message, **kwargs):
    await group_ids_to_remove_template(message, user_data, **kwargs)

# Обработчик присоединения к группам по ссылкам


@dp.callback_query_handler(template_cd.filter(action="add_groups_link"))
async def process_join_group_by_link_template(query: CallbackQuery, callback_data: dict, **kwargs):
    await join_group_by_link_template(query, callback_data, user_data, bot, **kwargs)


@dp.message_handler(lambda message: message.text and message.from_user.id in user_data and user_data[message.from_user.id] == "add_groups_link")
async def process_join_group_by_link_handler_template(message: types.Message, **kwargs):
    await join_group_by_link_handler_template(message, user_data, bot, current_client, **kwargs)

# Обработчик команды добавления в группу через поиск


@dp.callback_query_handler(template_cd.filter(action="add_groups_search"))
async def process_join_group_by_search_handler_template(query: CallbackQuery, callback_data: dict, **kwargs):
    await join_group_by_search_handler_template(query, callback_data, user_data, bot, **kwargs)


@dp.message_handler(lambda message: user_data.get(message.from_user.id, {}).get('state') == "join_group_by_search_template")
async def process_join_group_by_search_handler_template_msg(msg: types.Message, **kwargs):
    await join_group_by_search_handler_template_msg(msg, user_data, current_client,  **kwargs)


@dp.callback_query_handler(lambda call: call.data.startswith('addGroup'))
async def process_process_add_group_button(call: aiogram.types.CallbackQuery, **kwargs):
    await process_add_group_button(call, current_client, **kwargs)

# Список ключевых слов шаблона


@dp.callback_query_handler(template_cd.filter(action="list_keywords_from_tamplate"))
async def process_list_keywords_handler_template(query: CallbackQuery, callback_data: dict, **kwargs):
    await list_keywords_handler_template(query, callback_data, **kwargs)

# Список слов-исключений шаблона


@dp.callback_query_handler(template_cd.filter(action="list_stopkeywords_from_tamplate"))
async def process_list_stopwords_handler_tamplate(query: CallbackQuery, callback_data: dict, **kwargs):
    await list_stopwords_handler_tamplate(query, callback_data, **kwargs)

# Добавление ключевых слов


@dp.callback_query_handler(template_cd.filter(action="add_keywords_to_tamplate"))
async def process_add_keywords_to_tamplate_handler(query: CallbackQuery, callback_data: dict, **kwargs):
    await add_keywords_to_tamplate_handler(query, callback_data, user_data, bot, **kwargs)


@dp.message_handler(lambda message: message.text and message.from_user.id in user_data and "add_keywords_template" in user_data[message.from_user.id])
async def process_add_keywords_to_tamplate_msg(msg: types.Message, **kwargs):
    await add_keywords_to_tamplate_msg(msg, user_data, bot, **kwargs)

# Добавление слов-исключений


@dp.callback_query_handler(template_cd.filter(action="add_stopwords_to_tamplate"))
async def process_add_blacklistkeyword_to_tamplate_handler(query: CallbackQuery, callback_data: dict, **kwargs):
    await add_blacklistkeyword_to_tamplate_handler(query, callback_data, user_data, bot, **kwargs)


@dp.message_handler(lambda message: message.text and message.from_user.id in user_data and "add_blacklistkeyword_template" in user_data[message.from_user.id])
async def process_add_blacklistkeywords_to_tamplate(msg: types.Message, **kwargs):
    await add_blacklistkeywords_to_tamplate(msg, user_data, bot, **kwargs)

# Удаление ключевых слов из шаблона


@dp.callback_query_handler(template_cd.filter(action="remove_keywords_from_tamplate"))
async def process_remove_keywords_from_tamplate_handler(query: CallbackQuery, callback_data: dict, **kwargs):
    await remove_keywords_from_tamplate_handler(query, callback_data, user_data, bot, **kwargs)


@dp.message_handler(lambda message: message.text and message.from_user.id in user_data and "remove_keywords_template" in user_data[message.from_user.id])
async def process_remove_keywords_from_tamplate(msg: types.Message, **kwargs):
    await remove_keywords_from_tamplate(msg, user_data, bot, **kwargs)

# Удаление слов-исключений из шаблона


@dp.callback_query_handler(template_cd.filter(action="remove_stopwords_from_tamplate"))
async def process_remove_blacklistkeywords_from_template_handler(query: CallbackQuery, callback_data: dict, **kwargs):
    await remove_blacklistkeywords_from_template_handler(query, callback_data, user_data, bot, **kwargs)


@dp.message_handler(lambda message: message.text and message.from_user.id in user_data and "remove_blacklistkeyword_template" in user_data[message.from_user.id])
async def process_blacklistkeywords_from_template(msg: types.Message, **kwargs):
    await remove_blacklistkeywords_from_template(msg, user_data, bot, **kwargs)

# Просмотр черного списка отправителей


@dp.callback_query_handler(template_cd.filter(action="list_stopusers_from_tamplate"))
async def process_list_blacklist_senders_handler(query: CallbackQuery, callback_data: dict, **kwargs):
    await list_blacklisted_senders_handler_template(query, callback_data, **kwargs)

# Добавление отправителей в черный список


@dp.callback_query_handler(template_cd.filter(action="add_stopusers_to_tamplate"))
async def process_add_senders_to_blacklist_handler(query: CallbackQuery, callback_data: dict, **kwargs):
    await add_senders_to_blacklist_handler(query, callback_data, user_data, bot, **kwargs)


@dp.message_handler(lambda message: message.text and message.from_user.id in user_data and "add_senders_blacklist" in user_data[message.from_user.id])
async def process_add_senders_to_blacklist_msg(msg: types.Message, **kwargs):
    await add_senders_to_blacklist_msg(msg, user_data, bot, **kwargs)

# Удаление отправителей из черного списка


@dp.callback_query_handler(template_cd.filter(action="remove_stopusers_from_tamplate"))
async def process_remove_senders_from_blacklist_handler(query: CallbackQuery, callback_data: dict, **kwargs):
    await remove_senders_from_blacklist_handler(query, callback_data, user_data, bot, **kwargs)


@dp.message_handler(lambda message: message.text and message.from_user.id in user_data and "remove_senders_blacklist" in user_data[message.from_user.id])
async def process_remove_senders_from_blacklist_msg(msg: types.Message, **kwargs):
    await remove_senders_from_blacklist_msg(msg, user_data, bot, **kwargs)

print("templates handlers registered")


# Обработчик выгрузки в exel
@dp.callback_query_handler(menu_cd.filter(action=["month_messages", "week_messages", "day_messages"]))
async def send_messages_report(query: CallbackQuery, callback_data: dict):
    action = callback_data.get("action")
    time_range = action.replace("_messages", "")
    # Получите сообщения из базы данных
    messages = await read_messages_from_db(time_range)
    # Запишите сообщения в файл Excel
    filename = f"{query.from_user.id}_{time_range}_messages.xlsx"
    df = pd.DataFrame(messages)
    df.to_excel(filename, index=False)
    # Отправьте файл пользователю
    with open(filename, 'rb') as file:
        await query.message.answer_document(file)
    # Удалите файл
    os.remove(filename)
    await query.answer()
print("excel handlers registered")


async def main():
    await create_pool()
    await init_db()
    await current_client.start()

    aiogram_task = asyncio.create_task(dp.start_polling())

    print("Telethon started")
    logging.info("Telethon started")

    await asyncio.gather(current_client.run_until_disconnected(), aiogram_task)


if __name__ == '__main__':
    asyncio.run(main())
