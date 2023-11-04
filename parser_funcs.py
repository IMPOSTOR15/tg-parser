# Импорты тг-парсера и общие импорты
import sqlite3
import time
from telethon import errors, functions
from telethon.sync import events

import pytz
from aditional_functions import notify_users_for_listnere
import asyncio
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantSelf
from telethon.errors import (
    UserNotParticipantError,
    ChannelPrivateError,
    ChatAdminRequiredError,
    FloodWaitError
)
from dbtools import *
from telethon.tl.types import PeerChat, PeerChannel
import logging

from datetime import datetime, timedelta
from dateutil.parser import parse


class GroupsEventHandler:
    def __init__(self, client, bot):
        self.client = client
        self.bot = bot
        self.stop_listening = True
        self.isHandlerAlreadySatisfy = False
        self.mainHandler = None

    async def template_message_handler(self, event, chat_id, template_id):
        if self.stop_listening:
            return
        print("new msg")
        logging.info('new msg')

        keywords = await get_keywords_by_template_id(template_id)
        moscow_tz = pytz.timezone('Europe/Moscow')
        keywords_lower = [keyword.lower() for keyword in keywords]

        blacklistkeywords = await get_stopwords_by_template_id(template_id)
        blacklistkeywords_lower = [blacklistkeyword.lower()
                                   for blacklistkeyword in blacklistkeywords]

        # Получаем черный список отправителей
        blacklisted_senders = await get_blacklisted_senders_by_template_id(template_id)

        if event.text:
            event.date = event.date.astimezone(moscow_tz).isoformat()
            msg_lower = event.text.lower()

            sender = await event.get_sender()
            try:
                username = sender.username
            except AttributeError:
                username = "аноним"
            try:
                sender_id = sender.id
            except AttributeError:
                sender_id = 777

            chat = await event.get_chat()

            # Проверка наличия ключевого слова в сообщении
            keyword_found = next(
                (keyword for keyword in keywords_lower if keyword in msg_lower), None)
            blacklistkeyword_found = next(
                (blacklistkeyword for blacklistkeyword in blacklistkeywords_lower if blacklistkeyword in msg_lower), None)

            # Учитываем отправителя в черном списке аналогично словам-исключениям
            sender_blacklisted = username in blacklisted_senders
            # Если ключевое слово найдено в сообщении
            if keyword_found:
                historyMessages = await fetch_messageById(sender_id, event.text)
                if all(isinstance(item, tuple) and len(item) >= 2 for item in historyMessages):
                    try:
                        sorted_history_messages = sorted(
                            historyMessages, key=lambda x: parse(x[1]), reverse=True)
                    except Exception as e:
                        print(f"Ошибка при сортировке сообщений: {e}")
                        return
                    if sorted_history_messages:
                        latest_message_date_str = sorted_history_messages[0][1]
                        latest_message_date = parse(latest_message_date_str)
                        current_message_date = parse(event.date)
                        if (current_message_date - latest_message_date) < timedelta(hours=24):
                            return
                await insert_messages([{'text': event.text, 'date': str(event.date), 'sender': username}],
                                      chat.title, keyword_found, blacklistkeyword_found if not sender_blacklisted else username, template_id, sender_id)

                # Если нет слова-исключения и отправителя в черном списке
                if blacklistkeyword_found is None and not sender_blacklisted:
                    await notify_users_for_listnere(self.bot, event, chat_id, username, chat.title, keyword_found)
                    print(f"[{chat.title}] {sender.first_name}: {event.text}")
                    logging.info(
                        f"[{chat.title}] {sender.first_name}: {event.text}")

    async def create_template_groups_event_handler(self, groupIdArr, chat_id, template_id):
        print("Попытка создать Экземпляр уже в функции")
        logging.info("Попытка создать Экземпляр уже в функции")
        try:
            if not self.stop_listening:
                if self.mainHandler is None:
                    self.mainHandler = lambda e: self.template_message_handler(
                        e, chat_id, template_id)
                    print(self.mainHandler)
                    self.client.add_event_handler(
                        self.mainHandler, events.NewMessage(chats=groupIdArr))
                    print("Слушатель добавлен")
                    logging.info("Слушатель добавлен")
                else:
                    print("Слушатель уже существует")
                    logging.info("Слушатель уже существует")
        except Exception as e:
            print(e)
            logging.error(e)

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
    # Получение списка ключевых слов из базы данных
    keywords = await get_user_keywords(user_id)
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
            if (await is_member_of_group_title(client, entity.title)):
                await bot.send_message(chat_id=chat_id, text=f"Бот уже является членом группы '{entity.title}'")
                cur_group_list = await get_user_group_list(user_id)
                if ((f"{entity.id}", f"{entity.title}", f"{user_id}") not in cur_group_list):
                    await add_group(entity.id, entity.title, user_id, inviteLink)
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
            await add_group(group.chats[0].id, group.chats[0].title, user_id, inviteLink)
            await bot.send_message(chat_id=chat_id, text=f"Присединился к группе {group.chats[0].title}, ожидайте")
            return True
        except Exception as e:
            print("---------------------Ошибка-----------------")
            await bot.send_message(chat_id=chat_id, text=f"Ошибка: {e.args}")
            print(e.args)
            await asyncio.sleep(int(e.message.split(' ')[3]) + 1)

            return False


