"""Cog de eventos: mensagens automáticas de boas-vindas, saída e boost.

As mensagens só funcionam depois de ativadas com !addmsgin, !addmsgout e
!addmsgboost — cada servidor escolhe (ou não) os seus canais.
"""

import discord
from discord.ext import commands

from database import db

COR_ENTRADA = discord.Color.green()
COR_SAIDA = discord.Color.dark_grey()
COR_BOOST = discord.Color.fuchsia()

NOMES_TIPO = {
    "entrada": "boas-vindas",
    "saida": "saída",
    "boost": "boost",
}

COMANDOS_DESATIVAR = {
    "entrada": "!delmsgin",
    "saida": "!delmsgout",
    "boost": "!delmsgboost",
}


class Eventos(commands.Cog):
    """Mensagens automáticas do servidor."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:
        """A configuração das mensagens é por servidor: precisa de um guild_id."""
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def canal_configurado(self, guild: discord.Guild, tipo: str):
        """Retorna o canal configurado para um tipo de mensagem, se utilizável."""
        canal_id = await db.get_canal_mensagem(guild.id, tipo)
        if not canal_id:
            return None

        canal = guild.get_channel(canal_id)
        if canal and canal.permissions_for(guild.me).send_messages:
            return canal
        return None

    async def ativar(
        self, ctx: commands.Context, tipo: str, canal: discord.TextChannel
    ):
        """Ativa um tipo de mensagem automática no canal informado."""
        if not canal.permissions_for(ctx.guild.me).send_messages:
            await ctx.send(
                f"❌ Eu não tenho permissão para enviar mensagens em "
                f"{canal.mention}."
            )
            return

        if not await db.set_canal_mensagem(ctx.guild.id, tipo, canal.id):
            await ctx.send("❌ Não consegui salvar a configuração. Tente de novo.")
            return

        embed = discord.Embed(
            title="✅ Mensagens ativadas",
            description=(
                f"As mensagens de **{NOMES_TIPO[tipo]}** serão enviadas em "
                f"{canal.mention}."
            ),
            color=discord.Color.green()
        )
        embed.set_footer(
            text=f"Para desativar, use {COMANDOS_DESATIVAR[tipo]}"
        )
        await ctx.send(embed=embed)

    async def desativar(self, ctx: commands.Context, tipo: str):
        """Desativa um tipo de mensagem automática."""
        if await db.remover_canal_mensagem(ctx.guild.id, tipo):
            await ctx.send(
                f"🗑️ Mensagens de **{NOMES_TIPO[tipo]}** desativadas."
            )
        else:
            await ctx.send(
                f"❌ As mensagens de **{NOMES_TIPO[tipo]}** não estavam ativadas."
            )

    # ------------------------------------------------------------------
    # Comandos de configuração
    # ------------------------------------------------------------------

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def addmsgin(
        self, ctx: commands.Context, canal: discord.TextChannel
    ):
        """Ativa as mensagens de boas-vindas no canal informado."""
        await self.ativar(ctx, "entrada", canal)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def addmsgout(
        self, ctx: commands.Context, canal: discord.TextChannel
    ):
        """Ativa as mensagens de saída no canal informado."""
        await self.ativar(ctx, "saida", canal)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def addmsgboost(
        self, ctx: commands.Context, canal: discord.TextChannel
    ):
        """Ativa as mensagens de boost no canal informado."""
        await self.ativar(ctx, "boost", canal)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def delmsgin(self, ctx: commands.Context):
        """Desativa as mensagens de boas-vindas."""
        await self.desativar(ctx, "entrada")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def delmsgout(self, ctx: commands.Context):
        """Desativa as mensagens de saída."""
        await self.desativar(ctx, "saida")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def delmsgboost(self, ctx: commands.Context):
        """Desativa as mensagens de boost."""
        await self.desativar(ctx, "boost")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def msgconfig(self, ctx: commands.Context):
        """Mostra os canais configurados para as mensagens automáticas."""
        embed = discord.Embed(
            title="⚙️ Mensagens automáticas",
            description="Configuração atual deste servidor:",
            color=discord.Color.blurple()
        )

        emojis = {"entrada": "👋", "saida": "😢", "boost": "🚀"}

        for tipo, nome in NOMES_TIPO.items():
            canal_id = await db.get_canal_mensagem(ctx.guild.id, tipo)
            canal = ctx.guild.get_channel(canal_id) if canal_id else None
            valor = canal.mention if canal else "❌ desativadas"
            embed.add_field(
                name=f"{emojis[tipo]} Mensagens de {nome}",
                value=valor,
                inline=False
            )

        embed.set_footer(
            text="Use !addmsgin, !addmsgout e !addmsgboost para ativar."
        )
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Envia a mensagem de boas-vindas, se ativada."""
        canal = await self.canal_configurado(member.guild, "entrada")
        if not canal:
            return

        embed = discord.Embed(
            title="👋 Boas-vindas!",
            description=(
                f"{member.mention} acabou de chegar em "
                f"**{member.guild.name}**!\n"
                "Sinta-se em casa e aproveite a resenha 🎉"
            ),
            color=COR_ENTRADA
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(
            text=f"Agora somos {member.guild.member_count} membros!"
        )

        try:
            await canal.send(embed=embed)
        except discord.HTTPException as e:
            print(f"❌ Falha ao enviar boas-vindas em {member.guild.name}: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Envia a mensagem de saída, se ativada."""
        canal = await self.canal_configurado(member.guild, "saida")
        if not canal:
            return

        embed = discord.Embed(
            title="😢 Até mais...",
            description=(
                f"**{member.display_name}** saiu do servidor.\n"
                "Esperamos te ver de novo por aqui! 👋"
            ),
            color=COR_SAIDA
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(
            text=f"Agora somos {member.guild.member_count} membros."
        )

        try:
            await canal.send(embed=embed)
        except discord.HTTPException as e:
            print(f"❌ Falha ao enviar saída em {member.guild.name}: {e}")

    @commands.Cog.listener()
    async def on_member_update(
        self, before: discord.Member, after: discord.Member
    ):
        """Detecta um boost novo e envia a mensagem, se ativada."""
        if before.premium_since is not None or after.premium_since is None:
            return

        canal = await self.canal_configurado(after.guild, "boost")
        if not canal:
            return

        total = after.guild.premium_subscription_count
        embed = discord.Embed(
            title="🚀 Boost recebido!",
            description=(
                f"{after.mention} acabou de dar boost em "
                f"**{after.guild.name}**! 💜\n"
                "Muito obrigado pelo apoio!"
            ),
            color=COR_BOOST
        )
        embed.set_thumbnail(url=after.display_avatar.url)
        embed.set_footer(
            text=f"O servidor tem {total} boost(s) no total!"
        )

        try:
            await canal.send(embed=embed)
        except discord.HTTPException as e:
            print(f"❌ Falha ao enviar boost em {after.guild.name}: {e}")


async def setup(bot: commands.Bot):
    """Setup do cog Eventos."""
    await bot.add_cog(Eventos(bot))
