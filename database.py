import sqlite3

DB_NAME = "recipes.db"

def init_db():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS recipes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        category TEXT NOT NULL,
                        instructions TEXT
                        )''')
    connection.commit()
    connection.close()


def add_recipe(title: str, category: str, instructions: str=""):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    cursor.execute('''INSERT INTO recipes (title, category, instructions) VALUES(?,?,?)''',
                   (title,category,instructions))
    connection.commit()
    connection.close()

def delete_recipe(identifier: int|str) -> bool:
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    if isinstance(identifier, int):
        cursor.execute('''DELETE FROM recipes WHERE id = ?''', [identifier])
    elif isinstance(identifier, str):
        if identifier.isdigit():
            identifier=int(identifier)
            cursor.execute('''DELETE FROM recipes WHERE id = ?''', [identifier])
        else: cursor.execute('''DELETE FROM recipes WHERE LOWER(title) = LOWER(?)''', [identifier])
    connection.commit()
    deleted = cursor.rowcount>0
    connection.close()

    return deleted


def search_recipes_by_title(keyword: str):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    
    cursor.execute('''SELECT id, title, category FROM recipes 
        WHERE LOWER(title) LIKE LOWER(?)''', (f"%{keyword.strip()}%",))
    
    matches = cursor.fetchall()
    connection.close()
    return matches

def get_all_categories() -> list[str]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT DISTINCT category FROM recipes ORDER BY category ASC')
    categories = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return categories


def get_custom_meal_plan(mandatory_ids: list[int] = None,
    category_counts: dict[str, int] = None,
    mandatory_categories: list[str] = None,
    total_count: int = 3):

    mandatory_ids = mandatory_ids or []
    category_counts = category_counts or {}
    mandatory_categories = mandatory_categories or []
    
    conn = sqlite3.connect(DB_NAME)
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
            WHERE id IN ({placeholders})
        ''', mandatory_ids)
        
        for recipe in cursor.fetchall():
            selected_recipes.append(recipe)
            selected_ids.add(recipe[0])

    #fetch how many meals for each requested category is needed
    for category, count in category_counts.items():
        if count <= 0 or len(selected_recipes) >= total_count:
            continue
            
        exclude_sql = get_exclude_sql()
        params = [category] + list(selected_ids) + [count]
        
        cursor.execute(f'''
            SELECT id, title, category, instructions 
            FROM recipes 
            WHERE LOWER(category) = LOWER(?) {exclude_sql}
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
        params = [cat] + list(selected_ids) + [1]
        
        cursor.execute(f'''
            SELECT id, title, category, instructions 
            FROM recipes 
            WHERE LOWER(category) = LOWER(?) {exclude_sql}
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
        exclude_sql = f"WHERE id NOT IN ({','.join('?' for _ in selected_ids)})" if selected_ids else ""
        params = list(selected_ids) + [remaining_slots] if selected_ids else [remaining_slots]
        
        cursor.execute(f'''
            SELECT id, title, category, instructions 
            FROM recipes 
            {exclude_sql}
            ORDER BY RANDOM() 
            LIMIT ?
        ''', params)
        
        selected_recipes.extend(cursor.fetchall())

    conn.close()
    return selected_recipes