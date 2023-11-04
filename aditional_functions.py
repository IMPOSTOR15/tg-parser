import asyncio
from dbtools import clean_db



async def tasksList():
    tasks = asyncio.all_tasks()
    print("Текущие задачи:")
    for task in tasks:
        if (task._coro.startswith(getMessagesTask())):
            print(task)

async def notify_users(bot, new_messages, chat_id):
    for message in new_messages:
        text = f"{message['text']} \n\n ({message['date']})\n от {message['sender']}\n в группе: {message['group']}\n ключевое слово: {message['keyword']}"
        await bot.send_message(chat_id, text)

async def notify_users_for_listnere(bot, event, chat_id, sender_username, chat_title, keyword):
    text = f"{event.text} \n\n ({event.date})\n от @{sender_username}\n в группе: {chat_title}\n ключевое слово: {keyword}"
    await bot.send_message(chat_id, text)

async def clean_db_task():
    while True:
        await clean_db()
        await asyncio.sleep(3600)