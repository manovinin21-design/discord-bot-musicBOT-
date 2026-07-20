import discord
from discord.ext import commands

from database import db


LIMITE_TEXTO_REPORT = 900


class Admin(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="a")
    @commands.is_owner()
    async def anunciar(self, ctx: commands.Context, *, mensagem: str):
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
        embed = discord.Embed(
            title="📜 Regras do JotaBeEli",
            description=(
                "Regras do servidor do JotaBeEli"
            ),
            color=discord.Color.gold()
        )

        embed.add_field(
            name="1️ Sem spam de comandos",
            value=(
                "Não fique repetindo comandos sem necessidade — isso "
                "atrapalha o chat e pode travar as respostas do bot."
            ),
            inline=False
        )
        embed.add_field(
            name="2️ Respeite a fila de músicas",
            value=(
                "Não use `!skip`, `!encerrar` ou `!removerdafila` para "
                "sabotar as músicas dos outros membros."
            ),
            inline=False
        )
        embed.add_field(
            name="3️ Use os comandos no lugar certo",
            value=(
                "Comandos de música pedem que você esteja em um canal de "
                "voz; comandos de moderação são só para a equipe."
            ),
            inline=False
        )

        embed.add_field(
            name="4- Sem abusar de poder ou uso de forma incoveninente ",
            value=(
                "Não se aproveite do seu cargo para se aproveitar e se "
                "colocar acima do outro, sujeito a perca total do cargo."
            ),
            inline=False
        )
        embed.add_field(
            name="5- Não explore bugs",
            value=(
                "Achou um problema? Avise o dono do bot em vez "
                "de se aproveitar dele. Quem explorar bugs "
                "pode perder o acesso."
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
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def reportbug(self, ctx: commands.Context, *, texto: str):
        texto = texto.strip()
        if not texto:
            await ctx.send(
                "❌ Escreva o problema depois do comando — "
                "ex.: `!reportbug o !skip travou`."
            )
            return

        cortado = len(texto) > LIMITE_TEXTO_REPORT
        if cortado:
            texto = texto[:LIMITE_TEXTO_REPORT]

        guild_nome = ctx.guild.name if ctx.guild else "Mensagem privada (DM)"

        sucesso = await db.add_bug_report(
            ctx.author.id, ctx.author.name, guild_nome, texto
        )
        if not sucesso:
            await ctx.send("❌ Não consegui salvar o report. Tente de novo.")
            return

        mensagem = "✅ Report enviado! Obrigado por avisar 🐛"
        if cortado:
            mensagem += (
                f"\n(A mensagem era muito longa e foi cortada em "
                f"{LIMITE_TEXTO_REPORT} caracteres.)"
            )
        await ctx.send(mensagem)

    @commands.command()
    @commands.is_owner()
    async def showreports(self, ctx: commands.Context):
        reports = await db.get_bug_reports()

        if not reports:
            await ctx.send("📭 Nenhum report de bug armazenado.")
            return

        embed = discord.Embed(
            title="🐛 Reports de bugs",
            description=(
                f"**{len(reports)}** report(s) armazenado(s), "
                "do mais recente ao mais antigo:"
            ),
            color=discord.Color.red()
        )
        embeds = [embed]
        total_chars = len(embed.title) + len(embed.description)

        for report in reports:
            nome = (
                f"👤 {report['user_name']} — 🌐 {report['guild_name']}"
            )[:256]
            texto = report["texto"]
            if len(texto) > LIMITE_TEXTO_REPORT:
                texto = texto[:LIMITE_TEXTO_REPORT] + "…"
            valor = f"{texto}\n🕒 <t:{report['created_at']}:f>"


            if (
                len(embed.fields) >= 25
                or total_chars + len(nome) + len(valor) > 5500
            ):
                embed = discord.Embed(
                    title="🐛 Reports de bugs (continuação)",
                    color=discord.Color.red()
                )
                embeds.append(embed)
                total_chars = len(embed.title)

            embed.add_field(name=nome, value=valor, inline=False)
            total_chars += len(nome) + len(valor)

        for item in embeds:
            await ctx.send(embed=item)

    @commands.command()
    async def ajuda(self, ctx: commands.Context):
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
                "`!leaderboard` — ranking de XP do servidor\n"
                "`!reportbug <mensagem>` — reporta um bug para o dono do bot"
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
    await bot.add_cog(Admin(bot))
