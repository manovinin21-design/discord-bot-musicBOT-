"""Cog de diversão: comandos simples e o comando secreto."""

import random

from discord.ext import commands


class Fun(commands.Cog):
    """Comandos de diversão."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """Responde com Pong e a latência."""
        latencia = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! 🏓 ({latencia}ms)")

    @commands.command()
    async def oi(self, ctx: commands.Context):
        """Diz olá."""
        await ctx.send(f"Olá, {ctx.author.mention}! 👋")

    @commands.command()
    async def dado(self, ctx: commands.Context):
        """Rola um dado de 6 lados."""
        numero = random.randint(1, 6)
        await ctx.send(f"🎲 Você tirou {numero}!")

    @commands.command()
    async def voce_tem_relação_com_o_11_de_setembro(self, ctx: commands.Context):
        """Comando secreto."""
        await ctx.send(
            f"O USUARIO, {ctx.author.mention} ATIVOU O COMANDO SECRETO!"
        )
        await ctx.send(
            "a resposta é: É: SIM, EU SOU RELACIONADO COM O 11 DE SETEMBRO"
        )


async def setup(bot: commands.Bot):
    """Setup do cog Fun."""
    await bot.add_cog(Fun(bot))
