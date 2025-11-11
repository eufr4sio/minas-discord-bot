import aiosqlite
import asyncio
import os
from datetime import datetime

class Database:
    def __init__(self, db_path="bot.db"):
        self.db_path = db_path

    async def init_db(self):
        """Initialize database with required tables (async)"""
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.executescript('''
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    image_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS user_game_registrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    game_id INTEGER NOT NULL,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, game_id),
                    FOREIGN KEY (game_id) REFERENCES games (id)
                );

                -- NEW TABLE FOR ALIASES
                CREATE TABLE IF NOT EXISTS game_aliases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER NOT NULL,
                    alias TEXT NOT NULL UNIQUE,
                    FOREIGN KEY (game_id) REFERENCES games (id) ON DELETE CASCADE
                );
            ''')
            await conn.commit()
            print("✅ Database initialized successfully.")

    # --- CORE FUNCTION FOR ALIAS SYSTEM ---
    async def get_game_id_from_name_or_alias(self, name_or_alias):
        """Get a game's ID from its primary name or any of its aliases."""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute("SELECT id FROM games WHERE name = ?", (name_or_alias,))
            result = await cursor.fetchone()
            if result:
                return result[0]

            cursor = await conn.execute('''
                SELECT game_id FROM game_aliases WHERE alias = ?
            ''', (name_or_alias,))
            result = await cursor.fetchone()
            if result:
                return result[0]
            
            return None # Not found

    # --- CORRECTED FUNCTION ---
    async def add_game(self, name, image_url=None, aliases=None):
        """Add a new game to the database with optional aliases."""
        # Check if the main game name already exists
        game_id = await self.get_game_id_from_name_or_alias(name)
        if game_id:
            return None

        async with aiosqlite.connect(self.db_path) as conn:
            try:
                # Insert the main game first
                cursor = await conn.execute("INSERT INTO games (name, image_url) VALUES (?, ?)", (name, image_url))
                await conn.commit()
                game_id = cursor.lastrowid

                # If aliases are provided, add them
                if aliases:
                    alias_list = [a.strip() for a in aliases.split(',') if a.strip()]
                    for alias in alias_list:
                        try:
                            await conn.execute("INSERT INTO game_aliases (game_id, alias) VALUES (?, ?)", (game_id, alias))
                        except aiosqlite.IntegrityError:
                            # Alias already exists, skip it
                            pass
                    await conn.commit()
                
                return game_id
            except aiosqlite.IntegrityError:
                return None # Game name already exists

    async def get_all_games(self):
        """Get all games and their IDs from database"""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute("SELECT name FROM games ORDER BY name ASC")
            rows = await cursor.fetchall()
            return rows

    # --- ALL OTHER FUNCTIONS updated to use the new core function ---
    async def register_user_for_game(self, user_id, game_name):
        game_id = await self.get_game_id_from_name_or_alias(game_name)
        if not game_id:
            game_id = await self.add_game(game_name) # Add it if it doesn't exist
            if not game_id:
                return False

        async with aiosqlite.connect(self.db_path) as conn:
            try:
                await conn.execute("INSERT INTO user_game_registrations (user_id, game_id) VALUES (?, ?)",
                                   (user_id, game_id))
                await conn.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def unregister_user_from_game(self, user_id, game_name):
        game_id = await self.get_game_id_from_name_or_alias(game_name)
        if not game_id:
            return False

        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute("DELETE FROM user_game_registrations WHERE user_id = ? AND game_id = ?",
                                        (user_id, game_id))
            await conn.commit()
            return cursor.rowcount > 0

    async def get_user_registered_games(self, user_id):
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute('''
                SELECT g.name FROM games g
                JOIN user_game_registrations ugr ON g.id = ugr.game_id
                WHERE ugr.user_id = ?
            ''', (user_id,))
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

    async def get_users_registered_for_game(self, game_name):
        game_id = await self.get_game_id_from_name_or_alias(game_name)
        if not game_id:
            return []

        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute("SELECT user_id FROM user_game_registrations WHERE game_id = ?", (game_id,))
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

    async def delete_game(self, game_id):
        """Delete a game from the database"""
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                await conn.execute("DELETE FROM user_game_registrations WHERE game_id = ?", (game_id,))
                await conn.execute("DELETE FROM games WHERE id = ?", (game_id,))
                await conn.execute("DELETE FROM game_aliases WHERE game_id = ?", (game_id,)) # Also delete aliases
                await conn.commit()
                return True
            except Exception as e:
                print(f"Error deleting game: {e}")
                return False

    async def delete_game_by_name(self, name):
        """Delete a game from the database by its name or alias"""
        game_id = await self.get_game_id_from_name_or_alias(name)
        if not game_id:
            return False
        return await self.delete_game(game_id)
    # --- Add these new functions inside the Database class in database.py ---

    async def get_all_games_for_panel(self):
        """Get all games with their IDs for the control panel dropdowns."""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row # Return dictionary-like rows
            cursor = await conn.execute("SELECT id, name FROM games ORDER BY name ASC")
            rows = await cursor.fetchall()
            return rows

    # Synchronous version for fast UI loading
    def get_all_games_for_panel_sync(self):
        """Synchronous version of get_all_games_for_panel for UI setup."""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM games ORDER BY name ASC")
        rows = cursor.fetchall()
        conn.close()
        return rows

    async def get_game_name_by_id(self, game_id: int):
        """Fetches a game's name by its ID."""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute("SELECT name FROM games WHERE id = ?", (game_id,))
            result = await cursor.fetchone()
            return result[0] if result else None

    async def get_registrations_for_game_id(self, game_id: int):
        """Gets a list of user_ids registered for a specific game ID."""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute("SELECT user_id FROM user_game_registrations WHERE game_id = ?", (game_id,))
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

    # --- Config Table Functions for Settings like Alert Channel ---
    async def init_config_table(self):
        """Creates a config table for storing key-value settings."""
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')
            await conn.commit()

    async def get_config(self, key: str):
        """Get a value from the config table."""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute("SELECT value FROM config WHERE key = ?", (key,))
            result = await cursor.fetchone()
            return int(result[0]) if result and result[0].isdigit() else result[0] if result else None

    async def set_config(self, key: str, value):
        """Set a value in the config table."""
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute('''
                INSERT INTO config (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            ''', (key, str(value)))
            await conn.commit()
            # In database.py, add this new function inside the Database class

    def get_user_registered_games_sync(self, user_id: int):
        """Synchronously gets all games a user is registered for."""
        import sqlite3
        db_path = self.db_path
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT g.name FROM games g
            JOIN user_game_registrations ugr ON g.id = ugr.game_id
            WHERE ugr.user_id = ?
            ORDER BY g.name ASC
        ''', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [row['name'] for row in rows]