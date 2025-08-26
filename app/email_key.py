import logging
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()
mail_key = os.getenv("MAIL_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def send_key_to_email(user_mail: str, pass_key: str):
    # Настройки отправителя (mail.ru)
    sender_email = "daniilkondratuk@mail.ru"
    password = mail_key  # пароль для приложений
    receiver_email = user_mail  # Куда отправляем

    # Создаем сообщение
    message = MIMEText(f"Привет! Вот твой одноразовый код для входа в систему бота: {pass_key}\n\n"
                       f"Компания WaveAccess | Разработка программного ПО на заказ")
    message["Subject"] = "Авторизация HR-chatbot WaveAccess."
    message["From"] = sender_email
    message["To"] = receiver_email

    # Отправка через SMTP mail.ru
    try:
        # Подключаемся к серверу mail.ru (используем порт 465 с SSL)
        with smtplib.SMTP_SSL("smtp.mail.ru", 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        logger.info("✅ Письмо успешно отправлено!")
    except Exception as e:
        logger.error(f"❌ Ошибка отправка письма: {e}")
