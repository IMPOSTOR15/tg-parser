#Вспомогательные импорты
from dotenv import load_dotenv
import os
import asyncio
import uuid
import traceback
#Импорты thelethon парсера
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import InputPeerChannel
from telethon import TelegramClient, errors

#Импорты aiogram бота
import aiogram
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery
from aiogram.dispatcher.filters import Command
from aiogram.utils.callback_data import CallbackData
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ParseMode
from aiogram.utils.markdown import text, quote_html

#Организационные функции
from dbtools import *
from parser_funcs import *
from aditional_functions import *
from marckups import *
from config import config
#Загрузка переменных окружения
load_dotenv()

#Переменные парсера
api_id = os.environ.get('API_ID')
api_hash = os.environ.get('API_HASH')
phone = os.environ.get('PHONE')
client = TelegramClient(phone, api_id, api_hash)

# Переменные бота
bot_token = os.environ.get('BOT_TOKEN')
bot = Bot(token=bot_token)
dp = Dispatcher(bot)

#Глобальные переменные
going_tasks = {}
user_data = {}
#Список доступных команд
available_commands = [
    #Команды бота
    {'command': 'start', 'description': 'Приветственное сообщение'},
    {'command': 'help', 'description': 'Получить список доступных команд'},
    {'command': 'create_user', 'description': 'Добавить себя в список пользователей'},

    #Команды ключевых слов
    {'command': 'list_keywords', 'description': 'Отобразить список текущих кллючевых слов'},
    {'command': 'add_keywords', 'description': 'Добавить ключевые слова для отслеживания конкретных сообщений'},
    {'command': 'remove_keyword', 'description': 'Удалить ключевое слово'},

    #Команды групп
    {'command': 'list_groups', 'description': 'Отобразить список текущих добавленных вами групп'},
    {'command': 'add_group_search', 'description': 'Добавить группу в список при помощи поиска'},
    {'command': 'add_group_link', 'description': 'Добавить группу в список при помощи ссылки'},
    {'command': 'remove_group', 'description': 'Удалить добавленную ранее группу из списка'},

    #Команды сканирования
    {'command': 'start_scan', 'description': 'Выбрать добавленную группу и начать сканирование по добавленным ключевым словам'},
    {'command': 'stop_scan', 'description': 'Остановить запущенное сканирование группы'},

]

#Обработчик команды запуска бота
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply("""Привет! Я бот для отселживания сообщений в телеграм-чатах.
    \nЯ могу сканировать добавленные вами групповые чаты и искать в них сообщения, в которых есть добавленные вами ключевые слова.
    \nНапиши /menu, чтобы попасть в меню взаимодействия.""")

#Обработчик команды для получения списка команд
menu_cd = CallbackData("menu", "action")


@dp.callback_query_handler(menu_cd.filter(action="keywords"))
async def show_keywords_menu(query: CallbackQuery):
    text = "Меню взаимодействия с ключевыми словами"
    keyboard = await keywords_keyboard()
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



#Обработчик команды создания нового пользователя
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

    keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("Да", callback_data="add_user")).add(InlineKeyboardButton("Нет", callback_data="cancel_add_user"))
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

#Обработчик команды добавления ключевого слова
@dp.callback_query_handler(menu_cd.filter(action="add_keywords"))
async def add_keywords_handler(query: CallbackQuery):
    await query.answer()
    user_data[query.from_user.id] = "add_keywords"
    print(user_data)
    await bot.send_message(chat_id=query.message.chat.id, text="Введите ключевое слово или фразу, которое необходимо добавить, если их несколько разделите запятыми")

@dp.message_handler(lambda message: message.text and message.from_user.id in user_data and user_data[message.from_user.id] == "add_keywords")
async def add_keywords(msg: types.Message):
    keywords = msg.text.split(', ')

    added_keywords = []
    failed_keywords = []

    for keyword in keywords:
        keyword = keyword.strip()
        if await add_keyword(msg.from_user.id, keyword):
            added_keywords.append(keyword)
        else:
            failed_keywords.append(keyword)

    added_message = f"Ключевые слова добавлены: {', '.join(added_keywords)}" if added_keywords else ""
    failed_message = f"Не удалось добавить ключевые слова: {', '.join(failed_keywords)}" if failed_keywords else ""

    result_message = "\n".join(filter(bool, [added_message, failed_message]))

    await msg.reply(result_message)

    # Очистка user_data для текущего пользователя
    del user_data[msg.from_user.id]

