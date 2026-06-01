import sqlite3
from datetime import datetime

DB = "shopyai.db"

def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE, stock INTEGER,
        price REAL, category TEXT DEFAULT "general",
        shop_name TEXT DEFAULT "ShopyAI",
        location TEXT DEFAULT "")''')
    c.execute('''CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT, qty INTEGER,
        amount REAL, sale_time TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS whatsapp_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_number TEXT, message TEXT,
        ai_reply TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS cctv_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_type TEXT, confidence REAL,
        camera_id TEXT, timestamp TEXT)''')
    seeds = [('sabun',50,30.0),('chini',50,44.0),('tel',15,120.0)]
    c.executemany('INSERT OR IGNORE INTO products (name,stock,price) VALUES (?,?,?)', seeds)
    conn.commit()
    conn.close()
    print("ShopyAI DB Ready!")

def get_products():
    conn = get_conn()
    rows = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return [dict(r) for r in rows]

def sell_product(name, qty):
    conn = get_conn()
    p = conn.execute('SELECT * FROM products WHERE name=?',(name,)).fetchone()
    if not p: conn.close(); return None
    if p['stock'] < qty: conn.close(); return None
    conn.execute('UPDATE products SET stock=stock-? WHERE name=?',(qty,name))
    amount = p['price'] * qty
    conn.execute('INSERT INTO sales (product_name,qty,amount,sale_time) VALUES (?,?,?,?)',
                 (name, qty, amount, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return amount

def get_sales():
    conn = get_conn()
    rows = conn.execute('SELECT * FROM sales ORDER BY id DESC LIMIT 50').fetchall()
    conn.close()
    return [dict(r) for r in rows]

def log_whatsapp(from_num, msg, reply):
    conn = get_conn()
    conn.execute('INSERT INTO whatsapp_logs (from_number,message,ai_reply,timestamp) VALUES (?,?,?,?)',
                 (from_num, msg, reply, datetime.now().isoformat()))
    conn.commit()
    conn.close()