async def joinGroupByLink_template(client, inviteLink, user_id, bot, chat_id, template_id):
    if inviteLink == 'пропустить':
        return 'skip'
    else:
        try:
            entity = await client.get_entity(inviteLink)
            if (await is_member_of_group_title(client, entity.title)):
                await bot.send_message(chat_id=chat_id, text=f"Бот уже является членом группы '{entity.title}'")
                cur_group_list = await get_template_group_list(template_id)
                print(cur_group_list)
                target_id = str(entity.id)
                if any(target_id == group[0] for group in cur_group_list):
                    print("Группа уже существует в списке")
                else:
                    await add_group_template(entity.id, entity.title, user_id, template_id, inviteLink)
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
            await add_group_template(group.chats[0].id, group.chats[0].title, user_id, template_id, inviteLink)
            await bot.send_message(chat_id=chat_id, text=f"Присединился к группе {group.chats[0].title}, ожидайте")
            return True
        except Exception as e:
            print("---------------------Ошибка-----------------")
            await bot.send_message(chat_id=chat_id, text=f"Ошибка: {e.args}")
            print(e.args)
            await asyncio.sleep(int(e.message.split(' ')[3]) + 1)
            return False


async def is_member_of_group_title(client, group_title):
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


async def is_member_of_group_id(client, group_id):
    me = await client.get_me()
    try:
        participant = await client(GetParticipantRequest(group_id, me))
        if (isinstance(participant.participant, ChannelParticipantSelf)):
            print("is member")
        return isinstance(participant.participant, ChannelParticipantSelf)
    except UserNotParticipantError:
        print("not member")
        return False
    except Exception as e:
        print(f"An error occurred while check participate: {str(e)}")
        return False


async def join_group_by_id(client, group_id):
    try:

        if (not await is_member_of_group_id(client, group_id)):
            await client(functions.channels.JoinChannelRequest(group_id))
            print(f"Успешное присоединение к группе с id: {group_id}")
            return True

    except FloodWaitError as e:
        print(
            f"Got a flood wait error. Need to wait {e.seconds} seconds before trying again.")
        return False
    except Exception as e:
        print(f"An error occurred while trying to join the group: {str(e)}")
        return False


async def getGroupList(client):
    groups = []
    dialogs = await client.get_dialogs()
    for dialog in dialogs:
        if dialog.is_group:
            groups.append(dialog)
    return groups


def groupSelector(groupsArr):
    print("Выберите группы для парсинга сообщений и членов группы (вводите цифры через пробел):")
    i = 0
    for group in groupsArr:
        print(str(i) + " - " + 'Название группы: ' +
              group.title + ' id-группы: ')
        i += 1
    g_indexes = list(
        map(int, input("Введите нужные цифры групп для отслеживания: ").split()))
    target_groups = [groupsArr[index] for index in g_indexes]
    return target_groups


async def search_group_not_joined(client, group_name):
    for _ in range(5):  # попробуйте соединиться 5 раз
        try:
            # Поиск групп/каналов, содержащих название
            search_results = await client(functions.contacts.SearchRequest(
                q=group_name,
                limit=100
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
                print(
                    f"Группы с именем {group_name}, в которых вы не состоите, не найдены.")
                return None

        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                print("База данных заблокирована, попытка подключения номер", _+1)
                time.sleep(5)
            else:
                raise e

# Функция поиска группы по ee id


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