#Обработчик команды вывода списка ключевых слов
@dp.callback_query_handler(menu_cd.filter(action="list_keywords"))
async def list_keywords_handler(query: CallbackQuery):
    await query.answer()
    user_data[query.from_user.id] = "list_keywords"
    keywords = await get_user_keywords(query.from_user.id)

    if not keywords:
        text = "У вас нет ключевых слов. Добавьте их с помощью команды /add_keywords"
    else:
        keyword_list = "\n".join(keywords)
        text = f"Ваши ключевые слова:\n{keyword_list}"

    # Создаем клавиатуру с кнопкой "Назад"
    back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад", callback_data=menu_cd.new(action="back_list_keywords")))
    await query.message.edit_text(text, reply_markup=back_markup)
    await query.answer()
@dp.callback_query_handler(menu_cd.filter(action="back_list_keywords"))
async def back_to_groups_menu(query: CallbackQuery):
    text = "Меню взаимодействия с ключевыми словами"
    keyboard = await keywords_keyboard()
    await query.message.edit_text(text, reply_markup=keyboard)
    await query.answer()
#Обработчик команды вывода списка текущих групп пользователя
@dp.callback_query_handler(menu_cd.filter(action="list_groups"))
async def list_handler(query: CallbackQuery):
    groups = await get_user_group_list(query.from_user.id)
    print(groups)
    if not groups:
        text = "У вас нет добавленных групп."
    else:
        groups_list = ""
        for group in groups:
           groups_list += f"`{group[0]}` {group[1]}\n"
        text = f"Ваши добавленные группы:\n{groups_list}"

    back_keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад", callback_data=menu_cd.new(action="back_list_groups")))
    await query.message.edit_text(text, reply_markup=back_keyboard, parse_mode="Markdown")
    await query.answer()
@dp.callback_query_handler(menu_cd.filter(action="back_list_groups"))
async def back_to_groups_menu(query: CallbackQuery):
    text = "Меню взаимодействия с группами"
    keyboard = await groups_keyboard()
    await query.message.edit_text(text, reply_markup=keyboard)
    await query.answer()

#Обработчик команды удаления ключевого слова
@dp.callback_query_handler(menu_cd.filter(action="remove_keywords"))
async def remove_keywords_handler(query: CallbackQuery):
    await query.answer()
    user_data[query.from_user.id] = "remove_keywords"
    await bot.send_message(chat_id=query.message.chat.id, text="Введите ключевое слово, которое необходимо удалить, если их несколько разделите запятыми")

@dp.message_handler(lambda message: message.text and message.from_user.id in user_data and user_data[message.from_user.id] == "remove_keywords")
async def remove_handler(msg: types.Message):
    keywords = msg.text.split(', ')

    removed_keywords = []
    failed_keywords = []

    for keyword in keywords:
        keyword = keyword.strip()
        if await remove_keyword(msg.from_user.id, keyword):
            removed_keywords.append(keyword)
        else:
            failed_keywords.append(keyword)

    removed_message = f"Ключевые слова удалены: {', '.join(removed_keywords)}" if removed_keywords else ""
    failed_message = f"Не удалось удалить ключевые слова: {', '.join(failed_keywords)}" if failed_keywords else ""

    result_message = "\n".join(filter(bool, [removed_message, failed_message]))

    await msg.reply(result_message)

    # Очистка user_data для текущего пользователя
    del user_data[msg.from_user.id]

#Обработчик команды добавления в группу через поиск
@dp.callback_query_handler(menu_cd.filter(action="join_group_by_search"))
async def join_group_by_search_handler(query: CallbackQuery):
    await query.answer()
    user_data[query.from_user.id] = "join_group_by_search"
    await bot.send_message(chat_id=query.message.chat.id, text="Введите поисковой запрос.")

