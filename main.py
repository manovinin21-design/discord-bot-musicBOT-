"""Main entry point for the Discord bot."""

import sys

# O console do Windows usa cp1252 por padrão e quebra ao imprimir emojis
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import discord
import asyncio
from discord.ext import commands
from config import TOKEN
from database import db

# Setup bot
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True  # necessário para as mensagens de entrada/saída/boost

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    """Bot ready event."""
    print(f"✅ Bot conectado como {bot.user}")


@bot.event
async def on_voice_state_update(
    member: discord.Member,
    before: discord.VoiceState,
    after: discord.VoiceState
):
    """Voice state update handler."""
    if member == bot.user:
        print(f"Mudança no estado de voz: {before.channel} -> {after.channel}")


@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    """Global error handler."""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Você não possui permissão para usar esse comando.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Usuário não encontrado.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Faltam argumentos no comando.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Argumento inválido. Confira o comando no !ajuda.")
    elif isinstance(error, commands.NotOwner):
        await ctx.send("❌ Apenas o dono do bot pode usar esse comando.")
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send("❌ Esse comando só funciona dentro de um servidor.")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Silently ignore unknown commands
    else:
        print(f"❌ Error in command {ctx.command}: {error}")
        raise error


COGS = ["admin", "eventos", "fun", "moderation", "music", "social", "xp"]


async def load_cogs():
    """Load all cogs."""
    for cog_name in COGS:
        try:
            await bot.load_extension(cog_name)
            print(f"✅ Carregado cog: {cog_name}")
        except Exception as e:
            print(f"❌ Erro ao carregar {cog_name}: {e}")


async def main():
    """Main entry point."""
    if not TOKEN:
        print("❌ DISCORD_TOKEN não encontrado no .env")
        return

    async with bot:
        await load_cogs()
        try:
            await bot.start(TOKEN)
        except KeyboardInterrupt:
            print("\n⏸️  Bot interrompido pelo usuário")
        finally:
            db.close()
            print("🗑️  Banco de dados fechado")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Encerrando...")
