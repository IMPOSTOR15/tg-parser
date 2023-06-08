#Импорты тг-парсера и общие импорты
import telethon
from telethon import TelegramClient, errors, functions, types, client
from telethon.sync import events

from telethon.tl.functions.messages import ImportChatInviteRequest
from datetime import timedelta
import datetime
from datetime import datetime
import pytz
from aditional_functions import notify_users, notify_users_for_listnere
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
from telethon.tl.types import PeerUser, PeerChat, PeerChannel
import logging

class GroupsEventHandler:
    def __init__(self, client, bot):
        self.client = client
        self.bot = bot
        self.stop_listening = True
        self.isHandlerAlreadySatisfy = False
        self.mainHandler = None

    async def message_handler(self, event, user_id, chat_id, bot):
        if self.stop_listening:
            return
        print('new msg')
        logging.info('new msg')
        keywords = await get_user_keywords(user_id)
        moscow_tz = pytz.timezone('Europe/Moscow')
        keywords_lower = [keyword.lower() for keyword in keywords]
        blacklistkeywords = await get_user_blacklistkeywords(user_id)
        blacklistkeywords_lower = [blacklistkeyword.lower() for blacklistkeyword in blacklistkeywords]
        if event.text:
            event.date = event.date.astimezone(moscow_tz).isoformat()
            msg_lower = event.text.lower()
            print(msg_lower)
            sender = await event.get_sender()
            chat = await event.get_chat()
            for keyword in keywords_lower:
                if keyword in msg_lower:
                    blacklistkeyword_found = next((blacklistkeyword for blacklistkeyword in blacklistkeywords_lower if blacklistkeyword in msg_lower), None)
                    await insert_messages([{'text': event.text, 'date': event.date, 'sender': sender.username}], 
                                        chat.title, keyword, blacklistkeyword_found)
                    if blacklistkeyword_found is None:
                        await notify_users_for_listnere(bot, event, chat_id, sender.username, chat.title, keyword)
                        print(f"[{chat.title}] {sender.first_name}: {event.text}")
                        logging.info(f"[{chat.title}] {sender.first_name}: {event.text}")
                        break
                    
    def create_groups_event_handler(self, groupIdArr, user_id, chat_id):
        # if (self.stop_listening == False):
        #     self.client.add_event_handler(lambda e: self.message_handler(e, user_id, chat_id, self.bot), events.NewMessage(chats=groupIdArr))
        print("Попытка создать Экземпляр уже в функции")
        logging.info("Попытка создать Экземпляр уже в функции")
        try:   
            if self.stop_listening is False:
                if self.mainHandler is None:
                    self.mainHandler = lambda e: self.message_handler(e, user_id, chat_id, self.bot)
                    self.client.add_event_handler(self.mainHandler, events.NewMessage(chats=groupIdArr))
                    print("Слушатель добавлен")
                    logging.info("Слушатель добавлен")
                else:
                    print("Слушатель уже существует")
                    logging.info("Слушатель уже существует")
        except Exception as e:
            print(e)
            logging.info(e)

    def remove_groups_event_handler(self):
        if self.mainHandler is not None:
            self.client.remove_event_handler(self.mainHandler)
            self.mainHandler = None
            print("Слушатель удален")
            logging.info("Слушатель удален")
        else:
            print("Слушатель не существует")
            logging.info("Слушатель не существует")

    def stop_handler(self):
        self.stop_listening = True
        self.remove_groups_event_handler()

    def start_handler(self):
        self.stop_listening = False

# async def getMessagesTask(client, bot, curentGroup, user_id, task_uid, chat_id, groupArr):

