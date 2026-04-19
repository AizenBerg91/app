const express = require('express');
const Database = require('better-sqlite3');
const multer = require('multer');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const { exec, spawn } = require('child_process');

const app = express();
const PORT = process.env.PORT || 4444;

const BASE_DIR = process.env.DATA_DIR || '/app/data';
const UPLOADS_DIR = process.env.UPLOADS_DIR || '/app/uploads';

[BASE_DIR, UPLOADS_DIR].forEach(dir => {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }
});

app.use(cors());
app.use(express.json({ limit: '500mb' }));
app.use(express.urlencoded({ extended: true, limit: '500mb' }));
app.use(express.static('public'));
app.use('/uploads', express.static(UPLOADS_DIR));

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
        const modelId = req.body.modelId || req.params.id;
        const modelName = req.body.name || '';
        let folderName;
        if (!modelId || modelId === '0') {
            folderName = modelName ? sanitizeFolderName(modelName) : 'temp';
        } else {
            folderName = sanitizeFolderName(modelName);
        }
        const baseFolder = path.join(UPLOADS_DIR, folderName);
        let dest;
        if (file.fieldname === 'avatar') {
            dest = path.join(baseFolder, 'ava');
        } else if (file.fieldname === 'photos') {
            dest = path.join(baseFolder, 'photo');
        } else if (file.fieldname === 'videos') {
            dest = path.join(baseFolder, 'videos');
        } else {
            dest = baseFolder;
        }
        if (!fs.existsSync(dest)) {
            fs.mkdirSync(dest, { recursive: true });
        }
        cb(null, dest);
    },
    filename: (req, file, cb) => {
        const ext = path.extname(file.originalname);
        const baseName = path.basename(file.originalname, ext).replace(/[^a-zA-Z0-9\u0400-\u04FFа-яА-ЯёЁ\-\_]/g, '_').substring(0, 100);
        const uniqueSuffix = Date.now();
        cb(null, baseName + '_' + uniqueSuffix + ext);
    }
});

const upload = multer({ 
    storage, 
    limits: { fileSize: 500 * 1024 * 1024 }
});

function sanitizeFolderName(name) {
    if (!name) return 'unnamed';
    return String(name).replace(/[^a-zA-Z0-9\u0400-\u04FF]/g, '_').substring(0, 50);
}

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
    return String(str).replace(/[%_]/g, m => '\\' + m).replace(/'/g, "''");
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

const ALLOWED_IMAGES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
const ALLOWED_VIDEOS = ['video/mp4', 'video/webm', 'video/quicktime'];
const LEGACY_VIDEO_FORMATS = ['video/x-msvideo', 'video/avi', 'video/x-ms-wmv', 'video/mpeg', 'video/x-matroska', 'video/x-mpeg', 'video/x-theora', 'video/x-flv', 'video/quicktime'];
const ALL_VIDEO_TYPES = [...ALLOWED_VIDEOS, ...LEGACY_VIDEO_FORMATS];
const MAX_LIMIT = 100;

const convertVideo = (inputPath, outputDir, format = 'mp4') => {
    return new Promise((resolve, reject) => {
        const outputName = path.basename(inputPath, path.extname(inputPath)) + '.mp4';
        const outputPath = path.join(outputDir, outputName);

        if (fs.existsSync(outputPath)) {
            return resolve(outputName);
        }

        const args = [
            '-i', inputPath,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            '-y',
            outputPath
        ];

        const ffmpeg = spawn('ffmpeg', args);
        let stderr = '';

        ffmpeg.stderr.on('data', (data) => {
            stderr += data;
        });

        ffmpeg.on('close', (code) => {
            if (code === 0 && fs.existsSync(outputPath)) {
                resolve(outputName);
            } else {
                reject(new Error(`FFmpeg failed: ${stderr.slice(-500)}`));
            }
        });

        ffmpeg.on('error', (err) => {
            reject(err);
        });
    });
};

function validateId(id) {
    const num = parseInt(id);
    return !isNaN(num) && num > 0 && num < 2147483647;
}

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

function getFormArray(req, key, allowEmpty = false) {
    const vals = req?.body?.[key];
    if (!vals) return [];
    const arr = Array.isArray(vals) ? vals : [vals];
    return arr.filter(v => allowEmpty ? v !== undefined : v && String(v).trim());
}

app.get('/api/models', (req, res) => {
    const { search, tag, sort, page, limit } = req.query;
    let query = 'SELECT * FROM models';
    const params = [];
    const conditions = [];

    if (search) {
        const safeSearch = `%${escapeSqlLike(search)}%`;
        conditions.push('(name LIKE ? OR tags LIKE ?)');
        params.push(safeSearch, safeSearch);
    }
    if (tag) {
        const safeTag = `%${escapeSqlLike(tag)}%`;
        conditions.push('tags LIKE ?');
        params.push(safeTag);
    }
    if (conditions.length) query += ' WHERE ' + conditions.join(' AND ');

    const sortField = sort === 'name' ? 'name' : (sort === 'created_at' ? 'created_at' : 'created_at');
    const sortOrder = sort === 'name' ? 'ASC' : 'DESC';
    query += ` ORDER BY ${sortField} ${sortOrder}`;

    const totalQuery = 'SELECT COUNT(*) as count FROM models' + (conditions.length ? ' WHERE ' + conditions.join(' AND ') : '');
    const total = db.prepare(totalQuery).get(...params).count;
    const pageNum = Math.max(1, parseInt(page) || 1);
    const limitNum = Math.min(MAX_LIMIT, Math.max(1, parseInt(limit) || 20));
    const offset = (pageNum - 1) * limitNum;
    query += ` LIMIT ${limitNum} OFFSET ${offset}`;

    const models = db.prepare(query).all(...params);
    
    const getFileSize = (dir, filename) => {
        if (!filename) return 0;
        return fs.existsSync(dir) ? fs.statSync(path.join(dir, filename)).size : 0;
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
            modelFolder: sanitizeFolderName(m.name),
            photos: parseJson(m.photos).map(p => ({ name: p, size: getFileSize(path.join(UPLOADS_DIR, sanitizeFolderName(m.name), 'photo'), p) })),
            videos: parseJson(m.videos).map(v => ({ name: v, size: getFileSize(path.join(UPLOADS_DIR, sanitizeFolderName(m.name), 'videos'), v) })),
            tags: parseJson(m.tags)
        })),
        total,
        page: pageNum,
        limit: limitNum,
        pages: Math.ceil(total / limitNum)
    });
});

