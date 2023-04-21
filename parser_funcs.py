#Импорты тг-парсера и общие импорты
from telethon import TelegramClient, errors
from telethon import functions, types
from telethon.tl.functions.messages import ImportChatInviteRequest
from datetime import datetime, timedelta
import pytz
from aditional_functions import notify_users
import asyncio
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantSelf
from telethon.errors import (
    UserNotParticipantError,
    ChannelPrivateError,
    ChatAdminRequiredError
)
from telethon.tl.functions.channels import GetFullChannelRequest, GetParticipantsRequest
from telethon.tl.types import InputPeerChannel
from dbtools import *


async def getMessagesTask(client, bot, curentGroup, user_chat_id, task_uid, chat_id):
    newMessagesList = []
    oldMessagesList = []
    while True:
        end_date = datetime.now(pytz.utc)
        start_date = datetime.now(pytz.utc) - timedelta(hours=5)
        oldMessagesList = newMessagesList
        newMessagesList = await scanMessages(client, start_date, end_date, curentGroup)
        newMessages = []
        if(oldMessagesList != []):
            newMessages = compareResults(oldMessagesList, newMessagesList)
        if (newMessages != []):
            await insert_messages(newMessages, curentGroup.title)
            await notify_users(bot, newMessages, chat_id)
            print('Новые сообщения:')
            print(newMessages)
        await asyncio.sleep(60)

def compareResults(prevMessageArr, newMessagesArr):
    addedMessages = []
    for msg in newMessagesArr:
        if msg not in prevMessageArr:
            addedMessages.append(msg)
    return addedMessages
    
async def scanMessages(client, start_date, end_date, curentGroup):
    messagesInPeriod = await getMessagesInTimeDiapazone(client, start_date, end_date, curentGroup)
    messagesArr = []

    keywords = await get_user_keywords('all')  # Получение списка ключевых слов из базы данных

    for msg in messagesInPeriod:
        # Проверяем, что текст сообщения существует и проверяем наличие ключевых слов
        if msg.text and any(keyword.lower() in msg.text.lower() for keyword in keywords):
            sender = await msg.get_sender()
            messagesArr.append({
                'sender': '@' + sender.username if sender.username else 'N/A',
                'text': msg.text,
                'date': msg.date.strftime("%Y-%m-%d %H:%M:%S"),
                'group': curentGroup.title
            })
    return messagesArr


async def joinGroupByLink(client, inviteLink, user_id, bot, chat_id):
    if inviteLink == 'пропустить':
        return 'skip'
    else:
        try:
            entity = await client.get_entity(inviteLink)
            if (await is_member_of_group(client, entity.title)):
                await bot.send_message(chat_id=chat_id, text=f"Бот уже является членом группы '{entity.title}'")
                cur_group_list = await get_user_group_list(user_id)
                if ((f"{entity.id}",f"{entity.title}",f"{user_id}") not in cur_group_list):
                    await add_group(entity.id, entity.title, user_id)
                    print("Запись группы в бд")
                return True
            await asyncio.sleep(5)
            print("-------Попытка присоединения--------")
            if "t.me/+" in inviteLink:
                # Обработка ссылок с хэшем (плюсом)
                hash = inviteLink.split('/')[-1][1:]
                group = await client(functions.messages.ImportChatInviteRequest(hash))
                print("-----------Присоединился---------")
            elif "t.me/" in inviteLink:
                # Обработка ссылок без хэша (плюса)
                username = inviteLink.split('/')[-1]
                result = await client(functions.contacts.ResolveUsernameRequest(username))
                group = await client(functions.channels.JoinChannelRequest(result.peer))
                print("-----------Присоединился---------")
            else:
                # Некорректная ссылка
                print("-----------Не присоединился------")
                return False
            print("---------------Id-ЧАТА------------------")
            print(group.chats[0].id)
            await add_group(group.chats[0].id, group.chats[0].title, user_id)
            await bot.send_message(chat_id=chat_id, text=f"Присединился к группе {group.chats[0].title}, ожидайте")
            return True
        except Exception as e:
            print("---------------------Ошибка-----------------")
            await bot.send_message(chat_id=chat_id, text=f"Ошибка: {e.args}")
            print(e.args)
            # await bot.send_message(chat_id=chat_id, text=f"Привышен лимит на присоединенние к группам, до нового присоединения осталось: {int(e.message.split(' ')[3]) + 1}")
            await asyncio.sleep(int(e.message.split(' ')[3]) + 1)
            
            return False
        
async def is_member_of_group(client, group_title):
        me = await client.get_me()
        dialogs = await client.get_dialogs()
        
        for dialog in dialogs:
            if dialog.title == group_title:
                try:
                    await client(GetParticipantRequest(dialog.entity, me))
                    return True
                except UserNotParticipantError:
                    return False
        return False
    

async def getGroupList(client):
    groups=[]
    dialogs = await client.get_dialogs()
    for dialog in dialogs:
        if dialog.is_group:
            groups.append(dialog)
    return groups

def groupSelector(groupsArr):
    print("Выберите группы для парсинга сообщений и членов группы (вводите цифры через пробел):")
    i = 0
    for group in groupsArr:
        print(str(i) + " - " + 'Название группы: ' + group.title + ' id-группы: ')
        i += 1
    g_indexes = list(map(int, input("Введите нужные цифры групп для отслеживания: ").split()))
    target_groups = [groupsArr[index] for index in g_indexes]
    return target_groups

async def search_group_not_joined(client, group_name):
    await client.start()
    # Поиск групп/каналов, содержащих ссылку на группу
    search_results = await client(functions.contacts.SearchRequest(
        q = group_name,
        limit = 100
    ))
    # Фильтрация групп/каналов, в которых не состоит пользователь
    not_joined_groups = []
    me = await client.get_me()
    
    for chat in search_results.chats:
        try:
            if chat.broadcast:
                continue
        except:
            continue
        try:
            participant = await client(GetParticipantRequest(chat, me))
            if not isinstance(participant.participant, ChannelParticipantSelf):
                not_joined_groups.append(chat)
        except (UserNotParticipantError, ChannelPrivateError, ChatAdminRequiredError):
            not_joined_groups.append(chat)
        except Exception as e:
            print(e)

    if not_joined_groups:
        print("Группы, в которых вы не состоите:")
        for group in not_joined_groups:
            print(f"Название: {group.title}, ID: {group.id}")
        return not_joined_groups
    else:
        print(f"Группы с именем {group_name}, в которых вы не состоите, не найдены.")
        return None

#Функция поиска группы по ee id
async def get_group_by_id(group_id, client):
    try:
        input_channel = await client.get_input_entity(group_id)
    except TypeError as e:
        print(e)
        return "ошибка получения чата"
    try:
        group = await client.get_entity(input_channel)
    except errors.ChannelPrivateError:
        return "Это приватный чат, или бота прогнали"
    return group
    
async def getMessagesInTimeDiapazone(client, start_time, end_time, target_group):
    messagesArr = []

    async for message in client.iter_messages(target_group, reverse=True):
        if message.date < start_time:
            continue
        if message.date <= end_time:
            messagesArr.append(message)
    return messagesArr