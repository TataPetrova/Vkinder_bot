from random import randrange
import vk_db as db
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from datetime import datetime
from vk_api.exceptions import ApiError
from sqlalchemy.exc import IntegrityError

with open("token_group.txt", "r") as file:
    bot_token = file.read().strip()
with open("user_token.txt", "r") as file:
    user_token = file.read().strip()


vk_session = vk_api.VkApi(token=bot_token)
user_vk = vk_api.VkApi(token=user_token)
longpoll = VkLongPoll(vk_session)


def write_msg(user_id, message, attachment=''):
    vk_session.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7),
                                    'attachment': attachment})


class VK:
    def __init__(self, user_id):
        self.user_id = user_id
        self.pair_id = 0
        self.user = db.MainUser
        self.offset = 0
        self.pair_id = 0
        self.pair_name = ''
        self.best_photo = ''


    def data(self):
        info = vk_session.method("users.get", {"user_ids": self.user_id,
                                           "fields": 'sex, bdate, city, relation'})
        return info


    def name(self):
        name = self.data()[0]['first_name']
        return name


    def age(self):
        if 'bdate' in self.data()[0].keys():
            bdate = self.data()[0]['bdate']
            if bdate is not None and len(bdate.split('.')) == 3:
                birth = datetime.strptime(bdate, '%d.%m.%Y').year
                this = datetime.now().year
                age = this - birth
                return age
            else:
                return 'Данные отсутствуют'
        else:
            return 'Данные отсутствуют'


    def sex(self):
        sex = self.data()[0]['sex']
        if sex == 1:
            return 2
        elif sex == 2:
            return 1
        else:
            return 0


    def city(self):
        if 'city' in self.data()[0].keys():
            city = self.data()[0]['city']['id']
            return city
        else:
            return 0


    def relation(self):
        if 'relation' in self.data()[0].keys():
            relation = self.data()[0]['relation']
            return relation
        else:
            return 'Данные о семейном положении отсутствуют!'


    def start(self):
        db.create_tables()
        self.name()
        self.age()
        self.city()
        self.relation()
        try:
            self.user = db.MainUser(vk_id=self.user_id, name=self.name(), age=self.age(),
                                    city=self.city(), relation=self.relation())
            db.append_user(self.user)
        except IntegrityError:
            pass
        self.detect_pair()
        self.test_best_photo()
        write_msg(event.user_id, f'Твоя пара:\n'
                                 f'Имя: {self.pair_name}, ссылка: vk.com/id{self.pair_id}', self.best_photo)
        return self.pair()


    def pair(self):
        write_msg(event.user_id, f'Введи ДАЛЕЕ, чтобы продолжить поиск, '
                                 f'или СТОП, если не хочешь остановить поиск, или ПРОПУСТИТЬ, '
                                 f'и искать следующего.')
        while True:
            for new_event in longpoll.listen():
                if new_event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    if new_event.message.lower() == 'далее':
                        try:
                            make_pair = db.CoupleUser(vk_id=self.pair_id, name=self.pair_name,
                                                         id_main_user=self.user_id)
                            db.append_user(make_pair)
                        except IntegrityError:
                            pass
                        write_msg(event.user_id, 'Ищу следующую пару...')
                        self.offset += 1
                        self.detect_pair()
                        self.test_best_photo()
                        write_msg(event.user_id, f'Твоя пара:\n'
                                                 f'Имя: {self.pair_name}, ссылка: vk.com/id{self.pair_id}',
                                  self.best_photo)
                        return self.pair()
                    elif new_event.message.lower() == 'стоп' or new_event.message.lower() == 'нет':
                        write_msg(event.user_id, 'Поиск завершён, если передумал введи ПРОДОЛЖИТЬ.')
                    elif new_event.message.lower() == 'продолжить' or new_event.message.lower() == 'пропустить':
                        write_msg(event.user_id, f'Подыскиваю следующую пару...')
                        self.offset += 1
                        self.detect_pair()
                        self.test_best_photo()
                        write_msg(event.user_id, f'Твоя пара:\n'
                                                 f'Имя: {self.pair_name}, ссылка: vk.com/id{self.pair_id}',
                                  self.best_photo)
                        return self.pair()


    def detect_pair(self):
        resp = user_vk.method('users.search', {'count': 1, 'city': self.city(), 'sex': self.sex(), 'age': self.age(),
                                               'relation': self.relation(), 'offset': self.offset, 'status': (1, 6),
                                               'has photo': 1, 'fields': 'is_closed'})
        if resp['items'][0]['id'] in db.control_user():
            self.offset += 1
            self.detect_pair()
        else:
            if resp['items']:
                for pair in resp['items']:
                    if pair['is_closed']:
                        self.offset += 1
                        self.detect_pair()
                    else:
                        self.pair_id = pair['id']
                        self.pair_name = pair['first_name']
            else:
                self.offset += 1
                self.detect_pair()


    def test_best_photo(self):
        photo_list = []
        resp = user_vk.method('photos.get', {'owner_id': self.pair_id,
                                             'album_id': 'profile',
                                             'access_token': user_token,
                                             'extended': 1,
                                             'v': '5.131'})
        photos = []
        for photo in resp['items']:
            photo_info = {'id': photo['id'], 'owner_id': photo['owner_id'], }
            count = 0
            try:
                count_com = user_vk.method('photos.getComments', {'owner_id': self.pair_id, 'photo_id': photo['id']})
                count = count_com['count']
            except ApiError:
                pass
            photo_info['popular'] = photo['likes']['count'] + count
            photo_list.append(photo_info)
        photo_list = sorted(photo_list, key=lambda k: k['popular'], reverse=True)
        for i in photo_list:
            photos.append(f"photo{i['owner_id']}_{i['id']}")
        self.best_photo = ','.join(photos[:3])
        return self.best_photo


if __name__ == '__main__':
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            bot = VK(event.user_id)
            bot.data()
            req = event.text.lower()
            if req == 'привет' or req == 'ghbdtn':
                write_msg(event.user_id, 'Чтобы начать поиск введи Старт, если передумал искать пару, напиши СТОП.')
            elif req == 'старт':
                write_msg(event.user_id, f"Идет поиск, {bot.name()}. Пожалуйста, ожидай...")
                bot.start()
            elif req == 'стоп' or req == 'нет':
                write_msg(event.user_id, f'Bye,Bye, {bot.name()}, но если передумал, введи СТАРТ.')
            else:
                write_msg(event.user_id, f'Не понял вашего ответа, {bot.name()}, Для начала поздороваемся - '
                                         f'Привет, {bot.name()}.')