#     print(f"getMessagesTask started for group: {groupArr}")
#     newMessagesList = []
#     oldMessagesList = []
#     while True:
#         for group in groupArr:
#             try:
#                 print('Начала отработки группы')
#                 curentGroup = await get_group_by_id(int(group['chat_id']), client)
#                 print('Проверка группы на доступность')
#                 if (curentGroup == 'Это приватный чат, или бота прогнали'):
#                     print('Группа не прошла проверку')
#                     await bot.send_message(chat_id=chat_id, text=f"Возможно бота прогнали из группы {group['chat_name']} {group['chat_id']}")
#                     continue
#                 print('Установка дат')
#                 end_date = dt.now(pytz.utc)
#                 start_date = dt.now(pytz.utc) - timedelta(hours=1)
#                 print('Установка массивов сообщений')
#                 oldMessagesList = newMessagesList
#                 newMessagesList = await scanMessages(client, start_date, end_date, curentGroup, user_id)
#                 newMessages = []
#                 print(f'Отсканированна группа {curentGroup.title}')
#                 print('Попытка сравнить сообщения')
#                 if(oldMessagesList != []):
#                     newMessages = compareResults(oldMessagesList, newMessagesList)
#                     print('Произведено сравнение сообщений')
#                 if (newMessages != []):
#                     print('Оповещение поьзователей')
#                     await insert_messages(newMessages, curentGroup.title)
#                     await notify_users(bot, newMessages, chat_id)
#                     print('Новые сообщения:')
#                     print(newMessages)
#                 print('Отработка группы завершена')
#                 await asyncio.sleep(1)
#             except Exception as e:
#                 print(f'Ошибка: {e}')
    # while True:
    #     try:
    #         end_date = dt.now(pytz.utc)
    #         start_date = dt.now(pytz.utc) - timedelta(hours=1)
    #         oldMessagesList = newMessagesList
    #         newMessagesList = await scanMessages(client, start_date, end_date, curentGroup, user_id)
    #         newMessages = []
    #         if(oldMessagesList != []):
    #             newMessages = compareResults(oldMessagesList, newMessagesList)
    #         if (newMessages != []):
    #             await insert_messages(newMessages, curentGroup.title)
    #             await notify_users(bot, newMessages, chat_id)
    #             print('Новые сообщения:')
    #             print(newMessages)
            
    #     except Exception as e:
    #         print(e)

def compareResults(prevMessageArr, newMessagesArr):
    print('Начало сравнения')
    addedMessages = []
    for msg in newMessagesArr:
        if msg not in prevMessageArr:
            addedMessages.append(msg)
    print('Конец сравнения')
    return addedMessages
    
async def scanMessages(client, start_date, end_date, curentGroup, user_id):
    print('Начало сканирования сообщений')
    print(f"scanMessages started for {curentGroup.title}")
    try:
        messagesInPeriod = await getMessagesInTimeDiapazone(client, start_date, end_date, curentGroup)
    except Exception as e:
        print('Ошибка в getMessagesInTimeDiapazone')
        print(e)
    print('Сообщения отсканированны')
    messagesArr = []
    keywords = await get_user_keywords(user_id)  # Получение списка ключевых слов из базы данных
    keywords_lower = [keyword.lower() for keyword in keywords]
    for msg in messagesInPeriod:
        # Проверяем, что текст сообщения существует и проверяем наличие ключевых слов
        if msg.text:
            msg_lower = msg.text.lower()
            for keyword in keywords_lower:
                if keyword in msg_lower:
                    sender = await msg.get_sender()
                    messagesArr.append({
                        'sender': '@' + sender.username if sender.username else 'N/A',
                        'text': msg.text,
                        'date': msg.date.strftime("%Y-%m-%d %H:%M:%S"),
                        'group': curentGroup.title,
                        'keyword': keyword  # Добавляем найденное ключевое слово
                    })
        print('Найденные ключевые слова:')
        print(messagesArr)
        print('--------------------------------')
    print('Массив сообщений отправлен в функцию таски')
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
    logging.info("get_group_by_id")
    try:
        input_channel = await client.get_entity(PeerChat(group_id))
    except Exception as e:
        try:
            input_channel = await client.get_entity(PeerChannel(group_id))
        except Exception as e:
            print(e)
            logging.info(e)
            return "Это приватный чат, или бота прогнали"
    except TypeError as e:
        print(e)
        return "ошибка получения чата"
    try:
        group = await client.get_entity(input_channel)
    except errors.ChannelPrivateError:
        return "Это приватный чат, или бота прогнали"
    logging.info("get_group_by_id end")
    return group
    
async def getMessagesInTimeDiapazone(client, start_time, end_time, target_group):
    print('Попытка достать сообщения в диапазоне')
    messagesArr = []
    # print(client.iter_messages(target_group, reverse=True))
    async for message in client.iter_messages(target_group, reverse=True):
        if message.date < start_time:
            continue
        if message.date <= end_time:
            messagesArr.append(message)
    print('Сообщения отданы далее')
    return messagesArr