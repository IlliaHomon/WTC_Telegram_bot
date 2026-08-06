import sqlite3

DB_NAME = "recipes.db"

def init_db():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS recipes (
                        id INETEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        category TEXT NOT NULL,
                        instructions TEXT
                        )
                    ''')
    connection.commit()
    connection.close()

def add_recipe(title: str, category: str, instructions: str=""):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    cursor.execute('''INSERT INTO recipes (title, category, instructions) VALUES(?,?,?)''',
                   (title,category,instructions))
    connection.commit()
    connection.close()