import discord
import random
from discord.ext import commands
import yt_dlp
import asyncio
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="D:/musicBOT/.env")

print("Token encontrado:", os.getenv("DISCORD_TOKEN"))

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

ytdl_options = {
    "format": "bestaudio",
    "noplaylist": True
}

ffmpeg_options = {
    "options": "-vn"
}

ytdl = yt_dlp.YoutubeDL(ytdl_options)

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

@bot.command()
async def entrar(ctx):

    if ctx.author.voice:

        canal = ctx.author.voice.channel
        await canal.connect()

        await ctx.send("Entrei na call 🎵")

    else:
        await ctx.send("Você precisa estar em um canal de voz.")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")

@bot.command()
async def tocar(ctx, url):

    if not ctx.voice_client:
        await ctx.invoke(entrar)

    try:

        info = ytdl.extract_info(url, download=False)

        audio = info["url"]

        source = discord.FFmpegPCMAudio(
            audio,
            **ffmpeg_options
        )

        ctx.voice_client.play(source)

        await ctx.send(
            f"Tocando: {info['title']} 🎶"
        )

    except Exception as erro:

        await ctx.send(
            f"Erro: {erro}"
        )

@bot.command()
async def oi(ctx):
    await ctx.send(f"Olá, {ctx.author.mention}! 👋")

@bot.command()
async def dado(ctx):
    numero = random.randint(1, 6)
    await ctx.send(f"🎲 Você tirou {numero}!")

@bot.command()
async def ajuda(ctx):
    await ctx.send("""
Comandos disponíveis:

!ping
!oi
!dado
!entrar
!tocar <url>
""")

bot.run(TOKEN)