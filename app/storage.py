from typing import Dict


class UserData:
    def __init__(self):
        self.last_auth = None  # Будем хранить время последней авторизации


user_storage: Dict[int, UserData] = {}  # Пример временного хранилища (вместо базы данных)
