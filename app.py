import os
import secrets
import shutil
import json
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///models.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config['ADMIN_USERNAME'] = os.environ.get('ADMIN_USERNAME', 'admin')
app.config['ADMIN_PASSWORD'] = os.environ.get('ADMIN_PASSWORD', 'admin')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

class Girl(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    avatar = db.Column(db.String(500))
    photos = db.Column(db.String(2000))
    video = db.Column(db.String(500))
    tags = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def sanitize_filename(filename):
    filename = os.path.basename(filename)
    filename = ''.join(c for c in filename if c.isalnum() or c in '._-абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
    return filename[:200]

def sanitize_folder_name(name):
    name = name.strip()
    name = ''.join(c if c.isalnum() or c in ' _-абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ' else '_' for c in name)
    return name[:50]

def get_base_dir():
    if os.path.exists('/app'):
        return '/app'
    return os.path.dirname(os.path.abspath(__file__))

def get_model_folder(model_name):
    folder = os.path.join(get_base_dir(), 'uploads', model_name)
    os.makedirs(folder, exist_ok=True)
    return folder

def get_upload_folder():
    return os.path.join(get_base_dir(), 'uploads')

def delete_folder(folder_path):
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        shutil.rmtree(folder_path)

def init_db():
    db.create_all()
    sync_models_from_folders()

def sync_models_from_folders():
    base_dir = get_base_dir()
    uploads_dir = os.path.join(base_dir, 'uploads')
    
    if not os.path.exists(uploads_dir):
        return
    
    existing_folders = set()
    
    for folder_name in os.listdir(uploads_dir):
        folder_path = os.path.join(uploads_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue
        
        existing_folders.add(folder_name)
        folder_name_safe = folder_name.strip()
        
        existing = Girl.query.filter_by(name=folder_name_safe).first()
        
        if not existing:
            girl = Girl(name=folder_name_safe)
            db.session.add(girl)
            db.session.commit()
            existing = girl
        
        avatar_file = None
        photo_files = []
        video_file = None
        
        avatar_folder = os.path.join(folder_path, 'avatar')
        photo_folder = os.path.join(folder_path, 'photo')
        video_folder = os.path.join(folder_path, 'video')
        
        image_ext = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')
        video_ext = ('.mp4', '.webm', '.avi', '.mov', '.mkv')
        
        print(f"Processing: {folder_name}")
        
        if os.path.exists(avatar_folder):
            avatar_files = os.listdir(avatar_folder)
            for f in avatar_files:
                ext = os.path.splitext(f)[1].lower()
                if ext in image_ext:
                    avatar_file = os.path.join(folder_name, 'avatar', f).replace('\\', '/')
                    break
        
        if os.path.exists(photo_folder):
            photo_list = os.listdir(photo_folder)
            for f in photo_list:
                ext = os.path.splitext(f)[1].lower()
                if ext in image_ext:
                    photo_files.append(os.path.join(folder_name, 'photo', f).replace('\\', '/'))
        
        if os.path.exists(video_folder):
            for f in os.listdir(video_folder):
                ext = os.path.splitext(f)[1].lower()
                if ext in video_ext:
                    video_file = os.path.join(folder_name, 'video', f).replace('\\', '/')
                    break
        
        if avatar_file:
            existing.avatar = avatar_file
        if photo_files:
            existing.photos = ','.join(photo_files)
        if video_file:
            existing.video = video_file
        
        db.session.commit()
    
    for girl in Girl.query.all():
        if girl.name not in existing_folders:
            db.session.delete(girl)
    
    db.session.commit()

with app.app_context():
    init_db()

CSS = '''
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
:root {
    --bg-primary: #0f0f1a;
    --bg-secondary: #1a1a2e;
    --bg-card: rgba(30, 30, 50, 0.8);
    --bg-glass: rgba(255, 255, 255, 0.05);
    --text-primary: #ffffff;
    --text-secondary: #a0a0b0;
    --accent: #8b5cf6;
    --accent-secondary: #ec4899;
    --accent-gradient: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%);
    --border: rgba(255, 255, 255, 0.1);
    --shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    --radius: 16px;
    --radius-sm: 8px;
}
[data-theme="light"] {
    --bg-primary: #f0f2f8;
    --bg-secondary: #ffffff;
    --bg-card: rgba(255, 255, 255, 0.9);
    --bg-glass: rgba(255, 255, 255, 0.5);
    --text-primary: #1a1a2e;
    --text-secondary: #6b7280;
    --accent: #8b5cf6;
    --accent-secondary: #ec4899;
    --accent-gradient: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%);
    --border: rgba(0, 0, 0, 0.1);
    --shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15);
}
[data-theme="oled"] {
    --bg-primary: #000000;
    --bg-secondary: #0a0a0a;
    --bg-card: #111111;
    --text-primary: #ffffff;
    --text-secondary: #808080;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg-primary); color: var(--text-primary); min-height: 100vh; line-height: 1.6; -webkit-font-smoothing: antialiased; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
.container { max-width: 1400px; margin: 0 auto; padding: 40px 24px; }
header { display: flex; justify-content: space-between; align-items: center; padding: 20px 0; margin-bottom: 48px; flex-wrap: wrap; gap: 20px; }
.header-left { display: flex; align-items: center; gap: 16px; }
.logo { font-size: 1.75rem; font-weight: 700; background: var(--accent-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.header-controls { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.btn { display: inline-flex; align-items: center; gap: 8px; padding: 12px 20px; border-radius: 12px; font-size: 0.9rem; font-weight: 500; text-decoration: none; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); cursor: pointer; border: none; background: var(--bg-glass); color: var(--text-primary); backdrop-filter: blur(10px); border: 1px solid var(--border); }
.btn:hover { transform: translateY(-2px); box-shadow: var(--shadow); background: var(--bg-card); }
.btn-primary { background: var(--accent-gradient); color: white; border: none; box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3); }
.btn-primary:hover { box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4); }
.btn-danger { background: #ef4444; color: white; border: none; }
.btn-sm { padding: 8px 14px; font-size: 0.8rem; }
.theme-select { padding: 12px 16px; border-radius: 12px; background: var(--bg-glass); border: 1px solid var(--border); color: var(--text-primary); font-size: 0.9rem; cursor: pointer; backdrop-filter: blur(10px); }
.search-section { margin-bottom: 32px; }
.search-box { position: relative; max-width: 600px; }
.search-box input { width: 100%; padding: 16px 24px 16px 52px; border-radius: 16px; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-primary); font-size: 1rem; transition: all 0.3s; backdrop-filter: blur(10px); }
.search-box input:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.1); }
.search-box::before { content: "🔍"; position: absolute; left: 18px; top: 50%; transform: translateY(-50%); font-size: 1.1rem; opacity: 0.5; }
.filter-bar { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 32px; }
.filter-btn { padding: 10px 20px; border-radius: 12px; border: 1px solid var(--border); background: var(--bg-glass); color: var(--text-secondary); cursor: pointer; transition: all 0.3s; text-decoration: none; font-size: 0.9rem; backdrop-filter: blur(10px); }
.filter-btn:hover, .filter-btn.active { background: var(--accent-gradient); color: white; border-color: transparent; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 48px; }
.stat-card { background: var(--bg-card); border-radius: var(--radius); padding: 28px; border: 1px solid var(--border); backdrop-filter: blur(20px); transition: all 0.3s; }
.stat-card:hover { transform: translateY(-4px); box-shadow: var(--shadow); }
.stat-value { font-size: 2.5rem; font-weight: 700; background: var(--accent-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px; }
.stat-label { font-size: 0.9rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }
.models-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 28px; }
.model-card { background: var(--bg-card); border-radius: var(--radius); overflow: hidden; border: 1px solid var(--border); transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); cursor: pointer; position: relative; backdrop-filter: blur(20px); }
.model-card:hover { transform: translateY(-8px) scale(1.02); box-shadow: var(--shadow); }
.model-image { width: 100%; height: 280px; object-fit: cover; background: linear-gradient(135deg, var(--bg-secondary), var(--bg-primary)); }
.model-image-placeholder { width: 100%; height: 280px; display: flex; align-items: center; justify-content: center; font-size: 4rem; background: var(--bg-glass); color: var(--text-secondary); }
.model-content { padding: 24px; }
.model-name { font-size: 1.4rem; font-weight: 600; margin-bottom: 12px; color: var(--text-primary); }
.model-desc { font-size: 0.95rem; color: var(--text-secondary); margin-bottom: 16px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.5; }
.model-tags { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
.tag { padding: 6px 14px; background: var(--bg-glass); border-radius: 20px; font-size: 0.8rem; color: var(--accent); border: 1px solid var(--accent); backdrop-filter: blur(10px); }
.model-media { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.model-media img { width: 100%; height: 60px; object-fit: cover; border-radius: var(--radius-sm); cursor: pointer; transition: transform 0.3s; }
.model-media img:hover { transform: scale(1.1); }
.photo-count { font-size: 0.85rem; color: var(--text-secondary); margin-top: 12px; text-align: center; }
.model-actions { position: absolute; top: 16px; right: 16px; display: flex; gap: 10px; opacity: 0; transition: opacity 0.3s; }
.model-card:hover .model-actions { opacity: 1; }
.empty-state { text-align: center; padding: 100px 20px; }
.empty-state-icon { font-size: 5rem; margin-bottom: 24px; opacity: 0.3; }
.empty-state-text { font-size: 1.2rem; color: var(--text-secondary); }
.media-section { background: var(--bg-card); border-radius: var(--radius); padding: 32px; margin-bottom: 24px; border: 1px solid var(--border); backdrop-filter: blur(20px); }
.media-section h2 { font-size: 1.2rem; color: var(--text-secondary); margin-bottom: 20px; display: flex; align-items: center; gap: 12px; }
.media-section h2 span { background: var(--accent-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.avatar-full { width: 320px; height: 320px; object-fit: cover; border-radius: var(--radius); margin: 0 auto; display: block; box-shadow: var(--shadow); cursor: pointer; transition: transform 0.3s; }
.avatar-full:hover { transform: scale(1.03); }
.photo-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }
.photo-grid img { width: 100%; height: 200px; object-fit: cover; border-radius: var(--radius); cursor: pointer; transition: all 0.3s; box-shadow: var(--shadow); }
.photo-grid img:hover { transform: scale(1.05); box-shadow: 0 30px 60px rgba(0, 0, 0, 0.3); }
.video-container { border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow); }
.video-container video { width: 100%; border-radius: var(--radius); display: block; }
.empty-media { text-align: center; padding: 60px; color: var(--text-secondary); font-size: 1.1rem; }
.back-btn { display: inline-flex; align-items: center; gap: 8px; color: var(--accent); text-decoration: none; font-weight: 500; padding: 12px 20px; border-radius: 12px; background: var(--bg-glass); border: 1px solid var(--border); transition: all 0.3s; backdrop-filter: blur(10px); }
.back-btn:hover { background: var(--bg-card); transform: translateX(-4px); }
.model-header { text-align: center; padding: 60px 0; }
.model-header h2 { font-size: 3rem; font-weight: 700; margin-bottom: 20px; background: var(--accent-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

.detail-actions { display: flex; justify-content: center; gap: 16px; margin-top: 32px; }
.current-file { font-size: 0.85rem; color: var(--text-secondary); margin-top: 8px; padding: 8px 12px; background: var(--bg-glass); border-radius: var(--radius-sm); display: inline-block; }
.pagination { display: flex; justify-content: center; gap: 8px; margin-top: 60px; flex-wrap: wrap; }
.pagination a { min-width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; border-radius: 12px; background: var(--bg-card); color: var(--text-primary); text-decoration: none; transition: all 0.3s; border: 1px solid var(--border); }
.pagination a:hover { background: var(--bg-glass); }
.pagination a.active { background: var(--accent-gradient); color: white; border-color: transparent; }
.pagination a.disabled { opacity: 0.3; pointer-events: none; }
.lightbox { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); z-index: 3000; justify-content: center; align-items: center; backdrop-filter: blur(20px); }
.lightbox.active { display: flex; }
.lightbox img { max-width: 90%; max-height: 90%; border-radius: var(--radius); box-shadow: 0 50px 100px rgba(0, 0, 0, 0.5); }
.lightbox-close { position: absolute; top: 24px; right: 24px; width: 52px; height: 52px; border-radius: 50%; background: rgba(255,255,255,0.1); border: none; color: white; font-size: 1.8rem; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.3s; }
.lightbox-close:hover { background: rgba(255,255,255,0.2); transform: rotate(90deg); }
.lightbox-nav { position: absolute; top: 50%; transform: translateY(-50%); width: 52px; height: 52px; border-radius: 50%; background: rgba(255,255,255,0.1); border: none; color: white; font-size: 1.5rem; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.3s; }
.lightbox-nav:hover { background: rgba(255,255,255,0.2); }
.lightbox-nav.prev { left: 24px; }
.lightbox-nav.next { right: 24px; }
.modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 2000; justify-content: center; align-items: center; backdrop-filter: blur(10px); }
.modal.active { display: flex; }
.modal-content { background: var(--bg-secondary); border-radius: var(--radius); padding: 40px; max-width: 600px; width: 90%; max-height: 90vh; overflow-y: auto; box-shadow: var(--shadow); border: 1px solid var(--border); animation: modalIn 0.3s ease; }
@keyframes modalIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; }
.modal-header h2 { font-size: 1.5rem; font-weight: 600; }
.modal-close { width: 40px; height: 40px; border-radius: 50%; background: var(--bg-glass); border: none; font-size: 1.5rem; cursor: pointer; color: var(--text-secondary); display: flex; align-items: center; justify-content: center; transition: all 0.3s; }
.modal-close:hover { background: var(--bg-card); color: var(--text-primary); }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.form-group { display: flex; flex-direction: column; gap: 10px; }
.form-group label { font-size: 0.9rem; color: var(--text-secondary); font-weight: 500; }
.form-group input, .form-group textarea { padding: 16px 20px; border-radius: 12px; border: 1px solid var(--border); background: var(--bg-primary); color: var(--text-primary); font-size: 1rem; transition: all 0.3s; font-family: inherit; }
.form-group input:focus, .form-group textarea:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.1); }
.form-group textarea { min-height: 120px; resize: vertical; grid-column: 1 / -1; }
.form-group input[type="file"] { padding: 20px; border: 2px dashed var(--border); border-radius: 12px; background: var(--bg-primary); cursor: pointer; }
.form-group input[type="file"]::file-selector-button { background: var(--accent-gradient); color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; margin-right: 16px; font-weight: 500; }
.btn-submit { grid-column: 1 / -1; padding: 18px; border-radius: 14px; border: none; background: var(--accent-gradient); color: white; font-size: 1.1rem; font-weight: 600; cursor: pointer; transition: all 0.3s; box-shadow: 0 8px 25px rgba(139, 92, 246, 0.3); }
.btn-submit:hover { transform: translateY(-3px); box-shadow: 0 12px 35px rgba(139, 92, 246, 0.4); }
.login-container { min-height: calc(100vh - 80px); display: flex; align-items: center; justify-content: center; padding: 40px 24px; }
.login-card { background: var(--bg-card); border-radius: var(--radius); padding: 48px; max-width: 440px; width: 100%; border: 1px solid var(--border); backdrop-filter: blur(20px); box-shadow: var(--shadow); }
.login-card h2 { text-align: center; margin-bottom: 32px; font-size: 1.75rem; background: var(--accent-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.login-card input { margin-bottom: 24px; }
@media (max-width: 768px) {
    .container { padding: 24px 16px; }
    header { flex-direction: column; align-items: flex-start; }
    .models-grid { grid-template-columns: 1fr; }
    .form-grid { grid-template-columns: 1fr; }
    .stat-card { padding: 20px; }
    .stat-value { font-size: 2rem; }
    .model-header h2 { font-size: 2rem; }

}
</style>
'''

INDEX_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Картотека моделей</title>
    ''' + CSS + '''
</head>
<body data-theme="{{ theme }}">
    <div class="container">
        <header>
            <div class="header-left">
                <span class="logo">✨ Картотека</span>
            </div>
            <div class="header-controls">
                <select class="theme-select" onchange="setTheme(this.value)">
                    <option value="light" {% if theme == 'light' %}selected{% endif %}>☀️</option>
                    <option value="dark" {% if theme == 'dark' %}selected{% endif %}>🌙</option>
                    <option value="oled" {% if theme == 'oled' %}selected{% endif %}>⚫</option>
                </select>
                {% if admin %}
                <button class="btn btn-primary" onclick="openModal('addModal')">➕ Добавить</button>
                <a href="{{ url_for('export_data') }}" class="btn">📤 Экспорт</a>
                <a href="{{ url_for('import_data') }}" class="btn">📥 Импорт</a>
                <a href="{{ url_for('logout') }}" class="btn">🚪</a>
                {% else %}
                <a href="{{ url_for('login') }}" class="btn">🔐 Вход</a>
                {% endif %}
            </div>
        </header>
        
        {% if admin %}
        <div id="addModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Добавить модель</h2>
                    <button class="modal-close" onclick="closeModal('addModal')">&times;</button>
                </div>
                <form method="post" enctype="multipart/form-data">
                    <div class="form-grid">
                        <div class="form-group">
                            <label>Имя модели</label>
                            <input type="text" name="name" placeholder="Имя" required>
                        </div>
                        <div class="form-group">
                            <label>Теги</label>
                            <input type="text" name="tags" placeholder="Через запятую">
                        </div>
                        <div class="form-group">
                            <label>Описание</label>
                            <textarea name="description" placeholder="Описание модели"></textarea>
                        </div>
                        <div class="form-group">
                            <label>📷 Аватар</label>
                            <input type="file" name="avatar" accept="image/*">
                        </div>
                        <div class="form-group">
                            <label>🖼️ Фото</label>
                            <input type="file" name="photos" accept="image/*" multiple>
                        </div>
                        <div class="form-group">
                            <label>🎬 Видео</label>
                            <input type="file" name="video" accept="video/*">
                        </div>
                        <button type="submit" class="btn-submit">Добавить</button>
                    </div>
                </form>
            </div>
        </div>
        {% endif %}
        
        <div class="search-section">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Поиск по имени или тегам..." value="{{ search }}">
            </div>
        </div>
        
        <div class="filter-bar">
            <a href="{{ url_for('index', sort='name') }}" class="filter-btn {% if sort=='name' or not sort %}active{% endif %}">А-Я</a>
            <a href="{{ url_for('index', sort='newest') }}" class="filter-btn {% if sort=='newest' %}active{% endif %}">Новые</a>
        </div>
        
        {% if stats.total_models %}
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{{ stats.total_models }}</div>
                <div class="stat-label">Моделей</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.total_photos }}</div>
                <div class="stat-label">Фото</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.total_videos }}</div>
                <div class="stat-label">Видео</div>
            </div>
        </div>
        {% endif %}
        
        {% if girls %}
        <div class="models-grid">
            {% for girl in girls %}
            <div class="model-card" onclick="window.location.href='{{ url_for('model_detail', girl_id=girl.id) }}'">
                {% if admin %}
                <div class="model-actions" onclick="event.stopPropagation()">
                    <a href="{{ url_for('edit_girl', girl_id=girl.id) }}" class="btn btn-sm btn-primary">✏️</a>
                    <a href="{{ url_for('delete_girl', girl_id=girl.id) }}" class="btn btn-sm btn-danger" onclick="return confirm('Удалить?')">🗑️</a>
                </div>
                {% endif %}
                {% if girl.avatar %}
                <img class="model-image" src="{{ url_for('uploaded_file', filename=girl.avatar) }}">
                {% else %}
                <div class="model-image-placeholder">👤</div>
                {% endif %}
                <div class="model-content">
                    <h3 class="model-name">{{ girl.name }}</h3>
                    {% if girl.description %}
                    <p class="model-desc">{{ girl.description }}</p>
                    {% endif %}
                    {% if girl.tags %}
                    <div class="model-tags">
                        {% for tag in girl.tags.split(',') %}<span class="tag">{{ tag.strip() }}</span>{% endfor %}
                    </div>
                    {% endif %}
                    {% if girl.photos %}
                    <div class="model-media">
                        {% for photo in girl.photos.split(',') %}{% if photo %}<img src="{{ url_for('uploaded_file', filename=photo) }}">{% endif %}{% endfor %}
                    </div>
                    <div class="photo-count">📷 {{ girl.photos.split(',')|length }}</div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
        
        {% if total_pages > 1 %}
        <div class="pagination">
            {% if page > 1 %}
            <a href="{{ url_for('index', page=1, sort=sort, search=search) }}">«</a>
            <a href="{{ url_for('index', page=page-1, sort=sort, search=search) }}">‹</a>
            {% endif %}
            {% for p in range(1, total_pages + 1) %}
            <a href="{{ url_for('index', page=p, sort=sort, search=search) }}" class="{% if p == page %}active{% endif %}">{{ p }}</a>
            {% endfor %}
            {% if page < total_pages %}
            <a href="{{ url_for('index', page=page+1, sort=sort, search=search) }}">›</a>
            <a href="{{ url_for('index', page=total_pages, sort=sort, search=search) }}">»</a>
            {% endif %}
        </div>
        {% endif %}
        {% else %}
        <div class="empty-state">
            <div class="empty-state-icon">📁</div>
            <p class="empty-state-text">Моделей пока нет</p>
        </div>
        {% endif %}
    </div>
    
    <div class="lightbox" id="lightbox" onclick="closeLightbox()">
        <button class="lightbox-close" onclick="closeLightbox()">&times;</button>
        <button class="lightbox-nav prev" onclick="event.stopPropagation(); lightboxPrev()">❮</button>
        <img src="" id="lightboxImg" onclick="event.stopPropagation()">
        <button class="lightbox-nav next" onclick="event.stopPropagation(); lightboxNext()">❯</button>
    </div>
    
    <script>
        let lightboxImages = [];
        let lightboxCurrent = 0;
        function setTheme(theme) {
            document.body.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
            fetch('/set-theme/' + theme);
        }
        function openLightbox(src, index) { 
            lightboxImages = Array.from(document.querySelectorAll('.photo-grid img')).map(img => img.src);
            lightboxCurrent = index || 0;
            document.getElementById('lightboxImg').src = src; 
            document.querySelector('.lightbox').classList.add('active'); 
        }
        function closeLightbox() { document.querySelector('.lightbox').classList.remove('active'); }
        function openModal(id) { document.getElementById(id).classList.add('active'); }
        function closeModal(id) { document.getElementById(id).classList.remove('active'); }
        function lightboxPrev() { lightboxCurrent = (lightboxCurrent - 1 + lightboxImages.length) % lightboxImages.length; document.getElementById('lightboxImg').src = lightboxImages[lightboxCurrent]; }
        function lightboxNext() { lightboxCurrent = (lightboxCurrent + 1) % lightboxImages.length; document.getElementById('lightboxImg').src = lightboxImages[lightboxCurrent]; }
        document.addEventListener('keydown', function(e) { if(e.key === 'Escape') closeLightbox(); if(e.key === 'ArrowLeft') lightboxPrev(); if(e.key === 'ArrowRight') lightboxNext(); });
        document.getElementById('searchInput').addEventListener('keyup', function(e) { if(e.key === 'Enter') window.location.href = '/?search=' + encodeURIComponent(this.value); });
        const saved = localStorage.getItem('theme') || 'light';
        document.body.setAttribute('data-theme', saved);
    </script>
