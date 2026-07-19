"""Configuration and constants for the Discord bot."""

import os
from dotenv import load_dotenv

load_dotenv()

# Bot configuration
TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_PATH = os.getenv("DATABASE_PATH", "database.db")
SHIPS_FILE = "ships.json"

# Music configuration
YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "default_search": "ytsearch",
    "quiet": True,
    "nocheckcertificate": True,
    # Com ignoreerrors o yt-dlp esconderia o motivo da falha; sem ele
    # conseguimos avisar no Discord por que a música não tocou
    "ignoreerrors": False,
    "extract_flat": False,
    # Deixa o yt-dlp baixar o resolvedor de desafios do YouTube (EJS).
    # Sem isso — e sem um runtime JS como deno/node instalado — o YouTube
    # entrega áudio lento ou bloqueado, e as músicas param de tocar
    "remote_components": ["ejs:github"],
}

# Cookies do YouTube (opcional): contornam o bloqueio "Sign in to confirm
# you're not a bot" que o YouTube aplica a IPs de hospedagem (ex.: Render).
# Exporte os cookies do navegador para um cookies.txt (veja o README).
COOKIES_FILE = os.getenv("YTDLP_COOKIES_FILE", "cookies.txt")
if os.path.exists(COOKIES_FILE):
    YTDL_OPTIONS["cookiefile"] = COOKIES_FILE

# Obs.: sem "-reconnect_at_eof" — ele faz o FFmpeg tentar reconectar no fim
# do arquivo, o que atrasava vários segundos a troca para a próxima música
FFMPEG_OPTIONS = {
    "before_options": (
        "-reconnect 1 "
        "-reconnect_streamed 1 "
        "-reconnect_delay_max 5"
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
