import asyncio
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from database.base_connection import Base, Session, engine
from database.tables import channels, clients, youtube_videos
from logger import log
from videos_db_handler import add_new_videos, list_channels_user, user_channel_request


def fetch_html(channel: str, driver) -> str:
    """Obtiene el archivo html final luego de ser procesado por Selenium Webdriver"""
    url = f"https://www.youtube.com/{channel}/videos"
    driver.get(url)
    # Wait until the page has an element with id "video-title"
    # time.sleep(10) # A easier way but static
    _ = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "video-title"))
    )

    html = driver.page_source.encode("utf-8").strip()
    soup = BeautifulSoup(html, "html.parser")
    common_tag = soup.findAll("a", id="video-title")[:5]
    titles = [element.get("title") for element in common_tag]
    urls = [element.get("href") for element in common_tag]
    return [titles, urls]


def scraper(queue_in, queue_results_user, queue_results_updater):
    """
    Despliega y mantiene el webdriver, el cual está siempre disponible para
    entregar los últimos videos de los canales puestos en la queue 'queue'
    """
    browser = webdriver.Firefox()

    while True:
        time.sleep(1)
        if queue_in.qsize() != 0:
            input_queue_data = queue_in.get()
            querier, channel = input_queue_data
            log.debug(f"Channel: {channel}")
            result = fetch_html(channel, browser)
            if querier == "user":
                queue_results_user.put(result)
            else:
                queue_results_updater.put(result)

    browser.close()


async def updater(queue_input, queue_results):
    """Se encarga de ejecutar la actualización de los videos de los canales de manera periódica"""
    session = Session()

    while True:
        await asyncio.sleep(60)

        log.info("Ejecutando actualización de canales")

        result_channels = session.query(channels).all()
        channel_names = [row.channelName for row in result_channels]

        for channel in channel_names:
            queue_input.put(["updater", channel])

        await asyncio.sleep(10)

        while queue_results.qsize() < len(channel_names):
            await asyncio.sleep(2)
        log.debug("Luego de counter")

        counter = 0
        while queue_results.qsize() != 0:
            log.debug(f"Tamaño queue de resultados: {queue_results.qsize()}")
            try:
                new_data = queue_results.get()
            except BaseException:
                raise ValueError("No hay entradas en la queue queue_results")

            channel_name = channel_names[counter]
            add_new_videos(session, channel_name, new_data)

            counter += 1

        log.info("Se terminó de actualizar los canales")
        session.commit()
    session.close()
