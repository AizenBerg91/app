import os
import secrets
import shutil
import json
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///models.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

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
    filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
    return filename[:200]

def sanitize_folder_name(name):
    name = name.strip()
    name = ''.join(c if c.isalnum() or c in ' _-' else '_' for c in name)
    return name[:50]

def get_base_dir():
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
        
        existing = Girl.query.filter_by(name=folder_name).first()
        
        if not existing:
            girl = Girl(name=folder_name)
            db.session.add(girl)
            db.session.commit()
            existing = girl
        
        files = os.listdir(folder_path)
        image_ext = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
        video_ext = ('.mp4', '.webm', '.avi', '.mov')
        
        avatar_file = None
        photo_files = []
        video_file = None
        
        for f in files:
            ext = os.path.splitext(f.lower())[1]
            full_path = os.path.join(folder_name, f)
            
            if ext in image_ext:
                if not avatar_file:
                    avatar_file = full_path
                    existing.avatar = avatar_file
                else:
                    photo_files.append(full_path)
            elif ext in video_ext:
                if not video_file:
                    video_file = full_path
                    existing.video = video_file
        
        if photo_files:
            existing.photos = ','.join(photo_files)
        
        db.session.commit()
    
    for girl in Girl.query.all():
        folder_name = sanitize_folder_name(girl.name)
        if folder_name not in existing_folders:
            db.session.delete(girl)
    
    db.session.commit()

