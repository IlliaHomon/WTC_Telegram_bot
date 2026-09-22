import sqlite3
import secrets
import string

DB_NAME = "recipes.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS families (
                        family_id TEXT PRIMARY KEY
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        family_id TEXT NOT NULL,
                        username TEXT,
                        FOREIGN KEY (family_id) REFERENCES families(family_id)
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS recipes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        family_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        category TEXT NOT NULL,
                        instructions TEXT,
                        FOREIGN KEY (family_id) REFERENCES families(family_id)
                    )''')
    
    connection.commit()
    connection.close()

    

#All functions regarding family  
def generate_family_id(length: int = 6):
    characters = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(characters) for i in range(length))

def create_family(user_id: int, username: str = None) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    while True:
        family_id = generate_family_id()
        cursor.execute("SELECT 1 FROM families WHERE family_id=?", (family_id,))
        if not cursor.fetchone():
            break

    cursor.execute("INSERT INTO families (family_id) VALUES (?)", (family_id,))
    cursor.execute("INSERT OR REPLACE INTO users (user_id, family_id, username) VALUES (?,?,?)", (user_id, family_id, username))

    conn.commit()
    conn.close()

    return family_id

def get_user_family_id(user_id:int, username:str = None):
    conn = get_connection()
    cursor = conn.cursor()
    if username:
        cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
        conn.commit()

    cursor.execute("SELECT family_id FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row and row[0]:
        return row[0]
    return None

def user_has_family(user_id:int) -> bool:
    return get_user_family_id(user_id) is not None

def assign_family_id(user_id:int, family_id:str, username: str = None) -> bool:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM families WHERE family_id = ?", (family_id,))
    if not cursor.fetchone():
        conn.close()
        return False
    
    cursor.execute("INSERT OR REPLACE INTO users (user_id, family_id, username) VALUES (?,?,?)", (user_id, family_id, username))
    cursor.execute("UPDATE recipes SET family_id = ? WHERE user_id = ?", (family_id, user_id))
    
    conn.commit()
    conn.close()
    return True

def leave_family(user_id:int, username:str = None):
    new_family_id = create_family(user_id,username)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE recipes SET family_id = ? WHERE user_id = ?", (new_family_id, user_id))

    conn.commit()
    conn.close()

#--------------------------------------------

def get_all_usernames(family_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE family_id = ?",(family_id,))
    usernames = [row[0] for row in cursor.fetchall() if row[0]]
    conn.close()
    return usernames

def add_recipe(user_id: int, title: str, family_id: str, category: str, instructions: str=""):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO recipes (user_id, family_id, title, category, instructions) VALUES(?,?,?,?,?)",
                   (user_id,family_id,title,category,instructions))
    connection.commit()
    connection.close()

def delete_recipe(identifier: int|str, user_id: int, family_id: str) -> bool:
    connection = get_connection()
    cursor = connection.cursor()
    if isinstance(identifier, int):
        cursor.execute("DELETE FROM recipes WHERE id = ? AND (user_id = ? OR family_id = ?)", [identifier,user_id,family_id])
    elif isinstance(identifier, str):
        if identifier.isdigit():
            identifier=int(identifier)
            cursor.execute("DELETE FROM recipes WHERE id = ? AND (user_id = ? OR family_id = ?)", [identifier,user_id,family_id])
        else: cursor.execute("DELETE FROM recipes WHERE LOWER(title) = LOWER(?) AND (user_id = ? OR family_id = ?)", [identifier,user_id,family_id])
    connection.commit()
    deleted = cursor.rowcount>0
    connection.close()  
    return deleted

def delete_all_user_recipes(user_id: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM recipes WHERE user_id = ?", (user_id,))
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted_count

def search_recipes_by_title(keyword: str, user_id: int, family_id: str):
    connection = get_connection()
    cursor = connection.cursor()
    
    cursor.execute('''SELECT title, category, instructions FROM recipes 
        WHERE LOWER(title) LIKE LOWER(?) AND (user_id = ? OR family_id = ?)''', [f"%{keyword.strip()}%",user_id,family_id])
    
    matches = cursor.fetchall()
    connection.close()  
    return matches

def search_recipes_by_category(category: str, user_id: int, family_id: str):
    connection = get_connection()
    cursor = connection.cursor()
    
    cursor.execute('''SELECT title, category, instructions FROM recipes 
        WHERE LOWER(category) LIKE LOWER(?) AND (user_id = ? OR family_id = ?)''', [f"%{category.strip()}%",user_id, family_id])
    
    matches = cursor.fetchall()
    connection.close()  
    return matches

def get_all_categories(user_id: int, family_id: str) -> list[str]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT LOWER(category) FROM recipes WHERE (user_id = ? OR family_id = ?) ORDER BY category ASC", [user_id, family_id])
    categories = [row[0] for row in cursor.fetchall()]

    conn.close()
    return categories


def get_custom_meal_plan(user_id: int, family_id: str, mandatory_ids: list[int] = None,
    category_counts: dict[str, int] = None,
    mandatory_categories: list[str] = None,
    total_count: int = 3):

    mandatory_ids = mandatory_ids or []
    category_counts = category_counts or {}
    mandatory_categories = mandatory_categories or []
    
    conn = get_connection()
    cursor = conn.cursor()
    
    selected_recipes = []
    selected_ids = set()

    def get_exclude_sql():
        if not selected_ids:
            return ""
        placeholders = ','.join('?' for _ in selected_ids)
        return f"AND id NOT IN ({placeholders})"

    #handle mandatory meals
    if mandatory_ids:
        placeholders = ','.join('?' for _ in mandatory_ids)
        cursor.execute(f'''
            SELECT id, title, category, instructions 
            FROM recipes 
            WHERE id IN ({placeholders}) AND (user_id = ? OR family_id = ?)
        ''', mandatory_ids + [user_id,family_id]  )
        
        for recipe in cursor.fetchall():
            selected_recipes.append(recipe)
            selected_ids.add(recipe[0])

    #fetch how many meals for each requested category is needed
    for category, count in category_counts.items():
        if count <= 0 or len(selected_recipes) >= total_count:
            continue
            
        exclude_sql = get_exclude_sql()
        params = [category] + list(selected_ids) + [user_id,family_id,count]
        
        cursor.execute(f'''
            SELECT id, title, category, instructions 
            FROM recipes 
            WHERE LOWER(category) = LOWER(?) {exclude_sql} AND (user_id = ? OR family_id = ?)
            ORDER BY RANDOM() 
            LIMIT ?
        ''', params)
        
        for recipe in cursor.fetchall():
            selected_recipes.append(recipe)
            selected_ids.add(recipe[0])

    #generate random meals in requested quantity for each category
    for cat in mandatory_categories:
        if len(selected_recipes) >= total_count:
            break
            
        already_has_category = any(r[2].lower() == cat.lower() for r in selected_recipes)
        if already_has_category:
            continue

        exclude_sql = get_exclude_sql()
        params = [cat] + list(selected_ids) + [user_id,family_id,1]
        
        cursor.execute(f'''
            SELECT id, title, category, instructions 
            FROM recipes 
            WHERE LOWER(category) = LOWER(?) {exclude_sql} AND (user_id = ? OR family_id = ?)
            ORDER BY RANDOM() 
            LIMIT ?
        ''', params)
        
        recipe = cursor.fetchone()
        if recipe:
            selected_recipes.append(recipe)
            selected_ids.add(recipe[0])

    #fill remaining slots with random recipes
    remaining_slots = total_count - len(selected_recipes)
    if remaining_slots > 0:
        if selected_ids:
            placeholders = ','.join('?' for _ in selected_ids)
            where_sql = f"WHERE id NOT IN ({placeholders}) AND (user_id = ? OR family_id = ?)"
            params = list(selected_ids) + [user_id,family_id, remaining_slots]
        else:
            where_sql = "WHERE (user_id = ? OR family_id = ?)"
            params = [user_id,family_id, remaining_slots]
            
        cursor.execute(f'''
            SELECT id, title, category, instructions 
            FROM recipes 
            {where_sql}
            ORDER BY RANDOM() 
            LIMIT ?
        ''', params)
        
        selected_recipes.extend(cursor.fetchall())

    conn.close()
    return selected_recipes