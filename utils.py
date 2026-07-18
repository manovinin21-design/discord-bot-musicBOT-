"""Funções utilitárias compartilhadas entre os cogs."""

import json
from config import SHIPS_FILE


def carregar_ships() -> dict:
    """Carrega o arquivo de ships. Retorna dict vazio se não existir."""
    try:
        with open(SHIPS_FILE, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def salvar_ships(dados: dict):
    """Salva o dicionário de ships no arquivo."""
    with open(SHIPS_FILE, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=4, ensure_ascii=False)


def ships_do_servidor(dados: dict, guild_id: int) -> dict:
    """Retorna os ships de um servidor específico.

    O ships.json antigo guardava tudo no nível raiz; o formato novo
    separa por guild_id. Esta função junta os dois para não perder
    os ships antigos.
    """
    resultado = {}

    # Formato antigo: pares direto na raiz (valor é um número)
    for chave, valor in dados.items():
        if isinstance(valor, int):
            resultado[chave] = valor

    # Formato novo: sub-dicionário com a chave do servidor
    por_guild = dados.get(str(guild_id))
    if isinstance(por_guild, dict):
        resultado.update(por_guild)

    return resultado


def registrar_ship(dados: dict, guild_id: int, nome_ship: str, porcentagem: int):
    """Registra um ship no formato novo (separado por servidor)."""
    chave = str(guild_id)
    if not isinstance(dados.get(chave), dict):
        dados[chave] = {}
    dados[chave][nome_ship] = porcentagem


def formatar_tempo(segundos: float) -> str:
    """Formata segundos como m:ss ou h:mm:ss."""
    segundos = int(segundos)
    horas, resto = divmod(segundos, 3600)
    minutos, seg = divmod(resto, 60)
    if horas:
        return f"{horas}:{minutos:02d}:{seg:02d}"
    return f"{minutos}:{seg:02d}"


def parsear_tempo(texto: str):
    """Converte "90", "1:30" ou "1:02:03" em segundos. Retorna None se inválido."""
    partes = texto.strip().split(":")
    if not 1 <= len(partes) <= 3:
        return None

    try:
        numeros = [int(parte) for parte in partes]
    except ValueError:
        return None

    if any(numero < 0 for numero in numeros):
        return None

    segundos = 0
    for numero in numeros:
        segundos = segundos * 60 + numero
    return segundos


def barra_progresso(decorrido: float, total: float, tamanho: int = 14) -> str:
    """Monta uma barra de progresso tipo ▬▬▬🔘▬▬▬▬."""
    if not total or total <= 0:
        return "🔴 AO VIVO"

    posicao = min(int((decorrido / total) * tamanho), tamanho - 1)
    return "▬" * posicao + "🔘" + "▬" * (tamanho - posicao - 1)
