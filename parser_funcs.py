#Импорты тг-парсера и общие импорты
from telethon import TelegramClient
from telethon import functions, types
from telethon.tl.functions.messages import ImportChatInviteRequest
from datetime import datetime, timedelta
import pytz
import time
from aditional_functions import notify_users
from dotenv import load_dotenv
import os
import asyncio
from dbtools import add_group, init_db, insert_messages, get_user_keywords
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantSelf
from telethon.errors import (
    UserNotParticipantError,
    ChannelPrivateError,
    ChatAdminRequiredError
)

async def getMessagesTask(client, bot, curentGroup, user_chat_id):
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
            await notify_users(bot, newMessages, user_chat_id)
            print('Новые сообщения:')
            print(newMessages)
        await asyncio.sleep(5)

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
        if msg.text and any(keyword in msg.text for keyword in keywords):
            sender = await msg.get_sender()
            messagesArr.append({
                'sender': '@' + sender.username if sender.username else 'N/A',
                'text': msg.text,
                'date': msg.date.strftime("%Y-%m-%d %H:%M:%S"),
            })
    return messagesArr

async def joinGroupByLink(client, inviteLink, user_id):
    if (inviteLink == 'пропустить'):
        return 'skip'
    else:
        try:
            hash = inviteLink.split('/')[-1][1:]
            print(hash)
            group = await client(functions.messages.ImportChatInviteRequest(hash))
            print(group.chats[0].id)
            await add_group(group.chats[0].id, group.chats[0].title, user_id)
            return True
        except Exception as e:
            print(e)
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
    
async def getMessagesInTimeDiapazone(client, start_time, end_time, target_group):
    messagesArr = []

    async for message in client.iter_messages(target_group, reverse=True):
        if message.date < start_time:
            continue
        if message.date <= end_time:
            messagesArr.append(message)
    return messagesArr