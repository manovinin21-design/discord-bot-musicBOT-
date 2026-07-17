"""Administrative commands cog."""

import discord
from discord.ext import commands


class Admin(commands.Cog):
    """Administrative commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="a")
    @commands.is_owner()
    async def anunciar(self, ctx: commands.Context, *, mensagem: str):
        """Envia um anúncio para todos os servidores do bot (só o dono)."""
        embed = discord.Embed(
            title="📢 Anúncio",
            description=mensagem,
            color=discord.Color.orange()
        )
        embed.set_footer(
            text=f"Enviado por {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )

        enviados = 0
        falhas = 0

        for guild in self.bot.guilds:
            canal = self.escolher_canal(guild)

            if canal is None:
                falhas += 1
                continue

            try:
                await canal.send(embed=embed)
                enviados += 1
            except discord.HTTPException as e:
                print(f"❌ Falha ao anunciar em {guild.name}: {e}")
                falhas += 1

        await ctx.send(
            f"📢 Anúncio enviado para **{enviados}** servidor(es)."
            + (f" Falhou em **{falhas}**." if falhas else "")
        )

    @staticmethod
    def escolher_canal(guild: discord.Guild):
        """Escolhe o melhor canal para o anúncio em um servidor.

        Preferência: canal de sistema (o das mensagens de boas-vindas);
        senão, o primeiro canal de texto onde o bot pode falar.
        """
        canal = guild.system_channel
        if canal and canal.permissions_for(guild.me).send_messages:
            return canal

        for canal in guild.text_channels:
            if canal.permissions_for(guild.me).send_messages:
                return canal

        return None

    @commands.command()
    async def ajuda(self, ctx: commands.Context):
        """Show help message."""
        await ctx.send("""
Comandos disponíveis:
!ajuda / mostra os comandos disponíveis
    
Comandos de interação:
!ping / responde com "Pong! 🏓"
!oi / diz olá
!dado / rola um dado
!ship <usuário1> <usuário2> / calcula a compatibilidade entre dois usuários
!topships / mostra o ranking dos ships mais altos
!kiss <usuário> / beija um usuário
!rank [usuário] / mostra o rank de XP de um usuário
!leaderboard / mostra o ranking de XP do servidor

Comandos de música:
!entrar / entra no canal de voz
!tocar <pesquisa> / toca uma música
!fim / finaliza a música atual
!sair / sai do canal de voz
!continuar / retoma a música pausada
!pausar / pausa a música em execução
!encerrar / limpa a fila de músicas
!fila / mostra as músicas na fila
!removerdafila <número> / remove uma música da fila
!mover <de> <para> / move uma música de posição na fila
!replay / repete a última música tocada
!duração / mostra a duração da música atual
!skip / vai pra proxima musica da fila

Comandos de moderação:
!mute <usuário> <minutos> [motivo] / silencia um usuário
!unmute <usuário> / remove o silêncio de um usuário
!lock / bloqueia o canal de texto
!unlock / desbloqueia o canal de texto
!ban <usuário> [motivo] / bane um usuário
!unban <usuário> / remove o banimento de um usuário (ID ou nome)
!kick <usuário> [motivo] / expulsa um usuário
!clear <quantidade> / apaga mensagens
!warn <usuário> [motivo] / dá uma advertência a um usuário
!warnings <usuário> / mostra as advertências de um usuário
!lockall / bloqueia todos os canais de texto
!unlockall / desbloqueia todos os canais de texto
!clearwarns <usuário> / remove todas as advertências de um usuário
!addxp <usuário> <quantidade> / adiciona XP a um usuário
!removexp <usuário> <quantidade> / remove XP de um usuário
""")


async def setup(bot: commands.Bot):
    """Setup the Admin cog."""
    await bot.add_cog(Admin(bot))
