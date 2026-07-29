import requests

from aspel.config import (
    ASPEL_API_URL,
    ASPEL_USERNAME,
    ASPEL_PASSWORD,
    ASPEL_ACCESS_KEY,
    TIMEOUT
)


class AspelAuth:

    def __init__(self):
        self.token = None

    def login(self):

        if not ASPEL_USERNAME:
            raise Exception("Falta ASPEL_USERNAME en el .env")

        if not ASPEL_PASSWORD:
            raise Exception("Falta ASPEL_PASSWORD en el .env")

        print("Preparando autenticación con Aspel...")

        print("URL:", ASPEL_API_URL)

        # Aquí irá el endpoint oficial de login
        #
        # Ejemplo:
        #
        # response = requests.post(
        #     ASPEL_API_URL + "/login",
        #     json={
        #         "username": ASPEL_USERNAME,
        #         "password": ASPEL_PASSWORD,
        #         "access_key": ASPEL_ACCESS_KEY
        #     },
        #     timeout=TIMEOUT
        # )
        #
        # self.token = response.json()["token"]

        return True