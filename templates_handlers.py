from aiogram import types

# from main import dp, bot, menu_cd, user_data, current_client
from aiogram.utils.callback_data import CallbackData
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from dbtools import *
from marckups import *
from parser_funcs import *
from aditional_functions import *
from telethon.tl.functions.messages import ExportChatInviteRequest
from telethon.tl.types import PeerUser, PeerChat, PeerChannel


import os
from openpyxl import Workbook

template_cd = CallbackData("template", "template_id", "action")


# @dp.callback_query_handler(menu_cd.filter(action="add_template"))
async def add_templates_handler(query: CallbackQuery, user_data, bot, **kwargs):
    await query.answer()
    user_data[query.from_user.id] = "add_template"
    logging.info(user_data)
    await query.message.edit_text(text="Введите название шаблона, которое необходимо добавить")

# @dp.message_handler(lambda message: message.text and message.from_user.id in user_data and user_data[message.from_user.id] == "add_template")


async def add_templates(msg: types.Message, user_data, **kwargs):
    template = msg.text.strip()

    if await add_template(template, msg.from_user.id):
        result_message = f"Шаблон '{template}' успешно добавлен."
    else:
        result_message = f"Не удалось добавить шаблон '{template}'."

    await msg.reply(result_message)
    del user_data[msg.from_user.id]

# @dp.callback_query_handler(menu_cd.filter(action="show_templates_button"))


async def show_templates_handler(query: CallbackQuery, bot, **kwargs):
    await query.answer()
    keyboard = InlineKeyboardMarkup(row_width=1)
    templates = await get_templates_by_user_id(query.from_user.id)
    if not templates:
        keyboard.add(InlineKeyboardButton(
            "Назад", callback_data=menu_cd.new(action="templates")))
        await query.message.edit_text(text="У вас нет созданных шаблонов.", reply_markup=keyboard)
        return

    for template in templates:
        if (template["is_select"]):
            button = InlineKeyboardButton(template["template_name"] + " ✅", callback_data=template_cd.new(
                template_id=template["id"], action="edit_template_button"))
        else:
            button = InlineKeyboardButton(template["template_name"], callback_data=template_cd.new(
                template_id=template["id"], action="edit_template_button"))
        keyboard.add(button)

    keyboard.add(InlineKeyboardButton(
        "Назад", callback_data=menu_cd.new(action="templates")))

    await query.message.edit_text(text="Выберите шаблон для редактирования:", reply_markup=keyboard)

# @dp.callback_query_handler(menu_cd.filter(action="remove_template"))


async def delete_templates_handler(query: CallbackQuery, bot, **kwargs):
    await query.answer()
    keyboard = InlineKeyboardMarkup(row_width=1)
    templates = await get_templates_by_user_id(query.from_user.id)

    if not templates:
        keyboard.add(InlineKeyboardButton(
            "Назад", callback_data=menu_cd.new(action="templates")))
        await query.message.edit_text(text="У вас нет созданных шаблонов.", reply_markup=keyboard)
        return

    for template in templates:
        if (template["is_select"]):
            button = InlineKeyboardButton(template["template_name"] + " ✅", callback_data=template_cd.new(
                template_id=template["id"], action="delete_template_button"))
        else:
            button = InlineKeyboardButton(template["template_name"], callback_data=template_cd.new(
                template_id=template["id"], action="delete_template_button"))
        keyboard.add(button)

    keyboard.add(InlineKeyboardButton(
        "Назад", callback_data=menu_cd.new(action="templates")))

    await query.message.edit_text(text="Выберите шаблон для Удаления", reply_markup=keyboard)

# @dp.callback_query_handler(template_cd.filter(action="delete_template_button"))


async def delete_template_handler(query: CallbackQuery, callback_data: dict, user_data, bot, **kwargs):
    await query.answer()

    template_id = int(callback_data.get('template_id'))
    print(template_id)
    template_name = await get_template_name_by_id(template_id)
    user_data[query.from_user.id] = {"edit_template": template_id}
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton(
        "Назад", callback_data=menu_cd.new(action="templates")))
    isDel = await delete_template(template_id)
    if (isDel):
        await query.message.edit_text(text=f"Шаблон <{template_name}> удален:", reply_markup=keyboard)
    else:
        await query.message.edit_text(text=f"Ошибка удаления шаблона <{template_name}>:", reply_markup=keyboard)

