from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile

from telethon.sync import TelegramClient
from telethon import functions
from telethon.tl.functions.channels import EditBannedRequest, GetParticipantsRequest
from telethon.tl.functions.messages import AddChatUserRequest, EditChatDefaultBannedRightsRequest, DeleteChatUserRequest
from telethon.tl.types import InputUser, InputPeerUser, PeerChat, PeerUser, ChatBannedRights, InputPeerChannel, \
    ChannelParticipantsAdmins

from dotenv import load_dotenv
import os
import asyncio
from datetime import datetime

from filework import create_chat, add_log, get_chats_id, parse_admins, update_admins

load_dotenv()
bot = Bot(os.getenv('TOKEN'))
dp = Dispatcher()
bot_accaunt = '@leannwalkerr'
telethon_client = TelegramClient(bot_accaunt, os.getenv('API_ID'), os.getenv('API_HASH'))

admins = parse_admins(bot_accaunt)


def is_it_admin(message):
    if f'@{message.from_user.username}' in admins:
        return admins[f'@{message.from_user.username}']


async def change_permissions(user_id, role, message):
    if is_it_admin(message) == 'A':

        if user_id in admins:
            if admins[user_id] == 'A':
                flag = False
            else:
                flag = True
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
                                                         manage_call=False,
                                                         ban_users=False, invite_users=False)
                        admins[user_id] = 'USER'
                except:
                    print("Пользователь не в группе")

            if role == 'PM':
                await bot.send_message(message.chat.id, 'Пользователь повышен ⬆️✅')
            elif role == 'USER':
                await bot.send_message(message.chat.id, 'Пользователь понижен ⬇️✅')

            update_admins(admins)

            add_log(f'пользователю {user_id} присвоена роль {role} пользователем {message.from_user.username}')
        else:
            print('nonono i dont will change')

    else:
        await bot.send_message(message.chat.id, 'Вы не являетесь админом ❌')


async def promote_to_admin(chat_id, user_id):
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
            print(e)


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
        command, chat_title = message.text.split(maxsplit=1)

        result = await telethon_client(functions.messages.CreateChatRequest(
            users=list(admins.keys()),
            title=chat_title,
        ))
        result = str(result)
        index = result.find(' chats')
        chat_id = result[index + 16: index + 26]
        create_chat(chat_id, chat_title)
        add_log(f'пользователем {message.from_user.username} создан чат с названием {chat_title} и id={chat_id}')

        # for key in admins:
        #     if admins[key] == 'A':
        #         print(chat_id, key)
        #         await promote_to_admin(chat_id, key)

        await message.reply(f'Чат "{chat_title}" создан! ✅')
    else:
        await bot.send_message(message.chat.id, 'Вы не являетесь админом')


@dp.message(Command('change_permissions'))
async def handle_change(message: types.Message):
    if is_it_admin(message) == 'A':
        cmd, user_id, role = message.text.split(maxsplit=2)
        await change_permissions(user_id, role, message)
    else:
        await bot.send_message(message.chat.id, 'Вы не являетесь админом')


@dp.message(Command('add_user'))
async def add_user(message: types.Message):
    if is_it_admin(message) in ('A', 'PM'):
        cmd, user_tag, chatname = message.text.split(maxsplit=2)
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
            await bot.send_message(message.chat.id, 'Пользователь добавлен в чат ✅')
        except Exception as e:
            print(e)
            if 'The authenticated user is already a participant of the chat' in str(e):
                await bot.send_message(message.chat.id, 'Пользователь уже состоит в чате ✅')
            else:
                await bot.send_message(message.chat.id, 'Неверное название чата или имя пользователя ❌')
        add_log(f'пользователь {user_tag} добавлен в чат {chatname} пользователем {message.from_user.username}')
    else:
        await bot.send_message(message.chat.id, 'Вы не являетесь админом ❌')


@dp.message(Command('logs'))
async def send_logs(message: types.Message):
    logs = FSInputFile('logs.txt')
    await bot.send_document(message.chat.id, logs)


@dp.message(Command('delete_from_group'))
async def delete_from_one_group(message: types.Message):
    if is_it_admin(message) in ('A', 'PM'):
        cmd, user_id, chat_name = message.text.split(maxsplit=2)
        chats = get_chats_id()
        for key in chats:
            if chats[key] == chat_name + '\n':
                chat_id = key
        add_log(f'пользователь {user_id} удален из группы {chat_name} пользователем {message.from_user.username}')
        try:
            await telethon_client(DeleteChatUserRequest(chat_id=chat_id, user_id=user_id))
            await bot.send_message('Пользователь успешно удален ✅')
        except Exception as e:
            print(e)
            await bot.send_message(message.chat.id, 'Неверное название чата или имя пользователя ❌')
    else:
        await bot.send_message(message.chat.id, 'Вы не являетесь админом ❌')


@dp.message(Command('delete_from_all'))
async def delete_from_all_groups(message: types.Message):
    cmd, user_id = message.text.split(maxsplit=1)
    if is_it_admin(message) == 'A':
        chats = get_chats_id()
        for chat_id in chats:
            try:
                await telethon_client(DeleteChatUserRequest(chat_id=chat_id, user_id=user_id))
                await bot.send_message(message.chat.id, str(chats[chat_id]).replace('\n', '') + ': ✅')
            except Exception as e:
                print(e)

        add_log(f"пользователь {user_id} удален из всех групп пользователем {message.from_user.username}")


    else:
        await bot.send_message(message.chat.id, 'Вы не являетесь админом')


async def main():
    async with telethon_client:
        await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
