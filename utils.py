import json
from config import SHIPS_FILE


def carregar_ships() -> dict:
    try:
        with open(SHIPS_FILE, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def formatar_tempo(segundos: float) -> str:
    segundos = int(segundos)
    horas, resto = divmod(segundos, 3600)
    minutos, seg = divmod(resto, 60)
    if horas:
        return f"{horas}:{minutos:02d}:{seg:02d}"
    return f"{minutos}:{seg:02d}"


def parsear_tempo(texto: str):
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
    if not total or total <= 0:
        return "🔴 AO VIVO"

    posicao = min(int((decorrido / total) * tamanho), tamanho - 1)
    return "▬" * posicao + "🔘" + "▬" * (tamanho - posicao - 1)
