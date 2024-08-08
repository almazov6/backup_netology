import configparser
import datetime
import json
import requests

from tqdm import tqdm


class ConfigParser:

    @staticmethod
    def config_pars(name_api) -> str:
        config = configparser.ConfigParser()
        config.read('settings.ini')
        if name_api == 'VK':
            return config['VK_TOKEN']['TOKEN']
        elif name_api == 'YD':
            return config['YD_TOKEN']['TOKEN']


cfg = ConfigParser()


class VK:
    VK_BASE_URL = 'https://api.vk.com/method'

    def __init__(self, token, user_id, version='5.199'):
        self.token = token
        self.user_id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def _build_url(self, api_method):
        return f'{self.VK_BASE_URL}/{api_method}'

    def profile_is_private(self):
        """
        Функция для определения приватности профиля Вконтакте.
        """
        result = False
        params = self.params
        params.update({
            'user_ids': self.user_id,
        })
        response = requests.get(self._build_url('users.get'), params=params)
        response = response.json()['response'][0]['is_closed']
        if response:
            result = True
            print('Это закрытый аккаунт')
            return result
        else:
            return result

    def get_photos(self):
        params = self.params
        params.update({'owner_id': self.user_id,
                       'album_id': 'profile',
                       'extended': 1
                       })
        response = requests.get(self._build_url('photos.get'),
                                params=params).json()
        response = response['response']
        # Проверка на приватность профиля.
        if not self.profile_is_private():
            file_name_list = []
            for item in tqdm(range(response['count'])):
                # Переменная для хранения ссылки фото профиля
                url_photo = response['items'][item]['orig_photo']['url']
                # Записываем количество лайков для названия файлов.
                file_name = response['items'][item]['likes']['count']
                # Записываем дату публикации фотографии профиля.
                photo_date_publication = datetime.datetime.fromtimestamp(
                    response['items'][item]['date']).date()
                # Если количество лайков одинаково, то добавляем дату загрузки.
                if file_name in file_name_list:
                    file_name = photo_date_publication
                else:
                    file_name_list.append(file_name)
                data = [{
                    'file_name': f'{file_name}.jpg',
                    'size': f'height '
                            f'{response['items'][item]['orig_photo']['height']}'
                            f', width '
                            f'{response['items'][item]['orig_photo']['width']}'
                }]
                # Создание JSON файла с названием и размером фото.
                with open(f'{file_name}.json', 'w') as file:
                    json.dump(data, file)
                YADisk(cfg.config_pars('YD')).download_photo(url_photo,
                                                             file_name)


vk = VK(cfg.config_pars('VK'), input('Введите ID пользователя: '))


class YADisk:
    YD_BASE_URL = 'https://cloud-api.yandex.net/v1/disk'

    def __init__(self, token):
        self.token = token

    def get_common_params(self):
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'OAuth {self.token}'
        }

    def _build_url(self, method):
        return f'{self.YD_BASE_URL}/{method}'

    def create_new_folder(self, folder_name=str(datetime.date.today())):
        """
        Функция для создания новой папки с проверкой на приватность профиля.
        """
        if not vk.profile_is_private():
            params = {
                'path': folder_name
            }
            response = requests.put(self._build_url('resources'), params=params,
                                    headers=self.get_common_params())
            print(f'Создана папка: {folder_name}')
            return response.status_code

    def download_photo(self, url, file_name):
        """
        Загружает файлы на ЯДиск.
        """
        headers = self.get_common_params()
        params = {
            'url': url,
            'path': f'{str(datetime.date.today())}/{file_name}.jpg'
        }
        response = requests.post(self._build_url('resources/upload'),
                                 params=params, headers=headers)
        return response


yadisk = YADisk(cfg.config_pars('YD'))
yadisk.create_new_folder()
vk.get_photos()
