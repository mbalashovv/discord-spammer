import aiohttp
import asyncio
import time
import json
import os
import re
import logging
from concurrent.futures import ThreadPoolExecutor

from utils import (
    print_settings, 
    print_channels_info, 
    print_processing_time, 
    print_token_stats,
    prompt,
    print_error,
)

# Константы из настроек
SPAM_MESSAGE = "Заглушка"
IMAGE_PATH = None
IS_TURBO = None
MAX_THREADS = 5
pattern = re.compile(r".*-[0-9]+$")


class TokenService:
    def __init__(self, token: str):
        self.token = token
        self.headers = {"Authorization": self.token}
        self._logger = None
        # self.__prepare_logging()
    
    #TODO: logs
    # def __prepare_logging(self):
    #     """Настройка вывода логов"""

    #     log_filename = f"logs/{self.token}.log"
    #     os.makedirs(os.path.dirname(log_filename), exist_ok=True)
    #     file_handler = logging.FileHandler(log_filename, mode="a")
    #     self._logger = logging.getLogger(str(self.__class__))
    #     self._logger.addHandler(file_handler)
        
    async def send_message(
        self,
        session: aiohttp.ClientSession, 
        channel_id: int, 
    ) -> bool:
        """Отслыает собщение в канал"""
        
        try:
            data = aiohttp.FormData()
            data.add_field("content", SPAM_MESSAGE)
            
            if IMAGE_PATH:
                data.add_field(
                    "file",
                    open(IMAGE_PATH, "rb"),
                    filename="image.png",
                    content_type="image/png"
                )
    
            r = await session.post(
                f"https://discord.com/api/v9/channels/{channel_id}/messages",
                headers=self.headers,
                data=data
            )
            if str(r.status).startswith("2"):
                return True
            return False
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")
            return False


    async def spam_by_token(self) -> tuple[int, int]:
        """Основная работа с юзером"""

        sended_messages = 0
        failed_messages = 0

        # Достаем все сервера юзера
        async with aiohttp.ClientSession() as session:
            guilds_response = await session.get("https://discord.com/api/v9/users/@me/guilds", headers=self.headers)

        # Проверка валидности токена
        if not guilds_response.ok:
            raise Exception("Token '%s' is invalid!" % self.token)

        guilds = await guilds_response.json()

        # Проходимся по каналам серверов
        async with aiohttp.ClientSession() as session:
            for guild in guilds:
                channels_response = await session.get(
                    f"https://discord.com/api/v9/guilds/{guild['id']}/channels",
                    headers=self.headers
                )
                if channels_response.status == 200:
                    channels = await channels_response.json()
                    channels = [
                        channel for channel in channels
                        if not pattern.match(channel["name"])
                    ]

                    # Красивый вывод панели каналов и сервера
                    print_channels_info(guild["name"], channels, self._logger)

                    # В турбо режиме все происходит намного быстрее, но есть шанс блока (он потом проходит)
                    if IS_TURBO:
                        tasks = [asyncio.create_task(self.send_message(session, channel['id'])) for channel in channels]
                        results = await asyncio.gather(*tasks)
                        sended_messages += sum(1 for success in results if success)
                        failed_messages += len(results) - sended_messages
                    else:
                        for channel in channels:
                            result = await self.send_message(session, channel['id'])
                            if result:
                                sended_messages += 1
                            else:
                                failed_messages += 1

                else:
                    print("Не смог взять каналы:", await channels_response.text())
                    print("Серверы:", [guild['name'] for guild in guilds])
        return sended_messages, failed_messages


    async def run(self) -> None:
        try:
            sended_messages, failed_messages = await self.spam_by_token()
            print_token_stats(self.token, sended_messages, failed_messages)
        except Exception as e:
            print_error("Возникла ошибка: %s" % e)


def launch_token(token: str) -> None:
    try:
        token_service = TokenService(token=token)
        asyncio.run(token_service.run())
    except Exception as e:
        print_error("Возникла ошибка: %s" % e)


def main():
    global IS_TURBO, SPAM_MESSAGE, IMAGE_PATH

    settings = None
    while settings is None:
        try:
            # Пытаемся достать настройки из дефолтной папки
            try:
                with open('./settings.json', 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            except FileNotFoundError:
                # Если не находим, то просим указать путь
                settings_path = prompt("Укажите путь к файлу настроек:")
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
        except FileNotFoundError:
            print_error("Файл не был найден, укажите существующий файл с разширением .json")

    
    IS_TURBO = prompt("Подключаем турбо (риск быстрого бана)? (y/N):") in ('y', '1', 'yes')
    settings["is_turbo"] = IS_TURBO
    print_settings(settings)
    
    start_time = time.time()

    SPAM_MESSAGE = settings["spam_message"]
    IMAGE_PATH = settings.get("image_path")
    try:
        with open(IMAGE_PATH, "rb") as _: 
            pass
    except FileNotFoundError:
        IMAGE_PATH = None
        
    discord_tokens = settings["discord_tokens"]

    for token in discord_tokens:
        launch_token(token=token)
    
    # # TODO: Конкурентная обработка токенов (максимум 5 токенов за раз)
    # with ThreadPoolExecutor(max_workers=min(len(discord_tokens), MAX_THREADS)) as worker:
    #     worker.map(launch_token, discord_tokens)

    print_processing_time(time.time() - start_time)


if __name__ == "__main__":
    main()
