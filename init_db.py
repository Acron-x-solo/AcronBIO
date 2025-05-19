import sqlite3
import os

# Удаляем старую базу данных, если она существует
if os.path.exists('bio.db'):
    os.remove('bio.db')

# Создаем новую базу данных
conn = sqlite3.connect('bio.db')
cur = conn.cursor()

# Создаем таблицу пользователей
cur.execute('''
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    avatar TEXT,
    color TEXT,
    social_vk TEXT,
    social_tg TEXT,
    social_ds TEXT,
    social_yt TEXT,
    social_ig TEXT,
    social_tw TEXT,
    social_gh TEXT,
    social_st TEXT,
    social_tt TEXT,
    social_fb TEXT,
    status TEXT,
    city TEXT,
    bio TEXT,
    activity TEXT,
    views INTEGER DEFAULT 0,
    plain_password TEXT,
    music_url TEXT,
    music_cover TEXT,
    background_effects TEXT DEFAULT 'none'
)
''')

# Создаем таблицу песен
cur.execute('''
CREATE TABLE songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    file_url TEXT NOT NULL,
    cover_url TEXT,
    link_url TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
''')

conn.commit()
conn.close()

print("База данных успешно создана!") 