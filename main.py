from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, ReplyKeyboardMarkup, KeyboardButton

from telethon.sync import TelegramClient
from telethon import functions
from telethon.tl.functions.channels import EditBannedRequest, GetParticipantsRequest
from telethon.tl.functions.messages import AddChatUserRequest, DeleteChatUserRequest
from telethon.tl.types import InputUser, InputPeerUser, PeerChat, PeerUser, ChannelParticipantsAdmins

from dotenv import load_dotenv
import os
import asyncio

from filework import create_chat, add_log, get_chats_id, parse_admins, update_admins

load_dotenv()
bot = Bot(os.getenv('TOKEN'))
dp = Dispatcher()
bot_accaunt = '@Bot_PRFTRL'
telethon_client = TelegramClient(bot_accaunt[1:], os.getenv('API_ID'), os.getenv('API_HASH'))

admins = parse_admins(bot_accaunt)


def is_it_admin(message):
    if f'@{message.from_user.username}' in admins:
        return admins[f'@{message.from_user.username}']


from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def confirmation_keyboard():
    keyboard = [
        [KeyboardButton(text="✅ Да"), KeyboardButton(text="❌ Нет")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)




async def promote_to_admin(chat_id, user_id, message):
    if user_id != bot_accaunt:
        try:
            my_chat = await telethon_client.get_entity(PeerChat(int(chat_id)))
            if admins[user_id] == 'A':
                await telethon_client.edit_admin(entity=my_chat, user=user_id, is_admin=True, manage_call=True,
                                                 ban_users=True, invite_users=True, add_admins=True)
            elif admins[user_id] == 'PM':
                await telethon_client.edit_admin(entity=my_chat, user=user_id, is_admin=True, manage_call=True,
                                                 ban_users=True, invite_users=True, add_admins=False)
        except Exception as e:
            await bot.send_message(933403584, text=f'{e}')
            await bot.send_message(message.chat.id, text=f'Ошибка ❌\n {str(e)}')


async def request_confirmation(message: types.Message, text: str):
    await message.answer(text, reply_markup=confirmation_keyboard())


async def handle_confirmation(message: types.Message, callback: callable, *args):
    if message.text == "✅ Да":
        await callback(*args)
    elif message.text == "❌ Нет":
        await message.answer("Действие отменено.")


async def handle_missing_args(message: types.Message, command_structure: str):
    await message.answer(f"Недостаточно аргументов. Используйте команду как: {command_structure}")


async def change_permissions(user_id, role, message):
    if is_it_admin(message) == 'A':
        if user_id in admins:
            flag = admins[user_id] != 'A'
        else:
            flag = True

        if flag:
            for id in get_chats_id():
                try:
                    my_user = user_id
                    my_chat = await telethon_client.get_entity(PeerChat(int(id)))
                    if role == 'PM':
                        await telethon_client.edit_admin(entity=my_chat, user=my_user, is_admin=True, manage_call=True,
                                                         ban_users=True, invite_users=True)
                        admins[user_id] = 'PM'

                    elif role == 'USER':
                        await telethon_client.edit_admin(entity=my_chat, user=my_user, is_admin=False,
                                                         manage_call=False, ban_users=False, invite_users=False)
                        admins[user_id] = 'USER'
                except Exception as e:
                    await bot.send_message(933403584, text=f'{e}')
                    await bot.send_message(message.chat.id, text=f'Ошибка ❌\n {str(e)}')

            update_admins(admins)
            add_log(f'пользователю {user_id} присвоена роль {role} пользователем {message.from_user.username}')
            await message.answer(f"Пользователь {user_id} теперь {role} ✅", reply_markup=types.ReplyKeyboardRemove())
        else:
            await message.answer("Недостаточно прав для изменения этого пользователя.", reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer('Вы не являетесь админом ❌', reply_markup=types.ReplyKeyboardRemove())


@dp.message(Command('start'))
async def handle_start(message: types.Message):
    await bot.send_message(message.chat.id,
                           text='<b>Привет, это бот для управления рабочими чатами, вот мои возможности:</b>\n\n' +
                                '/create_chat <i>chatname</i> — <b>создать чат</b>\n' +
                                '/add_user @username  <i>chatname</i> — <b>добавить пользователя в чат</b>\n' +
                                '/change_permissions <i>@username</i> PM/USER — <b>выдать/забрать права ПМа</b>\n' +
                                '/delete_from_group @username  <i>chatname</i> — <b>удалить пользователя из одного чата</b>\n' +
                                '/delete_from_all <i>@username</i> — <b>удалить пользователя из всех чатов</b>\n' +
                                '/logs — получить логи', parse_mode='html')


@dp.message(Command('create_chat'))
async def handle_create(message: types.Message):
    if is_it_admin(message) in ('A', 'PM'):
        command_parts = message.text.split(maxsplit=1)
        if len(command_parts) < 2:
            await handle_missing_args(message, '/create_chat <chatname>')
            return

        chat_title = command_parts[1]
        await request_confirmation(message, f"Вы точно хотите создать чат с названием {chat_title}?")

        @dp.message(lambda message: message.text in ["✅ Да", "❌ Нет"])
        async def confirm_create(message: types.Message):
            if message.text == "✅ Да":
                result = await telethon_client(functions.messages.CreateChatRequest(
                    users=list(admins.keys()),
                    title=chat_title,
                ))
                result = str(result)
                index = result.find(' chats')
                chat_id = result[index + 16: index + 26]
                create_chat(chat_id, chat_title)
                add_log(
                    f'пользователем {message.from_user.username} создан чат с названием {chat_title} и id={chat_id}')

                for key in admins:
                    await promote_to_admin(chat_id, key, message)

                await message.reply(f'Чат "{chat_title}" создан! ✅', reply_markup=types.ReplyKeyboardRemove())
            else:
                await message.reply("Создание чата отменено.", reply_markup=types.ReplyKeyboardRemove())

    else:
        await bot.send_message(message.chat.id, 'Вы не являетесь админом')


@dp.message(Command('change_permissions'))
async def handle_change(message: types.Message):
    if is_it_admin(message) == 'A':
        command_parts = message.text.split(maxsplit=2)
        if len(command_parts) < 3:
            await handle_missing_args(message, '/change_permissions <@username> PM/USER')
            return

        user_id, role = command_parts[1], command_parts[2]
        await request_confirmation(message, f"Вы точно хотите изменить роль пользователя {user_id} на {role}?")

        @dp.message(lambda message: message.text in ["✅ Да", "❌ Нет"])
        async def confirm_permissions(message: types.Message):
            if message.text == "✅ Да":
                await change_permissions(user_id, role, message)
            else:
                await message.answer("Изменение роли отменено.", reply_markup=types.ReplyKeyboardRemove())
    else:
        await bot.send_message(message.chat.id, 'Вы не являетесь админом ❌')


@dp.message(Command('add_user'))
async def add_user(message: types.Message):
    if is_it_admin(message) in ('A', 'PM'):
        command_parts = message.text.split(maxsplit=2)
        if len(command_parts) < 3:
            await handle_missing_args(message, '/add_user @username <chatname>')
            return

        user_tag, chatname = command_parts[1], command_parts[2]
        await request_confirmation(message, f"Вы точно хотите добавить пользователя {user_tag} в чат {chatname}?")

        @dp.message(lambda message: message.text in ["✅ Да", "❌ Нет"])
        async def confirm_add_user(message: types.Message):
            if message.text == "✅ Да":
                chats = get_chats_id()
                chat_id = 0
                try:
                    for key in chats:
                        if chats[key] == chatname + '\n':
                            chat_id = key
                    await telethon_client(AddChatUserRequest(
                        chat_id,
                        user_tag,
                        fwd_limit=100
                    ))
                    await bot.send_message(message.chat.id, 'Пользователь добавлен в чат ✅', reply_markup=types.ReplyKeyboardRemove())
                except Exception as e:
                    await bot.send_message(message.chat.id, text=f'Ошибка ❌\n {str(e)}', reply_markup=types.ReplyKeyboardRemove())

                add_log(f'пользователь {user_tag} добавлен в чат {chatname} пользователем {message.from_user.username}')
            else:
                await message.answer("Добавление пользователя отменено.", reply_markup=types.ReplyKeyboardRemove())
    else:
        await bot.send_message(message.chat.id, 'Вы не являетесь админом ❌')


@dp.message(Command('logs'))
async def send_logs(message: types.Message):
    if is_it_admin(message) in ('A', 'PM'):
        logs = FSInputFile('logs.txt')
        await bot.send_document(message.chat.id, logs)
    else:
        await bot.send_message(message.chat.id, 'Вы не являетесь админом ❌')


@dp.message(Command('delete_from_group'))
async def delete_from_one_group(message: types.Message):
    if is_it_admin(message) in ('A', 'PM'):
        command_parts = message.text.split(maxsplit=2)
        if len(command_parts) < 3:
            await handle_missing_args(message, '/delete_from_group @username <chatname>')
            return

        user_id, chat_name = command_parts[1], command_parts[2]
        await request_confirmation(message, f"Вы точно хотите удалить пользователя {user_id} из чата {chat_name}?")

        @dp.message(lambda message: message.text in ["✅ Да", "❌ Нет"])
        async def confirm_delete_user(message: types.Message):
            if message.text == "✅ Да":
                chats = get_chats_id()
                for key in chats:
                    if chats[key] == chat_name + '\n':
                        chat_id = key
                add_log(
                    f'пользователь {user_id} удален из группы {chat_name} пользователем {message.from_user.username}')
                try:
                    await telethon_client(DeleteChatUserRequest(chat_id=chat_id, user_id=user_id))
                    await bot.send_message(message.chat.id, 'Пользователь успешно удален ✅', reply_markup=types.ReplyKeyboardRemove())
                except Exception as e:
                    if 'Invalid object ID for a chat' in str(e):
                        await bot.send_message(message.chat.id, 'Неверное название чата или имя пользователя ❌')
            else:
                await bot.send_message(message.chat.id, 'Вы не являетесь админом ❌')


@dp.message(Command('delete_from_all'))
async def delete_from_one_group(message: types.Message):
    if is_it_admin(message) in ('A', 'PM'):
        command_parts = message.text.split(maxsplit=2)
        if len(command_parts) < 2:
            await handle_missing_args(message, '/delete_from_all @username')
            return

        user_id = command_parts[1]
        await request_confirmation(message, f"Вы точно хотите удалить пользователя {user_id} из всех чатов?")

        @dp.message(lambda message: message.text in ["✅ Да", "❌ Нет"])
        async def confirm_delete_user(message: types.Message):
            if message.text == "✅ Да":
                chats = get_chats_id()
                for chat_id in chats:
                    try:
                        await telethon_client(DeleteChatUserRequest(chat_id=chat_id, user_id=user_id))
                        await bot.send_message(message.chat.id, str(chats[chat_id]).replace('\n', '') + ': ✅', reply_markup=types.ReplyKeyboardRemove())
                    except Exception as e:
                        add_log(str(e))
                add_log(f"пользователь {user_id} удален из всех групп пользователем {message.from_user.username}")


            else:
                await bot.send_message(message.chat.id, 'Вы не являетесь админом', reply_markup=types.ReplyKeyboardRemove())


@dp.message(lambda message: message.text.startswith('/'))
async def unknown_command(message: types.Message):
    await message.reply("<b>Извините, такой команды нет. Вот список доступных команд:</b>\n"
                        '/create_chat <i>chatname</i> — <b>создать чат</b>\n' +
                        '/add_user @username  <i>chatname</i> — <b>добавить пользователя в чат</b>\n' +
                        '/change_permissions <i>@username</i> PM/USER — <b>выдать/забрать права ПМа</b>\n' +
                        '/delete_from_group @username  <i>chatname</i> — <b>удалить пользователя из одного чата</b>\n' +
                        '/delete_from_all <i>@username</i> — <b>удалить пользователя из всех чатов</b>\n' +
                        '/logs — получить логи', parse_mode='html')


async def main():
    async with telethon_client:
        await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
