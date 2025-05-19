from flask import Flask, render_template, redirect, url_for, request, flash, send_file, Response, session
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import requests
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)

DATABASE = 'db.sqlite3'

# Discord OAuth2 настройки
DISCORD_CLIENT_ID = 'YOUR_CLIENT_ID'  # Замените на ваш Client ID
DISCORD_CLIENT_SECRET = 'YOUR_CLIENT_SECRET'  # Замените на ваш Client Secret
DISCORD_REDIRECT_URI = 'http://localhost:5000/discord/callback'  # Измените на ваш URL
DISCORD_API_ENDPOINT = 'https://discord.com/api/v10'
DISCORD_BOT_TOKEN = 'YOUR_BOT_TOKEN'  # Замените на токен вашего бота

# Discord OAuth2 URL
DISCORD_OAUTH2_URL = f'https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&redirect_uri={DISCORD_REDIRECT_URI}&response_type=code&scope=identify%20guilds%20activities.read'

# Обновлённая модель пользователя
class User(UserMixin):
    def __init__(self, id, username, password_hash, avatar=None, color=None, social_vk=None, social_tg=None, social_ds=None, social_yt=None, social_gh=None, social_st=None, social_roblox=None, social_funpay=None, status=None, city=None, bio=None, activity=None, plain_password=None, music_url=None, music_cover=None, background_effects=None):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.avatar = avatar
        self.color = color
        self.social_vk = social_vk
        self.social_tg = social_tg
        self.social_ds = social_ds
        self.social_yt = social_yt
        self.social_gh = social_gh
        self.social_st = social_st
        self.social_roblox = social_roblox
        self.social_funpay = social_funpay
        self.status = status
        self.city = city
        self.bio = bio
        self.activity = activity
        self.plain_password = plain_password
        self.music_url = music_url
        self.music_cover = music_cover
        self.background_effects = background_effects