</body>
</html>
'''

DETAIL_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ girl.name }}</title>
    ''' + CSS + '''
</head>
<body data-theme="{{ theme }}">
    <div class="container">
        <header>
            <div class="header-left">
                <span class="logo">✨ Картотека</span>
            </div>
            <div class="header-controls">
                <a href="{{ url_for('index') }}" class="back-btn">← Назад</a>
                <select class="theme-select" onchange="setTheme(this.value)">
                    <option value="light" {% if theme == 'light' %}selected{% endif %}>☀️</option>
                    <option value="dark" {% if theme == 'dark' %}selected{% endif %}>🌙</option>
                    <option value="oled" {% if theme == 'oled' %}selected{% endif %}>⚫</option>
                </select>
            </div>
        </header>
        
        <div class="model-header">
            <h2>{{ girl.name }}</h2>
            {% if admin %}
            <div class="detail-actions">
                <a href="{{ url_for('edit_girl', girl_id=girl.id) }}" class="btn btn-primary">✏️</a>
                <a href="{{ url_for('delete_girl', girl_id=girl.id) }}" class="btn btn-danger" onclick="return confirm('Удалить?')">🗑️</a>
            </div>
            {% endif %}
        </div>
        
        {% if girl.description %}
        <div class="media-section">
            <h2><span>📝</span> Описание</h2>
            <p>{{ girl.description }}</p>
        </div>
        {% endif %}
        
        {% if girl.tags %}
        <div class="media-section">
            <h2><span>🏷️</span> Теги</h2>
            <div class="model-tags">
                {% for tag in girl.tags.split(',') %}<span class="tag">{{ tag.strip() }}</span>{% endfor %}
            </div>
        </div>
        {% endif %}
        
        {% if girl.avatar %}
        <div class="media-section">
            <h2><span>📷</span> Аватар</h2>
            <img class="avatar-full" src="{{ url_for('uploaded_file', filename=girl.avatar) }}" onclick="openLightbox(this.src, 0)">
        </div>
        {% endif %}
        
        {% if girl.photos %}
        <div class="media-section">
            <h2><span>🖼️</span> Фото ({{ girl.photos.split(',')|length }})</h2>
            <div class="photo-grid">
                {% for photo in girl.photos.split(',') %}{% if photo %}<img src="{{ url_for('uploaded_file', filename=photo) }}" onclick="openLightbox(this.src, {{ loop.index0 }})">{% endif %}{% endfor %}
            </div>
        </div>
        {% endif %}
        
        {% if girl.video %}
        <div class="media-section">
            <h2><span>🎬</span> Видео</h2>
            <div class="video-container">
                <video controls>
                    <source src="{{ url_for('uploaded_file', filename=girl.video) }}" type="video/mp4">
                </video>
            </div>
        </div>
        {% elif not girl.photos and not girl.avatar %}
        <div class="media-section">
            <div class="empty-media">Нет медиафайлов</div>
        </div>
        {% endif %}
    </div>
    
    <div class="lightbox" id="lightbox" onclick="closeLightbox()">
        <button class="lightbox-close" onclick="closeLightbox()">&times;</button>
        <button class="lightbox-nav prev" onclick="event.stopPropagation(); lightboxPrev()">❮</button>
        <img src="" id="lightboxImg" onclick="event.stopPropagation()">
        <button class="lightbox-nav next" onclick="event.stopPropagation(); lightboxNext()">❯</button>
    </div>
    
    <script>
        let lightboxImages = [];
        let lightboxCurrent = 0;
        function setTheme(theme) { document.body.setAttribute('data-theme', theme); localStorage.setItem('theme', theme); fetch('/set-theme/' + theme); }
        function openLightbox(src, index) { 
            lightboxImages = Array.from(document.querySelectorAll('.photo-grid img')).map(img => img.src);
            if (lightboxImages.length === 0 && document.querySelector('.avatar-full')) {
                lightboxImages.push(document.querySelector('.avatar-full').src);
            }
            lightboxCurrent = index !== undefined ? index : 0;
            document.getElementById('lightboxImg').src = src; 
            document.querySelector('.lightbox').classList.add('active'); 
        }
        function closeLightbox() { document.querySelector('.lightbox').classList.remove('active'); }
        function openModal(id) { document.getElementById(id).classList.add('active'); }
        function closeModal(id) { document.getElementById(id).classList.remove('active'); }
        function lightboxPrev() { lightboxCurrent = (lightboxCurrent - 1 + lightboxImages.length) % lightboxImages.length; document.getElementById('lightboxImg').src = lightboxImages[lightboxCurrent]; }
        function lightboxNext() { lightboxCurrent = (lightboxCurrent + 1) % lightboxImages.length; document.getElementById('lightboxImg').src = lightboxImages[lightboxCurrent]; }
        document.addEventListener('keydown', function(e) { if(e.key === 'Escape') closeLightbox(); if(e.key === 'ArrowLeft') lightboxPrev(); if(e.key === 'ArrowRight') lightboxNext(); });
        const saved = localStorage.getItem('theme') || 'light';
        document.body.setAttribute('data-theme', saved);
    </script>
</body>
</html>
'''