# @dp.callback_query_handler(template_cd.filter(action="edit_template_button"))


async def edit_template_handler(query: CallbackQuery, callback_data: dict, user_data, bot, **kwargs):
    await query.answer()

    template_id = int(callback_data.get('template_id'))
    template_name = await get_template_name_by_id(template_id)
    user_data[query.from_user.id] = {"edit_template": template_id}

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Ключевые слова шаблона", callback_data=template_cd.new(
            template_id=template_id, action="list_keywords_from_tamplate")),
        InlineKeyboardButton("Слова-исключения шаблона", callback_data=template_cd.new(
            template_id=template_id, action="list_stopkeywords_from_tamplate")),
        InlineKeyboardButton("Добавить ключевые слова", callback_data=template_cd.new(
            template_id=template_id, action="add_keywords_to_tamplate")),
        InlineKeyboardButton("Добавить слова-исключения", callback_data=template_cd.new(
            template_id=template_id, action="add_stopwords_to_tamplate")),
        InlineKeyboardButton("Удалить ключевые слова", callback_data=template_cd.new(
            template_id=template_id, action="remove_keywords_from_tamplate")),
        InlineKeyboardButton("Удалить слова-исключения", callback_data=template_cd.new(
            template_id=template_id, action="remove_stopwords_from_tamplate")),
        InlineKeyboardButton("Группы шаблона", callback_data=template_cd.new(
            template_id=template_id, action="groups_from_tamplate")),
        InlineKeyboardButton("Черный список отправителей", callback_data=template_cd.new(
            template_id=template_id, action="list_stopusers_from_tamplate")),
        InlineKeyboardButton("Добавить отправителей в черный список", callback_data=template_cd.new(
            template_id=template_id, action="add_stopusers_to_tamplate")),
        InlineKeyboardButton("Удалить отправителей из черного списка", callback_data=template_cd.new(
            template_id=template_id, action="remove_stopusers_from_tamplate")),
        InlineKeyboardButton("Выбрать основным", callback_data=template_cd.new(
            template_id=template_id, action="select_template")),
        InlineKeyboardButton("Назад", callback_data=menu_cd.new(
            action="show_templates_button"))
    )

    await query.message.edit_text(text=f"Выберите действие для шаблона <{template_name}>:", reply_markup=keyboard)

# #Выбор шаблона
# @dp.callback_query_handler(template_cd.filter(action="select_template"))


async def select_template_handler(query: CallbackQuery, callback_data: dict, bot, **kwargs):
    await query.answer()
    user_id = query.from_user.id
    template_id = int(callback_data.get('template_id'))
    template_name = await get_template_name_by_id(template_id)
    selected_template = await find_selected_template(user_id)

    if (selected_template):
        if (int(template_id) == selected_template[0]):
            back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад",
                                                                          callback_data=template_cd.new(template_id=template_id, action="edit_template_button")))
            await query.message.edit_text(text=f"Шаблон <{template_name}> уже выбран", reply_markup=back_markup)
            return
    if (await select_template(user_id, template_id)):
        back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад",
                                                                      callback_data=template_cd.new(template_id=template_id, action="edit_template_button")))
        await query.message.edit_text(text=f"Шаблон <{template_name}> успешно выбран", reply_markup=back_markup)
    else:
        back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад",
                                                                      callback_data=template_cd.new(template_id=template_id, action="edit_template_button")))
        await query.message.edit_text(text=f"Ошибка выбора шаблона <{template_name}>", reply_markup=back_markup)
# #Меню управления группами
# @dp.callback_query_handler(template_cd.filter(action="groups_from_tamplate"))


