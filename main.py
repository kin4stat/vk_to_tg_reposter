import aiohttp
import asyncio
import os
import sqlite3
from aiogram import Bot
from aiogram.utils.media_group import MediaGroupBuilder
connection = sqlite3.connect('/persistent/data.db')


VK_TOKEN = os.environ['VK_TOKEN']
TG_TOKEN = os.environ['TG_TOKEN']
VK_GROUP = int(os.environ['VK_GROUP_ID'])
TG_CHANNEL = os.environ['TG_CHANNEL_ID']
URL = "https://api.vk.com/method/wall.get"

REQUEST_DATA = {
    "access_token": VK_TOKEN,
    "owner_id": VK_GROUP,
    "offset": 0,
    "count": 1,
    "extended": 0,
    "v": "5.199",
}

bot = Bot(token=TG_TOKEN, parse_mode="html")

async def main():
    async with aiohttp.ClientSession() as session:
        while True:
            await asyncio.sleep(1)
            async with session.post(URL, data=REQUEST_DATA) as response:
                json = await response.json()
                if not json["response"]:
                    continue
                json = json["response"]
                if not len(json["items"]):
                    continue
                data = json["items"][0]
                if (data["type"] != "post"):
                    continue
                id = data["id"]
                cur = connection.cursor()
                cur.execute("SELECT latest_id FROM wall_data")
                latest_id = cur.fetchone()
                if latest_id == id:
                    continue

                if latest_id is None:
                    cur.execute("INSERT INTO wall_data (latest_id) VALUES (?)", (id, ))
                    latest_id = id
                else:
                    if latest_id[0] == id:
                        continue
                    cur.execute("UPDATE wall_data SET latest_id = ?", (id, ))

                connection.commit()
                media = MediaGroupBuilder()
                for pic in data["attachments"]:
                    if pic["type"] == "photo":
                        pic = max(pic["photo"]["sizes"], key=lambda x: (x["height"] * x["width"]))
                        media.add_photo(media=pic["url"])
                await bot.send_media_group(TG_CHANNEL, media=media.build())

if __name__ == "__main__":
    cur = connection.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS wall_data (latest_id INTEGER)''')
    connection.commit()
    asyncio.run(main())
    