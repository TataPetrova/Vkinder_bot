"""
Функции для работы бота
"""

import vk_api

from vk_api.exceptions import ApiError

import messages
from db_utils import Saver
from config import user_token

# Токен пользователя для поиска
VK_USER_TOKEN = user_token


class VKinder:
    """
    Класс для поиска пользоавтелей
    """
    def __init__(self, token):
        self.session = self.get_vk_session(token)

    @staticmethod
    def get_vk_session(token):
        """
        Получение сессии ВК
        :param token: Токен пользователя
        :return:      Объект сессии, None при ошибке
        """
        try:
            session = vk_api.VkApi(token=token)
        except vk_api.exceptions.ApiError as e:
            print(f"Ошибка при создании сессии ВКонтакте: {e}")
            return None

        return session

    def search_users(self, age, gender, city, status, count=1000):
        """
        Поиск по критериям
        :param age:     Возраст
        :param gender:  Пол
        :param city:    Город
        :param status:  Семейное положение
        :param count:   Количество пользователей
        :return:        Список пользователей
        """
        api = self.session.get_api()

        users = api.users.search(
            count=count,
            age_from=age,
            age_to=age,
            sex=gender,
            city=city,
            status=status,
            fields="photo_id"
        )

        return users["items"]

    def get_photo_popularity(self, photo_id):
        """
        Подсчет популярности фото
        :param photo_id: Id фото
        :return:         Количество лайков и комментариев
        """
        api = self.session.get_api()
        photo_data = api.photos.getById(photos=photo_id)[0]
        return photo_data["likes"]["count"] + photo_data["comments"]["count"]

    def get_top_photos(self, user_id, top_count=3):
        """
        Получение топ n фото
        :param user_id:     Id пользователя
        :param top_count:   Количество фото
        :return:            Топ n фото
        """
        api = self.session.get_api()
        # Получаем фото пользователя
        photos = api.photos.getAll(owner_id=user_id, extended=1)
        # Сортируем по популярности
        popular_photos = sorted(
            photos["items"], key=lambda x: x["likes"]["count"], reverse=True
        )
        # Возвращаем топ n фото
        return popular_photos[:top_count]


