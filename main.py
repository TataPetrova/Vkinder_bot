"""
Основой файл запуска программы
"""

from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.exceptions import ApiError

from vkinder import VKinderBot
from config import group_token, connstr

# Задаем токен
VK_BOT_TOKEN = group_token
# Задаем подключение
CONNECTION = connstr


def main():
    # Запуск API
    vkinder_bot = VKinderBot(token=VK_BOT_TOKEN, connstr=CONNECTION)
    try:
        longpoll = VkLongPoll(vkinder_bot.session)
    except ApiError as error:
        print(error)
        return

    # Если все хорошо, выведем сообщение
    print('Бот запущен!')

    # Для каждого сообщения
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.from_user and event.text:
            print(event.text)
            vkinder_bot.process_message(event)


if __name__ == "__main__":
    main()
