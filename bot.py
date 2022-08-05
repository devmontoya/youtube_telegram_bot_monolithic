import queue
import asyncio
import concurrent.futures
import time
import os

from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
from dotenv import load_dotenv

from telethon import TelegramClient, events

from sqlalchemy import select, and_
from base import Session, engine, Base
from tables import channels, youtube_videos, clients
from handling_videos_db import add_new_videos, user_channel_request, list_channels_user

load_dotenv()
api_id = os.environ["api_id"]
api_hash = os.environ["api_hash"]
bot_token = os.environ["bot_token"]


Base.metadata.create_all(engine)

q = queue.Queue()  # Queries queue

q_results_updater = queue.Queue()  # Bot updater results queue

q_results_user = queue.Queue()  # Results queue for users


def fetch_html(channel: str, driver) -> str:
    """Obtiene el archivo html final luego de ser procesado por Selenium Webdriver"""
    url = f'https://www.youtube.com/{channel}/videos'
    driver.get(url)
    # Wait until the page has an element with id "video-title"
    # time.sleep(10) # A easier way but static
    element = WebDriverWait(
        driver, 10).until(
        EC.presence_of_element_located(
            (By.ID, "video-title")))

    html = driver.page_source.encode('utf-8').strip()
    soup = BeautifulSoup(html, 'html.parser')
    common_tag = soup.findAll('a', id='video-title')[:5]
    titles = [element.get('title') for element in common_tag]
    urls = [element.get('href') for element in common_tag]
    return [titles, urls]


def scraper(queue_in, queue_results_user, queue_results_updater):
    """
    Despliega y mantiene el webdriver, el cual está siempre disponible para entregar
    los últimos videos de los canales puestos en la queue 'queue'
    """
    browser = webdriver.Firefox()

    while True:
        time.sleep(1)
        if queue_in.qsize() != 0:
            input_queue_data = queue_in.get()
            querier, channel = input_queue_data
            print(f"Channel: {channel}")
            result = fetch_html(channel, browser)
            if querier == "user":
                queue_results_user.put(result)
            else:
                queue_results_updater.put(result)

    browser.close()


# Bot initializer
client = TelegramClient('session_name', api_id, api_hash)

# Función que maneja mensajes entrantes