EDIT_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Редактировать {{ girl.name }}</title>
    ''' + CSS + '''
</head>
<body data-theme="{{ theme }}">
    <div class="container">
        <header>
            <div class="header-left">
                <span class="logo">✨ Редактирование</span>
            </div>
            <div class="header-controls">
                <a href="{{ url_for('model_detail', girl_id=girl.id) }}" class="back-btn">← Назад</a>
                <select class="theme-select" onchange="setTheme(this.value)">
                    <option value="light" {% if theme == 'light' %}selected{% endif %}>☀️</option>
                    <option value="dark" {% if theme == 'dark' %}selected{% endif %}>🌙</option>
                    <option value="oled" {% if theme == 'oled' %}selected{% endif %}>⚫</option>
                </select>
            </div>
        </header>
        
        <div class="media-section">
            <form method="post" enctype="multipart/form-data">
                <div class="form-grid">
                    <div class="form-group">
                        <label>Имя</label>
                        <input type="text" name="name" value="{{ girl.name }}" required>
                    </div>
                    <div class="form-group">
                        <label>Теги</label>
                        <input type="text" name="tags" value="{{ girl.tags or '' }}" placeholder="Через запятую">
                    </div>
                    <div class="form-group">
                        <label>Описание</label>
                        <textarea name="description">{{ girl.description or '' }}</textarea>
                    </div>
                    <div class="form-group">
                        <label>📷 Аватар</label>
                        {% if girl.avatar %}<div class="current-file">Текущий: {{ girl.avatar.split('/')[-1] }}</div>{% endif %}
                        <input type="file" name="avatar" accept="image/*">
                    </div>
                    <div class="form-group">
                        <label>🖼️ Фото</label>
                        {% if girl.photos %}<div class="current-file">Текущих: {{ girl.photos.split(',')|length }}</div>{% endif %}
                        <input type="file" name="photos" accept="image/*" multiple>
                    </div>
                    <div class="form-group">
                        <label>🎬 Видео</label>
                        {% if girl.video %}<div class="current-file">Текущее: {{ girl.video.split('/')[-1] }}</div>{% endif %}
                        <input type="file" name="video" accept="video/*">
                    </div>
                    <button type="submit" class="btn-submit">💾 Сохранить</button>
                </div>
            </form>
        </div>
    </div>
    
    <script>
        function setTheme(theme) { document.body.setAttribute('data-theme', theme); localStorage.setItem('theme', theme); fetch('/set-theme/' + theme); }
        const saved = localStorage.getItem('theme') || 'light';
        document.body.setAttribute('data-theme', saved);
    </script>
