#from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from base import Base


class clients(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer)
    channel = Column(String)
    lastVideoID = Column(Integer)

    def __init__(self, chat_id, channel, lastVideoID):
        self.chat_id = chat_id
        self.channel = channel
        self.lastVideoID = lastVideoID


class channels(Base):
    __tablename__ = 'channels'

    #id = Column(Integer, primary_key=True, autoincrement=True)
    channelName = Column(String, primary_key=True)
    lastVideoID = Column(Integer)

    def __init__(self, channelName, lastVideoID=0):
        self.channelName = channelName
        self.lastVideoID = lastVideoID


class youtube_videos(Base):
    __tablename__ = 'youtube_videos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    channelName = Column(String, ForeignKey("channels.channelName"))
    title = Column(String)
    url = Column(String)

    def __init__(self, channelName, title, url):
        self.channelName = channelName
        self.title = title
        self.url = url