@dp.message_handler(lambda message: user_data.get(message.from_user.id) == "join_group_by_search")
async def add_group_handler(msg: types.Message):
    group_name = msg.text
    if group_name == '':
        await msg.reply("Пожалуйста, укажите название группы.")
    else:
        groups = await search_group_not_joined(client, group_name)
        if not groups:
            await msg.reply(f"Группа '{group_name}' не найдена.")
        elif len(groups) == 1:
            group = groups[0]
            group_id = group.id
            group_title = group.title
            add_by_userid = msg.from_user.id
            
            # Проверка на дублирование группы
            all_groups = await get_all_group_list()
            if any(existing_group[0] == group_id for existing_group in all_groups):
                await msg.reply(f"Группа '{group_title}' (ID {group_id}) уже добавлена.")
            else:
                await add_group(group_id, group_title, add_by_userid)
                await msg.reply(f"Группа '{group_title}' (ID {group_id}) успешно добавлена")
        else:
            buttons = []
            for group in groups:
                buttons.append(aiogram.types.InlineKeyboardButton(text=group.title, callback_data=f"add_group_{group.id}"))
            markup = aiogram.types.InlineKeyboardMarkup(row_width=1)
            markup.add(*buttons)
            await msg.reply(f"Найдено несколько групп с названием '{group_name}'. Выберите нужную группу из списка ниже:", reply_markup=markup)
        
        # Очищаем состояние пользователя после обработки запроса
        del user_data[msg.from_user.id]

@dp.callback_query_handler(menu_cd.filter(action="join_group_by_link"))
async def join_group_by_link_handler(query: CallbackQuery):
    await query.answer()
    user_data[query.from_user.id] = "join_group_by_link"
    await bot.send_message(chat_id=query.message.chat.id, text="Пришлите ссылку, если ссылок несколько, разделите их запятыми. (Не стоит пытаться использовать более пяти ссылок чаще чем в 5-30 минут)")

# Обработчик присоединения к группам по ссылкам
@dp.message_handler(lambda message: message.text and message.from_user.id in user_data and user_data[message.from_user.id] == "join_group_by_link")
async def process_group_links(message: types.Message):
    links = message.text.split(', ')
    
    success_count = 0
    errors = []

    for link in links:
        link = link.strip()
        try:
            is_joined = await joinGroupByLink(client, link, message.from_user.id, bot, message.chat.id)
        except Exception as e:
            continue
        if is_joined:
            success_count += 1
        else:
            errors.append(link)

    success_message = f"Вы успешно присоединились к {success_count} группе(-ам)" if success_count > 0 else ""
    error_message = f"Следующие ссылки некорректны или истекли: {', '.join(errors)}" if errors else ""

    result_message = "\n".join(filter(bool, [success_message, error_message]))

    # Удаляем состояние пользователя после выполнения
    user_data.pop(message.from_user.id, None)

    await message.reply(result_message)

# Обработчик нажатия кнопки "Удалить" в меню групп
@dp.callback_query_handler(menu_cd.filter(action="remove_groups"))
async def remove_handler(query: CallbackQuery):
    await query.answer()
    user_data[query.from_user.id] = "remove_groups"
    await bot.send_message(chat_id=query.message.chat.id, text="Отправьте id группы, которую необходимо удалить. Если групп несколько, отправьте списком, разделяя пробелами.")

# Обработчик удаления групп по id
@dp.message_handler(lambda message: message.from_user.id in user_data and user_data[message.from_user.id] == "remove_groups")
async def process_group_ids_to_remove(message: types.Message):
    # Сброс состояния пользователя
    user_data.pop(message.from_user.id, None)
    
    group_ids = message.text.split(', ')

    # Получаем список всех групп пользователя
    all_user_groups = await get_user_group_list(message.from_user.id)

    # Получаем только id групп из списка всех групп пользователя
    user_group_ids = [str(group[0]) for group in all_user_groups]

    # Сравниваем id групп пользователя с id групп, которые отправил пользователь
    groups_to_remove = []
    invalid_group_ids = []

    for group_id in group_ids:
        group_id = group_id.strip()
        if group_id in user_group_ids:
            groups_to_remove.append(group_id)
        else:
            invalid_group_ids.append(group_id)

    # Удаляем группы и формируем сообщения о результате
    if groups_to_remove:
        for group_id in groups_to_remove:
            await remove_group(message.from_user.id, group_id)
        removed_message = "Группы удалены успешно."
    else:
        removed_message = ""

    if invalid_group_ids:
        invalid_message = f"Проверьте данные, следующие id групп не найдены: {', '.join(invalid_group_ids)}"
    else:
        invalid_message = ""

    result_message = "\n".join(filter(bool, [removed_message, invalid_message]))

    await message.reply(result_message)

