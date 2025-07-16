import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("API_KEY_DIFY")


def ask_dify(question: str) -> str:
    url = "https://api.dify.ai/v1"  # или другой endpoint (зависит от версии)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "inputs": {"question": question},
        "response_mode": "blocking"
    }

    response = requests.post(url, json=data, headers=headers)
    print(response.json())
    return response.json()["answer"]


import os
from dotenv import load_dotenv
import requests

load_dotenv()  # Загружаем переменные из .env

def test_api_key(api_key):
    url = "https://api.dify.ai/v1//workflows/run"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "inputs": {"question": "Как настроить Dify API?"},
        "response_mode": "blocking",
        "user": "1315154517"  # Обязательное поле!
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            print("✅ Успех! Ответ Dify:", response.json())
        else:
            print(f"❌ Ошибка {response.status_code}:", response.text)
    except Exception as e:
        print(f"🚫 Ошибка соединения: {e}")

# Проверяем ключ
if api_key:
    test_api_key(api_key)
else:
    print("❌ API_KEY_DIFY не найден в .env!")

