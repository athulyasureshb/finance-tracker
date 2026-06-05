from flask_login import UserMixin
from database import get_db

class User(UserMixin):
    def __init__(self, id, name, email, password):
        self.id = id
        self.name = name
        self.email = email
        self.password = password

    @staticmethod
    def get_by_id(user_id):
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        if user:
            return User(user["id"], user["name"], user["email"], user["password"])
        return None

    @staticmethod
    def get_by_email(email):
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        if user:
            return User(user["id"], user["name"], user["email"], user["password"])
        return None

    @staticmethod
    def create(name, email, hashed_password):
        conn = get_db()
        conn.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, hashed_password)
        )
        conn.commit()
        conn.close()