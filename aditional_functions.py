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
        text = f"{message['text']} ({message['date']}) от {message['sender']} в группе: {message['group']}"
        await bot.send_message(chat_id, text)

async def clean_db_task():
    while True:
        await clean_db()
        await asyncio.sleep(3600)