with app.app_context():
    db.create_all()
    sync_models_from_folders()
    
    if not os.path.exists(uploads_dir):
        return
    
    existing_folders = set()
    
    for folder_name in os.listdir(uploads_dir):
        folder_path = os.path.join(uploads_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue
            
        existing_folders.add(folder_name)
        
        existing = Girl.query.filter_by(name=folder_name).first()
        
        if not existing:
            girl = Girl(name=folder_name)
            db.session.add(girl)
            db.session.commit()
            existing = girl
        
        files = os.listdir(folder_path)
        image_ext = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
        video_ext = ('.mp4', '.webm', '.avi', '.mov')
        
        avatar_file = None
        photo_files = []
        video_file = None
        
        for f in files:
            ext = os.path.splitext(f.lower())[1]
            full_path = os.path.join(folder_name, f)
            
            if ext in image_ext:
                if not existing.avatar or 'avatar' in f.lower():
                    if not avatar_file:
                        avatar_file = full_path
                        existing.avatar = avatar_file
                else:
                    photo_files.append(full_path)
            elif ext in video_ext:
                if not existing.video:
                    video_file = full_path
                    existing.video = video_file
        
        if photo_files and not existing.photos:
            existing.photos = ','.join(photo_files)
        
        db.session.commit()
    
    for girl in Girl.query.all():
        folder_name = sanitize_folder_name(girl.name)
        if folder_name not in existing_folders:
            db.session.delete(girl)
    
    db.session.commit()

CSS = '''
<style>
    :root { --bg-primary: #f8f9fc; --bg-secondary: #ffffff; --bg-card: #ffffff; --text-primary: #1a1a2e; --text-secondary: #6b7280; --accent: #6366f1; --accent-hover: #4f46e5; --border: #e5e7eb; --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
    [data-theme="dark"] { --bg-primary: #0f0f1a; --bg-secondary: #1a1a2e; --bg-card: #252542; --text-primary: #f1f5f9; --text-secondary: #94a3b8; --accent: #818cf8; --accent-hover: #6366f1; --border: #374151; --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4); }
    [data-theme="oled"] { --bg-primary: #000000; --bg-secondary: #0a0a0a; --bg-card: #111111; --text-primary: #f1f5f9; --text-secondary: #94a3b8; --accent: #818cf8; --accent-hover: #6366f1; --border: #222222; --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.6); }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Inter', sans-serif; background: var(--bg-primary); color: var(--text-primary); min-height: 100vh; transition: background 0.3s, color 0.3s; }
    .container { max-width: 1200px; margin: 0 auto; padding: 30px 20px; }
    header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; flex-wrap: wrap; gap: 15px; }
    h1 { font-size: 2rem; font-weight: 700; background: linear-gradient(135deg, var(--accent), #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .header-controls { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    .theme-toggle, .btn { background: var(--bg-card); border: 1px solid var(--border); padding: 10px 16px; border-radius: 25px; cursor: pointer; font-size: 1rem; transition: all 0.3s; color: var(--text-primary); text-decoration: none; display: inline-flex; align-items: center; gap: 6px; }
    .theme-toggle:hover, .btn:hover { transform: scale(1.05); box-shadow: var(--shadow); }
    .btn-edit { background: var(--accent); color: white; border: none; }
    .btn-delete { background: #ef4444; color: white; border: none; }
    .search-box { display: flex; gap: 10px; margin-bottom: 25px; flex-wrap: wrap; }
    .search-box input { flex: 1; min-width: 200px; padding: 12px 18px; border: 2px solid var(--border); border-radius: 25px; font-size: 1rem; background: var(--bg-card); color: var(--text-primary); }
    .search-box input:focus { outline: none; border-color: var(--accent); }
    .filters { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 25px; }
    .filter-btn { padding: 8px 16px; border-radius: 20px; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-primary); cursor: pointer; transition: all 0.3s; text-decoration: none; }
    .filter-btn.active { background: var(--accent); color: white; border-color: var(--accent); }
    .stats-bar { display: flex; gap: 20px; padding: 20px; background: var(--bg-card); border-radius: 15px; margin-bottom: 30px; flex-wrap: wrap; }
    .stat-item { text-align: center; }
    .stat-value { font-size: 1.5rem; font-weight: 700; color: var(--accent); }
    .stat-label { font-size: 0.85rem; color: var(--text-secondary); }
    .add-form, .edit-form { background: var(--bg-card); border-radius: 20px; padding: 30px; margin-bottom: 30px; box-shadow: var(--shadow); border: 1px solid var(--border); }
    .add-form h2, .edit-form h2 { margin-bottom: 20px; font-size: 1.3rem; }
    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
    input[type="text"], textarea { padding: 14px 18px; border: 2px solid var(--border); border-radius: 12px; font-size: 1rem; background: var(--bg-primary); color: var(--text-primary); width: 100%; }
    input[type="text"]:focus, textarea:focus { outline: none; border-color: var(--accent); }
    textarea { min-height: 100px; resize: vertical; grid-column: 1 / -1; }
    .file-input-group { display: flex; flex-direction: column; gap: 8px; }
    .file-input-group label { font-size: 0.85rem; color: var(--text-secondary); font-weight: 500; }
    input[type="file"] { padding: 10px; border: 2px dashed var(--border); border-radius: 12px; background: var(--bg-primary); }
    input[type="file"]::file-selector-button { background: var(--accent); color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; margin-right: 15px; }
    .btn-submit { grid-column: 1 / -1; background: linear-gradient(135deg, var(--accent), #ec4899); color: white; border: none; padding: 16px; border-radius: 12px; font-size: 1.1rem; font-weight: 600; cursor: pointer; }
    .btn-submit:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(99, 102, 241, 0.3); }
    .models-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 25px; }
    .model-card { background: var(--bg-card); border-radius: 20px; overflow: hidden; box-shadow: var(--shadow); border: 1px solid var(--border); transition: transform 0.3s, box-shadow 0.3s; cursor: pointer; position: relative; }
    .model-card:hover { transform: translateY(-5px); box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15); }
    .model-avatar { width: 100%; height: 220px; object-fit: cover; background: var(--bg-primary); }
    .model-info { padding: 20px; }
    .model-name { font-size: 1.3rem; font-weight: 600; margin-bottom: 8px; color: var(--text-primary); }
    .model-desc { font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 10px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    .model-tags { display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 10px; }
    .tag { padding: 4px 10px; background: var(--accent); color: white; border-radius: 15px; font-size: 0.75rem; }
    .model-meta { font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 10px; }
    .model-media { display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 8px; }
    .model-media img { width: 100%; height: 80px; object-fit: cover; border-radius: 8px; background: var(--bg-primary); cursor: pointer; }
    .model-actions { position: absolute; top: 10px; right: 10px; display: flex; gap: 8px; z-index: 10; }
    .model-actions .btn { padding: 8px 12px; font-size: 0.9rem; border-radius: 10px; }
    .empty-state { text-align: center; padding: 60px 20px; color: var(--text-secondary); }
    .media-section { background: var(--bg-card); border-radius: 20px; padding: 30px; margin-bottom: 25px; box-shadow: var(--shadow); border: 1px solid var(--border); }
    .media-section h2 { font-size: 1.2rem; color: var(--text-secondary); margin-bottom: 20px; }
    .avatar-full { width: 300px; height: 300px; object-fit: cover; border-radius: 20px; margin: 0 auto; display: block; box-shadow: var(--shadow); cursor: zoom-in; }
    .photo-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 15px; }
    .photo-grid img { width: 100%; height: 180px; object-fit: cover; border-radius: 15px; box-shadow: var(--shadow); cursor: zoom-in; transition: transform 0.3s; }
    .photo-grid img:hover { transform: scale(1.05); }
    .video-container video { width: 100%; border-radius: 15px; box-shadow: var(--shadow); }
    .empty-media { text-align: center; padding: 40px; color: var(--text-secondary); }
    .back-btn { display: inline-flex; align-items: center; gap: 8px; color: var(--accent); text-decoration: none; font-weight: 500; margin-bottom: 30px; }
    .back-btn:hover { opacity: 0.7; }
    .model-header { text-align: center; margin-bottom: 40px; }
    .model-header h1 { font-size: 2.5rem; margin-bottom: 10px; }
    .detail-actions { display: flex; justify-content: center; gap: 15px; margin-top: 20px; flex-wrap: wrap; }
    .detail-meta { display: flex; justify-content: center; gap: 25px; color: var(--text-secondary); margin-bottom: 20px; flex-wrap: wrap; }
    .current-file { font-size: 0.85rem; color: var(--text-secondary); margin-top: 5px; }
    .pagination { display: flex; justify-content: center; gap: 10px; margin-top: 40px; flex-wrap: wrap; }
    .pagination a { padding: 10px 15px; border-radius: 10px; background: var(--bg-card); color: var(--text-primary); text-decoration: none; }
    .pagination a.active { background: var(--accent); color: white; }
    .lightbox { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 1000; justify-content: center; align-items: center; cursor: zoom-out; }
    .lightbox img { max-width: 90%; max-height: 90%; border-radius: 10px; }
    .lightbox.active { display: flex; }
    .login-form { max-width: 400px; margin: 100px auto; padding: 40px; background: var(--bg-card); border-radius: 20px; box-shadow: var(--shadow); }
    .login-form h2 { text-align: center; margin-bottom: 30px; }
    .login-form input { margin-bottom: 20px; }
    .login-form .btn-submit { width: 100%; }
    .export-import { display: flex; gap: 10px; margin-left: auto; }
    @media (max-width: 600px) { .form-grid { grid-template-columns: 1fr; } h1 { font-size: 1.5rem; } .header-controls { width: 100%; justify-content: space-between; } }
</style>
'''

INDEX_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Картатека моделей</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    ''' + CSS + '''
</head>
<body data-theme="{{ theme }}">
    <div class="container">
        <header>
            <h1>✨ Картатека моделей</h1>
            <div class="header-controls">
                <select class="theme-toggle" onchange="setTheme(this.value)">
                    <option value="light" {% if theme == 'light' %}selected{% endif %}>☀️</option>
                    <option value="dark" {% if theme == 'dark' %}selected{% endif %}>🌙</option>
                    <option value="oled" {% if theme == 'oled' %}selected{% endif %}>⚫</option>
                </select>
                {% if admin %}
                <a href="{{ url_for('export_data') }}" class="btn">📤 Экспорт</a>
                <a href="{{ url_for('logout') }}" class="btn">🚪 Выход</a>
                {% else %}
                <a href="{{ url_for('login') }}" class="btn">🔐 Вход</a>
                {% endif %}
            </div>
        </header>
        
        {% if admin %}
        <div class="stats-bar">
            <div class="stat-item"><div class="stat-value">{{ stats.total_models }}</div><div class="stat-label">Всего моделей</div></div>
            <div class="stat-item"><div class="stat-value">{{ stats.total_photos }}</div><div class="stat-label">Фото</div></div>
            <div class="stat-item"><div class="stat-value">{{ stats.total_videos }}</div><div class="stat-label">Видео</div></div>
        </div>
        
        <form class="add-form" method="post" enctype="multipart/form-data">
            <h2>Добавить модель</h2>
            <div class="form-grid">
                <input type="text" name="name" placeholder="Имя модели (будет создана папка)" required>
                <input type="text" name="tags" placeholder="Теги (через запятую)">
                <textarea name="description" placeholder="Описание модели"></textarea>
                <div class="file-input-group">
                    <label>📷 Аватар</label>
                    <input type="file" name="avatar" accept="image/*">
                </div>
                <div class="file-input-group">
                    <label>🖼️ Фото (можно несколько)</label>
                    <input type="file" name="photos" accept="image/*" multiple>
                </div>
                <div class="file-input-group">
                    <label>🎬 Видео</label>
                    <input type="file" name="video" accept="video/*">
                </div>
                <button type="submit" class="btn-submit">Добавить модель</button>
            </div>
        </form>
        {% endif %}
        
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Поиск по имени или тегам..." value="{{ search }}">
        </div>
        
        <div class="filters">
            <a href="{{ url_for('index', sort='name') }}" class="filter-btn {% if sort=='name' or not sort %}active{% endif %}">А-Я</a>
            <a href="{{ url_for('index', sort='newest') }}" class="filter-btn {% if sort=='newest' %}active{% endif %}">Новые</a>
        </div>
        
        {% if girls %}
        <div class="models-grid">
            {% for girl in girls %}
            <div class="model-card" onclick="window.location.href='{{ url_for('model_detail', girl_id=girl.id) }}'">
                {% if admin %}
                <div class="model-actions" onclick="event.stopPropagation()">
                    <a href="{{ url_for('edit_girl', girl_id=girl.id) }}" class="btn btn-edit">✏️</a>
                    <a href="{{ url_for('delete_girl', girl_id=girl.id) }}" class="btn btn-delete" onclick="return confirm('Удалить модель {{ girl.name }}?')">🗑️</a>
                </div>
                {% endif %}
                {% if girl.avatar %}
                <img class="model-avatar" src="{{ url_for('uploaded_file', filename=girl.avatar) }}">
                {% else %}
                <div class="model-avatar" style="display:flex;align-items:center;justify-content:center;color:var(--text-secondary)">Нет аватара</div>
                {% endif %}
                <div class="model-info">
                    <div class="model-name">{{ girl.name }}</div>
                    {% if girl.description %}
                    <div class="model-desc">{{ girl.description }}</div>
                    {% endif %}
                    {% if girl.tags %}
                    <div class="model-tags">
                        {% for tag in girl.tags.split(',') %}<span class="tag">{{ tag.strip() }}</span>{% endfor %}
                    </div>
                    {% endif %}
                    <div class="model-meta">📅 {{ girl.created_at.strftime('%d.%m.%Y') }}</div>
                    {% if girl.photos %}
                    <div class="model-media">
                        {% for photo in girl.photos.split(',') %}{% if photo %}<img src="{{ url_for('uploaded_file', filename=photo) }}">{% endif %}{% endfor %}
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
        
        {% if total_pages > 1 %}
        <div class="pagination">
            {% for p in range(1, total_pages + 1) %}
            <a href="{{ url_for('index', page=p, sort=sort, search=search) }}" class="{% if p == page %}active{% endif %}">{{ p }}</a>
            {% endfor %}
        </div>
        {% endif %}
        {% else %}
        <div class="empty-state">
            <p>Пока нет моделей. Создайте папку с именем модели в uploads!</p>
        </div>
        {% endif %}
    </div>
    
    <div class="lightbox" onclick="closeLightbox()">
        <img src="" id="lightboxImg">
    </div>
    
    <script>
        function setTheme(theme) {
            document.body.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
            fetch('/set-theme/' + theme);
        }
        function openLightbox(src) { document.getElementById('lightboxImg').src = src; document.querySelector('.lightbox').classList.add('active'); }
        function closeLightbox() { document.querySelector('.lightbox').classList.remove('active'); }
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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    ''' + CSS + '''
</head>
<body data-theme="{{ theme }}">
    <div class="container">
        <header>
            <a href="{{ url_for('index') }}" class="back-btn">← Назад</a>
            <select class="theme-toggle" onchange="setTheme(this.value)">
                <option value="light" {% if theme == 'light' %}selected{% endif %}>☀️</option>
                <option value="dark" {% if theme == 'dark' %}selected{% endif %}>🌙</option>
                <option value="oled" {% if theme == 'oled' %}selected{% endif %}>⚫</option>
            </select>
        </header>
        
        <div class="model-header">
            <h1>{{ girl.name }}</h1>
            <div class="detail-meta">
                <span>📅 {{ girl.created_at.strftime('%d.%m.%Y') }}</span>
            </div>
            {% if admin %}
            <div class="detail-actions">
                <a href="{{ url_for('edit_girl', girl_id=girl.id) }}" class="btn btn-edit">✏️ Редактировать</a>
                <a href="{{ url_for('delete_girl', girl_id=girl.id) }}" class="btn btn-delete" onclick="return confirm('Удалить модель?')">🗑️ Удалить</a>
            </div>
            {% endif %}
        </div>
        
        {% if girl.description %}
        <div class="media-section">
            <h2>📝 Описание</h2>
            <p>{{ girl.description }}</p>
        </div>
        {% endif %}
        
        {% if girl.tags %}
        <div class="media-section">
            <h2>🏷️ Теги</h2>
            <div class="model-tags">
                {% for tag in girl.tags.split(',') %}<span class="tag">{{ tag.strip() }}</span>{% endfor %}
            </div>
        </div>
        {% endif %}
        
        {% if girl.avatar %}
        <div class="media-section">
            <h2>📷 Аватар</h2>
            <img class="avatar-full" src="{{ url_for('uploaded_file', filename=girl.avatar) }}" onclick="openLightbox(this.src)">
        </div>
        {% endif %}
        
        {% if girl.photos %}
        <div class="media-section">
            <h2>🖼️ Фото ({{ girl.photos.split(',')|length }})</h2>
            <div class="photo-grid">
                {% for photo in girl.photos.split(',') %}{% if photo %}<img src="{{ url_for('uploaded_file', filename=photo) }}" onclick="openLightbox(this.src)">{% endif %}{% endfor %}
            </div>
        </div>
        {% endif %}
        
        {% if girl.video %}
        <div class="media-section">
            <h2>🎬 Видео</h2>
            <div class="video-container">
                <video controls>
                    <source src="{{ url_for('uploaded_file', filename=girl.video) }}" type="video/mp4">
                    Ваш браузер не поддерживает видео
                </video>
            </div>
        </div>
        {% elif not girl.photos and not girl.avatar %}
        <div class="media-section">
            <div class="empty-media">Нет медиафайлов</div>
        </div>
        {% endif %}
    </div>
    
    <div class="lightbox" onclick="closeLightbox()">
        <img src="" id="lightboxImg">
    </div>
    
    <script>
        function setTheme(theme) { document.body.setAttribute('data-theme', theme); localStorage.setItem('theme', theme); fetch('/set-theme/' + theme); }
        function openLightbox(src) { document.getElementById('lightboxImg').src = src; document.querySelector('.lightbox').classList.add('active'); }
        function closeLightbox() { document.querySelector('.lightbox').classList.remove('active'); }
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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    ''' + CSS + '''
</head>
<body data-theme="{{ theme }}">
    <div class="container">
        <header>
            <a href="{{ url_for('model_detail', girl_id=girl.id) }}" class="back-btn">← Назад</a>
            <select class="theme-toggle" onchange="setTheme(this.value)">
                <option value="light" {% if theme == 'light' %}selected{% endif %}>☀️</option>
                <option value="dark" {% if theme == 'dark' %}selected{% endif %}>🌙</option>
                <option value="oled" {% if theme == 'oled' %}selected{% endif %}>⚫</option>
            </select>
        </header>
        
        <form class="edit-form" method="post" enctype="multipart/form-data">
            <h2>Редактировать модель</h2>
            <div class="form-grid">
                <input type="text" name="name" value="{{ girl.name }}" required>
                <input type="text" name="tags" value="{{ girl.tags or '' }}" placeholder="Теги (через запятую)">
                <textarea name="description">{{ girl.description or '' }}</textarea>
                <div class="file-input-group">
                    <label>📷 Аватар (заменит текущий)</label>
                    {% if girl.avatar %}<div class="current-file">Текущий: {{ girl.avatar.split('/')[-1] }}</div>{% endif %}
                    <input type="file" name="avatar" accept="image/*">
                </div>
                <div class="file-input-group">
                    <label>🖼️ Фото (можно несколько, добавятся к существующим)</label>
                    {% if girl.photos %}<div class="current-file">Текущих: {{ girl.photos.split(',')|length }}</div>{% endif %}
                    <input type="file" name="photos" accept="image/*" multiple>
                </div>
                <div class="file-input-group">
                    <label>🎬 Видео (заменит текущее)</label>
                    {% if girl.video %}<div class="current-file">Текущее: {{ girl.video.split('/')[-1] }}</div>{% endif %}
                    <input type="file" name="video" accept="video/*">
                </div>
                <button type="submit" class="btn-submit">Сохранить</button>
            </div>
        </form>
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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    ''' + CSS + '''
</head>
<body data-theme="{{ theme }}">
    <div class="container">
        <form class="login-form" method="post">
            <h2>🔐 Вход</h2>
            <input type="text" name="username" placeholder="Логин" required>
            <input type="password" name="password" placeholder="Пароль" required>
            <button type="submit" class="btn-submit">Войти</button>
            <p style="text-align:center;margin-top:15px;color:var(--text-secondary)">Логин: admin, Пароль: admin</p>
        </form>
    </div>
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
        query = query.filter(Girl.name.ilike(f'%{search}%'))
    
    if sort == 'newest':
        query = query.order_by(Girl.created_at.desc())
    else:
        query = query.order_by(Girl.name)
    
    total = query.count()
    total_pages = (total + PER_PAGE - 1) // PER_PAGE if total > 0 else 1
    girls = query.offset((page - 1) * PER_PAGE).limit(PER_PAGE).all()
    
    stats = {
        'total_models': Girl.query.count(),
        'total_photos': sum(len(g.photos.split(',')) if g.photos else 0 for g in Girl.query.all()),
        'total_videos': sum(1 for g in Girl.query.all() if g.video)
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
    theme = session.get('theme', 'light')
    girl = Girl.query.get_or_404(girl_id)
    return render_template_string(EDIT_HTML, girl=girl, theme=theme)

@app.route('/edit/<int:girl_id>', methods=['POST'])
def edit_girl_post(girl_id):
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
    
    def save_file(file, old_path):
        if file and file.filename:
            try:
                safe_name = sanitize_filename(file.filename)
                filepath = os.path.join(model_folder, safe_name)
                file.save(filepath)
                return f"{new_folder}/{safe_name}"
            except Exception:
                return old_path
        return old_path
    
    avatar_file = request.files.get('avatar')
    photos_files = request.files.getlist('photos')
    video_file = request.files.get('video')
    
    if avatar_file and avatar_file.filename:
        girl.avatar = save_file(avatar_file, girl.avatar)
    
    if photos_files and photos_files[0].filename:
        new_photos = list(filter(None, (girl.photos or '').split(',')))
        for pf in photos_files:
            if pf.filename:
                try:
                    safe_name = sanitize_filename(pf.filename)
                    filepath = os.path.join(model_folder, safe_name)
                    pf.save(filepath)
                    new_photos.append(f"{new_folder}/{safe_name}")
                except Exception:
                    pass
        if new_photos:
            girl.photos = ','.join(new_photos)
    
    if video_file and video_file.filename:
        girl.video = save_file(video_file, girl.video)
    
    db.session.commit()
    
    if old_folder != new_folder:
        old_path = os.path.join(get_upload_folder(), old_folder)
        if os.path.exists(old_path):
            delete_folder(old_path)
    
    return redirect(url_for('model_detail', girl_id=girl_id))

@app.route('/delete/<int:girl_id>')
def delete_girl(girl_id):
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
        if username == 'admin' and password == 'admin':
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
    
    def save_file(file):
        if file and file.filename:
            try:
                safe_name = sanitize_filename(file.filename)
                filepath = os.path.join(model_folder, safe_name)
                file.save(filepath)
                return f"{folder_name}/{safe_name}"
            except Exception:
                return None
        return None
    
    def save_multiple_files(files):
        saved = []
        for f in files:
            if f and f.filename:
                try:
                    safe_name = sanitize_filename(f.filename)
                    filepath = os.path.join(model_folder, safe_name)
                    f.save(filepath)
                    saved.append(f"{folder_name}/{safe_name}")
                except Exception:
                    pass
        return ','.join(saved) if saved else None
    
    girl.avatar = save_file(request.files.get('avatar'))
    girl.photos = save_multiple_files(request.files.getlist('photos'))
    girl.video = save_file(request.files.get('video'))
    db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/export')
def export_data():
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

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    from flask import send_from_directory, abort
    upload_folder = get_upload_folder()
    full_path = os.path.join(upload_folder, filename)
    if os.path.exists(full_path):
        return send_from_directory(upload_folder, filename)
    abort(404)

@app.route('/refresh')
def refresh():
    with app.app_context():
        sync_models_from_folders()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4444)
