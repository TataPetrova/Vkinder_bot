"""
Файл, содержащий необходимые переменные
"""

import configparser

# Объект парсера
config = configparser.ConfigParser()

if len(config.read("settings.ini")) == 0:
    print('Добавьте файл setings.ini\nПример файла -> example/settings.ini')
    exit()

# Токен пользователя
user_token = config.get("settings", "user_token")
# Токен группы
group_token = config.get("settings", "group_token")
# Файл для логгирования
logging_file = config.get("settings", "logging_file")
# База данных
connstr = config.get("database", "connstr")