async def groups_from_tamplate(query: CallbackQuery, callback_data: dict, user_data, bot, **kwargs):
    await query.answer()

    template_id = int(callback_data.get('template_id'))
    template_name = await get_template_name_by_id(template_id)
    user_data[query.from_user.id] = {"edit_template": template_id}

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Список групп шаблона", callback_data=template_cd.new(
            template_id=template_id,  action="list_groups_template")),
        InlineKeyboardButton("Экспорт групп шаблона", callback_data=template_cd.new(
            template_id=template_id,  action="export_groups_template")),
        InlineKeyboardButton("Добавить по ссылке", callback_data=template_cd.new(
            template_id=template_id, action="add_groups_link")),
        InlineKeyboardButton("Добавить поиском", callback_data=template_cd.new(
            template_id=template_id, action="add_groups_search")),
        InlineKeyboardButton("Удалить группу", callback_data=template_cd.new(
            template_id=template_id, action="remove_group")),
        InlineKeyboardButton("Назад", callback_data=template_cd.new(
            template_id=template_id, action="edit_template_button"))
    )
    await query.message.edit_text(text=f"Выберите действие для групп шаблона <{template_name}>:", reply_markup=keyboard)

# #Список групп шаблона
# @dp.callback_query_handler(template_cd.filter(action="list_groups_template"))


async def list_groups_template(query: CallbackQuery, callback_data: dict, **kwargs):
    await query.answer()

    template_id = int(callback_data.get('template_id'))
    groups = await get_template_group_list(template_id)
    if not groups:
        text = "У этого шаблона нет групп."
    else:
        group_list = "\n".join(
            [f"id: {group[0]} Название: {group[1]}" for group in groups])
        text = f"Группы этого шаблона:\n{group_list}"

    back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад",
                                                                  callback_data=template_cd.new(template_id=template_id, action="groups_from_tamplate")))
    await query.message.edit_text(text, reply_markup=back_markup)

# Получение ссылки на группу


async def get_invite_link(client, chat_id: int) -> str:
    try:
        chat = await client.get_entity(PeerChannel(int(chat_id)))
    except Exception as e:
        try:
            chat = await client.get_entity(PeerChat(int(chat_id)))
        except Exception as e:
            print(e)
            return 'ошибка создания ссылки, возможно чат не существует в боте'
    if hasattr(chat, "username") and chat.username:
        return f"https://t.me/{chat.username}"
    else:
        updated_chat = await client(ExportChatInviteRequest(chat_id))
        return updated_chat.link

# # Обработчик экспорта групп из шаблона


async def export_groups_template(current_client, query, callback_data, **kwargs):

    await query.answer()
    await query.message.answer("Файл загружается...")
    template_id = int(callback_data.get('template_id'))
    groups = await get_template_group_list(template_id)
    if not groups:
        text = "У этого шаблона нет групп."
    else:
        text = f"Группы экспортированны"
        filename = f"template_{template_id}.xlsx"
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Группы"
        sheet.append(["ID", "Название", "Ссылка"])

        for group in groups:
            print(group[1])
            group_id = group[0]
            group_name = group[1]
            if (not group[3]):
                group_link = await get_invite_link(current_client, group_id)
            else:
                group_link = group[3]
            sheet.append([group_id, group_name, group_link])

        workbook.save(filename)

        await query.message.answer_document(document=InputFile(filename), caption="")
        os.remove(filename)

    back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад",
                                                                  callback_data=template_cd.new(template_id=template_id, action="groups_from_tamplate")))
    await query.message.edit_text(text, reply_markup=back_markup)

# # Обработчик удаления групп по id из шаблона
# @dp.callback_query_handler(template_cd.filter(action="remove_group"))


async def remove_group_template(query: CallbackQuery, callback_data: dict, user_data, **kwargs):
    await query.answer()
    user_data[query.from_user.id] = "remove_group"
    user_data["edit_template"] = int(callback_data.get('template_id'))
    await query.message.edit_text(text="Отправьте id группы, которую необходимо удалить. Если групп несколько, отправьте списком, разделяя пробелами.")


