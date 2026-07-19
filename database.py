"""Database operations for the Discord bot.

Suporta dois bancos:
- SQLite (padrão): arquivo local, perfeito para rodar no seu PC.
- Postgres (quando a variável DATABASE_URL existe): banco externo que
  sobrevive aos restarts da hospedagem. No plano gratuito do Render o
  disco é apagado toda vez que o bot reinicia — sem um banco externo,
  XP, advertências, ships e mensagens automáticas se perdem.
"""

import asyncio
import json
import os
import sqlite3
import threading
import time
from typing import List, Optional

from config import DATABASE_PATH, SHIPS_FILE

# Quantos reports de bug ficam guardados; os mais antigos são apagados
LIMITE_REPORTS = 25


class _BackendSQLite:
    """Guarda os dados em um arquivo .db local."""

    nome = "SQLite"

    # AUTOINCREMENT é sintaxe do SQLite; o Postgres usa SERIAL
    DDL = [
        """CREATE TABLE IF NOT EXISTS xp (
            user_id INTEGER,
            guild_id INTEGER,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            PRIMARY KEY(user_id, guild_id)
        )""",
        """CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            guild_id INTEGER,
            moderator_id INTEGER,
            motivo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS mensagens_config (
            guild_id INTEGER,
            tipo TEXT,
            channel_id INTEGER,
            PRIMARY KEY(guild_id, tipo)
        )""",
        """CREATE TABLE IF NOT EXISTS bug_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_name TEXT,
            guild_name TEXT,
            texto TEXT,
            created_at INTEGER
        )""",
        """CREATE TABLE IF NOT EXISTS ships (
            guild_id INTEGER,
            nome TEXT,
            porcentagem INTEGER,
            PRIMARY KEY(guild_id, nome)
        )""",
    ]

    def __init__(self, caminho: str):
        self.caminho = caminho
        self.connection = self._conectar_com_verificacao()
        self.connection.row_factory = sqlite3.Row
        # WAL deixa o banco muito mais resistente a corrupção quando o
        # bot é fechado no meio de uma escrita
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")

    def _conectar(self) -> sqlite3.Connection:
        return sqlite3.connect(
            self.caminho,
            check_same_thread=False,
            timeout=10.0
        )

    def _conectar_com_verificacao(self) -> sqlite3.Connection:
        """Conecta ao banco, verificando a integridade do arquivo.

        Se o arquivo estiver corrompido, move ele para um backup e
        recria um banco novo — assim o bot nunca deixa de iniciar.
        """
        conexao = self._conectar()

        try:
            resultado = conexao.execute("PRAGMA quick_check").fetchone()[0]
            if resultado == "ok":
                return conexao
            print(f"⚠️  Banco de dados com problemas: {resultado}")
        except sqlite3.DatabaseError as e:
            print(f"⚠️  Banco de dados corrompido: {e}")

        conexao.close()

        backup = f"{self.caminho}.corrompido-{int(time.time())}.bak"
        os.rename(self.caminho, backup)
        print(f"⚠️  Arquivo corrompido movido para: {backup}")
        print("⚠️  Criando um banco de dados novo (XP e advertências zerados)")

        return self._conectar()

    def preparar_tabelas(self):
        for ddl in self.DDL:
            self.connection.execute(ddl)
        self._migrate_warnings()
        self.connection.commit()

    def _migrate_warnings(self):
        """Adiciona guild_id em bancos criados antes dessa coluna existir."""
        cursor = self.connection.cursor()
        colunas = [
            linha[1] for linha in
            cursor.execute("PRAGMA table_info(warnings)")
        ]

        if "guild_id" not in colunas:
            total = cursor.execute("SELECT COUNT(*) FROM warnings").fetchone()[0]
            if total == 0:
                # Tabela vazia: recria já no formato novo
                cursor.execute("DROP TABLE warnings")
                cursor.execute("""
                    CREATE TABLE warnings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        guild_id INTEGER,
                        moderator_id INTEGER,
                        motivo TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            else:
                # Tabela com dados: só adiciona a coluna (fica NULL nas antigas)
                cursor.execute("ALTER TABLE warnings ADD COLUMN guild_id INTEGER")
                if "created_at" not in colunas:
                    cursor.execute(
                        "ALTER TABLE warnings ADD COLUMN created_at TIMESTAMP"
                    )
        cursor.close()

    def executar(self, sql: str, params=(), fetch: Optional[str] = None):
        """Roda uma query. fetch: "one", "all" ou None (retorna rowcount)."""
        cursor = self.connection.execute(sql, params)
        if fetch == "one":
            resultado = cursor.fetchone()
        elif fetch == "all":
            resultado = cursor.fetchall()
        else:
            resultado = cursor.rowcount
        cursor.close()
        self.connection.commit()
        return resultado

    def close(self):
        self.connection.close()


class _BackendPostgres:
    """Guarda os dados em um Postgres externo (Neon, Supabase etc.)."""

    nome = "Postgres"

    DDL = [
        """CREATE TABLE IF NOT EXISTS xp (
            user_id BIGINT,
            guild_id BIGINT,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            PRIMARY KEY(user_id, guild_id)
        )""",
        """CREATE TABLE IF NOT EXISTS warnings (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            guild_id BIGINT,
            moderator_id BIGINT,
            motivo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS mensagens_config (
            guild_id BIGINT,
            tipo TEXT,
            channel_id BIGINT,
            PRIMARY KEY(guild_id, tipo)
        )""",
        """CREATE TABLE IF NOT EXISTS bug_reports (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            user_name TEXT,
            guild_name TEXT,
            texto TEXT,
            created_at BIGINT
        )""",
        """CREATE TABLE IF NOT EXISTS ships (
            guild_id BIGINT,
            nome TEXT,
            porcentagem INTEGER,
            PRIMARY KEY(guild_id, nome)
        )""",
    ]

    def __init__(self, url: str):
        # Import adiado: quem roda só com SQLite não precisa do psycopg
        import psycopg
        from psycopg.rows import dict_row

        self._psycopg = psycopg
        self._dict_row = dict_row
        self.url = url
        self.connection = None
        self._conectar()

    def _conectar(self):
        self.connection = self._psycopg.connect(
            self.url,
            autocommit=True,
            row_factory=self._dict_row,
            connect_timeout=15
        )

    def preparar_tabelas(self):
        for ddl in self.DDL:
            self.connection.execute(ddl)

    def executar(self, sql: str, params=(), fetch: Optional[str] = None):
        """Roda uma query. fetch: "one", "all" ou None (retorna rowcount)."""
        # As queries são escritas com "?" (estilo SQLite); o psycopg usa %s
        sql = sql.replace("?", "%s")

        try:
            cursor = self.connection.execute(sql, params)
        except (self._psycopg.OperationalError, self._psycopg.InterfaceError):
            # Bancos gratuitos derrubam conexões ociosas — reconecta e repete
            print("⚠️  Conexão com o Postgres caiu, reconectando...")
            self._conectar()
            cursor = self.connection.execute(sql, params)

        if fetch == "one":
            resultado = cursor.fetchone()
        elif fetch == "all":
            resultado = cursor.fetchall()
        else:
            resultado = cursor.rowcount
        cursor.close()
        return resultado

    def close(self):
        if self.connection:
            self.connection.close()


class Database:
    """Fachada única usada pelos cogs; escolhe o backend na inicialização."""

    def __init__(self):
        self._trava = threading.Lock()
        self._backend = self._escolher_backend()
        self._backend.preparar_tabelas()
        self._migrar_ships_json()
        print(f"✅ Banco de dados pronto ({self._backend.nome})")

    def _escolher_backend(self):
        url = os.getenv("DATABASE_URL")

        if url:
            try:
                return _BackendPostgres(url)
            except Exception as e:
                print(f"❌ Falha ao conectar no Postgres: {e}")
                print("⚠️  Usando SQLite local como reserva")
        elif os.getenv("PORT"):
            # PORT existe = está rodando no Render; sem DATABASE_URL os
            # dados moram no disco efêmero e somem a cada restart
            print(
                "⚠️  ATENÇÃO: rodando na hospedagem sem DATABASE_URL — "
                "XP, ships e configurações serão APAGADOS a cada restart! "
                "Configure um Postgres gratuito (veja o README)."
            )

        return _BackendSQLite(DATABASE_PATH)

    def _migrar_ships_json(self):
        """Importa os ships por servidor do ships.json antigo (uma vez só).

        Os ships do formato antigo (globais, sem servidor) não entram —
        eles podem ser importados manualmente com !importships.
        """
        try:
            total = self._backend.executar(
                "SELECT COUNT(*) AS total FROM ships", (), "one"
            )["total"]
            if total > 0:
                return  # já migrou antes

            if not os.path.exists(SHIPS_FILE):
                return

            with open(SHIPS_FILE, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)

            migrados = 0
            for chave, valor in dados.items():
                if not (chave.isdigit() and isinstance(valor, dict)):
                    continue
                for nome, porcentagem in valor.items():
                    if isinstance(porcentagem, int):
                        self._backend.executar(
                            """INSERT INTO ships (guild_id, nome, porcentagem)
                               VALUES (?, ?, ?)
                               ON CONFLICT(guild_id, nome) DO NOTHING""",
                            (int(chave), nome, porcentagem)
                        )
                        migrados += 1

            if migrados:
                print(f"✅ {migrados} ship(s) migrados do ships.json para o banco")
        except Exception as e:
            print(f"❌ Erro ao migrar ships.json: {e}")

    async def _executar(self, sql: str, params=(), fetch: Optional[str] = None):
        """Roda a query em outra thread para não travar o bot.

        A trava garante uma query por vez — tanto o arquivo SQLite quanto
        a conexão única do Postgres não gostam de acessos simultâneos.
        """
        def _rodar():
            with self._trava:
                return self._backend.executar(sql, params, fetch)

        return await asyncio.to_thread(_rodar)

    # ------------------------------------------------------------------
    # XP
    # ------------------------------------------------------------------

    async def get_user_xp(self, user_id: int, guild_id: int):
        """Get user XP and level. Returns a row with xp/level or None."""
        try:
            return await self._executar(
                "SELECT xp, level FROM xp WHERE user_id=? AND guild_id=?",
                (user_id, guild_id), "one"
            )
        except Exception as e:
            print(f"❌ Error getting user XP: {e}")
            return None

    async def set_user_xp(
        self, user_id: int, guild_id: int, xp: int, level: int
    ) -> bool:
        """Set user XP and level. Returns success status."""
        try:
            await self._executar(
                """INSERT INTO xp (user_id, guild_id, xp, level)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(user_id, guild_id)
                   DO UPDATE SET xp=excluded.xp, level=excluded.level""",
                (user_id, guild_id, xp, level)
            )
            return True
        except Exception as e:
            print(f"❌ Error setting user XP: {e}")
            return False

    async def get_leaderboard(self, guild_id: int, limit: int = 10) -> List:
        """Get XP leaderboard. Returns rows with user_id/level/xp."""
        try:
            return await self._executar(
                """SELECT user_id, level, xp FROM xp
                   WHERE guild_id=?
                   ORDER BY level DESC, xp DESC
                   LIMIT ?""",
                (guild_id, limit), "all"
            ) or []
        except Exception as e:
            print(f"❌ Error getting leaderboard: {e}")
            return []

    # ------------------------------------------------------------------
    # Advertências
    # ------------------------------------------------------------------

    async def add_warning(
        self, user_id: int, guild_id: int, moderator_id: int, motivo: str
    ) -> bool:
        """Add a warning to a user. Returns success status."""
        try:
            await self._executar(
                """INSERT INTO warnings (user_id, guild_id, moderator_id, motivo)
                   VALUES (?, ?, ?, ?)""",
                (user_id, guild_id, moderator_id, motivo)
            )
            return True
        except Exception as e:
            print(f"❌ Error adding warning: {e}")
            return False

    async def get_warnings(self, user_id: int, guild_id: int) -> List[str]:
        """Get all warnings for a user in a guild. Returns list of motivos."""
        try:
            linhas = await self._executar(
                """SELECT motivo FROM warnings
                   WHERE user_id=? AND guild_id=?
                   ORDER BY created_at""",
                (user_id, guild_id), "all"
            )
            return [linha["motivo"] for linha in linhas] if linhas else []
        except Exception as e:
            print(f"❌ Error getting warnings: {e}")
            return []

    async def clear_warnings(self, user_id: int, guild_id: int) -> bool:
        """Clear all warnings for a user in a guild. Returns success status."""
        try:
            await self._executar(
                "DELETE FROM warnings WHERE user_id=? AND guild_id=?",
                (user_id, guild_id)
            )
            return True
        except Exception as e:
            print(f"❌ Error clearing warnings: {e}")
            return False

    async def get_warning_count(self, user_id: int, guild_id: int) -> int:
        """Get warning count for a user in a guild."""
        try:
            linha = await self._executar(
                """SELECT COUNT(*) AS total FROM warnings
                   WHERE user_id=? AND guild_id=?""",
                (user_id, guild_id), "one"
            )
            return linha["total"] if linha else 0
        except Exception as e:
            print(f"❌ Error getting warning count: {e}")
            return 0

    # ------------------------------------------------------------------
    # Mensagens automáticas
    # ------------------------------------------------------------------

    async def set_canal_mensagem(
        self, guild_id: int, tipo: str, channel_id: int
    ) -> bool:
        """Define o canal das mensagens automáticas (entrada/saida/boost)."""
        try:
            await self._executar(
                """INSERT INTO mensagens_config (guild_id, tipo, channel_id)
                   VALUES (?, ?, ?)
                   ON CONFLICT(guild_id, tipo)
                   DO UPDATE SET channel_id=excluded.channel_id""",
                (guild_id, tipo, channel_id)
            )
            return True
        except Exception as e:
            print(f"❌ Error setting message channel: {e}")
            return False

    async def get_canal_mensagem(
        self, guild_id: int, tipo: str
    ) -> Optional[int]:
        """Retorna o canal configurado para um tipo de mensagem, ou None."""
        try:
            linha = await self._executar(
                """SELECT channel_id FROM mensagens_config
                   WHERE guild_id=? AND tipo=?""",
                (guild_id, tipo), "one"
            )
            return linha["channel_id"] if linha else None
        except Exception as e:
            print(f"❌ Error getting message channel: {e}")
            return None

    async def remover_canal_mensagem(self, guild_id: int, tipo: str) -> bool:
        """Desativa um tipo de mensagem automática. Retorna se algo foi removido."""
        try:
            removidos = await self._executar(
                "DELETE FROM mensagens_config WHERE guild_id=? AND tipo=?",
                (guild_id, tipo)
            )
            return removidos > 0
        except Exception as e:
            print(f"❌ Error removing message channel: {e}")
            return False

    # ------------------------------------------------------------------
    # Ships
    # ------------------------------------------------------------------

    async def registrar_ship(
        self, guild_id: int, nome: str, porcentagem: int
    ) -> bool:
        """Guarda (ou atualiza) um ship do servidor."""
        try:
            await self._executar(
                """INSERT INTO ships (guild_id, nome, porcentagem)
                   VALUES (?, ?, ?)
                   ON CONFLICT(guild_id, nome)
                   DO UPDATE SET porcentagem=excluded.porcentagem""",
                (guild_id, nome, porcentagem)
            )
            return True
        except Exception as e:
            print(f"❌ Error registering ship: {e}")
            return False

    async def top_ships(self, guild_id: int, limit: int = 10) -> List:
        """Retorna os ships do servidor, do maior para o menor."""
        try:
            return await self._executar(
                """SELECT nome, porcentagem FROM ships
                   WHERE guild_id=?
                   ORDER BY porcentagem DESC, nome
                   LIMIT ?""",
                (guild_id, limit), "all"
            ) or []
        except Exception as e:
            print(f"❌ Error getting top ships: {e}")
            return []

    async def importar_ships(self, guild_id: int, ships: dict) -> int:
        """Importa um dicionário nome -> porcentagem para o servidor."""
        importados = 0
        for nome, porcentagem in ships.items():
            if isinstance(porcentagem, int):
                if await self.registrar_ship(guild_id, nome, porcentagem):
                    importados += 1
        return importados

    # ------------------------------------------------------------------
    # Reports de bug
    # ------------------------------------------------------------------

    async def add_bug_report(
        self, user_id: int, user_name: str, guild_name: str, texto: str
    ) -> bool:
        """Guarda um report de bug, mantendo só os LIMITE_REPORTS mais recentes."""
        try:
            await self._executar(
                """INSERT INTO bug_reports
                   (user_id, user_name, guild_name, texto, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, user_name, guild_name, texto, int(time.time()))
            )
            # Apaga os mais antigos quando o limite é ultrapassado
            await self._executar(
                """DELETE FROM bug_reports WHERE id NOT IN
                   (SELECT id FROM bug_reports ORDER BY id DESC LIMIT ?)""",
                (LIMITE_REPORTS,)
            )
            return True
        except Exception as e:
            print(f"❌ Error adding bug report: {e}")
            return False

    async def get_bug_reports(self) -> List:
        """Retorna todos os reports de bug, do mais recente ao mais antigo."""
        try:
            return await self._executar(
                """SELECT id, user_id, user_name, guild_name, texto, created_at
                   FROM bug_reports ORDER BY id DESC""",
                (), "all"
            ) or []
        except Exception as e:
            print(f"❌ Error getting bug reports: {e}")
            return []

    def close(self):
        """Close database connection."""
        try:
            self._backend.close()
            print("✅ Database connection closed")
        except Exception as e:
            print(f"❌ Error closing database: {e}")


# Initialize database on module import
db = Database()
