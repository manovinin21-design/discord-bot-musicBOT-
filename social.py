import random

import discord
from discord.ext import commands

from config import KISS_GIFS, NAKANO_EMBEDS
from database import db
from utils import carregar_ships


class Social(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    @commands.command()
    async def ship(
        self, ctx: commands.Context,
        user1: discord.Member, user2: discord.Member
    ):
        if user1 == user2:
            await ctx.send("voce ta shippando voce com a sua propria mão?")
            return

        porcentagem = random.randint(0, 100)

        nome_ship = f"{user1.name} + {user2.name}"
        await db.registrar_ship(ctx.guild.id, nome_ship, porcentagem)

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
        ranking = await db.top_ships(ctx.guild.id)

        if not ranking:
            await ctx.send("💔 Ainda não existem ships neste servidor.")
            return

        mensagem = "💘 **Ranking dos Ships** 💘\n\n"
        for i, linha in enumerate(ranking, start=1):
            mensagem += f"{i}. {linha['nome']} — ❤️ {linha['porcentagem']}%\n"

        await ctx.send(mensagem)

    @commands.command()
    @commands.is_owner()
    async def importships(self, ctx: commands.Context):
        antigos = {
            nome: valor
            for nome, valor in carregar_ships().items()
            if isinstance(valor, int)
        }

        if not antigos:
            await ctx.send("📭 Não existem ships antigos para importar.")
            return

        importados = await db.importar_ships(ctx.guild.id, antigos)
        await ctx.send(
            f"✅ {importados} ship(s) antigos importados para "
            f"**{ctx.guild.name}**."
        )

    @commands.command()
    async def kiss(self, ctx: commands.Context, membro: discord.Member):
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
        await ctx.send(
            f"O USUARIO, {ctx.author.mention} ATIVOU O COMANDO SECRETO!"
            )
        escolhida = random.choice(NAKANO_EMBEDS)

        embed = discord.Embed(
            title=escolhida["titulo"],
            color=discord.Color.purple()
        )
        embed.set_image(url=escolhida["imagem"])

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Social(bot))
