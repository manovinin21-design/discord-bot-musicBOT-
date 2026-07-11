import discord
import random
from discord.ext import commands
import yt_dlp
import asyncio
import json
import sqlite3
from dotenv import load_dotenv
from datetime import timedelta
import os

load_dotenv(dotenv_path="D:/musicBOT/.env")

print("Token encontrado:", os.getenv("DISCORD_TOKEN"))

TOKEN = os.getenv("DISCORD_TOKEN")

conexao = sqlite3.connect(
    "database.db",
    check_same_thread=False
)

cursor = conexao.cursor()

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

cursor.execute("""
CREATE TABLE IF NOT EXISTS warnings (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER,

    moderator_id INTEGER,

    motivo TEXT

)
""")

conexao.commit()

bot = commands.Bot(command_prefix="!", intents=intents)




ytdl_options = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "default_search": "ytsearch",
    "quiet": True,
    "nocheckcertificate": True,
    "ignoreerrors": True,
    "extract_flat": False
}

ffmpeg_options = {
    "options": "-vn",
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
}

ytdl = yt_dlp.YoutubeDL(ytdl_options)

filas = {}
ultima_musica = {}
warnings = {}




async def tocar_proxima(ctx):

    guild_id = ctx.guild.id

    if guild_id not in filas:
        filas[guild_id] = []

    if len(filas[guild_id]) == 0:
        return

    pesquisa = filas[guild_id].pop(0)
    ultima_musica[guild_id] = pesquisa

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
        print("a música terminou ou o player encerrou.")

        if erro:
            print("ERRO NO PLAYER:", erro)

        asyncio.run_coroutine_threadsafe(
            tocar_proxima(ctx),
            bot.loop
        )

    ctx.voice_client.play(source, after=depois)

    await ctx.send(f"🎶 Tocando: {info['title']}")




def carregar_ships():
    try:
        with open("ships.json", "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except:
        return {}


def salvar_ships(dados):
    with open("ships.json", "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=4, ensure_ascii=False)




@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user:
        print("Mudança no estado de voz:")
        print(before.channel, "->", after.channel)




@bot.command()
async def ship(ctx, user1: discord.Member, user2: discord.Member):
    import random

    porcentagem = random.randint(0, 100)

    ships = carregar_ships()

    nome_ship = f"{user1.name} + {user2.name}"

    ships[nome_ship] = porcentagem

    salvar_ships(ships)
    
    if user1 == user2:
        await ctx.send("voce ta shippando voce com a sua propria mão?")
        return 

    if porcentagem >= 90:
        mensagem = "💖 Casal perfeito! Já podem ir pra cama!"
    elif porcentagem >= 70:
        mensagem = "💕 Uma Breja e um Halls preto..."
    elif porcentagem >= 40:
        mensagem = "💛 ficou confusa e te largou as 3 da manhã"
    elif porcentagem >= 20:
        mensagem = "💔 nunca vai acontecer e voce ainda virou print no grupo das amigas"
    else:
        mensagem = "💀 nem estrupo resolve"

    embed = discord.Embed(
        title="💘 Calculadora de Ship",
        description=f"{user1.mention} + {user2.mention}",
        color=discord.Color.pink()
    )

    embed.add_field(
        name="Compatibilidade",
        value=f"❤️ {porcentagem}%\n\n{mensagem}",
        inline=False
    )

    await ctx.send(embed=embed)

@bot.command()
async def topships(ctx):
    ships = carregar_ships()

    if not ships:
        await ctx.send("💔 Ainda não existem ships registrados.")
        return

    ranking = sorted(
        ships.items(),
        key=lambda x: x[1],
        reverse=True
    )

    mensagem = "💘 **Ranking dos Ships** 💘\n\n"

    for i, (casal, porcentagem) in enumerate(ranking[:10], start=1):
        mensagem += f"{i}. {casal} — ❤️ {porcentagem}%\n"

    await ctx.send(mensagem)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, membro: discord.Member, minutos: int, *, motivo="Nenhum motivo informado"):

    await membro.timeout(
        timedelta(minutes=minutos),
        reason=motivo
    )

    await ctx.send(
        f"🔇 {membro.mention} foi silenciado por {minutos} minuto(s).\nMotivo: {motivo}"
    )

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, membro: discord.Member):

    await membro.timeout(None)

    await ctx.send(
        f"🔊 {membro.mention} pode falar novamente."
    )

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):

    canal = ctx.channel

    overwrite = canal.overwrites_for(ctx.guild.default_role)

    overwrite.send_messages = False

    await canal.set_permissions(
        ctx.guild.default_role,
        overwrite=overwrite
    )

    await ctx.send("Canal bloqueado.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):

    canal = ctx.channel

    overwrite = canal.overwrites_for(ctx.guild.default_role)

    overwrite.send_messages = True

    await canal.set_permissions(
        ctx.guild.default_role,
        overwrite=overwrite
    )

    await ctx.send("Canal desbloqueado.")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, membro: discord.Member, *, motivo="Nenhum motivo informado"):

    await membro.ban(reason=motivo)

    await ctx.send(
        f"🔨 {membro.mention} foi banido.\nMotivo: {motivo}"
    )

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, membro: discord.Member, *, motivo="Nenhum motivo informado"):

    await membro.kick(reason=motivo)

    await ctx.send(
        f"👢 {membro.mention} foi expulso.\nMotivo: {motivo}"
    )

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, quantidade: int):

    if quantidade < 1:
        await ctx.send("Informe uma quantidade maior que 0.")
        return

    await ctx.channel.purge(limit=quantidade + 1)

    msg = await ctx.send(f"🧹 {quantidade} mensagens apagadas.")
    await asyncio.sleep(3)
    await msg.delete()

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, usuario):

    banidos = [entry async for entry in ctx.guild.bans()]

    nome, discriminador = usuario.split("#")

    for banido in banidos:

        user = banido.user

        if user.name == nome and user.discriminator == discriminador:

            await ctx.guild.unban(user)

            await ctx.send(f"✅ {user} foi desbanido.")

            return

    await ctx.send("Usuário não encontrado na lista de banidos.")


