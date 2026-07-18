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

    @commands.command(name="servidores")
    @commands.is_owner()
    async def servidores(self, ctx: commands.Context):
        """Lista os servidores em que o bot está (só o dono)."""
        guilds = sorted(
            self.bot.guilds,
            key=lambda g: g.member_count or 0,
            reverse=True
        )

        embed = discord.Embed(
            title="🌐 Servidores",
            description=f"Estou em **{len(guilds)}** servidor(es):",
            color=discord.Color.blurple()
        )

        for guild in guilds[:25]:
            embed.add_field(
                name=guild.name,
                value=f"👥 {guild.member_count} membros\n🆔 `{guild.id}`",
                inline=True
            )

        if len(guilds) > 25:
            embed.set_footer(
                text=f"Mostrando 25 de {len(guilds)} servidores."
            )

        await ctx.send(embed=embed)

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

    @commands.command(name="rules", aliases=["regras"])
    @commands.is_owner()
    async def rules(self, ctx: commands.Context):
        """Mostra as regras do bot (só o dono)."""
        embed = discord.Embed(
            title="📜 Regras do JotaBeEli",
            description=(
                "Para a resenha continuar boa para todo mundo, "
                "siga estas regras ao usar o bot:"
            ),
            color=discord.Color.gold()
        )

        embed.add_field(
            name="1️⃣ Sem spam de comandos",
            value=(
                "Não fique repetindo comandos sem necessidade — isso "
                "atrapalha o chat e pode travar as respostas do bot."
            ),
            inline=False
        )
        embed.add_field(
            name="2️⃣ Respeite a fila de músicas",
            value=(
                "Não use `!skip`, `!encerrar` ou `!removerdafila` para "
                "sabotar as músicas dos outros membros."
            ),
            inline=False
        )
        embed.add_field(
            name="3️⃣ Use os comandos no lugar certo",
            value=(
                "Comandos de música pedem que você esteja em um canal de "
                "voz; comandos de moderação são só para a equipe."
            ),
            inline=False
        )
        embed.add_field(
            name="4️⃣ Respeito acima de tudo",
            value=(
                "Nada de usar `!ship`, `!kiss` ou os comandos sociais "
                "para constranger alguém. É diversão, não provocação."
            ),
            inline=False
        )
        embed.add_field(
            name="5️⃣ Não explore bugs",
            value=(
                "Achou um problema? Avise o dono do bot em vez de abusar "
                "dele. Quem explorar bugs pode perder o acesso."
            ),
            inline=False
        )

        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(
            text=f"{self.bot.user.name} • use !ajuda para ver os comandos",
            icon_url=self.bot.user.display_avatar.url
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def ajuda(self, ctx: commands.Context):
        """Mostra todos os comandos disponíveis."""
        embed = discord.Embed(
            title="📖 Central de Ajuda — JotaBeEli",
            description=(
                "Aqui está tudo o que eu sei fazer! Meu prefixo é `!`"
            ),
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="🎮 Interação",
            value=(
                "`!ping` — responde com Pong e a latência\n"
                "`!oi` — diz olá\n"
                "`!dado` — rola um dado\n"
                "`!ship <user1> <user2>` — compatibilidade entre dois usuários\n"
                "`!topships` — ranking dos ships mais altos\n"
                "`!kiss <usuário>` — beija um usuário\n"
                "`!rank [usuário]` — rank de XP de um usuário\n"
                "`!leaderboard` — ranking de XP do servidor"
            ),
            inline=False
        )

        embed.add_field(
            name="🎵 Música — player",
            value=(
                "`!entrar` — entra no canal de voz\n"
                "`!tocar <nome/link>` — toca ou adiciona à fila (`!play`, `!p`)\n"
                "`!pausar` / `!continuar` — pausa e retoma a música\n"
                "`!skip` — pula para a próxima música\n"
                "`!jumpto <tempo>` — pula para um momento (ex.: `!jumpto 1:23`)\n"
                "`!reset` — reseta o tempo da música (volta ao início)\n"
                "`!replay` — volta para o início da última música tocada\n"
                "`!replayall` — duplica todas as músicas, até as que já tocaram\n"
                "`!lyrics` — letra da música ou legenda do vídeo (`!letra`)\n"
                "`!duração` — progresso da música atual (`!np`)\n"
                "`!fim` — finaliza a música atual"
            ),
            inline=False
        )

        embed.add_field(
            name="🎵 Música — fila",
            value=(
                "`!fila` — mostra as músicas na fila (`!queue`, `!q`)\n"
                "`!removerdafila <número>` — remove da fila (`!remover`)\n"
                "`!mover <de> <para>` — move uma música de posição\n"
                "`!encerrar` — limpa a fila de músicas\n"
                "`!sair` — sai do canal de voz"
            ),
            inline=False
        )

        embed.add_field(
            name="💬 Mensagens automáticas",
            value=(
                "`!addmsgin <#canal>` — ativa as mensagens de boas-vindas\n"
                "`!addmsgout <#canal>` — ativa as mensagens de saída\n"
                "`!addmsgboost <#canal>` — ativa as mensagens de boost\n"
                "`!delmsgin` / `!delmsgout` / `!delmsgboost` — desativa\n"
                "`!msgconfig` — mostra os canais configurados"
            ),
            inline=False
        )

        embed.add_field(
            name="🛡️ Moderação",
            value=(
                "`!mute <usuário> <min> [motivo]` — silencia um usuário\n"
                "`!unmute <usuário>` — remove o silêncio\n"
                "`!warn <usuário> [motivo]` — dá uma advertência\n"
                "`!warnings <usuário>` — mostra as advertências\n"
                "`!clearwarns <usuário>` — remove as advertências\n"
                "`!ban <usuário> [motivo]` / `!unban <ID/nome>` — bane/desbane\n"
                "`!kick <usuário> [motivo]` — expulsa um usuário\n"
                "`!clear <quantidade>` — apaga mensagens\n"
                "`!lock` / `!unlock` — bloqueia/libera o canal\n"
                "`!lockall` / `!unlockall` — bloqueia/libera todos os canais\n"
                "`!addxp` / `!removexp <usuário> <qtd>` — ajusta o XP"
            ),
            inline=False
        )

        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Dizem que existem comandos secretos... 👀")

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    """Setup the Admin cog."""
    await bot.add_cog(Admin(bot))