# @dp.message_handler(lambda message: message.from_user.id in user_data and user_data[message.from_user.id] == "remove_group")
async def group_ids_to_remove_template(message: types.Message, user_data, **kwargs):
    template_id = user_data["edit_template"]
    group_ids = message.text.split(', ')

    # Получаем список всех групп шаблона
    all_template_groups = await get_template_group_list(template_id)

    # Получаем только id групп из списка всех групп шаблона
    template_group_ids = [str(group[0]) for group in all_template_groups]

    # Сравниваем id групп пользователя с id групп, которые отправил пользователь
    groups_to_remove = []
    invalid_group_ids = []

    for group_id in group_ids:
        group_id = group_id.strip()
        if group_id in template_group_ids:
            groups_to_remove.append(group_id)
        else:
            invalid_group_ids.append(group_id)

    # Удаляем группы и формируем сообщения о результате
    if groups_to_remove:
        for group_id in groups_to_remove:
            await remove_groupTemplate(message.from_user.id, group_id, template_id)
        removed_message = "Группы удалены успешно."
    else:
        removed_message = ""

    if invalid_group_ids:
        invalid_message = f"Проверьте данные, следующие id групп не найдены: {', '.join(invalid_group_ids)}"
    else:
        invalid_message = ""

    result_message = "\n".join(
        filter(bool, [removed_message, invalid_message]))

    user_data.pop(message.from_user.id, None)
    await message.reply(result_message)

# # Обработчик присоединения к группам по ссылкам
# @dp.callback_query_handler(template_cd.filter(action="add_groups_link"))


async def join_group_by_link_template(query: CallbackQuery, callback_data: dict, user_data, bot, **kwargs):
    await query.answer()
    user_data[query.from_user.id] = "add_groups_link"
    user_data["edit_template"] = int(callback_data.get('template_id'))
    await bot.send_message(chat_id=query.message.chat.id, text="Пришлите ссылку, если ссылок несколько, разделите их запятыми. (Не стоит пытаться использовать более пяти ссылок чаще чем в 5-30 минут)")

# @dp.message_handler(lambda message: message.text and message.from_user.id in user_data and user_data[message.from_user.id] == "add_groups_link")


async def join_group_by_link_handler_template(message: types.Message, user_data, bot, current_client, **kwargs):
    links = message.text.split(', ')
    template_id = user_data["edit_template"]
    success_count = 0
    errors = []

    for link in links:
        link = link.strip()
        try:
            is_joined = await joinGroupByLink_template(current_client, link, message.from_user.id, bot, message.chat.id, template_id)
        except Exception as e:
            continue
        if is_joined:
            success_count += 1
        else:
            errors.append(link)

    success_message = f"Вы успешно присоединились к {success_count} группе(-ам)" if success_count > 0 else ""
    error_message = f"Следующие ссылки некорректны или истекли: {', '.join(errors)}" if errors else ""
    result_message = "\n".join(filter(bool, [success_message, error_message]))
    user_data.pop(message.from_user.id, None)
    await message.reply(result_message)

# #Обработчик команды добавления в группу через поиск
# @dp.callback_query_handler(template_cd.filter(action="add_groups_search"))


async def join_group_by_search_handler_template(query: CallbackQuery, callback_data: dict, user_data, bot, **kwargs):
    await query.answer()
    template_id = int(callback_data.get('template_id'))
    template_name = await get_template_name_by_id(template_id)
    user_data[query.from_user.id] = {
        "state": "join_group_by_search_template",
        "template_name": template_name,
        "template_id": template_id
    }
    await bot.send_message(chat_id=query.message.chat.id, text="Введите поисковой запрос.")

group_button_cd = CallbackData("group_id", "add_by_userid")
groups_data = {}

# @dp.message_handler(lambda message: user_data.get(message.from_user.id, {}).get('state') == "join_group_by_search_template")