@bot.command()
@commands.has_permissions(moderate_members=True)
async def warn(ctx, membro: discord.Member, *, motivo):

    # Não pode advertir a si mesmo
    if membro == ctx.author:
        await ctx.send("❌ Você não pode advertir a si mesmo.")
        return

    # Não pode advertir o bot
    if membro == bot.user:
        await ctx.send("❌ Eu não posso receber advertências.")
        return

    # Não pode advertir administradores
    if membro.guild_permissions.administrator:
        await ctx.send("❌ Você não pode advertir um administrador.")
        return

    # Não pode advertir alguém com cargo igual ou superior
    if membro.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
        await ctx.send("❌ Esse usuário possui um cargo igual ou superior ao seu.")
        return

    # Salva a advertência no banco
    cursor.execute(
        """
        INSERT INTO warnings (user_id, moderator_id, motivo)
        VALUES (?, ?, ?)
        """,
        (
            membro.id,
            ctx.author.id,
            motivo
        )
    )

    conexao.commit()

    # Conta quantas advertências o usuário possui
    cursor.execute(
        "SELECT COUNT(*) FROM warnings WHERE user_id=?",
        (membro.id,)
    )

    quantidade = cursor.fetchone()[0]

    # Envia a mensagem
    await ctx.send(
        f"""
⚠️ **Advertência aplicada!**

👤 Usuário: {membro.mention}
🛡️ Moderador: {ctx.author.mention}
📝 Motivo: {motivo}
📋 Total de advertências: **{quantidade}**
"""
    )


@bot.command()
async def warnings(ctx, membro: discord.Member):

    cursor.execute(

        "SELECT motivo FROM warnings WHERE user_id=?",

        (membro.id,)

    )

    resultados = cursor.fetchall()

    if len(resultados) == 0:

        await ctx.send(
            "Esse usuário não possui advertências."
        )

        return

    texto = ""

    for i, warn in enumerate(resultados, start=1):

        texto += f"{i}. {warn[0]}\n"

    await ctx.send(
        f"📋 Advertências de {membro.mention}\n\n{texto}"
    )

