import os, requests
from requests.exceptions import RequestException


class Email_api_service:
    """
    SMTP Service via API - SENDINBLUE
    """
    SMTP_API_URL = os.environ['SMTP_API_URL']
    EMAIL_SERVICE_MODE = os.environ['EMAIL_SERVICE_MODE']
    SMTP_API_KEY = os.environ['SMTP_API_KEY']
    DEFAULT_SENDER = {"name": "Luis Lucena [estokealo]", "email": "luis.lucena89@gmail.com"}
    DEFAULT_CONTENT = "<!DOCTYPE html><html><body><h1>Email de prueba default</h1><p>development mode</p></body></html> "
    DEFAULT_SUBJECT = "this is a test email"
    ERROR_MSG = "Connection error with smtp server"
    SERVICE_NAME = "email_service"

    def __init__(self, email_to: str, content=None, sender=None, subject=None):
        self.email_to = email_to
        self.content = content if content is not None else self.DEFAULT_CONTENT
        self.sender = sender if sender is not None else self.DEFAULT_SENDER
        self.subject = subject if subject is not None else self.DEFAULT_SUBJECT

    @property
    def recipients(self) -> dict:
        return {
            "email": self.email_to
        }

    @property
    def headers(self) -> dict:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "api-key": self.API_KEY
        }

    @property
    def body(self) -> dict:
        return {
            "sender": self.sender,
            "to": self.recipients,
            "subject": self.subject,
            "htmlContent": self.content
        }

    def send_email(self) -> tuple:
        """
        SMTP API request function
        return tuple with status and message:
        * (success:bool, msg:str)
        """
        if self.EMAIL_SERVICE_MODE == 'development':
            print(self.content)
            return True, {self.SERVICE_NAME: "email was printed in console"}

        try:
            r = requests.post(headers=self.headers, json=self.body, url=self.SMTP_API_URL, timeout=3)
            r.raise_for_status()

        except RequestException as e:
            return False, {self.SERVICE_NAME: f"{self.ERROR_MSG} - {e}"}

        return True, {self.SERVICE_NAME: f"email was sent to: [{self.email_to}]"}

    @classmethod
    def user_verification(cls, email_to:str, verification_code:int):
        content = f"El código de verificación que solicitó: {verification_code}"
        sender = "luis.lucena89@gmail.com"
        subject = "código de verificación | estokealo"
        
        return cls(email_to=email_to, content=content, sender=sender, subject=subject)