async def join_group_by_search_handler_template_msg(msg: types.Message, user_data, current_client, **kwargs):
    group_name = msg.text
    user_info = user_data.get(msg.from_user.id, {})
    template_name = user_info.get('template_name')
    template_id = user_info.get('template_id')
    add_by_userid = msg.from_user.id

    if not group_name:
        await msg.reply("Пожалуйста, укажите название группы.")
    else:
        groups = await search_group_not_joined(current_client, group_name)

        if not groups:
            await msg.reply(f"Группа '{group_name}' не найдена.")
        elif len(groups) == 1:
            groups_data[add_by_userid] = {
                'groups': groups, 'template_id': template_id}
            group = groups[0]
            group_id = group.id
            group_title = group.title

            # Проверка на дублирование группы
            all_groups = await get_all_group_list()
            if any(existing_group[0] == group_id for existing_group in all_groups):
                await msg.reply(f"Группа '{group_title}' (ID {group_id}) уже добавлена.")
            else:
                link = await get_invite_link(current_client, group_id)
                await add_group(group_id, group_title, add_by_userid, link)
                await msg.reply(f"Группа '{group_title}' (ID {group_id}) успешно добавлена")

        else:
            groups_data[add_by_userid] = {
                'groups': groups, 'template_id': template_id}
            buttons = []
            for group in groups:
                buttons.append(InlineKeyboardButton(
                    text=group.title,
                    callback_data=f"addGroup_{group.id}_{add_by_userid}"
                )
                )
            buttons.append(InlineKeyboardButton("Назад", callback_data=template_cd.new(
                template_id=template_id, action="groups_from_tamplate")))
            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(*buttons)
            await msg.reply(f"Найдено несколько групп с названием '{group_name}'. Выберите нужную группу из списка ниже:", reply_markup=markup)

# @dp.callback_query_handler(lambda call: call.data.startswith('addGroup'))


async def process_add_group_button(call: aiogram.types.CallbackQuery, current_client, **kwargs):
    _, group_id, add_by_userid = call.data.split("_")

    add_by_userid = int(add_by_userid)
    group_id = int(group_id)
    user_data = groups_data.get(add_by_userid)

    user_groups = user_data['groups']
    template_id = user_data['template_id']

    if user_groups is not None:
        group = next(
            (group for group in user_groups if group.id == group_id), None)

    isJoined = await join_group_by_id(current_client, group_id)
    if (isJoined):
        try:
            link = await get_invite_link(current_client, group_id)
            await add_group_template(group.id, group.title, add_by_userid, template_id, link)
            await call.answer(f'Вы успешно присоединились к группе: {group.title}', show_alert=True)
        except Exception as e:
            await call.answer(f'Ошибка присоединеия к группе: {e}', show_alert=True)
    else:
        await call.answer(f'Ошибка присоединения к группе: {group.title}', show_alert=True)


# #Список ключевых слов шаблона
# @dp.callback_query_handler(template_cd.filter(action="list_keywords_from_tamplate"))
async def list_keywords_handler_template(query: CallbackQuery, callback_data: dict, **kwargs):
    await query.answer()

    template_id = int(callback_data.get('template_id'))
    template_name = await get_template_name_by_id(template_id)
    keywords = await get_keywords_by_template_id(template_id)

    if not keywords:
        text = "У этого шаблона нет ключевых слов."
    else:
        keyword_list = "\n".join(keywords)
        text = f"Ключевые слова этого шаблона:\n{keyword_list}"

    back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад",
                                                                  callback_data=template_cd.new(template_id=template_id, action="edit_template_button")))
    await query.message.edit_text(text, reply_markup=back_markup)

# #Список слов-исключений шаблона
# @dp.callback_query_handler(template_cd.filter(action="list_stopkeywords_from_tamplate"))


async def list_stopwords_handler_tamplate(query: CallbackQuery, callback_data: dict, **kwargs):
    await query.answer()

    template_id = int(callback_data.get('template_id'))
    template_name = await get_template_name_by_id(template_id)
    stopwords = await get_stopwords_by_template_id(template_id)

    if not stopwords:
        text = "У этого шаблона нет стоп слов."
    else:
        stopwords_list = "\n".join(stopwords)
        text = f"Стоп-слова этого шаблона:\n{stopwords_list}"

    back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад",
                                                                  callback_data=template_cd.new(template_id=template_id, action="edit_template_button")))
    await query.message.edit_text(text, reply_markup=back_markup)

# Список отправителей в блэклисте


