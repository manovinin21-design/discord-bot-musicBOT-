"""Cog de moderação: punições, bloqueio de canais e advertências."""

import asyncio
from datetime import timedelta

import discord
from discord.ext import commands

from database import db


class Moderation(commands.Cog):
    """Comandos de moderação."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def mute(
        self, ctx: commands.Context, membro: discord.Member,
        minutos: int, *, motivo: str = "Nenhum motivo informado"
    ):
        """Silencia um usuário por X minutos."""
        if minutos < 1:
            await ctx.send("❌ Informe uma quantidade de minutos maior que 0.")
            return

        # Timeout do Discord tem limite de 28 dias
        if minutos > 40320:
            await ctx.send("❌ O tempo máximo de mute é 28 dias (40320 minutos).")
            return

        await membro.timeout(timedelta(minutes=minutos), reason=motivo)
        await ctx.send(
            f"🔇 {membro.mention} foi silenciado por {minutos} minuto(s).\n"
            f"Motivo: {motivo}"
        )

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx: commands.Context, membro: discord.Member):
        """Remove o silêncio de um usuário."""
        await membro.timeout(None)
        await ctx.send(f"🔊 {membro.mention} pode falar novamente.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx: commands.Context):
        """Bloqueia o canal de texto atual."""
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await ctx.channel.set_permissions(
            ctx.guild.default_role, overwrite=overwrite
        )
        await ctx.send("🔒 Canal bloqueado.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx: commands.Context):
        """Desbloqueia o canal de texto atual."""
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        await ctx.channel.set_permissions(
            ctx.guild.default_role, overwrite=overwrite
        )
        await ctx.send("🔓 Canal desbloqueado.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def lockall(self, ctx: commands.Context):
        """Bloqueia todos os canais de texto."""
        quantidade = 0
        for canal in ctx.guild.text_channels:
            overwrite = canal.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = False
            await canal.set_permissions(
                ctx.guild.default_role, overwrite=overwrite
            )
            quantidade += 1

        await ctx.send(f"🔒 {quantidade} canais foram bloqueados.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unlockall(self, ctx: commands.Context):
        """Desbloqueia todos os canais de texto."""
        quantidade = 0
        for canal in ctx.guild.text_channels:
            overwrite = canal.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = True
            await canal.set_permissions(
                ctx.guild.default_role, overwrite=overwrite
            )
            quantidade += 1

        await ctx.send(f"🔓 {quantidade} canais foram desbloqueados.")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(
        self, ctx: commands.Context, membro: discord.Member,
        *, motivo: str = "Nenhum motivo informado"
    ):
        """Bane um usuário."""
        if membro == ctx.author:
            await ctx.send("❌ Você não pode banir a si mesmo.")
            return

        await membro.ban(reason=motivo)
        await ctx.send(f"🔨 {membro.mention} foi banido.\nMotivo: {motivo}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, *, usuario: str):
        """Remove o banimento de um usuário (por ID ou nome)."""
        banidos = [entry async for entry in ctx.guild.bans()]

        for banido in banidos:
            user = banido.user
            # Aceita ID ou nome de usuário (Discord não usa mais nome#0000)
            if usuario in (str(user.id), user.name, str(user)):
                await ctx.guild.unban(user)
                await ctx.send(f"✅ {user} foi desbanido.")
                return

        await ctx.send("Usuário não encontrado na lista de banidos.")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(
        self, ctx: commands.Context, membro: discord.Member,
        *, motivo: str = "Nenhum motivo informado"
    ):
        """Expulsa um usuário."""
        if membro == ctx.author:
            await ctx.send("❌ Você não pode expulsar a si mesmo.")
            return

        await membro.kick(reason=motivo)
        await ctx.send(f"👢 {membro.mention} foi expulso.\nMotivo: {motivo}")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, quantidade: int):
        """Apaga mensagens do canal (máximo 100 por vez)."""
        if quantidade < 1:
            await ctx.send("Informe uma quantidade maior que 0.")
            return

        if quantidade > 100:
            await ctx.send("❌ O máximo é 100 mensagens por vez.")
            return

        await ctx.channel.purge(limit=quantidade + 1)

        msg = await ctx.send(f"🧹 {quantidade} mensagens apagadas.")
        await asyncio.sleep(3)
        await msg.delete()

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def warn(
        self, ctx: commands.Context, membro: discord.Member,
        *, motivo: str = "Nenhum motivo informado"
    ):
        """Dá uma advertência a um usuário."""
        if membro == ctx.author:
            await ctx.send("❌ Você não pode advertir a si mesmo.")
            return

        if membro == self.bot.user:
            await ctx.send("❌ Eu não posso receber advertências.")
            return

        if membro.guild_permissions.administrator:
            await ctx.send("❌ Você não pode advertir um administrador.")
            return

        if membro.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ Esse usuário possui um cargo igual ou superior ao seu.")
            return

        sucesso = await db.add_warning(
            membro.id, ctx.guild.id, ctx.author.id, motivo
        )
        if not sucesso:
            await ctx.send("❌ Erro ao salvar a advertência.")
            return

        quantidade = await db.get_warning_count(membro.id, ctx.guild.id)

        await ctx.send(
            f"""
⚠️ **Advertência aplicada!**

👤 Usuário: {membro.mention}
🛡️ Moderador: {ctx.author.mention}
📝 Motivo: {motivo}
📋 Total de advertências: **{quantidade}**
"""
        )

    @commands.command()
    async def warnings(self, ctx: commands.Context, membro: discord.Member):
        """Mostra as advertências de um usuário."""
        motivos = await db.get_warnings(membro.id, ctx.guild.id)

        if not motivos:
            await ctx.send("Esse usuário não possui advertências.")
            return

        texto = ""
        for i, motivo in enumerate(motivos, start=1):
            texto += f"{i}. {motivo}\n"

        await ctx.send(f"📋 Advertências de {membro.mention}\n\n{texto}")

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def clearwarns(self, ctx: commands.Context, membro: discord.Member):
        """Remove todas as advertências de um usuário."""
        sucesso = await db.clear_warnings(membro.id, ctx.guild.id)
        if sucesso:
            await ctx.send(f"🗑️ Advertências de {membro.mention} removidas.")
        else:
            await ctx.send("❌ Erro ao remover as advertências.")


async def setup(bot: commands.Bot):
    """Setup do cog Moderation."""
    await bot.add_cog(Moderation(bot))
