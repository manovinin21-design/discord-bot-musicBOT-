import asyncio
import re
import time
from dataclasses import dataclass
from typing import Optional

import aiohttp
import discord
import yt_dlp
from discord.ext import commands

from config import YTDL_OPTIONS, FFMPEG_OPTIONS
from utils import formatar_tempo, barra_progresso, parsear_tempo

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

COR_MUSICA = discord.Color.from_rgb(88, 101, 242)


LIMITE_HISTORICO = 200


IDIOMAS_LEGENDA = ["pt", "pt-BR", "pt-PT", "en", "en-US"]


RUIDO_TITULO = re.compile(
    r"[\(\[\{][^\)\]\}]*[\)\]\}]"
    r"|(?i:official|oficial|clipe|video|vídeo|lyrics?|audio|áudio"
    r"|visualizer|legendado|remaster(?:ed)?|hd|4k|mv)"
)


@dataclass
class Musica:

    titulo: str
    url: str
    duracao: Optional[int]
    thumb: Optional[str]
    pedido_por: str
    stream_url: Optional[str] = None
    stream_expira: float = 0.0

    @property
    def duracao_texto(self) -> str:
        if self.duracao:
            return formatar_tempo(self.duracao)
        return "🔴 ao vivo"


class Music(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.filas = {}
        self.ultima_musica = {}
        self.historicos = {}
        self.tocando_agora = {}
        self.locks = {}
        self.ignorar_fim = set()
        self.ultimo_erro = None

    async def cog_check(self, ctx: commands.Context) -> bool:
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True


    def fila_de(self, guild_id: int) -> list:
        if guild_id not in self.filas:
            self.filas[guild_id] = []
        return self.filas[guild_id]

    def historico_de(self, guild_id: int) -> list:
        if guild_id not in self.historicos:
            self.historicos[guild_id] = []
        return self.historicos[guild_id]

    def lock_de(self, guild_id: int) -> asyncio.Lock:
        if guild_id not in self.locks:
            self.locks[guild_id] = asyncio.Lock()
        return self.locks[guild_id]

    def limpar_estado(self, guild_id: int):
        self.fila_de(guild_id).clear()
        self.historico_de(guild_id).clear()
        self.tocando_agora.pop(guild_id, None)

    async def conectar_voz(self, ctx: commands.Context) -> bool:
        if ctx.voice_client:
            return True

        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("Você precisa estar em um canal de voz.")
            return False

        await ctx.author.voice.channel.connect()
        return True

    async def buscar_info(self, pesquisa: str) -> Optional[dict]:
        self.ultimo_erro = None
        try:
            info = await asyncio.to_thread(
                ytdl.extract_info, pesquisa, download=False
            )
        except Exception as e:
            print(f"❌ Erro ao buscar música: {e}")
            self.ultimo_erro = str(e)
            return None

        if info is None:
            return None

        if "entries" in info:
            entries = [e for e in info["entries"] if e]
            if not entries:
                return None
            info = entries[0]

        return info

    def mensagem_falha(self, pesquisa: str) -> str:
        erro = self.ultimo_erro or ""

        if "Sign in to confirm you're not a bot" in erro or "cookies" in erro:
            return (
                "❌ O YouTube bloqueou o IP deste servidor (pede login). "
                "O dono do bot precisa configurar um `cookies.txt` — "
                "veja a seção **YouTube bloqueado** do README."
            )
        if "confirm your age" in erro or "age" in erro.lower():
            return (
                f"❌ **{pesquisa}** tem restrição de idade e o YouTube "
                "não deixa tocar sem login."
            )
        if "Video unavailable" in erro or "Private video" in erro:
            return f"❌ Esse vídeo está indisponível ou privado: **{pesquisa}**"

        mensagem = f"❌ Não consegui encontrar/tocar: **{pesquisa}**"
        if erro:

            resumo = erro.replace("ERROR: ", "").split("\n")[0][:200]
            mensagem += f"\n(`{resumo}`)"
        return mensagem

    @staticmethod
    def _expira_stream(stream_url: Optional[str]) -> float:
        if not stream_url:
            return 0.0


        match = re.search(r"[?&]expire=(\d+)", stream_url)
        if match:
            return int(match.group(1)) - 60

        return time.time() + 20 * 60

    async def resolver_stream(self, musica: Musica) -> bool:
        if musica.stream_url and time.time() < musica.stream_expira:
            return True

        info = await self.buscar_info(musica.url)
        if info is None or "url" not in info:
            return False

        musica.stream_url = info["url"]
        musica.stream_expira = self._expira_stream(info["url"])
        return True

    def embed_tocando(self, musica: Musica) -> discord.Embed:
        embed = discord.Embed(
            title="🎶 Tocando agora",
            description=f"**[{musica.titulo}]({musica.url})**",
            color=COR_MUSICA
        )
        embed.add_field(name="⏱️ Duração", value=musica.duracao_texto, inline=True)
        embed.add_field(name="🙋 Pedido por", value=musica.pedido_por, inline=True)
        if musica.thumb:
            embed.set_thumbnail(url=musica.thumb)
        return embed

    def _criar_callback(self, ctx: commands.Context):
        guild_id = ctx.guild.id

        def depois(erro):
            if erro:
                print("ERRO NO PLAYER:", erro)


            if guild_id in self.ignorar_fim:
                self.ignorar_fim.discard(guild_id)
                return

            asyncio.run_coroutine_threadsafe(
                self.tocar_proxima(ctx),
                self.bot.loop
            )

        return depois

    async def tocar_proxima(self, ctx: commands.Context):
        guild_id = ctx.guild.id
        fila = self.fila_de(guild_id)


        async with self.lock_de(guild_id):
            while True:
                if not ctx.voice_client or not ctx.voice_client.is_connected():
                    self.tocando_agora.pop(guild_id, None)
                    return

                if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                    return

                if not fila:
                    self.tocando_agora.pop(guild_id, None)
                    return

                musica = fila.pop(0)
                self.ultima_musica[guild_id] = musica


                if not await self.resolver_stream(musica):
                    await ctx.send(
                        f"❌ Não consegui tocar: **{musica.titulo}**\n"
                        + self.mensagem_falha(musica.titulo)
                    )
                    continue


                if not ctx.voice_client or not ctx.voice_client.is_connected():
                    self.tocando_agora.pop(guild_id, None)
                    return

                source = discord.FFmpegPCMAudio(
                    musica.stream_url, **FFMPEG_OPTIONS
                )

                self.tocando_agora[guild_id] = {
                    "musica": musica,
                    "inicio": time.time(),
                    "pausado_em": None
                }

                historico = self.historico_de(guild_id)
                historico.append(musica)
                del historico[:-LIMITE_HISTORICO]

                ctx.voice_client.play(source, after=self._criar_callback(ctx))


                if fila:
                    asyncio.create_task(self.resolver_stream(fila[0]))
                break

        await ctx.send(embed=self.embed_tocando(musica))

    async def pular_para(self, ctx: commands.Context, segundos: int) -> bool:
        guild_id = ctx.guild.id
        atual = self.tocando_agora.get(guild_id)
        vc = ctx.voice_client

        if not atual or not vc or not (vc.is_playing() or vc.is_paused()):
            await ctx.send("Não há nenhuma música tocando.")
            return False

        musica = atual["musica"]

        if not musica.duracao:
            await ctx.send("❌ Não dá para navegar em uma transmissão ao vivo.")
            return False

        if segundos >= musica.duracao:
            await ctx.send(
                f"❌ A música só tem **{formatar_tempo(musica.duracao)}**."
            )
            return False

        if not await self.resolver_stream(musica):
            await ctx.send("❌ Não consegui recuperar o áudio da música.")
            return False

        opcoes = dict(FFMPEG_OPTIONS)
        opcoes["before_options"] = (
            f"-ss {segundos} {FFMPEG_OPTIONS['before_options']}"
        )
        source = discord.FFmpegPCMAudio(musica.stream_url, **opcoes)


        self.ignorar_fim.add(guild_id)
        vc.stop()
        try:
            vc.play(source, after=self._criar_callback(ctx))
        except discord.ClientException as e:
            self.ignorar_fim.discard(guild_id)
            print(f"❌ Erro ao reposicionar a música: {e}")
            await ctx.send("❌ Não consegui reposicionar a música.")
            return False

        atual["inicio"] = time.time() - segundos
        atual["pausado_em"] = None
        return True

    @staticmethod
    def tempo_decorrido(atual: dict) -> float:
        agora = atual.get("pausado_em") or time.time()
        return agora - atual["inicio"]


    @staticmethod
    def _limpar_titulo(titulo: str) -> str:
        limpo = RUIDO_TITULO.sub(" ", titulo)
        limpo = re.sub(r"\s+", " ", limpo).strip(" -–|•")
        return limpo or titulo

    async def _letra_lrclib(
        self, session: aiohttp.ClientSession, titulo: str
    ) -> Optional[str]:
        try:
            async with session.get(
                "https://lrclib.net/api/search",
                params={"q": self._limpar_titulo(titulo)},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resposta:
                if resposta.status != 200:
                    return None
                resultados = await resposta.json()
        except Exception as e:
            print(f"❌ Erro ao buscar letra: {e}")
            return None

        for item in resultados or []:
            letra = item.get("plainLyrics")
            if letra and letra.strip():
                return letra.strip()
        return None

    @staticmethod
    def _escolher_legenda(info: dict) -> Optional[str]:
        manuais = info.get("subtitles") or {}
        automaticas = info.get("automatic_captions") or {}

        def url_json3(formatos):
            for formato in formatos or []:
                if formato.get("ext") == "json3" and formato.get("url"):
                    return formato["url"]
            return None


        for idioma in IDIOMAS_LEGENDA + sorted(manuais.keys()):
            url = url_json3(manuais.get(idioma))
            if url:
                return url


        originais = [k for k in automaticas if k.endswith("-orig")]
        for idioma in IDIOMAS_LEGENDA + originais:
            url = url_json3(automaticas.get(idioma))
            if url:
                return url

        return None

    @staticmethod
    def _montar_texto_json3(dados: dict) -> Optional[str]:
        linhas = []
        for evento in dados.get("events", []):
            segmentos = evento.get("segs")
            if not segmentos:
                continue
            texto = "".join(s.get("utf8", "") for s in segmentos).strip()
            if texto and texto != "\n" and (not linhas or linhas[-1] != texto):
                linhas.append(texto)

        return "\n".join(linhas) if linhas else None

    async def _legenda_video(
        self, session: aiohttp.ClientSession, musica: Musica
    ) -> Optional[str]:
        info = await self.buscar_info(musica.url)
        if info is None:
            return None

        url_legenda = self._escolher_legenda(info)
        if not url_legenda:
            return None

        try:
            async with session.get(
                url_legenda,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resposta:
                if resposta.status != 200:
                    return None
                dados = await resposta.json(content_type=None)
        except Exception as e:
            print(f"❌ Erro ao baixar legenda: {e}")
            return None

        return self._montar_texto_json3(dados)

    async def obter_letra(self, musica: Musica):
        async with aiohttp.ClientSession() as session:
            letra = await self._letra_lrclib(session, musica.titulo)
            if letra:
                return letra, "letra via LRCLIB"

            legenda = await self._legenda_video(session, musica)
            if legenda:
                return legenda, "legendas do vídeo"

        return None, None

    @staticmethod
    def _dividir_texto(texto: str, limite: int = 3900, max_partes: int = 3):
        partes = []
        restante = texto

        while restante and len(partes) < max_partes:
            if len(restante) <= limite:
                partes.append(restante)
                restante = ""
                break

            corte = restante.rfind("\n", 0, limite)
            if corte < limite // 2:
                corte = limite
            partes.append(restante[:corte])
            restante = restante[corte:].lstrip("\n")

        return partes, bool(restante)


    @commands.command()
    async def entrar(self, ctx: commands.Context):
        if ctx.voice_client:
            await ctx.send("Já estou conectado.")
            return

        if await self.conectar_voz(ctx):
            await ctx.send("Entrei na call 🎵")

    @commands.command(aliases=["play", "p"])
    async def tocar(self, ctx: commands.Context, *, pesquisa: str):
        if not await self.conectar_voz(ctx):
            return

        async with ctx.typing():
            info = await self.buscar_info(pesquisa)

        if info is None:
            await ctx.send(self.mensagem_falha(pesquisa))
            return

        musica = Musica(
            titulo=info.get("title", pesquisa),
            url=info.get("webpage_url") or info.get("url", pesquisa),
            duracao=info.get("duration"),
            thumb=info.get("thumbnail"),
            pedido_por=ctx.author.display_name,

            stream_url=info.get("url"),
            stream_expira=self._expira_stream(info.get("url"))
        )

        fila = self.fila_de(ctx.guild.id)
        fila.append(musica)

        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            embed = discord.Embed(
                title="✅ Adicionada à fila",
                description=f"**[{musica.titulo}]({musica.url})**",
                color=COR_MUSICA
            )
            embed.add_field(
                name="📍 Posição", value=str(len(fila)), inline=True
            )
            embed.add_field(
                name="⏱️ Duração", value=musica.duracao_texto, inline=True
            )
            if musica.thumb:
                embed.set_thumbnail(url=musica.thumb)
            await ctx.send(embed=embed)
        else:
            await self.tocar_proxima(ctx)

    @commands.command()
    async def replay(self, ctx: commands.Context):
        guild_id = ctx.guild.id

        if not await self.conectar_voz(ctx):
            return

        vc = ctx.voice_client
        fila = self.fila_de(guild_id)
        historico = self.historico_de(guild_id)
        tocando = vc.is_playing() or vc.is_paused()

        if tocando and guild_id in self.tocando_agora:
            atual = self.tocando_agora[guild_id]["musica"]

            if len(historico) >= 2:
                anterior = historico[-2]
                fila.insert(0, anterior)
                fila.insert(1, atual)
                vc.stop()
                await ctx.send(
                    f"🔁 Voltando para **{anterior.titulo}** — "
                    f"**{atual.titulo}** ficará como próxima."
                )
            else:

                if await self.pular_para(ctx, 0):
                    await ctx.send(
                        f"🔁 **{atual.titulo}** voltou para o início."
                    )
            return

        if guild_id not in self.ultima_musica:
            await ctx.send("❌ Não existe nenhuma música anterior para repetir.")
            return

        fila.insert(0, self.ultima_musica[guild_id])
        await self.tocar_proxima(ctx)

    @commands.command()
    async def replayall(self, ctx: commands.Context):
        guild_id = ctx.guild.id
        fila = self.fila_de(guild_id)
        historico = self.historico_de(guild_id)

        duplicatas = list(historico) + list(fila)
        if not duplicatas:
            await ctx.send("❌ Não há músicas para duplicar.")
            return

        if not await self.conectar_voz(ctx):
            return

        fila[0:0] = duplicatas

        embed = discord.Embed(
            title="🔁 Replay geral!",
            description=(
                f"**{len(duplicatas)}** música(s) duplicadas e colocadas "
                "como próximas — incluindo as que já tocaram."
            ),
            color=COR_MUSICA
        )
        embed.set_footer(text="Use !fila para conferir a ordem.")
        await ctx.send(embed=embed)

        vc = ctx.voice_client
        if not (vc.is_playing() or vc.is_paused()):
            await self.tocar_proxima(ctx)

    @commands.command()
    async def jumpto(self, ctx: commands.Context, *, tempo: str):
        segundos = parsear_tempo(tempo)

        if segundos is None:
            await ctx.send(
                "❌ Tempo inválido. Use segundos ou m:ss — ex.: "
                "`!jumpto 90` ou `!jumpto 1:30`."
            )
            return

        if await self.pular_para(ctx, segundos):
            await ctx.send(f"⏩ Pulei para **{formatar_tempo(segundos)}**.")

    @commands.command()
    async def reset(self, ctx: commands.Context):
        if await self.pular_para(ctx, 0):
            await ctx.send("⏪ Música reiniciada do começo.")

    @commands.command(aliases=["letra"])
    async def lyrics(self, ctx: commands.Context):
        atual = self.tocando_agora.get(ctx.guild.id)

        if not atual:
            await ctx.send("Não há nenhuma música tocando.")
            return

        musica = atual["musica"]

        async with ctx.typing():
            texto, fonte = await self.obter_letra(musica)

        if not texto:
            await ctx.send(
                f"❌ Não encontrei a letra nem legendas para "
                f"**{musica.titulo}**."
            )
            return

        partes, cortado = self._dividir_texto(texto)
        titulo_embed = f"🎤 {musica.titulo}"[:256]

        for i, parte in enumerate(partes):
            embed = discord.Embed(
                title=titulo_embed if i == 0 else f"{titulo_embed[:245]} (cont.)",
                description=parte,
                color=COR_MUSICA
            )
            if i == 0 and musica.thumb:
                embed.set_thumbnail(url=musica.thumb)
            if i == len(partes) - 1:
                rodape = f"Fonte: {fonte}"
                if cortado:
                    rodape += " • letra cortada por ser muito longa"
                embed.set_footer(text=rodape)
            await ctx.send(embed=embed)

    @commands.command()
    async def skip(self, ctx: commands.Context):
        if not ctx.voice_client:
            await ctx.send("Não estou em um canal de voz.")
            return

        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Música pulada.")
        else:
            await ctx.send("Não há nenhuma música tocando.")

    @commands.command(name="duração", aliases=["duracao", "np"])
    async def duracao(self, ctx: commands.Context):
        atual = self.tocando_agora.get(ctx.guild.id)

        if not atual or not ctx.voice_client or not (
            ctx.voice_client.is_playing() or ctx.voice_client.is_paused()
        ):
            await ctx.send("Não há nenhuma música tocando.")
            return

        musica = atual["musica"]
        decorrido = self.tempo_decorrido(atual)

        embed = discord.Embed(
            title="🎵 Música atual",
            description=f"**[{musica.titulo}]({musica.url})**",
            color=COR_MUSICA
        )

        if musica.duracao:
            barra = barra_progresso(decorrido, musica.duracao)
            tempo = f"{formatar_tempo(decorrido)} / {formatar_tempo(musica.duracao)}"
            embed.add_field(name=tempo, value=barra, inline=False)
        else:
            embed.add_field(
                name=f"{formatar_tempo(decorrido)} decorridos",
                value="🔴 AO VIVO",
                inline=False
            )

        embed.add_field(name="🙋 Pedido por", value=musica.pedido_por, inline=True)
        if musica.thumb:
            embed.set_thumbnail(url=musica.thumb)

        await ctx.send(embed=embed)

    @commands.command(aliases=["queue", "q"])
    async def fila(self, ctx: commands.Context):
        fila = self.fila_de(ctx.guild.id)
        atual = self.tocando_agora.get(ctx.guild.id)

        if not fila and not atual:
            await ctx.send("A fila está vazia.")
            return

        embed = discord.Embed(title="📋 Fila de músicas", color=COR_MUSICA)

        if atual:
            musica = atual["musica"]
            decorrido = self.tempo_decorrido(atual)
            if musica.duracao:
                progresso = (
                    f"{formatar_tempo(decorrido)} / "
                    f"{formatar_tempo(musica.duracao)}"
                )
            else:
                progresso = "🔴 ao vivo"
            embed.add_field(
                name="🎶 Tocando agora",
                value=f"**[{musica.titulo}]({musica.url})**\n⏱️ {progresso}",
                inline=False
            )
            if musica.thumb:
                embed.set_thumbnail(url=musica.thumb)

        if fila:
            linhas = []
            for i, musica in enumerate(fila[:10], start=1):
                linhas.append(
                    f"`{i}.` **{musica.titulo}** "
                    f"({musica.duracao_texto}) — {musica.pedido_por}"
                )

            texto = "\n".join(linhas)
            if len(fila) > 10:
                texto += f"\n... e mais {len(fila) - 10} música(s)"

            embed.add_field(name="⏭️ Próximas", value=texto, inline=False)

            duracao_total = sum(m.duracao or 0 for m in fila)
            embed.set_footer(
                text=(
                    f"{len(fila)} música(s) na fila • "
                    f"duração total: {formatar_tempo(duracao_total)}"
                )
            )

        await ctx.send(embed=embed)

    @commands.command(aliases=["remover", "rf"])
    async def removerdafila(self, ctx: commands.Context, numero: int):
        fila = self.fila_de(ctx.guild.id)

        if not fila:
            await ctx.send("A fila está vazia.")
            return

        if numero < 1 or numero > len(fila):
            await ctx.send(
                f"❌ Número inválido. A fila vai de 1 a {len(fila)}."
            )
            return

        musica = fila.pop(numero - 1)
        await ctx.send(f"🗑️ Removida da fila: **{musica.titulo}**")

    @commands.command()
    async def mover(self, ctx: commands.Context, de: int, para: int):
        fila = self.fila_de(ctx.guild.id)

        if not fila:
            await ctx.send("A fila está vazia.")
            return

        if len(fila) < 2:
            await ctx.send("A fila só tem uma música, não há o que mover.")
            return

        if not (1 <= de <= len(fila)) or not (1 <= para <= len(fila)):
            await ctx.send(
                f"❌ Posição inválida. A fila vai de 1 a {len(fila)}."
            )
            return

        if de == para:
            await ctx.send("❌ A música já está nessa posição.")
            return

        musica = fila.pop(de - 1)
        fila.insert(para - 1, musica)

        await ctx.send(
            f"↕️ **{musica.titulo}** movida da posição {de} para a {para}."
        )

    @commands.command()
    async def pausar(self, ctx: commands.Context):
        if not ctx.voice_client:
            await ctx.send("Não estou em um canal de voz.")
            return

        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            atual = self.tocando_agora.get(ctx.guild.id)
            if atual:
                atual["pausado_em"] = time.time()
            await ctx.send("⏸️ Música pausada.")
        else:
            await ctx.send("Não há nenhuma música tocando.")

    @commands.command()
    async def continuar(self, ctx: commands.Context):
        if not ctx.voice_client:
            await ctx.send("Não estou em um canal de voz.")
            return

        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            atual = self.tocando_agora.get(ctx.guild.id)
            if atual and atual.get("pausado_em"):

                atual["inicio"] += time.time() - atual["pausado_em"]
                atual["pausado_em"] = None
            await ctx.send("▶️ Música retomada.")
        else:
            await ctx.send("Nenhuma música está pausada.")

    @commands.command()
    async def fim(self, ctx: commands.Context):
        if not ctx.voice_client:
            await ctx.send("Não estou em um canal de voz.")
            return

        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()
            await ctx.send("Música finalizada.")
        else:
            await ctx.send("Não há nenhuma música tocando.")

    @commands.command()
    async def encerrar(self, ctx: commands.Context):
        fila = self.fila_de(ctx.guild.id)
        fila.clear()

        if not ctx.voice_client:
            await ctx.send("Não estou em um canal de voz.")
            return

        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()
            await ctx.send("Fila limpa.")
        else:
            await ctx.send("Não há nenhuma música tocando.")

    @commands.command()
    async def sair(self, ctx: commands.Context):
        if ctx.voice_client:
            self.limpar_estado(ctx.guild.id)
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Saí do canal de voz.")
        else:
            await ctx.send("Não estou em um canal de voz.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
