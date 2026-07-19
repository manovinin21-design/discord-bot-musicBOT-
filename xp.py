"""Cog de XP: ganho por mensagem, rank e leaderboard."""

import random
import time

import discord
from discord.ext import commands

from config import COOLDOWN_XP_SECONDS, XP_GAIN_MIN, XP_GAIN_MAX
from database import db


def xp_para_proximo_nivel(level: int) -> int:
    """XP necessário para subir do nível atual para o próximo."""
    return level * 100


class XP(commands.Cog):
    """Sistema de XP e níveis."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ultimo_ganho = {}  # (user_id, guild_id) -> timestamp

    async def cog_check(self, ctx: commands.Context) -> bool:
        """XP é separado por servidor: os comandos precisam de um guild_id."""
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Dá XP por mensagem, respeitando o cooldown."""
        if message.author.bot or message.guild is None:
            return

        # Mensagens que são comandos não dão XP
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        chave = (message.author.id, message.guild.id)
        agora = time.time()

        if agora - self.ultimo_ganho.get(chave, 0) < COOLDOWN_XP_SECONDS:
            return

        self.ultimo_ganho[chave] = agora

        dados = await db.get_user_xp(message.author.id, message.guild.id)
        if dados:
            xp, level = dados["xp"], dados["level"]
        else:
            xp, level = 0, 1

        xp += random.randint(XP_GAIN_MIN, XP_GAIN_MAX)

        subiu_de_nivel = False
        while xp >= xp_para_proximo_nivel(level):
            xp -= xp_para_proximo_nivel(level)
            level += 1
            subiu_de_nivel = True

        await db.set_user_xp(message.author.id, message.guild.id, xp, level)

        if subiu_de_nivel:
            try:
                await message.channel.send(
                    f"🎉 {message.author.mention} subiu para o nível **{level}**!"
                )
            except discord.HTTPException:
                pass  # sem permissão de falar no canal — o XP já foi salvo

    @commands.command()
    async def rank(
        self, ctx: commands.Context, membro: discord.Member = None
    ):
        """Mostra o rank de XP de um usuário."""
        membro = membro or ctx.author

        dados = await db.get_user_xp(membro.id, ctx.guild.id)
        if not dados:
            await ctx.send(f"{membro.mention} ainda não possui XP.")
            return

        xp, level = dados["xp"], dados["level"]
        proximo = xp_para_proximo_nivel(level)

        embed = discord.Embed(
            title=f"📊 Rank de {membro.display_name}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Nível", value=str(level), inline=True)
        embed.add_field(name="XP", value=f"{xp}/{proximo}", inline=True)
        embed.set_thumbnail(url=membro.display_avatar.url)

        await ctx.send(embed=embed)

    @commands.command(aliases=["lb", "top"])
    async def leaderboard(self, ctx: commands.Context):
        """Mostra o ranking de XP do servidor."""
        ranking = await db.get_leaderboard(ctx.guild.id)

        if not ranking:
            await ctx.send("Ainda não existe ninguém no ranking.")
            return

        texto = ""
        medalhas = ["🥇", "🥈", "🥉"]

        for i, linha in enumerate(ranking, start=1):
            user_id, level, xp = linha["user_id"], linha["level"], linha["xp"]
            membro = ctx.guild.get_member(user_id)
            nome = membro.display_name if membro else f"Usuário {user_id}"
            posicao = medalhas[i - 1] if i <= 3 else f"{i}."
            texto += f"{posicao} **{nome}** — Nível {level} ({xp} XP)\n"

        embed = discord.Embed(
            title=f"🏆 Ranking de XP — {ctx.guild.name}",
            description=texto,
            color=discord.Color.gold()
        )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addxp(
        self, ctx: commands.Context, membro: discord.Member, quantidade: int
    ):
        """Adiciona XP a um usuário."""
        if quantidade < 1:
            await ctx.send("❌ Informe uma quantidade maior que 0.")
            return

        dados = await db.get_user_xp(membro.id, ctx.guild.id)
        if dados:
            xp, level = dados["xp"], dados["level"]
        else:
            xp, level = 0, 1

        xp += quantidade
        while xp >= xp_para_proximo_nivel(level):
            xp -= xp_para_proximo_nivel(level)
            level += 1

        await db.set_user_xp(membro.id, ctx.guild.id, xp, level)
        await ctx.send(
            f"✅ {quantidade} XP adicionado a {membro.mention}. "
            f"(Nível {level}, {xp} XP)"
        )

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removexp(
        self, ctx: commands.Context, membro: discord.Member, quantidade: int
    ):
        """Remove XP de um usuário."""
        if quantidade < 1:
            await ctx.send("❌ Informe uma quantidade maior que 0.")
            return

        dados = await db.get_user_xp(membro.id, ctx.guild.id)
        if not dados:
            await ctx.send(f"{membro.mention} ainda não possui XP.")
            return

        xp, level = dados["xp"], dados["level"]
        xp -= quantidade

        # Desce de nível se o XP ficar negativo
        while xp < 0 and level > 1:
            level -= 1
            xp += xp_para_proximo_nivel(level)

        xp = max(xp, 0)

        await db.set_user_xp(membro.id, ctx.guild.id, xp, level)
        await ctx.send(
            f"✅ {quantidade} XP removido de {membro.mention}. "
            f"(Nível {level}, {xp} XP)"
        )


async def setup(bot: commands.Bot):
    """Setup do cog XP."""
    await bot.add_cog(XP(bot))