#Обработчик команды запуска сканирования
@dp.callback_query_handler(menu_cd.filter(action="selective_scan"))
async def add_start_scan__handler(query: CallbackQuery):
    user_id = query.from_user.id
    groupList = await get_user_group_list(user_id)
    global groupArr
    groupArr = []
    global groupIdArr
    groupIdArr = []

    for group in groupList:
        groupArr.append({'chat_id': group[0], 'chat_name': group[1]})
        groupIdArr.append(int(group[0]))

    if (len(groupArr) > 0):
        buttons = []
        buttons.append(aiogram.types.InlineKeyboardButton(text="Запустить все", callback_data=f"start_scan_all"))
        for group in groupArr:
            buttons.append(aiogram.types.InlineKeyboardButton(text=group['chat_name'], callback_data=f"start_scan_{group['chat_id']}"))
        markup = aiogram.types.InlineKeyboardMarkup(row_width=1)
        markup.add(*buttons)
        markup.add(back_button())

        await query.message.edit_text(f"Выберите нужную группу для старта сканирования из списка ниже:", reply_markup=markup)
    else:
        await query.message.edit_text(f"У вас нет добавленных групп", reply_markup=markup)


#Отработчик кнопки старта задачи на сканирование
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('start_scan_'))
async def add_group_callback_handler(callback_query: aiogram.types.CallbackQuery):
    callback_data = callback_query.data
    chat_id = callback_query.message.chat.id
    group_id = callback_data.split('_')[2]
    cur_user_id = callback_query.from_user.id

    markup = aiogram.types.InlineKeyboardMarkup(row_width=1)
    markup.add(back_button())
    config["stop_listening"] = False

    if (group_id == "all"):
        msg_text = "Запущенно сканирование следующих групп: \n"
        await callback_query.message.edit_text("Ожидайте....")
        for id in groupIdArr:
            selected_group = await get_group_by_id(int(id), client)
            if (selected_group == 'Это приватный чат, или бота прогнали'):
                await bot.send_message(chat_id=chat_id, text=f"Возможно бота прогнали из группы {id}")
                groupIdArr.remove(id)
                continue
        try:
            create_groups_event_handler(client, bot, groupIdArr, cur_user_id, chat_id)

        except Exception as e:
            print("Произошла ошибка:")
            print(str(e))
            traceback.print_exc()
        for group in groupArr:
            msg_text += f"{group['chat_name']} id: {group['chat_id']}\n"
        await callback_query.message.edit_text(msg_text, reply_markup=markup)
    else:
        selected_group = await get_group_by_id(int(group_id), client)
        if (selected_group == 'Это приватный чат, или бота прогнали'):
            await bot.send_message(chat_id=chat_id, text=f"Возможно бота прогнали из группы {id} Попробуйте выбрать другую группу")
        else:
            try:
                create_groups_event_handler(client, bot, [int(group_id),], cur_user_id, chat_id)

                await callback_query.message.edit_text(f"Начал сканированние группы '{selected_group.title}' (ID {selected_group.id})", reply_markup=markup)
            except Exception as e:
                print("Произошла ошибка:")
                print(str(e))
                traceback.print_exc()

#Обработчик команды остановки сканирования
@dp.callback_query_handler(menu_cd.filter(action="selective_stop"))
async def add_stop_scan__handler(query: CallbackQuery):
    user_id = query.from_user.id
    markup = aiogram.types.InlineKeyboardMarkup()
    markup.add(back_button())
    config["stop_listening"] = True
    await query.message.edit_text(text="Все задачи остановленны", reply_markup = await back_keyboard())


#Обработчик получения команды без обработчика
@dp.message_handler(commands=['unknown_command'], commands_prefix='/', regexp='^/')
async def cmd_unknown(message: types.Message):
    await message.reply("К сожалению, я не знаю такой команды. Попробуйте /help для списка доступных команд.")



#Функция запуска парсера
async def main_telegram():
    await client.start()
    print("PARSER STARTED")
    await init_db()
    print("DB INITED")

    while True:
        print("working....")
        await asyncio.sleep(10)

#Функция запуска телеграм-бота
async def main_bot():
    print('BOT STARTED')
    await dp.start_polling()

async def main():
    # Создаем корутины для каждой из программ
    first_program = main_telegram()
    second_program = main_bot()
    # Запускаем корутины совместно с помощью asyncio.gather()
    await asyncio.gather(first_program, second_program)
    #Запуск очистки дб
    asyncio.create_task(clean_db_task())

if __name__ == "__main__":
    asyncio.run(main())