
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

    def test_params(self, user_ids, fields: str = "bdate, city, sex, relation"):
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


    def test_people(self, age_from, age_to, sex, city, status, offset, sorting: int = 0, count: int = 50):
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

    def test_photos(self, owner_id, album_id ="profile", photo_sizes = 1, extended = 1):
        params = {
            "owner_id": owner_id,
            "album_id": album_id,
            "photo_sizes": photo_sizes,
            "extended": extended
        }
        try:
            response = requests.get(f"{self.base_url}/method/photos.get",
                            params={**self.general_params(), **params}).json()["response"]["items"], owner_id
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
                print("test_photos() function has returned None object")
                pass


utilizer_vk = Vkinder(token=token, api_version="5.131")