class VKinderBot:
    """
    Бот для группы
    """
    def __init__(self, token, **kwargs):
        self.session = self.get_vk_session(token)
        self.api = self.session.get_api()
        self.top_users = 2
        self.user_data_cache = {}
        self.user_data = Saver(**kwargs)
        self.vkinder = None

    def send_photos_and_link(self, user_id, photos, link):
        """
        Отправляет фотографии и ссылку на пользователя ВКонтакте.

        :param user_id: int, идентификатор пользователя, которому отправлять сообщение.
        :param photos: список фотографий.
        :param link: str, ссылка на пользователя ВКонтакте.
        """
        attachments = ",".join([f"photo{photo['owner_id']}_{photo['id']}" for photo in photos])
        self.api.messages.send(user_id=user_id, attachment=attachments, message=link, random_id=0)

    def send_message(self, user_id, message):
        """
        Отправка сообщения
        :param user_id: Id пользователя
        :param message: Сообщение
        """
        self.api.messages.send(user_id=user_id, message=message, random_id=0)

    def process_age(self, user_id):
        """
        Ввод года
        :param user_id: Id пользователя
        :return:        Статус пользователя в боте
        """
        self.send_message(user_id, messages.process_age)
        return "age"

    def process_gender(self, user_id):
        """
        Ввод пола
        :param user_id: Id пользователя
        :return:        Статус пользователя в боте
        """
        self.send_message(user_id, messages.process_gender)
        return "gender"

    def process_city(self, user_id):
        """
        Ввод города
        :param user_id: Id пользователя
        :return:        Статус пользователя в боте
        """
        self.send_message(user_id, messages.process_city)
        return "city"

    def process_status(self, user_id):
        """
        Ввод семейного положения
        :param user_id: Id пользователя
        :return:        Статус пользователя в боте
        """
        self.send_message(user_id, messages.process_status)
        return "status"

    def final_status(self, user_id):
        """
        Финальный статус
        :param user_id: Id пользователя
        :return:        Статус пользователя в боте
        """
        if 'profiles' in self.user_data_cache[user_id]:
            # Сохраняем результаты в бд
            self.user_data.save_session_to_db(user_id, [profile['id'] for profile in
                                                        self.user_data_cache[user_id]['profiles']])

        self.send_message(user_id, messages.final_status)
        return "final"

    def get_next_profile(self, user_id):
        """
        Возвращает следующую анкету из сохраненных для данного пользователя.

        :param user_id: int, идентификатор пользователя.
        :return: dict, информация об анкете или None, если анкеты закончились.
        """
        if not self.user_data_cache[user_id].get('profiles'):
            return None
        return self.user_data_cache[user_id]['profiles'].pop(-1)

    def process_message(self, event):
        """
        Обработка ввода пользователя
        :param event: Событие
        """
        # Вернет None, если нет данных о пользователе
        current_step = self.user_data_cache.get(event.user_id)
        # Если данных нет, проверим БД
        if current_step is None:
            # Создадим словарь для пользователя в Кэше
            self.user_data_cache[event.user_id] = {}
            # Есть ли данные о пользователе
            self.user_data_cache[event.user_id]['in_db'] = self.user_data.get_user_data_from_db(event.user_id)
            # Если есть данные, поздороваемся снова
            current_step = "again" if self.user_data_cache[event.user_id]['in_db'] else None
        else:
            current_step = current_step['step']

        # Если начальный шаг, поздороваемся
        if current_step is None:
            self.send_message(event.user_id, messages.greet_status)
            next_step = self.process_age(event.user_id)
        # Если пользователь вводит команду "еще", отправьте следующую анкету
        elif event.text.lower() == "еще" and current_step == 'final':
            next_profile = self.get_next_profile(event.user_id)
            if next_profile:
                top_photos = self.vkinder.get_top_photos(next_profile["id"])
                self.send_photos_and_link(event.user_id, top_photos, f"https://vk.com/id{next_profile['id']}")
                next_step = "final"
            else:
                self.send_message(event.user_id, 'Больше анкет нет. Хочешь еще? Напиши "Заново"')
                next_step = None

        # Иначе поищем его статус
        elif self.is_valid_input(event.text, current_step):
            if current_step == "again":
                self.send_message(event.user_id, messages.greet_status)
                next_step = self.process_age(event.user_id)
            elif current_step == "age":
                self.user_data_cache[event.user_id]["age"] = int(event.text)
                next_step = self.process_gender(event.user_id)
            elif current_step == "gender":
                self.user_data_cache[event.user_id]["gender"] = int(event.text)
                next_step = self.process_city(event.user_id)
            elif current_step == "city":
                self.user_data_cache[event.user_id]["city"] = int(event.text)
                next_step = self.process_status(event.user_id)
            elif current_step == "status":
                self.user_data_cache[event.user_id]["status"] = int(event.text)
                age, gender, city, status = (
                    self.user_data_cache[event.user_id]["age"],
                    self.user_data_cache[event.user_id]["gender"],
                    self.user_data_cache[event.user_id]["city"],
                    self.user_data_cache[event.user_id]["status"],
                )

                user_id = event.user_id
                token = VK_USER_TOKEN
                if not token:
                    self.send_message(user_id, messages.session_error)
                    return

                # Инициализируем объект поиска
                self.vkinder = VKinder(token)
                # Ищем пользователей
                try:
                    users = self.vkinder.search_users(age, gender, city, status)
                except ApiError:
                    self.send_message(user_id, messages.session_error)
                    return

                # Сохраняем пользователей в кэше
                self.user_data_cache[event.user_id]['profiles'] = [user for user in users if
                                                                   not user.get('is_closed', True) and user['id'] not in
                                                                   self.user_data_cache[event.user_id]['in_db']][
                                                                  :self.top_users]

                # Сохраняем статус и найденных пользователей
                next_step = self.final_status(event.user_id)

                # Отправляем первую анкету, если она есть
                next_profile = self.get_next_profile(event.user_id)
                if next_profile:
                    top_photos = self.vkinder.get_top_photos(next_profile["id"])
                    self.send_photos_and_link(user_id, top_photos, f"https://vk.com/id{next_profile['id']}")
                """
                # Список пользователей для сохранения в бд
                for_save = []
                # Выводим первых n пользователей
                for user in users:
                    # Если для сохранения уже больше пользователей, чем нужно вывести, выйдем из цикла
                    if len(for_save) > self.top_users:
                        break
                    # Если пользователь не скрыт и мы можем его вывести
                    if not user.get('is_closed', True):
                        if user['id'] not in self.user_data_cache[event.user_id]['in_db']:
                            for_save.append(user['id'])
                            top_photos = vkinder.get_top_photos(user["id"])
                            self.send_photos_and_link(user_id, top_photos, f"https://vk.com/id{user['id']}")
                
                self.final_status(event.user_id)
                # Сохраняем результаты в бд
                self.user_data.save_session_to_db(user_id, for_save)
                # Удалим данные о пользователе из кэша
                del self.user_data_cache[user_id]
                
                # Выход из функции
                return
                """
            # Попрощаемся
            else:
                self.send_message(event.user_id, messages.some_error)
                next_step = "final"
        # Если что-то не так, напишем пользователю
        else:
            self.send_message(event.user_id, messages.incorrect_data)
            next_step = current_step

        self.user_data_cache[event.user_id]['step'] = next_step

    @staticmethod
    def get_vk_session(token):
        """
        Получение сессии VK
        :param token: Токен
        :return:      Объект сессии
        """
        try:
            session = vk_api.VkApi(token=token)
        except vk_api.exceptions.ApiError as e:
            print(e)
            return None
        return session

    @staticmethod
    def is_valid_input(text, step):
        """
        Проверка корректности ввода состояния
        :param text: Текст сообщения
        :param step: Шаг
        :return:     True, если корректно, иначе False
        """
        if step == "again" or step == 'final':
            print(step, 'asd')
            print(text.lower() == 'заново')

            print(text.lower())
            return text.lower() == 'заново'
        if step == "age":
            # Проверяем, что число, входит в промежуток доступных возрастов, а также
            # что не float
            return text.isdigit() and (12 < int(text) < 100)
        if step == "gender":
            return text in ("1", "2")
        if step == "city":
            return text.isdigit()
        if step == "status":
            return text in ("1", "2", "3", "4", "5")
        if step == "final":
            return text == 'Заново'
        return False
