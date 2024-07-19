from datetime import datetime


def create_chat(chat_id, chat_name):
    file = open('chats.txt', 'a')
    file.write(f'{chat_id} {chat_name}\n')
    file.close()


def add_log(s):
    file = open('logs.txt', 'a')
    date = datetime.now()
    file.write(date + ' ' + s + '\n')
    file.close()


def get_chats_id():
    return [int(el.split()[0]) for el in open('chats.txt')]