async def list_blacklisted_senders_handler_template(query: CallbackQuery, callback_data: dict, **kwargs):
    await query.answer()

    template_id = int(callback_data.get('template_id'))

    # Получение имени шаблона
    template_name = await get_template_name_by_id(template_id)

    # Получение списка заблокированных отправителей
    blacklisted_senders = await get_blacklisted_senders_by_template_id(template_id)

    if not blacklisted_senders:
        text = "В этом шаблоне нет отправителей из черного списка."
        await query.message.edit_text(text)
    else:
        sender_list = "\n".join(blacklisted_senders)
        full_text = f"Отправители в черном списке этого шаблона:\n{sender_list}"

        # Разбивка текста на части, если он превышает 4000 символов
        max_length = 4000
        parts = [full_text[i:i+max_length] for i in range(0, len(full_text), max_length)]

        for i, part in enumerate(parts):
            if i < len(parts) - 1:
                # Отправка части текста без маркапа
                await query.message.answer(part)
            else:
                # Для последней части добавляем маркап
                back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад",
                                                                              callback_data=template_cd.new(template_id=template_id, action="edit_template_button")))
                await query.message.answer(part, reply_markup=back_markup)


# #Добавление ключевых слов
# @dp.callback_query_handler(template_cd.filter(action="add_keywords_to_tamplate"))


async def add_keywords_to_tamplate_handler(query: CallbackQuery, callback_data: dict, user_data, bot, **kwargs):
    await query.answer()

    template_id = int(callback_data.get('template_id'))
    template_name = await get_template_name_by_id(template_id)

    user_data[query.from_user.id] = {"edit_template": template_id,
                                     "template_name": template_name, "add_keywords_template": True}

    back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад",
                                                                  callback_data=template_cd.new(template_id=template_id, action="edit_template_button")))
    await bot.send_message(chat_id=query.message.chat.id, text="Введите ключевые слова, которые необходимо добавить (разделите слова запятыми)", reply_markup=back_markup)

# @dp.message_handler(lambda message: message.text and message.from_user.id in user_data and "add_keywords_template" in user_data[message.from_user.id])


async def add_keywords_to_tamplate_msg(msg: types.Message, user_data, bot, **kwargs):
    template_id = user_data[msg.from_user.id]["edit_template"]
    template_name = await get_template_name_by_id(template_id)

    keywords = msg.text.split(', ')
    user_id = list(user_data.keys())[0]

    added_keywords = []
    failed_keywords = []

    for keyword in keywords:
        keyword = keyword.strip()
        if await add_keyword_to_tamplate(user_id, keyword, template_id):
            added_keywords.append(keyword)
        else:
            failed_keywords.append(keyword)

    added_message = f"Ключевые слова добавлены: {', '.join(added_keywords)}" if added_keywords else ""
    failed_message = f"Не удалось добавить ключевые слова: {', '.join(failed_keywords)}" if failed_keywords else ""

    result_message = "\n".join(filter(bool, [added_message, failed_message]))

    del user_data[msg.from_user.id]
    back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад",
                                                                  callback_data=template_cd.new(template_id=template_id, action="edit_template_button")))
    await bot.send_message(msg.chat.id, result_message, reply_markup=back_markup)

# Добавление отправителя в черный список


async def add_senders_to_blacklist_handler(query: CallbackQuery, callback_data: dict, user_data, bot, **kwargs):
    await query.answer()

    template_id = int(callback_data.get('template_id'))
    template_name = await get_template_name_by_id(template_id)

    user_data[query.from_user.id] = {
        "edit_template": template_id,
        "template_name": template_name,
        "add_senders_blacklist": True
    }

    back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад",
                                                                  callback_data=template_cd.new(template_id=template_id, action="edit_template_button")))
    await bot.send_message(chat_id=query.message.chat.id, text="Введите имена отправителей для добавления в черный список (разделите имена запятыми)", reply_markup=back_markup)


async def add_senders_to_blacklist_msg(msg: types.Message, user_data, bot, **kwargs):
    template_id = user_data[msg.from_user.id]["edit_template"]
    template_name = await get_template_name_by_id(template_id)

    senders = msg.text.replace('\n','').split(', ')
    user_id = list(user_data.keys())[0]

    added_senders = []
    failed_senders = []

    for sender in senders:
        sender = sender.strip()
        if await add_sender_to_blacklist(user_id, sender, template_id):
            added_senders.append(sender)
        else:
            failed_senders.append(sender)

    added_message = f"Отправители добавлены в черный список: {', '.join(added_senders)}" if added_senders else ""
    failed_message = f"Не удалось добавить следующих отправителей: {', '.join(failed_senders)}" if failed_senders else ""

    result_message = "\n".join(filter(bool, [added_message, failed_message]))

    del user_data[msg.from_user.id]
    back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад",
                                                                  callback_data=template_cd.new(template_id=template_id, action="edit_template_button")))
    await bot.send_message(msg.chat.id, result_message, reply_markup=back_markup)

