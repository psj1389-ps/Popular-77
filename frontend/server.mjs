import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import { createProxyMiddleware } from 'http-proxy-middleware';
import history from 'connect-history-api-fallback';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const port = process.env.PORT || 10000;
const distDir = path.join(__dirname, 'dist');

// Health check for Render
app.get('/health', (req, res) => res.json({ ok: true }));

// Proxy for Image→JPG service
const imagesJpgTarget = process.env.IMAGES_JPG_URL || 'https://images-jpg-service.onrender.com';
app.use(
  '/api/image-to-jpg',
  createProxyMiddleware({
    target: imagesJpgTarget,
    changeOrigin: true,
    secure: true,
    // Keep the same path on the target
    pathRewrite: {
      '^/api/image-to-jpg': '/api/image-to-jpg',
    },
    onError(err, req, res) {
      console.error('[Proxy Error] /api/image-to-jpg:', err?.message || err);
      res.status(502).json({ error: '이미지 변환 서비스를 호출할 수 없습니다.' });
    },
  })
);

// SPA history fallback (exclude API paths)
app.use(
  history({
    verbose: false,
    disableDotRule: true,
    htmlAcceptHeaders: ['text/html', 'application/xhtml+xml'],
    rewrites: [
      { from: /^\/api\/.*$/, to: (ctx) => ctx.parsedUrl.pathname },
    ],
  })
);

// Serve built static assets
app.use(express.static(distDir, { maxAge: '1h', index: 'index.html' }));

app.listen(port, () => {
  console.log(`Frontend server running on port ${port}`);
  console.log(`Serving dist from: ${distDir}`);
  console.log(`Proxying /api/image-to-jpg -> ${imagesJpgTarget}/api/image-to-jpg`);
});