</body>
</html>
'''

LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Вход</title>
    ''' + CSS + '''
</head>
<body data-theme="{{ theme }}">
    <div class="container">
        <header>
            <div class="header-left">
                <span class="logo">✨ Картотека</span>
            </div>
            <div class="header-controls">
                <a href="{{ url_for('index') }}" class="back-btn">← На главную</a>
                <select class="theme-select" onchange="setTheme(this.value)">
                    <option value="light" {% if theme == 'light' %}selected{% endif %}>☀️</option>
                    <option value="dark" {% if theme == 'dark' %}selected{% endif %}>🌙</option>
                    <option value="oled" {% if theme == 'oled' %}selected{% endif %}>⚫</option>
                </select>
            </div>
        </header>
        
        <div class="login-container">
            <div class="login-card">
                <h2>🔐 Вход</h2>
                <form method="post">
                    <div class="form-group">
                        <label>Логин</label>
                        <input type="text" name="username" placeholder="Введите логин" required>
                    </div>
                    <div class="form-group">
                        <label>Пароль</label>
                        <input type="password" name="password" placeholder="Введите пароль" required>
                    </div>
                    <button type="submit" class="btn-submit">🔐 Войти</button>
                </form>
            </div>
        </div>
    </div>
    
    <script>
        function setTheme(theme) { document.body.setAttribute('data-theme', theme); localStorage.setItem('theme', theme); fetch('/set-theme/' + theme); }
        const saved = localStorage.getItem('theme') || 'light';
        document.body.setAttribute('data-theme', saved);
    </script>
</body>
</html>
'''

