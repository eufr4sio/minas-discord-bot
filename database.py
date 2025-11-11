import sqlite3
import os
from datetime import datetime

class Database:
    def __init__(self, db_path="bot.db"):                                   # Line 1
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):                                                     # Line 2
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create games table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create user_game_registrations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_game_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                game_id INTEGER NOT NULL,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, game_id),
                FOREIGN KEY (game_id) REFERENCES games (id)
            )
        ''')
        
        # Create events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                game_id INTEGER,
                creator_id INTEGER NOT NULL,
                description TEXT,
                start_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games (id)
            )
        ''')
        
        # Create event_attendees table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS event_attendees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                responded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(event_id, user_id),
                FOREIGN KEY (event_id) REFERENCES events (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):                                                 # Line 3
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def add_game(self, name, image_url=None):                              # Line 4
        """Add a new game to the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("INSERT INTO games (name, image_url) VALUES (?, ?)", (name, image_url))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None  # Game already exists
        finally:
            conn.close()
    
    def get_game_id(self, name):                                          # Line 5
        """Get game ID by name"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM games WHERE name = ?", (name,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def register_user_for_game(self, user_id, game_name):                    # Line 6
        """Register a user for a game"""
        game_id = self.get_game_id(game_name)
        if not game_id:
            game_id = self.add_game(game_name)
            if not game_id:
                return False  # Failed to add game
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("INSERT INTO user_game_registrations (user_id, game_id) VALUES (?, ?)", 
                          (user_id, game_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # User already registered
        finally:
            conn.close()
    
    def unregister_user_from_game(self, user_id, game_name):               # Line 7
        """Unregister a user from a game"""
        game_id = self.get_game_id(game_name)
        if not game_id:
            return False
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM user_game_registrations WHERE user_id = ? AND game_id = ?", 
                      (user_id, game_id))
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0
    
    def get_user_registered_games(self, user_id):                 # Line 8
        """Get all games a user is registered for"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT g.name FROM games g
            JOIN user_game_registrations ugr ON g.id = ugr.game_id
            WHERE ugr.user_id = ?
        ''', (user_id,))
        
        games = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return games
    
    def get_users_registered_for_game(self, game_name):               # Line 9
        """Get all users registered for a specific game"""
        game_id = self.get_game_id(game_name)
        if not game_id:
            return []
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id FROM user_game_registrations WHERE game_id = ?", (game_id,))
        users = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return users
    
    def create_event(self, title, description, creator_id):               # Line 10
        """Create a new event"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO events (title, description, creator_id) VALUES (?, ?, ?)",
                (title, description, creator_id)
            )
            conn.commit()
            event_id = cursor.lastrowid
            print(f"Event created with ID: {event_id}")
            return event_id
        except Exception as e:
            print(f"Error creating event: {e}")
            return None
        finally:
            conn.close()
    
    def get_upcoming_events(self):                                          # Line 11
        """Get all upcoming events"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT e.id, e.title, e.description, e.start_time, e.creator_id
            FROM events e
            ORDER BY e.created_at DESC
            LIMIT 10
        """)
        
        events = cursor.fetchall()
        conn.close()
        
        return events
    
    def update_event_rsvp(self, event_id, user_id, status):            # Line 12
        """Update user's RSVP status for an event"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO event_attendees (event_id, user_id, status)
                VALUES (?, ?, ?)
            """, (event_id, user_id, status))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating RSVP: {e}")
            return False
        finally:
            conn.close()
    
    def delete_game(self, game_id):                                       # Line 13
        """Delete a game from the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # First, remove all user registrations for this game
            cursor.execute("DELETE FROM user_game_registrations WHERE game_id = ?", (game_id,))
            
            # Then delete the game
            cursor.execute("DELETE FROM games WHERE id = ?", (game_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting game: {e}")
            return False
        finally:
            conn.close()