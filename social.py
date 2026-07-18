"""Cog social: ships, kiss e as Nakano."""

import random

import discord
from discord.ext import commands

from config import KISS_GIFS, NAKANO_EMBEDS
from utils import (
    carregar_ships,
    salvar_ships,
    ships_do_servidor,
    registrar_ship,
)


class Social(commands.Cog):
    """Comandos de interação social."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:
        """Ships e afins são separados por servidor: precisam de um guild_id."""
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    @commands.command()
    async def ship(
        self, ctx: commands.Context,
        user1: discord.Member, user2: discord.Member
    ):
        """Calcula a compatibilidade entre dois usuários."""
        if user1 == user2:
            await ctx.send("voce ta shippando voce com a sua propria mão?")
            return

        porcentagem = random.randint(0, 100)

        ships = carregar_ships()
        nome_ship = f"{user1.name} + {user2.name}"
        registrar_ship(ships, ctx.guild.id, nome_ship, porcentagem)
        salvar_ships(ships)

        if porcentagem >= 90:
            mensagem = "💖 Casal perfeito! Já podem ir pra cama!"
        elif porcentagem >= 70:
            mensagem = "💕 Uma Breja e um Halls preto..."
        elif porcentagem >= 40:
            mensagem = "💛 ficou confusa e te largou as 3 da manhã"
        elif porcentagem >= 20:
            mensagem = "💔 nunca vai acontecer e voce ainda virou print no grupo das amigas"
        else:
            mensagem = "💀 nem macumba resolve"

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

    @commands.command()
    async def topships(self, ctx: commands.Context):
        """Mostra o ranking dos ships mais altos."""
        ships = ships_do_servidor(carregar_ships(), ctx.guild.id)

        if not ships:
            await ctx.send("💔 Ainda não existem ships registrados.")
            return

        ranking = sorted(ships.items(), key=lambda x: x[1], reverse=True)

        mensagem = "💘 **Ranking dos Ships** 💘\n\n"
        for i, (casal, porcentagem) in enumerate(ranking[:10], start=1):
            mensagem += f"{i}. {casal} — ❤️ {porcentagem}%\n"

        await ctx.send(mensagem)

    @commands.command()
    async def kiss(self, ctx: commands.Context, membro: discord.Member):
        """Beija um usuário."""
        if membro == ctx.author:
            await ctx.send("beijando o espelho? tá tudo bem em casa?")
            return

        gif = random.choice(KISS_GIFS)

        embed = discord.Embed(
            description=f"💋 {ctx.author.mention} beijou {membro.mention}!",
            color=discord.Color.red()
        )
        embed.set_image(url=gif)

        await ctx.send(embed=embed)

    @commands.command()
    async def nakano(self, ctx: commands.Context):
        """Sorteia uma das quíntuplas."""
        escolhida = random.choice(NAKANO_EMBEDS)

        embed = discord.Embed(
            title=escolhida["titulo"],
            color=discord.Color.purple()
        )
        embed.set_image(url=escolhida["imagem"])

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    """Setup do cog Social."""
    await bot.add_cog(Social(bot))
