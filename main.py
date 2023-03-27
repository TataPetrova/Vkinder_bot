from datetime import date

from sqlalchemy import event
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from vk_db import *
from vk import *


with open("token_group.txt", "r") as file:
    bot_token = file.read().strip()

vk_session = vk_api.VkApi(token=bot_token)
longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()

def write_msg(user_id, message, attachment = None):
    vk_session.method("messages.send", {"user_id": user_id, "message": message,
                                        "attachment": attachment,  "random_id": get_random_id()})

removal = 0
all_user = []
total_couple = []

def get_user():

    for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                try:
                    request = event.text
                    if request.lower() == "старт" or request.lower() == "start":
                        write_msg(event.user_id, 'Начнём искать вторую половинку - введи "поиск" ')
                        user_id = event.user_id
                        user = (utilizer_vk.test_params(user_ids=user_id)["response"][0])
                        if "bdate" not in user.keys():
                            write_msg(event.user_id, f'Чего-то не хватает.'
                                                     f' Укажите дату рождения в настройках своего профиля\
                                                        и разрешите её показ')
                            continue
                        if "city" not in user.keys():
                            write_msg(event.user_id,
                                    f'Чего-то не хватает. Укажите в профиле город своего проживания')
                            continue
                        try:
                            user
                        except vk_api.exceptions.ApiError:
                            write_msg(event.user_id, f'Что-то пошло не так')
                            continue
                        else:
                            if user is not None:
                                total_couple.clear()
                                all_user.clear()
                                all_user.append(user)
                            else:
                                write_msg(event.user_id, 'Что-то пошло не так.\
                                                            Проверьте настройки учётной записи ')
                    if request.lower() == "поиск" or request.lower() == "search":
                        write_msg(event.user_id, 'Для подтверждения поиска введите "поиск" ')
                        user = (utilizer_vk.test_params(user_ids=event.user_id)["response"][0])
                        if user is not None:
                            all_user.clear()
                            all_user.append(user)
                except:
                    write_msg(event.user_id, f'Что-то пошло не так ')
                break

def matchmaking():

    if all_user[0] is not None:
        birth_year = int(all_user[0]["bdate"][-4:])
        stream_year = date.today().year
        age = stream_year - birth_year

        sex = 0
        if all_user[0]["sex"] == 1:
            sex += 2
        else:
            sex += 1
        user_city = all_user[0]["city"]["id"]
        relation = all_user[0]["relation"]
        try:
            shown_people = utilizer_vk.test_people(age - 1, age + 1, sex, user_city, relation, removal)
        except vk_api.exceptions.ApiError:
            write_msg(event.user_id, f'Что-то пошло не так')
        else:
            if shown_people is not None:
                return shown_people
            else:
                write_msg(event.user_id, f'Не удалось найти подходящую пару.\
                                повторите попытку позже')
    else:
        write_msg(event.user_id, f'Не удалось осуществить поиск')

