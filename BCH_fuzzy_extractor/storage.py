import sqlite3

class Storage:
    def __init__(self, db_path='helper_data.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Store helper_data as BLOB with user_id as primary key
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS helpers (
                    user_id TEXT PRIMARY KEY,
                    helper_data BLOB
                )
            ''')
            conn.commit()

    def save_helper(self, user_id, helper_data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO helpers (user_id, helper_data)
                VALUES (?, ?)
            ''', (user_id, helper_data))
            conn.commit()

    def load_helper(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT helper_data FROM helpers WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return row[0] if row else None