app.get('/api/models/:id', (req, res) => {
    const id = req.params.id;
    if (!validateId(id)) return res.status(400).json({ error: 'Invalid ID' });
    const model = db.prepare('SELECT * FROM models WHERE id = ?').get(id);
    if (!model) return res.status(404).json({ error: 'Model not found' });

    const getFileSize = (dir, filename) => {
        if (!filename) return 0;
        return fs.existsSync(dir) ? fs.statSync(path.join(dir, filename)).size : 0;
    };

    const modelFolder = sanitizeFolderName(model.name);
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
        modelFolder: modelFolder,
        photos: photos.map(p => ({ name: p, size: getFileSize(path.join(UPLOADS_DIR, modelFolder, 'photo'), p) })),
        videos: videos.map(v => ({ name: v, size: getFileSize(path.join(UPLOADS_DIR, modelFolder, 'videos'), v) })),
        tags: parseJson(model.tags)
    });
});

app.post('/api/models', upload.fields([
    { name: 'avatar', maxCount: 1 },
    { name: 'photos', maxCount: 10 },
    { name: 'videos', maxCount: 10 },
    { name: 'existing_photos' },
    { name: 'existing_videos' }
]), async (req, res) => {
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

    const videosFiles = req.files?.['videos']?.filter(f => validateFile(f, ALL_VIDEO_TYPES)) || [];
    const supportedVideos = videosFiles.filter(f => validateFile(f, ALLOWED_VIDEOS));
    const legacyVideos = videosFiles.filter(f => LEGACY_VIDEO_FORMATS.includes(f.mimetype));
    const videos = supportedVideos.map(f => f.filename);

    if (legacyVideos.length > 0) {
        const modelFolder = sanitizeFolderName(name.trim());
        const videosDir = path.join(UPLOADS_DIR, modelFolder, 'videos');
        if (!fs.existsSync(videosDir)) fs.mkdirSync(videosDir, { recursive: true });

        const convertPromises = legacyVideos.map(async (f) => {
            try {
                const converted = await convertVideo(f.path, videosDir, 'mp4');
                videos.push(converted);
                if (fs.existsSync(f.path)) fs.unlinkSync(f.path);
                return converted;
            } catch (err) {
                console.error('Video conversion failed:', f.filename, err.message);
                return null;
            }
        });

        const convertedVideos = await Promise.all(convertPromises);
        convertedVideos.filter(Boolean).forEach(v => {
            if (!videos.includes(v)) videos.push(v);
        });
    }

    const tagsArray = tags ? parseJson(tags) : [];
    const description = String(req.body.description || '');
    const socialLinks = req.body.social_links ? parseJson(req.body.social_links) : [];
    const category = String(req.body.category || '');

    const result = db.prepare(`
        INSERT INTO models (name, avatar, tags, videos, photos, description, social_links, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `).run(name.trim(), avatar, JSON.stringify(tagsArray), JSON.stringify(videos), JSON.stringify(photos), description, JSON.stringify(socialLinks), category);

    const newId = result.lastInsertRowid;
    const modelFolder = sanitizeFolderName(name.trim());

    const moveFiles = (srcSubFolder, destSubFolder) => {
        const srcDir = path.join(UPLOADS_DIR, modelFolder, srcSubFolder);
        const destDir = path.join(UPLOADS_DIR, modelFolder, destSubFolder);
        if (fs.existsSync(srcDir)) {
            if (!fs.existsSync(destDir)) {
                fs.mkdirSync(destDir, { recursive: true });
            }
            fs.readdirSync(srcDir).forEach(file => {
                fs.renameSync(path.join(srcDir, file), path.join(destDir, file));
            });
            try { fs.rmdirSync(srcDir); } catch {}
        }
    };

    moveFiles('ava', 'ava');
    moveFiles('photo', 'photo');
    moveFiles('videos', 'videos');
    
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
    { name: 'videos', maxCount: 10 },
    { name: 'existing_photos' },
    { name: 'existing_videos' }
]), (req, res) => {
    const id = req.params.id;
    if (!validateId(id)) return res.status(400).json({ error: 'Invalid ID' });

    const { name, tags, existing_avatar } = req.body;
    const existingPhotos = getFormArray(req, 'existing_photos');
    const existingVideos = getFormArray(req, 'existing_videos');

    const model = db.prepare('SELECT * FROM models WHERE id = ?').get(id);
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
            deleteFiles([model.avatar], path.join(UPLOADS_DIR, newFolder, 'ava'));
        }
    }

    const photosFiles = req.files?.['photos']?.filter(f => validateFile(f, ALLOWED_IMAGES)) || [];
    const newPhotos = photosFiles.map(f => f.filename);

    const videosFiles = req.files?.['videos']?.filter(f => validateFile(f, ALLOWED_VIDEOS)) || [];
    const newVideos = videosFiles.map(f => f.filename);
    
    const photosArray = newPhotos.length > 0 ? newPhotos : (existingPhotos.length > 0 && existingPhotos[0] ? existingPhotos : oldPhotos);
    const videosArray = newVideos.length > 0 ? newVideos : (existingVideos.length > 0 && existingVideos[0] ? existingVideos : oldVideos);
    const tagsArray = tags ? parseJson(tags) : parseJson(model.tags);
    const description = req.body.description !== undefined ? req.body.description : (model.description || '');
    const socialLinks = req.body.social_links ? parseJson(req.body.social_links) : parseJson(model.social_links);
    const category = req.body.category !== undefined ? req.body.category : (model.category || '');

    const newName = name ? name.trim() : model.name;
    const oldFolder = sanitizeFolderName(model.name);
    const newFolder = sanitizeFolderName(newName);

    if (oldFolder !== newFolder && fs.existsSync(path.join(UPLOADS_DIR, oldFolder))) {
        fs.renameSync(path.join(UPLOADS_DIR, oldFolder), path.join(UPLOADS_DIR, newFolder));
    }

    db.prepare(`
        UPDATE models SET name = ?, avatar = ?, tags = ?, videos = ?, photos = ?, description = ?, social_links = ?, category = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    `).run(newName, avatar, JSON.stringify(tagsArray), JSON.stringify(videosArray), JSON.stringify(photosArray), description, JSON.stringify(socialLinks), category, id);

    res.json({ 
        id, 
        name: escapeHtml(newName), 
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
    const id = req.params.id;
    if (!validateId(id)) return res.status(400).json({ error: 'Invalid ID' });
    const model = db.prepare('SELECT * FROM models WHERE id = ?').get(id);
    if (!model) return res.status(404).json({ error: 'Model not found' });

    const modelFolder = sanitizeFolderName(model.name);
    const oldPhotos = parseJson(model.photos);
    const oldVideos = parseJson(model.videos);

    if (fs.existsSync(path.join(UPLOADS_DIR, modelFolder))) {
        fs.rmSync(path.join(UPLOADS_DIR, modelFolder), { recursive: true, force: true });
    }

    db.prepare('DELETE FROM models WHERE id = ?').run(id);
    res.json({ success: true });
});