PER_PAGE = 12

@app.route('/')
def index():
    theme = session.get('theme', 'light')
    admin = session.get('admin', False)
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'name')
    page = int(request.args.get('page', 1))
    
    query = Girl.query
    
    if search:
        search_term = f'%{search}%'
        query = query.filter((Girl.name.ilike(search_term)) | (Girl.tags.ilike(search_term)))
    
    if sort == 'newest':
        query = query.order_by(Girl.created_at.desc())
    else:
        query = query.order_by(Girl.name)
    
    total = query.count()
    total_pages = (total + PER_PAGE - 1) // PER_PAGE if total > 0 else 1
    girls = query.offset((page - 1) * PER_PAGE).limit(PER_PAGE).all()
    
    stats = {
        'total_models': total,
        'total_photos': sum(len(g.photos.split(',')) if g.photos else 0 for g in girls),
        'total_videos': sum(1 for g in girls if g.video)
    }
    
    return render_template_string(INDEX_HTML, girls=girls, theme=theme, admin=admin, stats=stats, 
                                search=search, sort=sort, page=page, total_pages=total_pages)

@app.route('/model/<int:girl_id>')
def model_detail(girl_id):
    theme = session.get('theme', 'light')
    girl = Girl.query.get_or_404(girl_id)
    return render_template_string(DETAIL_HTML, girl=girl, theme=theme)