# #Добавление слов-исключений
# @dp.callback_query_handler(template_cd.filter(action="add_stopwords_to_tamplate"))


async def add_blacklistkeyword_to_tamplate_handler(query: CallbackQuery, callback_data: dict, user_data, bot, **kwargs):
    await query.answer()

    template_id = int(callback_data.get('template_id'))
    template_name = await get_template_name_by_id(template_id)

    user_data[query.from_user.id] = {"edit_template": template_id,
                                     "template_name": template_name, "add_blacklistkeyword_template": True}

    back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад",
                                                                  callback_data=template_cd.new(template_id=template_id, action="edit_template_button")))
    await bot.send_message(chat_id=query.message.chat.id, text="Введите слова-исключения, которые необходимо добавить (разделите слова запятыми)", reply_markup=back_markup)

# @dp.message_handler(lambda message: message.text and message.from_user.id in user_data and "add_blacklistkeyword_template" in user_data[message.from_user.id])


async def add_blacklistkeywords_to_tamplate(msg: types.Message, user_data, bot, **kwargs):
    template_id = user_data[msg.from_user.id]["edit_template"]
    template_name = await get_template_name_by_id(template_id)

    keywords = msg.text.split(', ')
    user_id = list(user_data.keys())[0]

    added_keywords = []
    failed_keywords = []

    for keyword in keywords:
        keyword = keyword.strip()
        if await add_blacklistkeyword_to_tamplate(user_id, keyword, int(template_id)):
            added_keywords.append(keyword)
        else:
            failed_keywords.append(keyword)

    added_message = f"Слова-исключения добавлены: {', '.join(added_keywords)}" if added_keywords else ""
    failed_message = f"Не удалось добавить слова-исключения: {', '.join(failed_keywords)}" if failed_keywords else ""

    result_message = "\n".join(filter(bool, [added_message, failed_message]))

    del user_data[msg.from_user.id]
    back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад",
                                                                  callback_data=template_cd.new(template_id=template_id, action="edit_template_button")))
    await bot.send_message(msg.chat.id, result_message, reply_markup=back_markup)

# #Удаление ключевых слов из шаблона
# @dp.callback_query_handler(template_cd.filter(action="remove_keywords_from_tamplate"))


async def remove_keywords_from_tamplate_handler(query: CallbackQuery, callback_data: dict, user_data, bot, **kwargs):
    await query.answer()

    template_id = int(callback_data.get('template_id'))
    template_name = await get_template_name_by_id(template_id)

    user_data[query.from_user.id] = {"edit_template": template_id,
                                     "template_name": template_name, "remove_keywords_template": True}

    back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад",
                                                                  callback_data=template_cd.new(template_id=template_id, action="edit_template_button")))
    await bot.send_message(chat_id=query.message.chat.id, text=f"Введите ключевые слова, которые необходимо удалить из шаблона <{template_name}> (разделите слова запятыми)", reply_markup=back_markup)

# @dp.message_handler(lambda message: message.text and message.from_user.id in user_data and "remove_keywords_template" in user_data[message.from_user.id])


async def remove_keywords_from_tamplate(msg: types.Message, user_data, bot, **kwargs):
    template_id = user_data[msg.from_user.id]["edit_template"]

    keywords = msg.text.split(', ')

    removed_keywords = []
    failed_keywords = []

    for keyword in keywords:
        keyword = keyword.strip()
        if await remove_keyword_from_template(keyword, template_id):
            removed_keywords.append(keyword)
        else:
            failed_keywords.append(keyword)

    added_message = f"Ключевые слова удалены: {', '.join(removed_keywords)}" if removed_keywords else ""
    failed_message = f"Не удалось удалить ключевые слова: {', '.join(failed_keywords)}" if failed_keywords else ""

    result_message = "\n".join(filter(bool, [added_message, failed_message]))

    del user_data[msg.from_user.id]
    back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад",
                                                                  callback_data=template_cd.new(template_id=template_id, action="edit_template_button")))
    await bot.send_message(msg.chat.id, result_message, reply_markup=back_markup)

