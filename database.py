"""Database operations for the Discord bot."""

import os
import sqlite3
import time
from typing import Optional, Tuple, List
from config import DATABASE_PATH


class Database:
    """SQLite database handler."""

    def __init__(self):
        self.connection = self._conectar_com_verificacao()
        self.connection.row_factory = sqlite3.Row
        self._create_tables()

    def _conectar_com_verificacao(self) -> sqlite3.Connection:
        """Conecta ao banco, verificando a integridade do arquivo.

        Se o arquivo estiver corrompido, move ele para um backup e
        recria um banco novo — assim o bot nunca deixa de iniciar.
        """
        conexao = sqlite3.connect(
            DATABASE_PATH,
            check_same_thread=False,
            timeout=10.0
        )

        try:
            resultado = conexao.execute("PRAGMA quick_check").fetchone()[0]
            if resultado == "ok":
                return conexao
            print(f"⚠️  Banco de dados com problemas: {resultado}")
        except sqlite3.DatabaseError as e:
            print(f"⚠️  Banco de dados corrompido: {e}")

        conexao.close()

        backup = f"{DATABASE_PATH}.corrompido-{int(time.time())}.bak"
        os.rename(DATABASE_PATH, backup)
        print(f"⚠️  Arquivo corrompido movido para: {backup}")
        print("⚠️  Criando um banco de dados novo (XP e advertências zerados)")

        return sqlite3.connect(
            DATABASE_PATH,
            check_same_thread=False,
            timeout=10.0
        )

    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS xp (
                    user_id INTEGER,
                    guild_id INTEGER,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    PRIMARY KEY(user_id, guild_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    guild_id INTEGER,
                    moderator_id INTEGER,
                    motivo TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mensagens_config (
                    guild_id INTEGER,
                    tipo TEXT,
                    channel_id INTEGER,
                    PRIMARY KEY(guild_id, tipo)
                )
            """)

            self._migrate_warnings(cursor)

            self.connection.commit()
        except sqlite3.Error as e:
            print(f"❌ Table creation error: {e}")
            raise
        finally:
            cursor.close()

    def _migrate_warnings(self, cursor: sqlite3.Cursor):
        """Adiciona guild_id em bancos criados antes dessa coluna existir."""
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

    async def get_user_xp(
        self, user_id: int, guild_id: int
    ) -> Optional[Tuple[int, int]]:
        """Get user XP and level. Returns (xp, level) or None."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT xp, level FROM xp WHERE user_id=? AND guild_id=?",
                (user_id, guild_id)
            )
            result = cursor.fetchone()
            cursor.close()
            return result if result else None
        except sqlite3.Error as e:
            print(f"❌ Error getting user XP: {e}")
            return None

    async def set_user_xp(
        self, user_id: int, guild_id: int, xp: int, level: int
    ) -> bool:
        """Set user XP and level. Returns success status."""
        try:
            cursor = self.connection.cursor()
            existing = await self.get_user_xp(user_id, guild_id)

            if existing:
                cursor.execute(
                    "UPDATE xp SET xp=?, level=? WHERE user_id=? AND guild_id=?",
                    (xp, level, user_id, guild_id)
                )
            else:
                cursor.execute(
                    "INSERT INTO xp (user_id, guild_id, xp, level) VALUES (?, ?, ?, ?)",
                    (user_id, guild_id, xp, level)
                )

            self.connection.commit()
            cursor.close()
            return True
        except sqlite3.Error as e:
            print(f"❌ Error setting user XP: {e}")
            self.connection.rollback()
            return False

    async def get_leaderboard(
        self, guild_id: int, limit: int = 10
    ) -> List[Tuple[int, int, int]]:
        """Get XP leaderboard. Returns list of (user_id, level, xp)."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """SELECT user_id, level, xp FROM xp 
                   WHERE guild_id=? 
                   ORDER BY level DESC, xp DESC 
                   LIMIT ?""",
                (guild_id, limit)
            )
            results = cursor.fetchall()
            cursor.close()
            return results if results else []
        except sqlite3.Error as e:
            print(f"❌ Error getting leaderboard: {e}")
            return []

    async def add_warning(
        self, user_id: int, guild_id: int, moderator_id: int, motivo: str
    ) -> bool:
        """Add a warning to a user. Returns success status."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """INSERT INTO warnings (user_id, guild_id, moderator_id, motivo)
                   VALUES (?, ?, ?, ?)""",
                (user_id, guild_id, moderator_id, motivo)
            )
            self.connection.commit()
            cursor.close()
            return True
        except sqlite3.Error as e:
            print(f"❌ Error adding warning: {e}")
            self.connection.rollback()
            return False

    async def get_warnings(self, user_id: int, guild_id: int) -> List[str]:
        """Get all warnings for a user in a guild. Returns list of motivos."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """SELECT motivo FROM warnings
                   WHERE user_id=? AND guild_id=?
                   ORDER BY created_at""",
                (user_id, guild_id)
            )
            results = cursor.fetchall()
            cursor.close()
            return [r[0] for r in results] if results else []
        except sqlite3.Error as e:
            print(f"❌ Error getting warnings: {e}")
            return []

    async def clear_warnings(self, user_id: int, guild_id: int) -> bool:
        """Clear all warnings for a user in a guild. Returns success status."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "DELETE FROM warnings WHERE user_id=? AND guild_id=?",
                (user_id, guild_id)
            )
            self.connection.commit()
            cursor.close()
            return True
        except sqlite3.Error as e:
            print(f"❌ Error clearing warnings: {e}")
            self.connection.rollback()
            return False

    async def get_warning_count(self, user_id: int, guild_id: int) -> int:
        """Get warning count for a user in a guild."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM warnings WHERE user_id=? AND guild_id=?",
                (user_id, guild_id)
            )
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except sqlite3.Error as e:
            print(f"❌ Error getting warning count: {e}")
            return 0

    async def set_canal_mensagem(
        self, guild_id: int, tipo: str, channel_id: int
    ) -> bool:
        """Define o canal das mensagens automáticas (entrada/saida/boost)."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO mensagens_config
                   (guild_id, tipo, channel_id) VALUES (?, ?, ?)""",
                (guild_id, tipo, channel_id)
            )
            self.connection.commit()
            cursor.close()
            return True
        except sqlite3.Error as e:
            print(f"❌ Error setting message channel: {e}")
            self.connection.rollback()
            return False

    async def get_canal_mensagem(
        self, guild_id: int, tipo: str
    ) -> Optional[int]:
        """Retorna o canal configurado para um tipo de mensagem, ou None."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """SELECT channel_id FROM mensagens_config
                   WHERE guild_id=? AND tipo=?""",
                (guild_id, tipo)
            )
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else None
        except sqlite3.Error as e:
            print(f"❌ Error getting message channel: {e}")
            return None

    async def remover_canal_mensagem(self, guild_id: int, tipo: str) -> bool:
        """Desativa um tipo de mensagem automática. Retorna se algo foi removido."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "DELETE FROM mensagens_config WHERE guild_id=? AND tipo=?",
                (guild_id, tipo)
            )
            removido = cursor.rowcount > 0
            self.connection.commit()
            cursor.close()
            return removido
        except sqlite3.Error as e:
            print(f"❌ Error removing message channel: {e}")
            self.connection.rollback()
            return False

    def close(self):
        """Close database connection."""
        if self.connection:
            try:
                self.connection.close()
                print("✅ Database connection closed")
            except sqlite3.Error as e:
                print(f"❌ Error closing database: {e}")


# Initialize database on module import
db = Database()