app.get('/api/tags', (req, res) => {
    const models = db.prepare('SELECT tags FROM models').all();
    const allTags = new Set();
    models.forEach(m => parseJson(m.tags).forEach(t => allTags.add(escapeHtml(t))));
    res.json(Array.from(allTags).sort());
});

app.post('/api/convert-video', upload.single('video'), async (req, res) => {
    const file = req.file;
    if (!file) return res.status(400).json({ error: 'No video file' });

    const ext = path.extname(file.originalname).toLowerCase();
    if (ALLOWED_VIDEOS.includes(file.mimetype)) {
        return res.json({ filename: file.filename, converted: false });
    }

    if (!LEGACY_VIDEO_FORMATS.includes(file.mimetype)) {
        if (fs.existsSync(file.path)) fs.unlinkSync(file.path);
        return res.status(400).json({ error: 'Unsupported video format' });
    }

    try {
        const modelId = req.body.modelId;
        const modelName = req.body.name || 'temp';
        const folderName = sanitizeFolderName(modelName);
        const targetDir = path.join(UPLOADS_DIR, folderName, 'videos');

        if (!fs.existsSync(targetDir)) {
            fs.mkdirSync(targetDir, { recursive: true });
        }

        const convertedFilename = await convertVideo(file.path, targetDir, 'mp4');

        if (fs.existsSync(file.path)) {
            fs.unlinkSync(file.path);
        }

        res.json({ filename: convertedFilename, converted: true });
    } catch (err) {
        if (fs.existsSync(file.path)) fs.unlinkSync(file.path);
        res.status(500).json({ error: 'Conversion failed', details: err.message });
    }
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