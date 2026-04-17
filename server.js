const express = require('express');
const Database = require('better-sqlite3');
const multer = require('multer');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 4444;

app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
app.use(express.static('public'));
app.use('/uploads', express.static('uploads'));
app.use('/videos', express.static('videos'));

const BASE_DIR = process.env.DATA_DIR || '/app/data';
const UPLOADS_DIR = process.env.UPLOADS_DIR || '/app/uploads';
const VIDEOS_DIR = process.env.VIDEOS_DIR || '/app/videos';

[BASE_DIR, UPLOADS_DIR, VIDEOS_DIR].forEach(dir => {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }
});

const db = new Database(path.join(BASE_DIR, 'models.db'));

db.exec(`
    CREATE TABLE IF NOT EXISTS models (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        avatar TEXT,
        photos TEXT DEFAULT '[]',
        videos TEXT DEFAULT '[]',
        tags TEXT DEFAULT '[]',
        description TEXT DEFAULT '',
        social_links TEXT DEFAULT '[]',
        category TEXT DEFAULT '',
        views INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
`);

["description", "social_links", "category"].forEach(col => {
    try { db.exec(`ALTER TABLE models ADD COLUMN ${col} TEXT DEFAULT '';`); } catch {}
});

const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        const dest = file.fieldname === 'videos' ? VIDEOS_DIR : UPLOADS_DIR;
        cb(null, dest);
    },
    filename: (req, file, cb) => {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, uniqueSuffix + path.extname(file.originalname));
    }
});

const upload = multer({ 
    storage, 
    limits: { fileSize: 100 * 1024 * 1024 }
});

function parseJson(str, defaultVal = []) {
    if (!str) return defaultVal;
    try {
        return JSON.parse(str);
    } catch {
        return defaultVal;
    }
}