def collection_with_id():
    import requests
    import vk_api

    with open("user_token.txt", "r") as file:
        token = file.read().strip()

    class Vkinder:
        def __init__(self, token: str, api_version: str, base_url: str = "https://api.vk.com/"):
            self.token = token
            self.api_version = api_version
            self.base_url = base_url

        def general_params(self):
            return {
                "access_token": self.token,
                "v": self.api_version,
            }

        def test_params(self, user_ids,
                        fields: str = "bdate, city, sex, relation"):  # Функция для получения параметров пользователя бота для подбора подходящей пары
            params = {
                "user_ids": user_ids,
                "fields": fields
            }
            try:
                response = requests.get(f"{self.base_url}/method/users.get",
                                        params={**params, **self.general_params()}).json()
            except vk_api.exceptions.ApiError:
                pass
            except KeyError:
                pass
            except:
                print("Error")
            else:
                if response is not None:
                    return response
                else:
                    print("test_params() function has returned None object")
                    pass

        def test_people(self, age_from, age_to, sex, city, status, offset, sorting: int = 0,
                        count: int = 50):  # Функция для получения списка людей по подходящим параметрам
            params = {
                "age_from": age_from,
                "age_to": age_to,
                "sex": sex,
                "city": city,
                "status": status,
                "offset": offset,
                "sort": sorting,
                "count": count
            }
            try:
                response = requests.get(f"{self.base_url}/method/users.search",
                                        params={**self.general_params(), **params}).json()["response"]["items"]
            except vk_api.exceptions.ApiError:
                pass
            except KeyError:
                pass
            except:
                print("Error")
            else:
                if response is not None:
                    return response
                else:
                    print("test_people() function has returned None object")
                    pass

        def test_photos(self, owner_id, album_id="profile", photo_sizes=1,
                        extended=1):  # Функция для получения списка фотографий профиля и id выбранного пользователя
            params = {
                "owner_id": owner_id,
                "album_id": album_id,
                "photo_sizes": photo_sizes,
                "extended": extended
            }
            try:
                response = requests.get(f"{self.base_url}/method/photos.get",
                                        params={**self.general_params(), **params}).json()["response"][
                               "items"], owner_id
            except vk_api.exceptions.ApiError:
                pass
            except KeyError:
                pass
            except:
                print("Error")
            else:
                if response is not None:
                    return response
                else:
                    print("get_photos() function has returned None object")
                    pass

    utilizer_vk = Vkinder(token=token, api_version="5.131")

    people_ids = []
    for people in matchmaking():
        if people['is_closed'] == False:
            people_info = (people["id"], f'{people["first_name"]} {people["last_name"]}')
            if people_info is not None:
                people_ids.append(people_info)
    return people_ids

def collection_with_foto():

    whole_info = []
    for couple in collection_with_id():
        couple_name = couple[1]
        try:
            id_couple = f'https://vk.com/id{utilizer_vk.test_photos(owner_id=str(couple[0]))[1]}'
            all_photos = utilizer_vk.test_photos(owner_id=str(couple[0]))[0]
        except vk_api.exceptions.ApiError:
            write_msg(event.user_id, f'Ошибка api Вконтакте')

        photos_ids = {}
        if all_photos is not None:
            if len(all_photos) >= 3:
                for photo in all_photos:
                    photos_ids[(photo["id"])] = photo["comments"]["count"] + photo["likes"][
                                 "count"] + photo["likes"]["user_likes"]
            else:
                pass
        else:
            write_msg(event.user_id, f'не удалось найти фотографии для показа. Повторите поиск')
        sorted_ids = (sorted(photos_ids.items(), key=lambda x: x[1]))[-3:]
        only_ids = []
        for id in sorted_ids:
            only_ids.append(f'photo{id_couple[17:]}_{id[0]}')
        info = (couple_name, id_couple, only_ids)
        whole_info.append(info)
    return whole_info

def all_go():
   
    global removal
    for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                request = event.text
                matchmaking()
                collection_with_id()
                collection_with_foto()

                for couple in collection_with_foto():
                    if couple not in total_couple and couple is not None:
                        total_couple.append(couple)
                        try:
                            write_msg(event.user_id, message=f'Ваша пара - {couple[0]}, {couple[1]}',
                                            attachment=f'{couple[2][0]},{couple[2][1]},{couple[2][2]}')
                            user_table_name = f'id{event.user_id}'
                            couple_id = f'{couple[1][15:]}'

                            engine = sq.create_engine(DSN)
                            Session = sessionmaker(bind=engine)
                            session = Session()
                            User = work_list(user_table_name)
                            work_table(engine)
                            try:
                                table_columns = User(id_couple=couple_id, name_couple=couple[0])
                                session.add(table_columns)
                                session.commit()
                            except:
                                pass
                            session.close()
                        except:
                            continue

                removal += 50
                write_msg(event.user_id, 'для продолжения поиска введите "поиск" ')

def run_bot():
    get_user()
    while True:
        all_go()