@client.on(events.NewMessage)
async def channel(event):
    """Función que maneja las peticiones del usuario"""
    await event.reply(f"Recibido: {event.raw_text}")
    # Asegura que el id a usar no lleve a overflow en la database SQL
    user_id = event.chat_id % 1000000
    print(f"Chat id: {user_id}")

    session = Session()

    if event.raw_text == "/start":
        mensaje = """\n
    Hola 👋, por favor introduce un número para elegir una de las siguientes opciones:
    1. Conocer los últimos videos.\n
    2. Introducir un canal nuevo:
        Escribir '2' seguido por espacio y el nombre del canal.
        Ejemplo: '2 BBCMundo'.\n
    3. Deja de realizar seguimiento a un canal:
        Escribir '3' seguido por espacio y el nombre del canal.
        Ejemplo: '3 BBCMundo'.\n
    4. Listar canales seguidos.\n
    5. Eliminar sus datos de la base de datos.
    """
        await event.reply(mensaje)

    elif event.raw_text == "1":

        result_client = session.query(clients).filter(
            clients.chat_id == user_id).all()
        channel_names = [row.channel for row in result_client]

        if len(channel_names) != 0:

            for channel_name in channel_names:

                new_data = user_channel_request(
                    session, channel_name, user_id, q)

                if len(new_data[0]) != 0:
                    string = f"Nuevos videos del canal **{channel_name}**\n"
                    for title, url in zip(new_data[0], new_data[1]):
                        string += f"- [{title}](https://www.youtube.com{url})\n"

                    string += "Preview of the latest video:"
                else:
                    string = f"¡No hay videos nuevos de **{channel_name}**!"
                await event.reply(string)

        session.commit()

    elif event.raw_text[0] == "2":
        channel_name = event.raw_text[2:].lower()
        print(f"Canal '{channel_name}'")

        new_data = user_channel_request(session, channel_name, user_id, q)
        print(f"Tamaño de la cola: {q.qsize()}")
        print(f"new_data: {new_data}")

        if len(new_data) != 0:  # La información ya está lista
            print("La información ya está lista")

        else:  # Es necesario buscar la información
            while (q_results_user.qsize() == 0):
                time.sleep(1)
            new_data = q_results_user.get()
            add_new_videos(session, channel_name, new_data)

            # Updating last_id client
            curr_videos = session.query(youtube_videos).filter(
                youtube_videos.channelName == channel_name).all()
            last_id = max([i.id for i in curr_videos])
            client = session.execute(
                select(clients).filter_by(
                    channel=channel_name)).scalar_one()
            client.lastVideoID = last_id

        print("Datos:")
        print(new_data)
        session.commit()

        # Printing process
        if len(new_data[0]) != 0:
            string = f"Nuevos videos del canal **{channel_name}**\n"
            for title, url in zip(new_data[0], new_data[1]):
                string += f"- [{title}](https://www.youtube.com{url})\n"

            string += "Preview of the latest video:"
        else:
            string = "**¡No hay videos nuevos!**"
        await event.reply(string)

    elif event.raw_text[0] == "3":
        channel_name = event.raw_text[2:].lower()
        print(f"Canal '{channel_name}'")

        list_channels = list_channels_user(session, user_id)

        if not channel_name:
            await event.reply("No se eligió un canal")
        elif channel_name in list(list_channels):
            session.query(clients).filter(
                and_(
                    clients.chat_id == user_id,
                    clients.channel == channel_name)).delete()
            session.commit()
            await event.reply(f"Usted ya no sigue el canal {channel_name}")
        else:
            await event.reply("Usted no sigue actualmente ese canal")

    elif event.raw_text == "4":
        str = "Listado de canales a los que usted sigue:\n"
        for channel in list_channels_user(session, user_id):
            str += f"- {channel}\n"
        await event.reply(str)

    elif event.raw_text == "5":

        session.query(clients).filter(clients.chat_id == user_id).delete()
        session.commit()

        await event.reply("Se eliminó su información")

    else:
        await event.reply("Opción no válida")
    session.close()


async def bot():
    """Función que inicial el bot Telegram"""
    print("Inicio del bot")

    await client.start(bot_token=bot_token)
    print("Bot corriendo")
    await client.run_until_disconnected()


async def updater(queue_input, queue_results):
    """Se encarga de ejecutar la actualización de los videos de los canales de manera periódica"""
    session = Session()

    while True:
        await asyncio.sleep(60)

        print("Ejecutando actualización de canales")

        result_channels = session.query(channels).all()
        channel_names = [row.channelName for row in result_channels]

        for channel in channel_names:
            queue_input.put(["updater", channel])

        await asyncio.sleep(10)

        while (queue_results.qsize() < len(channel_names)):
            await asyncio.sleep(2)
        print("Luego de counter")

        counter = 0
        while (queue_results.qsize() != 0):
            print(f"Tamaño queue de resultados: {queue_results.qsize()}")
            try:
                new_data = queue_results.get()
            except BaseException:
                raise ValueError("No hay entradas en la queue queue_results")

            channel_name = channel_names[counter]
            add_new_videos(session, channel_name, new_data)

            counter += 1

        print("Se terminó de actualizar los canales")
        session.commit()
    session.close()


async def main():
    loop = asyncio.get_running_loop()

    bot_task = asyncio.create_task(bot())
    updater_task = asyncio.create_task(updater(q, q_results_updater))

    with concurrent.futures.ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, scraper, q, q_results_user, q_results_updater)

    await updater_task
    await bot_task

asyncio.get_event_loop().run_until_complete(main())
asyncio.run(main())
