import sqlite3
from typing import List, Dict

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect('twitch_users.db')
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                login TEXT NOT NULL,
                display_name TEXT NOT NULL,
                profile_image_url TEXT
            )
        ''')
        self.conn.commit()
        
        # コメントテーブルの作成
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                streamer_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                user_color TEXT,
                comment_time TIMESTAMP NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (streamer_id) REFERENCES users (id)
            )
        ''')
        self.conn.commit()

    def add_user(self, user_data: Dict) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)',
                (user_data['id'], user_data['login'], user_data['display_name'], user_data['profile_image_url'])
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False

    def get_all_users(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users')
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'login': row[1],
                'display_name': row[2],
                'profile_image_url': row[3]
            })
        return users

    def remove_user(self, user_id: str) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error removing user: {e}")
            return False

    def save_comments(self, video_id: str, streamer_id: str, comments: list):
        cursor = self.conn.cursor()
        cursor.executemany(
            '''
            INSERT INTO comments (video_id, streamer_id, user_id, user_color, comment_time, message)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            comments
        )
        self.conn.commit()

    def get_video_comments(self, video_id: str):
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT * FROM comments WHERE video_id = ? ORDER BY comment_time',
            (video_id,)
        )
        return cursor.fetchall()
