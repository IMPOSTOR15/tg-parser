import uuid
from telethon import TelegramClient, errors

from aditional_functions import clean_db_task
from dotenv import load_dotenv
import os
import asyncio
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import InputPeerChannel
import aiogram
from aiogram import Bot, Dispatcher, types

from dbtools import *
from parser_funcs import *


# Импорты и переменные для первой программы
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
    \nНапиши /help, чтобы узнать список доступных команд.""")

#Обработчик команды для получения списка команд
@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    help_text = "Доступные команды:\n\n"
    for command in available_commands:
        help_text += f"/{command['command']} - {command['description']}\n"
    await message.reply(help_text)

#Обработчик команды создания нового пользователя    
@dp.message_handler(commands=['create_user'])
async def process_start_command(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    await bot.send_message(user_id, "Хотите добавить себя в список пользователей? (да/нет)")
    
    @dp.message_handler(chat_id=user_id)
    async def process_answer(message: types.Message):
        if message.text.lower() == 'да':
            await add_user(user_id, user_name, user_id)
            await bot.send_message(user_id, "Отлично! Вы добавленны")
        else:
            await bot.send_message(user_id, "Вы отказались от добавления в список оповещаемых.")

#Обработчик команды добавления ключевого слова
@dp.message_handler(commands=['add_keywords'])
async def add_handler(msg: types.Message):
    keywords = msg.get_args().split(' ')
    if not keywords:
        await msg.reply("Пожалуйста, укажите ключевые слово после команды /add через пробел")
    else:
        for keyword in keywords:
            await add_keyword(msg.from_user.id, keyword)
        if (len(keywords) == 1):
            await msg.reply(f"Ключевое слово '{keywords[0]}' добавлено")
        else:
            await msg.reply(f"Ключевые слова '{ ', '.join(keywords) }' добавлены")

#Обработчик команды вывода списка ключевых слов
@dp.message_handler(commands=['list_keywords'])
async def list_handler(msg: types.Message):
    keywords = await get_user_keywords(msg.from_user.id)
    print(keywords)
    if not keywords:
        await msg.reply("У вас нет ключевых слов. Добавьте их с помощью команды /add_keywords")
    else:
        keyword_list = "\n".join(keywords)
        await msg.reply(f"Ваши ключевые слова:\n{keyword_list}")

#Обработчик команды вывода списка текущих групп пользователя
@dp.message_handler(commands=['list_groups'])
async def list_handler(msg: types.Message):
    groups = await get_user_group_list(msg.from_user.id)
    print(groups)
    if not groups:
        await msg.reply("У вас нет добавленных групп. Добавьте их с помощью команды /add_group или .add_group_link")
    else:
        groups_list = ""
        for group in groups:
           groups_list += " ".join(group) + "\n"
        print(groups_list)
        await msg.reply(f"Ваши добавленные группы:\n{groups_list}")

#Обработчик команды удаления ключевого слова
@dp.message_handler(commands=['remove_keyword'])
async def remove_handler(msg: types.Message):
    keyword = msg.get_args()
    if not keyword:
        await msg.reply("Пожалуйста, укажите ключевое слово после команды /remove_keyword")
    else:
        await remove_keyword(msg.from_user.id, keyword)
        await msg.reply(f"Ключевое слово '{keyword}' удалено.")

#Обработчик команды добавления в группу через поиск
@dp.message_handler(commands=['add_group_search'])
async def add_group_handler(msg: types.Message):
    group_name = msg.get_args()
    if group_name == '':
        await msg.reply("Пожалуйста, укажите название группы после команды /add_group_search")
    else:
        groups = await search_group_not_joined(client, group_name)
        if not groups:
            await msg.reply(f"Группа '{group_name}' не найдена.")
        elif len(groups) == 1:
            group = groups[0]
            group_id = group.id
            group_title = group.title
            add_by_userid = msg.from_user.id
            await add_group(group_id, group_title, add_by_userid)
            await msg.reply(f"Группа '{group_title}' (ID {group_id}) успешно добавлена")
        else:
            buttons = []
            for group in groups:
                buttons.append(aiogram.types.InlineKeyboardButton(text=group.title, callback_data=f"add_group_{group.id}"))
            markup = aiogram.types.InlineKeyboardMarkup(row_width=1)
            markup.add(*buttons)
            await msg.reply(f"Найдено несколько групп с названием '{group_name}'. Выберите нужную группу из списка ниже:", reply_markup=markup)

#Обработчик колбэка кнопки выбранной группы
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('add_group_'))
async def add_group_callback_handler(callback_query: aiogram.types.CallbackQuery):
    callback_data = callback_query.data
    group_id = int(callback_data.split('_')[2])
    group_title = None
    for row in callback_query.message.reply_markup.inline_keyboard:
        for button in row:
            if button.callback_data == callback_query.data:
                group_title = button.text
                break
        if group_title:
            break
    add_by_userid = callback_query.from_user.id
    await add_group(group_id, group_title, add_by_userid)
    group = await client.get_entity(group_id)
    
    # Присоединение к группе или каналу
    await client(JoinChannelRequest(group))
    await bot.send_message(add_by_userid, f"Группа '{group_title}' (ID {group_id}) успешно добавлена.")

#Отработчик команды добавления в группу по ссылке
@dp.message_handler(commands=['add_group_link'])
async def add_group_link__handler(msg: types.Message):
    grouplink = msg.get_args()
    if not grouplink:
        await msg.reply("Пожалуйста, укажите ключевое слово после команды /remove.")
    else:
        isJoined = await joinGroupByLink(client, grouplink, msg.from_user.id)
        if (isJoined):
            await msg.reply(f"Вы успешно присоединились к группе")
        else:
            await msg.reply(f"Ссылка некорректная. Проверьте корректность ввода и срок действия ссылки")

#Обработчик команды удаления группы
@dp.message_handler(commands=['remove_group'])
async def remove_handler(msg: types.Message):
    keyword = msg.get_args()
    if not keyword:
        await msg.reply("Пожалуйста, укажите название группы после команды /remove_group")
    else:
        await remove_group(msg.from_user.id, keyword)
        await msg.reply(f"Группа '{keyword}' удаленна.")

#Обработчик команды запуска сканирования
@dp.message_handler(commands=['start_scan'])
async def add_start_scan__handler(msg: types.Message):
    user_id = msg.from_user.id
    groupList = await get_user_group_list(user_id)
    groupArr = []
    for group in groupList:
        groupArr.append({'chat_id': group[0], 'chat_name': group[1]})
    
    buttons = []
    for group in groupArr:
        buttons.append(aiogram.types.InlineKeyboardButton(text=group['chat_name'], callback_data=f"start_scan_{group['chat_id']}"))
    markup = aiogram.types.InlineKeyboardMarkup(row_width=1)
    markup.add(*buttons)
    await msg.reply(f"Выберите нужную группу для старта сканирования из списка ниже:", reply_markup=markup)

#Отработчик кнопки старта задачи на сканирование
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('start_scan_'))
async def add_group_callback_handler(callback_query: aiogram.types.CallbackQuery):
    callback_data = callback_query.data
    group_id = int(callback_data.split('_')[2])
    selected_group = await get_group_by_id(group_id, client)
    #Получаем id текущего чата
    cur_user_id = callback_query.from_user.id
    # Запуск сканирования
    task_uid = str(uuid.uuid4())
    task = asyncio.create_task(getMessagesTask(client, bot, selected_group, cur_user_id, task_uid))
    going_tasks[task_uid] = {"task": task,"by_user": cur_user_id, "scan_group": selected_group.title}

    await bot.send_message(cur_user_id, f"Начал сканированние группы '{selected_group.title}' (ID {selected_group.id}) \n Id отслеживания: {task_uid}")

#Обработчик команды остановки сканирования
@dp.message_handler(commands=['stop_scan'])
async def add_stop_scan__handler(msg: types.Message):
    user_id = msg.from_user.id
    markup = aiogram.types.InlineKeyboardMarkup()
    for task_uid, task_info in going_tasks.items():
        if task_info['by_user'] == user_id:
            button_text = f"{task_info['scan_group']} ({task_uid})"
            callback_data = f"cancel_task_{task_uid}"
            markup.add(aiogram.types.InlineKeyboardButton(text=button_text, callback_data=callback_data))
    if markup.inline_keyboard:
        await bot.send_message(chat_id=user_id, text="Выберите задачу для остановки:", reply_markup=markup)
    else:
        await bot.send_message(chat_id=user_id, text="У вас нет активных задач.")

#Обработчик кнопки отмены задачи на сканирование
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('cancel_task_'))
async def add_stop_scan_callback_handler(callback_query: aiogram.types.CallbackQuery):
    user_id = callback_query.from_user.id
    callback_data = callback_query.data
    task_id = callback_data.split('_')[2]
    task_name = going_tasks[task_id]['scan_group']
    task_entity = going_tasks[task_id]['task']
    task_entity.cancel()
    del going_tasks[task_id]
    await bot.send_message(chat_id=user_id, text=f"Задача сканирования группы '{task_name}' остановленна.")


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
        await asyncio.sleep(50)

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