@bot.command()
@commands.has_permissions(moderate_members=True)
async def clearwarns(ctx, membro: discord.Member):

    cursor.execute(

        "DELETE FROM warnings WHERE user_id=?",

        (membro.id,)

    )

    conexao.commit()

    await ctx.send(
        f"🗑️ Advertências removidas."
    )

@bot.command()
@commands.has_permissions(administrator=True)
async def lockall(ctx):

    quantidade = 0

    for canal in ctx.guild.text_channels:

        overwrite = canal.overwrites_for(ctx.guild.default_role)

        overwrite.send_messages = False

        await canal.set_permissions(
            ctx.guild.default_role,
            overwrite=overwrite
        )

        quantidade += 1

    await ctx.send(
        f"🔒 {quantidade} canais foram bloqueados."
    )

@bot.command()
@commands.has_permissions(administrator=True)
async def unlockall(ctx):

    quantidade = 0

    for canal in ctx.guild.text_channels:

        overwrite = canal.overwrites_for(ctx.guild.default_role)

        overwrite.send_messages = True

        await canal.set_permissions(
            ctx.guild.default_role,
            overwrite=overwrite
        )

        quantidade += 1

    await ctx.send(
        f"🔓 {quantidade} canais foram desbloqueados."
    )

@bot.command()
async def entrar(ctx):

    if ctx.voice_client:
        await ctx.send("Já estou conectado.")
        return

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
async def replay(ctx):

    guild_id = ctx.guild.id

    if guild_id not in ultima_musica:
        await ctx.send("❌ Não existe nenhuma música anterior para repetir.")
        return

    musica = ultima_musica[guild_id]

    if guild_id not in filas:
        filas[guild_id] = []

    filas[guild_id].insert(0, musica)

    if ctx.voice_client.is_playing():
        await ctx.send(f"🔁 Adicionei novamente: **{musica}**")
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
async def voce_tem_relação_com_o_11_de_setembro(ctx):
    await ctx.send(f"O USUARIO, {ctx.author.mention}ATIVOU O COMANDO SECRETO!")
    await ctx.send("a resposta é: É: SIM, EU SOU RELACIONADO COM O 11 DE SETEMBRO")




@bot.command()
async def ajuda(ctx):
    await ctx.send("""
Comandos disponíveis:
!ajuda / mostra os comandos disponíveis
                   
Comandos de interação:
!ping / responde com "Pong! 🏓"
!oi / diz olá
!dado / rola um dado
!ship <usuário1> <usuário2> / calcula a compatibilidade entre dois usuários
!topships / mostra o ranking dos ships mais altos

Comandos de música:
!entrar / entra no canal de voz
!tocar <pesquisa> / toca uma música
!fim / finaliza a música atual
!sair / sai do canal de voz
!continuar / retoma a música pausada
!pausar / pausa a música em execução
!encerrar / limpa a fila de músicas
!replay / repete a última música tocada

Comandos de moderação:
!mute <usuário> <minutos> [motivo] / silencia um usuário
!unmute <usuário> / remove o silêncio de um usuário
!lock / bloqueia o canal de texto
!unlock / desbloqueia o canal de texto
!ban <usuário> [motivo] / bane um usuário
!unban <usuário> / remove o banimento de um usuário
!kick <usuário> [motivo] / expulsa um usuário
!clear <quantidade> / apaga mensagens
!warn <usuário> [motivo] / dá uma advertência a um usuário
!warnings <usuário> / mostra as advertências de um usuário
!lockall / bloqueia todos os canais de texto
!unlockall / desbloqueia todos os canais de texto
!clearwarns <usuário> / remove todas as advertências de um usuário
""")

@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Você não possui permissão para usar esse comando.")

    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Usuário não encontrado.")

    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Faltam argumentos no comando.")

    else:
        raise error 

bot.run(TOKEN)