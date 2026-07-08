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
    "format": "bestaudio/best",
    "noplaylist": True,
    "default_search": "ytsearch",
    "quiet": True
}

ffmpeg_options = {
    "options": "-vn"
}

ytdl = yt_dlp.YoutubeDL(ytdl_options)

filas = {}

async def tocar_proxima(ctx):

    guild_id = ctx.guild.id

    if guild_id not in filas:
        filas[guild_id] = []

    if len(filas[guild_id]) == 0:
        return

    pesquisa = filas[guild_id].pop(0)

    info = await asyncio.to_thread(
        ytdl.extract_info,
        pesquisa,
        download=False
    )

    if "entries" in info:
        info = info["entries"][0]

    audio = info["url"]

    source = discord.FFmpegPCMAudio(
        audio,
        **ffmpeg_options
    )

    def depois(erro):
        if erro:
            print(erro)

        asyncio.run_coroutine_threadsafe(
            tocar_proxima(ctx),
            bot.loop
        )

    ctx.voice_client.play(source, after=depois)

    await ctx.send(f"🎶 Tocando: {info['title']}")

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
async def tocar(ctx, *, pesquisa):

    if not ctx.voice_client:
        await ctx.invoke(entrar)

    guild_id = ctx.guild.id

    if guild_id not in filas:
        filas[guild_id] = []

    filas[guild_id].append(pesquisa)

    if ctx.voice_client.is_playing():

        await ctx.send(
            f"✅ Música adicionada à fila.\nPosição: {len(filas[guild_id])}"
        )

    else:

        await tocar_proxima(ctx)

@bot.command()
async def oi(ctx):
    await ctx.send(f"Olá, {ctx.author.mention}! 👋")

@bot.command()
async def dado(ctx):
    numero = random.randint(1, 6)
    await ctx.send(f"🎲 Você tirou {numero}!")

@bot.command()
async def pausar(ctx):

    if not ctx.voice_client:
        await ctx.send("Não estou em um canal de voz.")
        return

    if ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Música pausada.")
    else:
        await ctx.send("Não há nenhuma música tocando.")

@bot.command()
async def encerrar(ctx):

    guild_id = ctx.guild.id

    if guild_id in filas:
        filas[guild_id].clear()

    if not ctx.voice_client:
        await ctx.send("Não estou em um canal de voz.")
        return

    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("fila limpa.")
    else:
        await ctx.send("Não há nenhuma música tocando.")

@bot.command()
async def continuar(ctx):

    if not ctx.voice_client:
        await ctx.send("Não estou em um canal de voz.")
        return

    if ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Música retomada.")
    else:
        await ctx.send("Nenhuma música está pausada.")

@bot.command()
async def fim(ctx):

    if not ctx.voice_client:
        await ctx.send("Não estou em um canal de voz.")
        return

    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Música finalizada.")
    else:
        await ctx.send("Não há nenhuma música tocando.")

@bot.command()
async def sair(ctx):

    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Saí do canal de voz.")
    else:
        await ctx.send("Não estou em um canal de voz.")

@bot.command()
async def ajuda(ctx):
    await ctx.send("""
Comandos disponíveis:

!ping / responde com "Pong! 🏓"
!oi / diz olá
!dado / rola um dado
!entrar / entra no canal de voz
!tocar <pesquisa> / toca uma música
!fim / finaliza a música atual
!sair / sai do canal de voz
!ajuda / mostra os comandos disponíveis
!continuar / retoma a música pausada
!pausar / pausa a música em execução
!encerrar / limpa a fila de músicas
""")

bot.run(TOKEN)