@app.route('/edit/<int:girl_id>')
def edit_girl(girl_id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    theme = session.get('theme', 'light')
    girl = Girl.query.get_or_404(girl_id)
    return render_template_string(EDIT_HTML, girl=girl, theme=theme)

@app.route('/edit/<int:girl_id>', methods=['POST'])
def edit_girl_post(girl_id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    girl = Girl.query.get_or_404(girl_id)
    old_folder = sanitize_folder_name(girl.name)
    
    name = request.form.get('name')
    if not name or not name.strip():
        return redirect(url_for('edit_girl', girl_id=girl_id))
    
    new_folder = sanitize_folder_name(name.strip())
    girl.name = name.strip()
    girl.description = request.form.get('description', '')
    girl.tags = request.form.get('tags', '')
    
    model_folder = get_model_folder(new_folder)
    
    avatar_folder = os.path.join(model_folder, 'avatar')
    photo_folder = os.path.join(model_folder, 'photo')
    video_folder = os.path.join(model_folder, 'video')
    os.makedirs(avatar_folder, exist_ok=True)
    os.makedirs(photo_folder, exist_ok=True)
    os.makedirs(video_folder, exist_ok=True)
    
    def save_file(file, old_path, subfolder):
        if file and file.filename:
            try:
                safe_name = sanitize_filename(file.filename)
                filepath = os.path.join(model_folder, subfolder, safe_name)
                file.save(filepath)
                return f"{new_folder}/{subfolder}/{safe_name}"
            except Exception:
                return old_path
        return old_path
    
    avatar_file = request.files.get('avatar')
    photos_files = request.files.getlist('photos')
    video_file = request.files.get('video')
    
    if avatar_file and avatar_file.filename:
        girl.avatar = save_file(avatar_file, girl.avatar, 'avatar')
    
    if photos_files and photos_files[0].filename:
        new_photos = list(filter(None, (girl.photos or '').split(',')))
        for pf in photos_files:
            if pf.filename:
                try:
                    safe_name = sanitize_filename(pf.filename)
                    filepath = os.path.join(model_folder, 'photo', safe_name)
                    pf.save(filepath)
                    new_photos.append(f"{new_folder}/photo/{safe_name}")
                except Exception:
                    pass
        if new_photos:
            girl.photos = ','.join(new_photos)
    
    if video_file and video_file.filename:
        girl.video = save_file(video_file, girl.video, 'video')
    
    db.session.commit()
    
    if old_folder != new_folder:
        old_path = os.path.join(get_upload_folder(), old_folder)
        if os.path.exists(old_path):
            delete_folder(old_path)
    
    return redirect(url_for('model_detail', girl_id=girl_id))

@app.route('/delete/<int:girl_id>')
def delete_girl(girl_id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    girl = Girl.query.get_or_404(girl_id)
    folder_name = sanitize_folder_name(girl.name)
    folder_path = os.path.join(get_upload_folder(), folder_name)
    
    db.session.delete(girl)
    db.session.commit()
    
    if os.path.exists(folder_path):
        delete_folder(folder_path)
    
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    theme = session.get('theme', 'light')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == app.config['ADMIN_USERNAME'] and password == app.config['ADMIN_PASSWORD']:
            session['admin'] = True
            return redirect(url_for('index'))
    return render_template_string(LOGIN_HTML, theme=theme)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

@app.route('/set-theme/<theme>')
def set_theme(theme):
    session['theme'] = theme
    return '', 204

@app.route('/', methods=['POST'])
def add_girl_post():
    name = request.form.get('name')
    
    if not name or not name.strip():
        return redirect(url_for('index'))
    
    girl = Girl(
        name=name.strip(),
        description=request.form.get('description', ''),
        tags=request.form.get('tags', '')
    )
    db.session.add(girl)
    db.session.commit()
    
    folder_name = sanitize_folder_name(girl.name)
    model_folder = get_model_folder(folder_name)
    
    avatar_folder = os.path.join(model_folder, 'avatar')
    photo_folder = os.path.join(model_folder, 'photo')
    video_folder = os.path.join(model_folder, 'video')
    os.makedirs(avatar_folder, exist_ok=True)
    os.makedirs(photo_folder, exist_ok=True)
    os.makedirs(video_folder, exist_ok=True)
    
    def save_file(file, subfolder):
        if file and file.filename:
            try:
                safe_name = sanitize_filename(file.filename)
                filepath = os.path.join(model_folder, subfolder, safe_name)
                file.save(filepath)
                return f"{folder_name}/{subfolder}/{safe_name}"
            except Exception:
                return None
        return None
    
    def save_multiple_files(files, subfolder):
        saved = []
        for f in files:
            if f and f.filename:
                try:
                    safe_name = sanitize_filename(f.filename)
                    filepath = os.path.join(model_folder, subfolder, safe_name)
                    f.save(filepath)
                    saved.append(f"{folder_name}/{subfolder}/{safe_name}")
                except Exception:
                    pass
        return ','.join(saved) if saved else None
    
    girl.avatar = save_file(request.files.get('avatar'), 'avatar')
    girl.photos = save_multiple_files(request.files.getlist('photos'), 'photo')
    girl.video = save_file(request.files.get('video'), 'video')
    db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/export')
def export_data():
    if not session.get('admin'):
        return redirect(url_for('login'))
    girls = Girl.query.all()
    data = []
    for g in girls:
        data.append({
            'name': g.name,
            'description': g.description,
            'tags': g.tags,
            'avatar': g.avatar,
            'photos': g.photos,
            'video': g.video,
            'created_at': g.created_at.isoformat() if g.created_at else None
        })
    return json.dumps(data, ensure_ascii=False, indent=2), 200, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/import', methods=['GET', 'POST'])
def import_data():
    if not session.get('admin'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            data = json.loads(request.form.get('json_data'))
            for item in data:
                name = item.get('name', '').strip()
                if not name:
                    continue
                existing = Girl.query.filter_by(name=name).first()
                if existing:
                    existing.description = item.get('description', '')
                    existing.tags = item.get('tags', '')
                    existing.avatar = item.get('avatar', '')
                    existing.photos = item.get('photos', '')
                    existing.video = item.get('video', '')
                else:
                    girl = Girl(
                        name=name,
                        description=item.get('description', ''),
                        tags=item.get('tags', ''),
                        avatar=item.get('avatar', ''),
                        photos=item.get('photos', ''),
                        video=item.get('video', '')
                    )
                    db.session.add(girl)
                folder_name = sanitize_folder_name(name)
                model_folder = get_model_folder(folder_name)
                for subfolder in ['avatar', 'photo', 'video']:
                    os.makedirs(os.path.join(model_folder, subfolder), exist_ok=True)
            db.session.commit()
        except Exception as e:
            return f'Ошибка импорта: {str(e)}', 400
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Импорт</title>
        ''' + CSS + '''
    </head>
    <body data-theme="{{ theme }}">
        <div class="container">
            <header>
                <div class="header-left">
                    <span class="logo">✨ Импорт</span>
                </div>
                <div class="header-controls">
                    <a href="{{ url_for("index") }}" class="back-btn">← На главную</a>
                </div>
            </header>
            <div class="media-section">
                <h2>Импорт данных</h2>
                <form method="post" enctype="multipart/form-data">
                    <div class="form-group">
                        <label>JSON данные</label>
                        <textarea name="json_data" placeholder='[{"name": "Модель", "tags": "тег1, тег2", "description": "Описание"}]'></textarea>
                    </div>
                    <button type="submit" class="btn-submit">📥 Импортировать</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    ''')
def uploaded_file(filename):
    upload_folder = get_upload_folder()
    filename = filename.replace('\\', '/')
    safe_path = os.path.normpath(os.path.join(upload_folder, filename))
    if safe_path.startswith(os.path.normpath(upload_folder)):
        if os.path.exists(safe_path):
            return send_from_directory(upload_folder, filename)
    abort(404)

@app.route('/refresh')
def refresh():
    if not session.get('admin'):
        return redirect(url_for('login'))
    with app.app_context():
        init_db()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4444)
