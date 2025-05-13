import aiohttp
import asyncio
import time
import json
import re
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
pattern = re.compile(r".*-[0-9]+$")


async def send_message(
        session: aiohttp.ClientSession, 
        channel_id: int, 
        headers: dict,
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
            headers=headers,
            data=data
        )
        if str(r.status).startswith("2"):
            return True
        return False
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")
        return False


async def spam_by_token(token: str) -> tuple[int, int]:
    """Основная работа с юзером"""

    headers = {"Authorization": token}
    sended_messages = 0
    failed_messages = 0

    # Достаем все сервера юзера
    async with aiohttp.ClientSession() as session:
        guilds_response = await session.get("https://discord.com/api/v9/users/@me/guilds", headers=headers)

    guilds = await guilds_response.json()

    # Проходимся по каналам серверов
    async with aiohttp.ClientSession() as session:
        for guild in guilds:
            channels_response = await session.get(
                f"https://discord.com/api/v9/guilds/{guild['id']}/channels",
                headers=headers
            )
            if channels_response.status == 200:
                channels = await channels_response.json()
                channels = [
                    channel for channel in channels
                    if not pattern.match(channel["name"])
                ]

                # Красивый вывод панели каналов и сервера
                print_channels_info(guild["name"], channels)

                # В турбо режиме все происходит намного быстрее, но есть шанс блока (он потом проходит)
                if IS_TURBO:
                    tasks = [asyncio.create_task(send_message(session, channel['id'], headers)) for channel in channels]
                    results = await asyncio.gather(*tasks)
                    sended_messages += sum(1 for success in results if success)
                    failed_messages += len(results) - sended_messages
                else:
                    for channel in channels:
                        result = await send_message(session, channel['id'], headers)
                        if result:
                            sended_messages += 1
                        else:
                            failed_messages += 1

            else:
                print("Не смог взять каналы:", await channels_response.text())
                print("Серверы:", [guild['name'] for guild in guilds])
    return sended_messages, failed_messages


def run(token: str) -> None:
    sended_messages, failed_messages = asyncio.run(spam_by_token(token))
    print_token_stats(token, sended_messages, failed_messages)


def main():
    global IS_TURBO, SPAM_MESSAGE, IMAGE_PATH

    settings = None
    while settings is None:
        try:
            settings_path = prompt("Укажите путь к файлу настроек:")
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except FileNotFoundError:
            print_error("Файл не был найден, укажите существующий файл с разширением .json")

    
    IS_TURBO = prompt("Подключаем турбо? (y/N):") in ('y', '1', 'yes')
    settings["is_turbo"] = IS_TURBO
    print_settings(settings)
    
    start_time = time.time()

    SPAM_MESSAGE = settings["spam_message"]
    IMAGE_PATH = settings.get("image_path")
    discord_tokens = settings["discord_tokens"]

    for token in discord_tokens:
        run(token=token)
    
    # TODO: 1 token per thread (possible ouput problem)
    # with ThreadPoolExecutor(max_workers=len(discord_tokens)) as worker: #TODO: max limit
    #     worker.map(run, discord_tokens)

    print_processing_time(time.time() - start_time)


if __name__ == "__main__":
    main()