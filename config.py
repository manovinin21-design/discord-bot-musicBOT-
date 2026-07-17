"""Configuration and constants for the Discord bot."""

import os
from dotenv import load_dotenv

load_dotenv()

# Bot configuration
TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_PATH = "database.db"
SHIPS_FILE = "ships.json"

# Music configuration
YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "default_search": "ytsearch",
    "quiet": True,
    "nocheckcertificate": True,
    "ignoreerrors": True,
    "extract_flat": False
}

FFMPEG_OPTIONS = {
    "before_options": (
        "-reconnect 1 "
        "-reconnect_streamed 1 "
        "-reconnect_delay_max 10 "
        "-reconnect_at_eof 1"
    ),
    "options": (
        "-vn "
        "-bufsize 64k"
    )
}

# Social content
KISS_GIFS = [
    "https://media.tenor.com/QUzj0izZ-5kAAAAj/kiss.gif",
    "https://c.tenor.com/m6xs0NvfODkAAAAd/tenor.gif",
    "https://c.tenor.com/yQij1WWOLtkAAAAd/tenor.gif",
    "https://c.tenor.com/ebi-Gt7Rr_IAAAAd/tenor.gif",
    "https://c.tenor.com/xpyZ3UhL_WEAAAAd/tenor.gif",
    "https://c.tenor.com/2qvjI-SYF_YAAAAd/tenor.gif",
    "https://c.tenor.com/waEnbrA5v0oAAAAd/tenor.gif"
]

NAKANO_EMBEDS = [
    {
        "titulo": "YOTSUBA THE GOATTT",
        "imagem": "https://c.tenor.com/VLtqnbrzq7QAAAAC/tenor.gif"
    },
    {
        "titulo": "ITSUKI THE GOATTT",
        "imagem": "https://c.tenor.com/khWESKnOJUEAAAAC/tenor.gif"
    },
    {
        "titulo": "ICHIKA THE GOATTT",
        "imagem": "https://c.tenor.com/mqljn-Ok5xsAAAAC/tenor.gif"
    },
    {
        "titulo": "NINO THE GOATTT",
        "imagem": "https://c.tenor.com/Rkjs48-BAzwAAAAC/tenor.gif"
    },
    {
        "titulo": "MIKU THE GOATTT",
        "imagem": "https://c.tenor.com/6N-Xh1IS3pEAAAAC/tenor.gif"
    }
]

COOLDOWN_XP_SECONDS = 60
XP_GAIN_MIN = 10
XP_GAIN_MAX = 20