# Получение пользователя из БД
@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('SELECT id, username, password_hash, avatar, color, social_vk, social_tg, social_ds, social_yt, social_gh, social_st, social_roblox, social_funpay, status, city, bio, activity, plain_password, music_url, music_cover, background_effects FROM users WHERE id=?', (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return User(*row)
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute('SELECT id FROM users WHERE username=?', (username,))
        if cur.fetchone():
            flash('Пользователь уже существует!')
            conn.close()
            return redirect(url_for('register'))
        password_hash = generate_password_hash(password)
        # Сохраняем открытый пароль (только для теста!)
        cur.execute('INSERT INTO users (username, password_hash, plain_password) VALUES (?, ?, ?)', (username, password_hash, password))
        conn.commit()
        conn.close()
        flash('Регистрация успешна! Войдите в аккаунт.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute('SELECT id, username, password_hash FROM users WHERE username=?', (username,))
        row = cur.fetchone()
        conn.close()
        if row and check_password_hash(row[2], password):
            user = User(*row)
            remember = bool(request.form.get('remember'))
            login_user(user, remember=remember)
            return redirect(url_for('index'))
        flash('Неверный логин или пароль!')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    # Добавление новой песни
    if request.method == 'POST' and 'add_song' in request.form:
        title = request.form.get('song_title', '')
        link_url = request.form.get('song_link', '')
        file_url = ''
        cover_url = ''
        # Загрузка mp3
        if 'song_file' in request.files:
            song_file = request.files['song_file']
            if song_file and song_file.filename and song_file.filename.lower().endswith('.mp3'):
                music_dir = os.path.join('static', 'music')
                if not os.path.exists(music_dir):
                    os.makedirs(music_dir)
                fname = f"{current_user.id}_{uuid.uuid4().hex}_{song_file.filename}"
                music_path = f'static/music/{fname}'
                song_file.save(music_path)
                file_url = '/' + music_path.replace('\\', '/')
        # Загрузка обложки
        if 'song_cover' in request.files:
            cover_file = request.files['song_cover']
            if cover_file and cover_file.filename and (cover_file.filename.lower().endswith('.jpg') or cover_file.filename.lower().endswith('.jpeg') or cover_file.filename.lower().endswith('.png') or cover_file.filename.lower().endswith('.gif')):
                cover_dir = os.path.join('static', 'music_covers')
                if not os.path.exists(cover_dir):
                    os.makedirs(cover_dir)
                fname = f"{current_user.id}_{uuid.uuid4().hex}_{cover_file.filename}"
                cover_path = f'static/music_covers/{fname}'
                cover_file.save(cover_path)
                cover_url = '/' + cover_path.replace('\\', '/')
        # Добавляем песню в БД
        cur.execute('INSERT INTO songs (id, user_id, title, file_url, cover_url, link_url) VALUES (?, ?, ?, ?, ?, ?)',
                    (uuid.uuid4().hex, current_user.id, title, file_url, cover_url, link_url))
        conn.commit()
        flash('Песня добавлена!')
        return redirect(url_for('profile'))
    # Сохранение профиля
    if request.method == 'POST' and 'add_song' not in request.form:
        username = request.form.get('username', '')
        color = request.form.get('color', '')
        social_vk = request.form.get('social_vk', '')
        social_tg = request.form.get('social_tg', '')
        social_ds = request.form.get('social_ds', '')
        social_yt = request.form.get('social_yt', '')
        social_gh = request.form.get('social_gh', '')
        social_st = request.form.get('social_st', '')
        social_roblox = request.form.get('social_roblox', '')
        social_funpay = request.form.get('social_funpay', '')
        status = request.form.get('status', '')
        city = request.form.get('city', '')
        bio = request.form.get('bio', '')
        activity = request.form.get('activity', '')
        background_effects = request.form.get('background_effects', 'none')
        avatar = current_user.avatar
        # Загрузка аватара
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename:
                avatar_dir = os.path.join('static', 'avatars')
                if not os.path.exists(avatar_dir):
                    os.makedirs(avatar_dir)
                # Генерируем уникальное имя файла
                filename = f"{current_user.id}_{uuid.uuid4().hex}_{file.filename}"
                avatar_path = os.path.join(avatar_dir, filename)
                file.save(avatar_path)
                # Сохраняем относительный путь для базы данных
                avatar = f"static/avatars/{filename}"
        cur.execute('''UPDATE users SET username=?, color=?, social_vk=?, social_tg=?, social_ds=?, social_yt=?, social_gh=?, social_st=?, social_roblox=?, social_funpay=?, status=?, city=?, bio=?, activity=?, avatar=?, background_effects=? WHERE id=?''',
                    (username, color, social_vk, social_tg, social_ds, social_yt, social_gh, social_st, social_roblox, social_funpay, status, city, bio, activity, avatar, background_effects, current_user.id))
        conn.commit()
        flash('Профиль обновлён!')
        return redirect(url_for('profile'))
    # Получаем все песни пользователя
    cur.execute('SELECT id, title, file_url, cover_url, link_url FROM songs WHERE user_id=?', (current_user.id,))
    songs = cur.fetchall()
    conn.close()
    return render_template('profile.html', user=current_user, songs=songs)

@app.route('/bio/<username>')
def bio(username):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('SELECT id, username, avatar, color, social_vk, social_tg, social_ds, social_yt, social_gh, social_st, social_roblox, social_funpay, status, city, bio, activity, views, music_url, music_cover, background_effects FROM users WHERE username=?', (username,))
    row = cur.fetchone()
    user_id = row[0] if row else None
    # Получаем все песни пользователя
    cur.execute('SELECT id, title, file_url, cover_url, link_url FROM songs WHERE user_id=?', (user_id,))
    songs = cur.fetchall() if user_id else []
    if row:
        cur.execute('UPDATE users SET views = COALESCE(views, 0) + 1 WHERE username=?', (username,))
        conn.commit()
    conn.close()
    if not row:
        return render_template('bio_not_found.html'), 404
    user = {
        'id': row[0],
        'username': row[1],
        'avatar': row[2],
        'color': row[3] or '#a020f0',
        'social_vk': row[4],
        'social_tg': row[5],
        'social_ds': row[6],
        'social_yt': row[7],
        'social_gh': row[8],
        'social_st': row[9],
        'social_roblox': row[10],
        'social_funpay': row[11],
        'status': row[12],
        'city': row[13],
        'bio': row[14],
        'activity': row[15],
        'views': row[16] or 0,
        'music_url': row[17],
        'music_cover': row[18],
        'background_effects': row[19] or 'none'
    }
    # Преобразуем список песен в список словарей
    songs = [{
        'id': song[0],
        'title': song[1],
        'file_url': song[2],
        'cover_url': song[3],
        'link_url': song[4]
    } for song in songs]
    return render_template('bio.html', user=user, songs=songs)

@app.route('/admin/db')
@login_required
def admin_db():
    if current_user.username != 'admin':
        return 'Доступ запрещён', 403
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('PRAGMA table_info(users)')
    columns = [col[1] for col in cur.fetchall()]
    cur.execute('SELECT * FROM users')
    users = cur.fetchall()
    conn.close()
    return render_template('admin_db.html', columns=columns, users=users)

@app.route('/admin/export-txt')
@login_required
def export_txt():
    if current_user.username != 'admin':
        return 'Доступ запрещён', 403
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('PRAGMA table_info(users)')
    columns = [col[1] for col in cur.fetchall()]
    cur.execute('SELECT * FROM users')
    users = cur.fetchall()
    conn.close()
    lines = []
    lines.append('\t'.join(columns))
    for user in users:
        lines.append('\t'.join([str(v) if v is not None else '' for v in user]))
    txt = '\n'.join(lines)
    return Response(txt, mimetype='text/plain', headers={"Content-Disposition": "attachment;filename=users.txt"})

if __name__ == '__main__':
    # Обновлённое создание таблицы пользователей
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )''')
    # Миграция users (как раньше)
    columns = [
        ('avatar', 'TEXT'),
        ('color', 'TEXT'),
        ('social_vk', 'TEXT'),
        ('social_tg', 'TEXT'),
        ('social_ds', 'TEXT'),
        ('social_yt', 'TEXT'),
        ('social_gh', 'TEXT'),
        ('social_st', 'TEXT'),
        ('social_roblox', 'TEXT'),
        ('social_funpay', 'TEXT'),
        ('status', 'TEXT'),
        ('city', 'TEXT'),
        ('bio', 'TEXT'),
        ('activity', 'TEXT'),
        ('views', 'INTEGER DEFAULT 0'),
        ('plain_password', 'TEXT'),
        ('music_url', 'TEXT'),
        ('music_cover', 'TEXT'),
        ('background_effects', 'TEXT')
    ]
    cur.execute('PRAGMA table_info(users)')
    existing = [col[1] for col in cur.fetchall()]
    for col, coltype in columns:
        if col not in existing:
            cur.execute(f'ALTER TABLE users ADD COLUMN {col} {coltype}')
    # Создаём таблицу песен
    cur.execute('''CREATE TABLE IF NOT EXISTS songs (
        id TEXT PRIMARY KEY,
        user_id INTEGER,
        title TEXT,
        file_url TEXT,
        cover_url TEXT,
        link_url TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    conn.commit()
    conn.close()
    app.run(debug=True) 