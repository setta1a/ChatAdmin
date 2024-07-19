from aiogram import Bot, Dispatcher, types, F

from aiogram.filters import Command
from telethon.sync import TelegramClient
from telethon import functions
from telethon.tl.types import InputUser, InputPeerUser, PeerChat, PeerUser

from dotenv import load_dotenv
import os
import asyncio
from datetime import datetime

from filework import create_chat, add_log, get_chats_id

load_dotenv()
bot = Bot(os.getenv('TOKEN'))
dp = Dispatcher()
telethon_client = TelegramClient("setta1a", os.getenv('API_ID'), os.getenv('API_HASH'))

admins = {'@setta1a': 'U', '@leannwalkerr': 'A'}


async def change_permissions(user_id, role, message):
    if user_id in admins and admins['@' + message.from_user.username] == 'A':
        for id in get_chats_id():
            my_user = await telethon_client.get_entity(PeerUser(user_id))
            my_chat = await telethon_client.get_entity(PeerChat(int(id)))
            if role == 'PM':
                await telethon_client.edit_admin(entity=my_chat, user=my_user, is_admin=True, manage_call=True,
                                                 ban_users=True, invite_users=True)

            elif role == 'USER':
                await telethon_client.edit_admin(entity=my_chat, user=my_user, is_admin=False, manage_call=False,
                                                 ban_users=False, invite_users=False)

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


@dp.message(Command('change_permissions'))
async def handle_change(message: types.Message):
    cmd, user_id, role = message.text.split(maxsplit=2)
    await change_permissions(user_id, role, message)


@dp.message(Command('add_user'))
async def add_user(message: types.Message):
    cmd, user_tag, chatname = message.text.split(maxsplit=2)


async def main():
    async with telethon_client:
        await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