# Удаоление отправителя из черного списка


async def remove_senders_from_blacklist_handler(query: CallbackQuery, callback_data: dict, user_data, bot, **kwargs):
    await query.answer()

    template_id = int(callback_data.get('template_id'))
    template_name = await get_template_name_by_id(template_id)

    user_data[query.from_user.id] = {
        "edit_template": template_id,
        "template_name": template_name,
        "remove_senders_blacklist": True
    }

    back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад",
                                                                  callback_data=template_cd.new(template_id=template_id, action="edit_template_button")))
    await bot.send_message(chat_id=query.message.chat.id, text=f"Введите имена отправителей, которые необходимо удалить из черного списка <{template_name}> (разделите имена запятыми)", reply_markup=back_markup)


async def remove_senders_from_blacklist_msg(msg: types.Message, user_data, bot, **kwargs):
    template_id = user_data[msg.from_user.id]["edit_template"]

    senders = msg.text.split(', ')

    removed_senders = []
    failed_senders = []

    for sender in senders:
        sender = sender.strip()
        if await remove_sender_from_blacklist(sender, template_id):
            removed_senders.append(sender)
        else:
            failed_senders.append(sender)

    removed_message = f"Отправители удалены из черного списка: {', '.join(removed_senders)}" if removed_senders else ""
    failed_message = f"Не удалось удалить следующих отправителей: {', '.join(failed_senders)}" if failed_senders else ""

    result_message = "\n".join(filter(bool, [removed_message, failed_message]))

    del user_data[msg.from_user.id]
    back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад",
                                                                  callback_data=template_cd.new(template_id=template_id, action="edit_template_button")))
    await bot.send_message(msg.chat.id, result_message, reply_markup=back_markup)

# #Удаление слов-исключений из шаблона
# @dp.callback_query_handler(template_cd.filter(action="remove_stopwords_from_tamplate"))


async def remove_blacklistkeywords_from_template_handler(query: CallbackQuery, callback_data: dict, user_data, bot, **kwargs):
    await query.answer()

    template_id = int(callback_data.get('template_id'))
    template_name = await get_template_name_by_id(template_id)

    user_data[query.from_user.id] = {"edit_template": template_id,
                                     "template_name": template_name, "remove_blacklistkeyword_template": True}

    back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад",
                                                                  callback_data=template_cd.new(template_id=template_id, action="edit_template_button")))
    await bot.send_message(chat_id=query.message.chat.id, text=f"Введите слова-исключения, которые необходимо удалить из шаблона <{template_name}> (разделите слова запятыми)", reply_markup=back_markup)

# @dp.message_handler(lambda message: message.text and message.from_user.id in user_data and "remove_blacklistkeyword_template" in user_data[message.from_user.id])


async def remove_blacklistkeywords_from_template(msg: types.Message, user_data, bot, **kwargs):

    template_id = user_data[msg.from_user.id]["edit_template"]

    keywords = msg.text.split(', ')

    added_keywords = []
    failed_keywords = []

    for keyword in keywords:
        keyword = keyword.strip()
        if await remove_blacklistkeyword_from_template(keyword, template_id):
            added_keywords.append(keyword)
        else:
            failed_keywords.append(keyword)

    added_message = f"Слова-исключения удалены: {', '.join(added_keywords)}" if added_keywords else ""
    failed_message = f"Не удалось удалить слова-исключения: {', '.join(failed_keywords)}" if failed_keywords else ""

    result_message = "\n".join(filter(bool, [added_message, failed_message]))

    del user_data[msg.from_user.id]
    back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад",
                                                                  callback_data=template_cd.new(template_id=template_id, action="edit_template_button")))
    await bot.send_message(msg.chat.id, result_message, reply_markup=back_markup)


print("templates handlers registered")
