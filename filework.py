from datetime import datetime


def create_chat(chat_id, chat_name):
    file = open('chats.txt', 'a')
    file.write(f'{chat_id} {chat_name}\n')
    file.close()


def add_log(s):
    file = open('logs.txt', 'a')
    date = datetime.now()
    file.write(f'{date} {s} \n')
    file.close()


def get_chats_id():
    file = open('chats.txt')
    res = {}
    for line in file:
        key, val = line.split(maxsplit=1)
        res[int(key)] = val

    return res


def parse_pm():
    return [int(el) for el in open('pms.txt')]


def add_pm(username):
    file = open('pms.txt', 'a')
    file.write(username + '\n')
    file.close()


def remove_pm(line_to_remove):
    with open('pms.txt', 'r') as file:
        lines = file.readlines()

    with open('pms.txt', 'w') as file:
        for line in lines:
            if line.strip("\n") != line_to_remove:
                file.write(line)


def parse_admins(bot_ac):
    res = {bot_ac: 'A'}
    file = open('admins.txt')
    for line in file:
        key, role = line.split()
        res[key] = role

    file.close()

    return res


def update_admins(admins):
    file = open('admins.txt', 'w')
    for key in admins:
        file.write(f'{key} {admins[key]}')

    file.close()