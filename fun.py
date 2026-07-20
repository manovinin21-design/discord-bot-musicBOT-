import random

from discord.ext import commands


class Fun(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context):
        latencia = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! 🏓 ({latencia}ms)")

    @commands.command()
    async def oi(self, ctx: commands.Context):
        await ctx.send(f"Olá, {ctx.author.mention}! 👋")

    @commands.command()
    async def dado(self, ctx: commands.Context):
        numero = random.randint(1, 6)
        await ctx.send(f"🎲 Você tirou {numero}!")

    @commands.command()
    async def voce_tem_relação_com_o_11_de_setembro(self, ctx: commands.Context):
        await ctx.send(
            f"O USUARIO, {ctx.author.mention} ATIVOU O COMANDO SECRETO!"
        )
        await ctx.send(
            "a resposta é: É: SIM, EU SOU RELACIONADO COM O 11 DE SETEMBRO"
        )

    @commands.command()
    async def para(self, ctx: commands.Context):
        await ctx.send(
            f"O USUARIO, {ctx.author.mention} ATIVOU O COMANDO SECRETO!"
        )
        await ctx.send(
            "oque é que voce disse cara?🥵"
        )

    @commands.command()
    async def continua(self, ctx: commands.Context):
        await ctx.send(
            f"O USUARIO {ctx.author.mention} ATIVOU O COMANDO SECRETO!"
        )
        await ctx.send(
            "eu não estou te escutando 🥵"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
