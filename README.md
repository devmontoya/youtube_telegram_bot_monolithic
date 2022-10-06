# Youtube Telegram bot

**Bot de Telegram desarrollado en lenguaje Python** que permite realizar seguimiento a canales de Youtube elegidos por un usuario, con la capacidad de conservar de manera persistente listas de videos y preferencias de los usuarios para así indicar en una próxima visita únicamente los videos que el usuario no ha visto con anterioridad. Además, este bot funciona de manera **asíncrona**, logrando actualizar su base de datos de videos de manera periódica en segundo plano.

Se ha probado usando bases **SQLite** y **postgresql** en docker.

## Biblitecas usadas y requeridas:

- Theleton: API telegram para Python.
- Selenium: Obtención del código html de los videos de un canal determinado.
- BeautifulSoup: Para realizar web scraping sobre el html obtenido anteriormente usando Selenium Webdriver.
- Asyncio: Usado para lograr la asincronía, es usada también por Theleton.
- sqlalchemy: Manejo de bases de datos SQLite o postgresql gracias a su implementación ORM.

## Uso:

- Conseguir credenciales de acceso a la API Telegram, información en: [signing-in](https://docs.telethon.dev/en/stable/basic/signing-in.html)
- Cargar las credenciales como variables de entorno en el archivo `.env`:
```
    api_id="..."
    api_hash="..."
    bot_token="..."
    engine="..." #Connection Pool: Archivo SQLite, o dirección a DB postgresql.
```
- Haciendo uso de la herramienta de manejo de dependencias **Poetry** instalar los paquetes necesarios ejecutando `poetry install`.
- Ejecutar `poetry run python bot.py`

## Uso por parte del usuario:

- Ingresar al chat bot desde cualquier cliente Telegram.
- Dar click en iniciar o en su defecto escribir `/start`,  se presentarán las opciones.
- Para inscribir un primer canal de Youtube a seguir, escribir `2 <canal>` donde canal es el tramo final que aparece en la url `https://www.youtube.com/c/<canal>`.
