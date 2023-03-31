"""
Файл, содержащий необходимые переменные
"""

import configparser

# Объект парсера
config = configparser.ConfigParser()
if len(config.read("settings.ini")) == 0:
    print('Добавьте в файл settings.ini токен пользователя и токен группы, а так же данные postgresql')
    exit()

# Токен пользователя
user_token = config.get("settings", "user_token")
# Токен группы
group_token = config.get("settings", "group_token")
# База данных
connstr = config.get("database", "connstr")
