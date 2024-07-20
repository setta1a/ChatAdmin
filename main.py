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

from filework import create_chat, add_log, get_chats_id

load_dotenv()
bot = Bot(os.getenv('TOKEN'))
dp = Dispatcher()
telethon_client = TelegramClient("setta1a", os.getenv('API_ID'), os.getenv('API_HASH'))

admins = {'@setta1a': 'A', '@leannwalkerr': 'A'}


# async def is_it_pm(message, chat_id):
#     chat = await telethon_client.get_entity(chat_id)
#     is_admin = False
#
#     if hasattr(chat, 'megagroup') and chat.megagroup:
#         participants = await telethon_client(GetParticipantsRequest(
#             channel=InputPeerChannel(chat.id, chat.access_hash),
#             filter=ChannelParticipantsAdmins(),
#             offset=0,
#             limit=100,
#             hash=0
#         ))
#
#         # Проверка, является ли пользователь администратором
#         is_admin = any(participant.user_id == message.from_user.username for participant in participants.participants)
#
#     return is_admin


def is_it_admin(message):
    if f'@{message.from_user.username}' in admins:
        return admins[f'@{message.from_user.username}']


async def change_permissions(user_id, role, message):
    if is_it_admin(message) == 'A':
        for id in get_chats_id():
            try:
                my_user = user_id
                my_chat = await telethon_client.get_entity(PeerChat(int(id)))
                if role == 'PM':
                    await telethon_client.edit_admin(entity=my_chat, user=my_user, is_admin=True, manage_call=True,
                                                     ban_users=True, invite_users=True)
                    admins[user_id] = 'PM'

                elif role == 'USER':
                    await telethon_client.edit_admin(entity=my_chat, user=my_user, is_admin=False, manage_call=False,
                                                     ban_users=False, invite_users=False)
                    admins[user_id] = 'USER'
            except:
                print("Пользователь не в группе")

        if role == 'PM':
            await bot.send_message(message.chat.id, 'Пользователь повышен')
        elif role == 'USER':
            await bot.send_message(message.chat.id, 'Пользователь понижен')

        add_log(f'пользователю {user_id} присвоена роль {role}')

    else:
        await bot.send_message(message.chat.id, 'Вы не являетесь админом')


async def promote_to_admin(chat_id, user_id):
    my_chat = await telethon_client.get_entity(PeerChat(int(chat_id)))
    await telethon_client.edit_admin(entity=my_chat, user=user_id, is_admin=True, manage_call=True,
                                     ban_users=True, invite_users=True, add_admins=True)


@dp.message(Command('start'))
async def handle_start(message: types.Message):
    await bot.send_message(message.chat.id, 'hello world')


@dp.message(Command('create_chat'))
async def handle_create(message: types.Message):
    if is_it_admin(message) in ('A', 'PM'):
        command, chat_title = message.text.split(maxsplit=1)

        async with telethon_client:
            result = await telethon_client(functions.messages.CreateChatRequest(
                users=list(admins.keys()),
                title=chat_title,
            ))
            result = str(result)
            index = result.find(' chats')
            chat_id = result[index + 16: index + 26]
            create_chat(chat_id, chat_title)
            add_log(f'создан чат с навазнием {chat_title} и id={chat_id}')

            for key in admins:
                if admins[key] == 'A':
                    print(chat_id, key)
                    await promote_to_admin(chat_id, key)

            await message.reply(f'Чат "{chat_title}" создан!')
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
        for key in chats:
            if chats[key] == chatname:
                chat_id = key
        try:
            await telethon_client(AddChatUserRequest(
                chat_id,
                user_tag,
                fwd_limit=100
            ))
            await bot.send_message(message.chat.id, 'Пользователь добавлен в чат')
        except:
            await bot.send_message(message.chat.id, 'Неверное название чата или имя пользователя')
        add_log(f'пользователь {user_tag} добавлен в чат {chatname}')
    else:
        await bot.send_message(message.chat.id, 'Вы не являетесь админом')


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
            if chats[key] == chat_name:
                chat_id = key

        await telethon_client(DeleteChatUserRequest(chat_id=chat_id, user_id=user_id))
    else:
        await bot.send_message(message.chat.id, 'Вы не являетесь админом')


@dp.message(Command('delete_from_all'))
async def delete_from_all_groups(message: types.Message):
    cmd, user_id = message.text.split(maxsplit=1)
    if is_it_admin(message) == 'A':
        for chat_id in get_chats_id():
            try:
                await telethon_client(DeleteChatUserRequest(chat_id=chat_id, user_id=user_id))
            except:
                print('Пользователь не состоит в данной группе')


async def main():
    async with telethon_client:
        await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
