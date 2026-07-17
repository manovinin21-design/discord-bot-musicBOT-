"""Cog de música: fila, player e controles de voz."""

import asyncio
import time
from dataclasses import dataclass
from typing import Optional

import discord
import yt_dlp
from discord.ext import commands

from config import YTDL_OPTIONS, FFMPEG_OPTIONS
from utils import formatar_tempo, barra_progresso

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

COR_MUSICA = discord.Color.from_rgb(88, 101, 242)


@dataclass
class Musica:
    """Uma música da fila, já com as informações resolvidas."""

    titulo: str
    url: str                      # link da página (usado para tocar depois)
    duracao: Optional[int]        # em segundos; None para lives
    thumb: Optional[str]
    pedido_por: str

    @property
    def duracao_texto(self) -> str:
        if self.duracao:
            return formatar_tempo(self.duracao)
        return "🔴 ao vivo"


class Music(commands.Cog):
    """Comandos de música."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.filas = {}           # guild_id -> lista de Musica
        self.ultima_musica = {}   # guild_id -> última Musica tocada
        self.tocando_agora = {}   # guild_id -> {"musica": Musica, "inicio": float}
        self.locks = {}           # guild_id -> asyncio.Lock (evita play duplo)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def fila_de(self, guild_id: int) -> list:
        """Retorna (criando se preciso) a fila do servidor."""
        if guild_id not in self.filas:
            self.filas[guild_id] = []
        return self.filas[guild_id]

    def lock_de(self, guild_id: int) -> asyncio.Lock:
        """Retorna (criando se preciso) o lock do player do servidor."""
        if guild_id not in self.locks:
            self.locks[guild_id] = asyncio.Lock()
        return self.locks[guild_id]

    def limpar_estado(self, guild_id: int):
        """Limpa fila e música atual de um servidor."""
        self.fila_de(guild_id).clear()
        self.tocando_agora.pop(guild_id, None)

    async def conectar_voz(self, ctx: commands.Context) -> bool:
        """Garante que o bot está em um canal de voz. Retorna False se falhar."""
        if ctx.voice_client:
            return True

        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("Você precisa estar em um canal de voz.")
            return False

        await ctx.author.voice.channel.connect()
        return True

    async def buscar_info(self, pesquisa: str) -> Optional[dict]:
        """Busca as informações de uma música no yt-dlp. Retorna None se falhar."""
        try:
            info = await asyncio.to_thread(
                ytdl.extract_info, pesquisa, download=False
            )
        except Exception as e:
            print(f"❌ Erro ao buscar música: {e}")
            return None

        # ignoreerrors=True faz o yt-dlp retornar None em vez de lançar erro
        if info is None:
            return None

        if "entries" in info:
            entries = [e for e in info["entries"] if e]
            if not entries:
                return None
            info = entries[0]

        return info

    def embed_tocando(self, musica: Musica) -> discord.Embed:
        """Embed de "tocando agora"."""
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

    async def tocar_proxima(self, ctx: commands.Context):
        """Toca a próxima música da fila."""
        guild_id = ctx.guild.id
        fila = self.fila_de(guild_id)

        # O lock evita dois play() ao mesmo tempo (ex.: !tocar durante a
        # troca de música), o que derrubaria o player
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

                # Busca de novo na hora de tocar: o link direto do áudio
                # expira, então guardamos a página e resolvemos o stream aqui
                info = await self.buscar_info(musica.url)
                if info is None or "url" not in info:
                    await ctx.send(f"❌ Não consegui tocar: **{musica.titulo}**")
                    continue  # tenta a próxima da fila

                # O bot pode ter sido desconectado durante a busca
                if not ctx.voice_client or not ctx.voice_client.is_connected():
                    self.tocando_agora.pop(guild_id, None)
                    return

                source = discord.FFmpegPCMAudio(info["url"], **FFMPEG_OPTIONS)

                self.tocando_agora[guild_id] = {
                    "musica": musica,
                    "inicio": time.time()
                }

                def depois(erro):
                    if erro:
                        print("ERRO NO PLAYER:", erro)

                    asyncio.run_coroutine_threadsafe(
                        self.tocar_proxima(ctx),
                        self.bot.loop
                    )

                ctx.voice_client.play(source, after=depois)
                break

        await ctx.send(embed=self.embed_tocando(musica))

    # ------------------------------------------------------------------
    # Comandos
    # ------------------------------------------------------------------

    @commands.command()
    async def entrar(self, ctx: commands.Context):
        """Entra no canal de voz."""
        if ctx.voice_client:
            await ctx.send("Já estou conectado.")
            return

        if await self.conectar_voz(ctx):
            await ctx.send("Entrei na call 🎵")

    @commands.command(aliases=["play", "p"])
    async def tocar(self, ctx: commands.Context, *, pesquisa: str):
        """Toca uma música ou adiciona à fila."""
        if not await self.conectar_voz(ctx):
            return

        async with ctx.typing():
            info = await self.buscar_info(pesquisa)

        if info is None:
            await ctx.send(f"❌ Não encontrei resultados para: **{pesquisa}**")
            return

        musica = Musica(
            titulo=info.get("title", pesquisa),
            url=info.get("webpage_url") or info.get("url", pesquisa),
            duracao=info.get("duration"),
            thumb=info.get("thumbnail"),
            pedido_por=ctx.author.display_name
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
        """Repete a última música tocada."""
        guild_id = ctx.guild.id

        if guild_id not in self.ultima_musica:
            await ctx.send("❌ Não existe nenhuma música anterior para repetir.")
            return

        if not await self.conectar_voz(ctx):
            return

        musica = self.ultima_musica[guild_id]
        fila = self.fila_de(guild_id)
        fila.insert(0, musica)

        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            await ctx.send(f"🔁 Adicionei novamente: **{musica.titulo}**")
        else:
            await self.tocar_proxima(ctx)

    @commands.command()
    async def skip(self, ctx: commands.Context):
        """Pula para a próxima música da fila."""
        if not ctx.voice_client:
            await ctx.send("Não estou em um canal de voz.")
            return

        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()  # o callback "depois" toca a próxima
            await ctx.send("⏭️ Música pulada.")
        else:
            await ctx.send("Não há nenhuma música tocando.")

    @commands.command(name="duração", aliases=["duracao", "np"])
    async def duracao(self, ctx: commands.Context):
        """Mostra a duração e o progresso da música atual."""
        atual = self.tocando_agora.get(ctx.guild.id)

        if not atual or not ctx.voice_client or not (
            ctx.voice_client.is_playing() or ctx.voice_client.is_paused()
        ):
            await ctx.send("Não há nenhuma música tocando.")
            return

        musica = atual["musica"]
        decorrido = time.time() - atual["inicio"]

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
        """Mostra as músicas na fila."""
        fila = self.fila_de(ctx.guild.id)
        atual = self.tocando_agora.get(ctx.guild.id)

        if not fila and not atual:
            await ctx.send("A fila está vazia.")
            return

        embed = discord.Embed(title="📋 Fila de músicas", color=COR_MUSICA)

        if atual:
            musica = atual["musica"]
            decorrido = time.time() - atual["inicio"]
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
        """Remove uma música da fila pelo número dela."""
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
        """Move uma música de posição na fila."""
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
        """Pausa a música em execução."""
        if not ctx.voice_client:
            await ctx.send("Não estou em um canal de voz.")
            return

        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Música pausada.")
        else:
            await ctx.send("Não há nenhuma música tocando.")

    @commands.command()
    async def continuar(self, ctx: commands.Context):
        """Retoma a música pausada."""
        if not ctx.voice_client:
            await ctx.send("Não estou em um canal de voz.")
            return

        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Música retomada.")
        else:
            await ctx.send("Nenhuma música está pausada.")

    @commands.command()
    async def fim(self, ctx: commands.Context):
        """Finaliza a música atual (a próxima da fila continua)."""
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
        """Limpa a fila e para a música atual."""
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
        """Sai do canal de voz."""
        if ctx.voice_client:
            self.limpar_estado(ctx.guild.id)
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Saí do canal de voz.")
        else:
            await ctx.send("Não estou em um canal de voz.")


async def setup(bot: commands.Bot):
    """Setup do cog Music."""
    await bot.add_cog(Music(bot))