function escapeSqlLike(str) {
    if (!str) return '';
    return String(str).replace(/[%_]/g, m => m === '%' ? '\\%' : '\\_');
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

const ALLOWED_IMAGES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
const ALLOWED_VIDEOS = ['video/mp4', 'video/webm', 'video/quicktime'];

function validateFile(file, allowedTypes) {
    return file && allowedTypes.includes(file.mimetype);
}

function deleteFiles(files, dir) {
    if (!Array.isArray(files)) return;
    files.forEach(f => {
        if (!f) return;
        const filepath = path.join(dir, f);
        if (fs.existsSync(filepath)) {
            fs.unlinkSync(filepath);
        }
    });
}

function getFormArray(req, key) {
    const vals = req?.body?.[key];
    if (!vals) return [];
    return Array.isArray(vals) ? vals : [vals];
}

app.get('/api/models', (req, res) => {
    const { search, tag, sort, page, limit } = req.query;
    let query = 'SELECT * FROM models';
    const params = [];
    const conditions = [];

    if (search) {
        const safeSearch = `%${escapeSqlLike(search)}%`;
        conditions.push('(name LIKE ? ESCAPE "\\" OR tags LIKE ? ESCAPE "\\")');
        params.push(safeSearch, safeSearch);
    }
    if (tag) {
        const safeTag = `%"${escapeSqlLike(tag)}"%`;
        conditions.push('tags LIKE ? ESCAPE "\\"');
        params.push(safeTag);
    }
    if (conditions.length) query += ' WHERE ' + conditions.join(' AND ');

    const sortField = sort === 'name' ? 'name' : (sort === 'created_at' ? 'created_at' : 'created_at');
    const sortOrder = sort === 'name' ? 'ASC' : 'DESC';
    query += ` ORDER BY ${sortField} ${sortOrder}`;

    const total = db.prepare('SELECT COUNT(*) as count FROM models' + (conditions.length ? ' WHERE ' + conditions.join(' AND ') : '')).get().count;
    const pageNum = parseInt(page) || 1;
    const limitNum = parseInt(limit) || 100;
    const offset = (pageNum - 1) * limitNum;
    query += ` LIMIT ${limitNum} OFFSET ${offset}`;

    const models = db.prepare(query).all(...params);
    
    const getFileSize = (dir, filename) => {
        if (!filename) return 0;
        const fp = path.join(dir, filename);
        return fs.existsSync(fp) ? fs.statSync(fp).size : 0;
    };

    res.json({
        data: models.map(m => ({
            ...m,
            name: escapeHtml(m.name),
            description: m.description || '',
            social_links: parseJson(m.social_links),
            category: m.category || '',
            views: m.views || 0,
            created_at: m.created_at,
            photos: parseJson(m.photos).map(p => ({ name: p, size: getFileSize(UPLOADS_DIR, p) })),
            videos: parseJson(m.videos).map(v => ({ name: v, size: getFileSize(VIDEOS_DIR, v) })),
            tags: parseJson(m.tags)
        })),
        total,
        page: pageNum,
        limit: limitNum,
        pages: Math.ceil(total / limitNum)
    });
});

app.get('/api/models/:id', (req, res) => {
    const model = db.prepare('SELECT * FROM models WHERE id = ?').get(req.params.id);
    if (!model) return res.status(404).json({ error: 'Model not found' });

    const getFileSize = (dir, filename) => {
        if (!filename) return 0;
        const fp = path.join(dir, filename);
        return fs.existsSync(fp) ? fs.statSync(fp).size : 0;
    };

    const photos = parseJson(model.photos);
    const videos = parseJson(model.videos);

    res.json({
        ...model,
        name: escapeHtml(model.name),
        avatar: model.avatar,
        description: model.description || '',
        social_links: parseJson(model.social_links),
        category: model.category || '',
        views: model.views || 0,
        created_at: model.created_at,
        photos: photos.map(p => ({ name: p, size: getFileSize(UPLOADS_DIR, p) })),
        videos: videos.map(v => ({ name: v, size: getFileSize(VIDEOS_DIR, v) })),
        tags: parseJson(model.tags)
    });
});

app.post('/api/models', upload.fields([
    { name: 'avatar', maxCount: 1 },
    { name: 'photos', maxCount: 10 },
    { name: 'videos', maxCount: 10 }
]), (req, res) => {
    const { name, tags } = req.body;
    
    if (!name || typeof name !== 'string' || name.trim().length === 0) {
        return res.status(400).json({ error: 'Name is required' });
    }
    if (name.length > 255) {
        return res.status(400).json({ error: 'Name too long (max 255 chars)' });
    }

    const avatarFile = req.files?.['avatar']?.[0];
    if (avatarFile && !validateFile(avatarFile, ALLOWED_IMAGES)) {
        return res.status(400).json({ error: 'Invalid avatar file type' });
    }
    const avatar = avatarFile?.filename || null;

    const photosFiles = req.files?.['photos']?.filter(f => validateFile(f, ALLOWED_IMAGES)) || [];
    const photos = photosFiles.map(f => f.filename);

    const videosFiles = req.files?.['videos']?.filter(f => validateFile(f, ALLOWED_VIDEOS)) || [];
    const videos = videosFiles.map(f => f.filename);

    const tagsArray = tags ? parseJson(tags) : [];
    const description = String(req.body.description || '');
    const socialLinks = req.body.social_links ? parseJson(req.body.social_links) : [];
    const category = String(req.body.category || '');

    const result = db.prepare(`
        INSERT INTO models (name, avatar, tags, videos, photos, description, social_links, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `).run(name.trim(), avatar, JSON.stringify(tagsArray), JSON.stringify(videos), JSON.stringify(photos), description, JSON.stringify(socialLinks), category);

    res.json({ 
        id: result.lastInsertRowid, 
        name: escapeHtml(name.trim()), 
        avatar, 
        tags: tagsArray, 
        videos,
        photos,
        description,
        social_links: socialLinks,
        category,
        views: 0,
        created_at: new Date().toISOString()
    });
});

app.put('/api/models/:id', upload.fields([
    { name: 'avatar', maxCount: 1 },
    { name: 'photos', maxCount: 10 },
    { name: 'videos', maxCount: 10 }
]), (req, res) => {
    const { name, tags, existing_avatar } = req.body;
    const existingPhotos = getFormArray(req, 'existing_photos');
    const existingVideos = getFormArray(req, 'existing_videos');

    const model = db.prepare('SELECT * FROM models WHERE id = ?').get(req.params.id);
    if (!model) return res.status(404).json({ error: 'Model not found' });

    if (name !== undefined && (typeof name !== 'string' || name.length > 255)) {
        return res.status(400).json({ error: 'Invalid name (max 255 chars)' });
    }

    const oldPhotos = parseJson(model.photos);
    const oldVideos = parseJson(model.videos);

    let avatar = existing_avatar || model.avatar;
    const avatarFile = req.files?.['avatar']?.[0];
    if (avatarFile) {
        if (!validateFile(avatarFile, ALLOWED_IMAGES)) {
            return res.status(400).json({ error: 'Invalid avatar file type' });
        }
        avatar = avatarFile.filename;
        if (model.avatar) {
            deleteFiles([model.avatar], UPLOADS_DIR);
        }
    }

    const photosFiles = req.files?.['photos']?.filter(f => validateFile(f, ALLOWED_IMAGES)) || [];
    const newPhotos = photosFiles.map(f => f.filename);

    const videosFiles = req.files?.['videos']?.filter(f => validateFile(f, ALLOWED_VIDEOS)) || [];
    const newVideos = videosFiles.map(f => f.filename);
    
    const photosArray = newPhotos.length > 0 ? newPhotos : (existingPhotos.length > 0 ? existingPhotos : oldPhotos);
    const videosArray = newVideos.length > 0 ? newVideos : (existingVideos.length > 0 ? existingVideos : oldVideos);
    const tagsArray = tags ? parseJson(tags) : parseJson(model.tags);
    const description = req.body.description !== undefined ? req.body.description : (model.description || '');
    const socialLinks = req.body.social_links ? parseJson(req.body.social_links) : parseJson(model.social_links);
    const category = req.body.category !== undefined ? req.body.category : (model.category || '');

    db.prepare(`
        UPDATE models SET name = ?, avatar = ?, tags = ?, videos = ?, photos = ?, description = ?, social_links = ?, category = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    `).run(name ? name.trim() : model.name, avatar, JSON.stringify(tagsArray), JSON.stringify(videosArray), JSON.stringify(photosArray), description, JSON.stringify(socialLinks), category, req.params.id);

    res.json({ 
        id: req.params.id, 
        name: escapeHtml(name ? name.trim() : model.name), 
        avatar, 
        tags: tagsArray, 
        videos: videosArray, 
        photos: photosArray,
        description,
        social_links: socialLinks,
        category,
        views: model.views || 0,
        created_at: model.created_at
    });
});

app.delete('/api/models/:id', (req, res) => {
    const model = db.prepare('SELECT * FROM models WHERE id = ?').get(req.params.id);
    if (!model) return res.status(404).json({ error: 'Model not found' });

    const oldPhotos = parseJson(model.photos);
    const oldVideos = parseJson(model.videos);

    deleteFiles(oldPhotos, UPLOADS_DIR);
    deleteFiles(oldVideos, VIDEOS_DIR);
    if (model.avatar) deleteFiles([model.avatar], UPLOADS_DIR);

    db.prepare('DELETE FROM models WHERE id = ?').run(req.params.id);
    res.json({ success: true });
});

app.get('/api/tags', (req, res) => {
    const models = db.prepare('SELECT tags FROM models').all();
    const allTags = new Set();
    models.forEach(m => parseJson(m.tags).forEach(t => allTags.add(escapeHtml(t))));
    res.json(Array.from(allTags).sort());
});

app.use((err, req, res, next) => {
    console.error(err.stack);
    if (err instanceof SyntaxError && err.status === 400) {
        return res.status(400).json({ error: 'Invalid JSON' });
    }
    if (err.code === 'LIMIT_FILE_SIZE') {
        return res.status(413).json({ error: 'File too large' });
    }
    res.status(500).json({ error: 'Internal server error' });
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});