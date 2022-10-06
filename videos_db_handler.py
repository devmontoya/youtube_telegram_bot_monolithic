from sqlalchemy import select, and_
from tables import channels, youtube_videos, clients
from logger import log

def user_channel_request(session, channel_name, user_id, queue):
    """
    Maneja la petición de un usuario acerca de un canal, en caso de ser nuevo la función
    se encargará de buscar los videos y en caso de que no, se buscará los videos ya presentes en la DB.
    """
    result_channels = session.query(channels).filter(
        channels.channelName == channel_name).all()

    new_data = []
    if len(result_channels) != 0:
        log.debug("Ya existe información del canal")
        result_channel_client = session.query(clients).filter(
            and_(clients.chat_id == user_id, clients.channel == channel_name)).all()

        if len(result_channel_client) != 0:
            log.debug("Este usuario ya ha solicitado información de este canal")
            client = session.execute(
                select(clients).filter(
                    and_(
                        clients.chat_id == user_id,
                        clients.channel == channel_name))).scalar_one()

            new_videos = session.query(youtube_videos).filter(
                and_(
                    youtube_videos.channelName == channel_name,
                    youtube_videos.id > client.lastVideoID)).all()
            new_videos = list(reversed(new_videos))

            # Actualiza el id del último video para el cliente si es necesario
            if len(new_videos) != 0:
                client.lastVideoID = new_videos[0].id

        else:
            log.info(f"Usuario nuevo ID: {user_id}")

            new_videos = session.query(youtube_videos).filter(
                youtube_videos.channelName == channel_name).all()
            new_videos = list(reversed(new_videos))

            last_id = max((i.id for i in new_videos))

            new_row_to_db = clients(user_id, channel_name, last_id)
            session.add(new_row_to_db)

        new_data = [[i.title for i in new_videos], [i.url for i in new_videos]]

    else:
        log.info(f"Usuario nuevo ID: {user_id}")
        new_row_to_db = clients(user_id, channel_name, 0)
        session.add(new_row_to_db)

        log.info("Se debe buscar la información correspondiente al canal")
        # Se buscan videos para este canal encolando su nombre en scraper
        queue.put(["user", channel_name])
        new_row_to_db = channels(channel_name)
        session.add(new_row_to_db)
        new_data = []

    return new_data


def add_new_videos(session, new_channel, new_data):
    """
    Cuando se le ingresa la lista de los últimos videos de un canal 'new_data', esta función
    los ingresa los videos a la base de datos en caso de que sean nuevos y actualiza los 'lastVideoID'
    """

    # Se reversa el orden para insertar los nuevos videos si es necesario
    new_data = [list(reversed(new_data[0])), list(reversed(new_data[1]))]

    try:
        curr_videos = session.query(youtube_videos).filter(
            youtube_videos.channelName == new_channel).all()
        last_id = max((i.id for i in curr_videos))
    except BaseException:
        log.info(f"No se encuentra información sobre este canal '{new_channel}'")
        curr_videos = []
        last_id = 0

    if len(curr_videos) == 0:
        log.info("No existen videos de este canal")
        for new_title, new_url in zip(*new_data):
            log.info(f"Se agrega un video con título: '{new_title}'")
            new_row_to_db = youtube_videos(new_channel, new_title, new_url)
            session.add(new_row_to_db)

    else:

        youtube_videos_db = [[video.id, video.title, video.url]
                             for video in reversed(curr_videos)]
        urls_yt_db = [video.url for video in reversed(curr_videos)]

        log.debug(new_data[1])

        # Videos que no se encuentran en el array de nuevos videos son
        # eliminados
        for id_video, _, url in youtube_videos_db:
            log.debug(url)
            if not (url in new_data[1]):
                session.delete(session.get(youtube_videos, id_video))
                log.debug(f"Eliminado la id {id_video}")

        # Se agregan los nuevos videos

        for new_title, new_url in zip(*new_data):
            if not (new_url in urls_yt_db):
                log.info(f"Se agrega un video con titulado: '{new_title}'")
                new_row_to_db = youtube_videos(new_channel, new_title, new_url)
                session.add(new_row_to_db)

    # Updating LastID
    curr_videos_last_id = session.query(youtube_videos).filter(
        youtube_videos.channelName == new_channel).all()
    last_id = max((i.id for i in curr_videos_last_id))

    channel = session.execute(
        select(channels).filter_by(
            channelName=new_channel)).scalar_one()
    channel.lastVideoID = last_id

    log.info(f"LastVideoID del canal {new_channel}: {channel.lastVideoID}")


def list_channels_user(session, user_id):
    channels_list = session.query(clients).filter(
        clients.chat_id == user_id).all()
    return (row.channel for row in channels_list)
