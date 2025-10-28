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

// 이미지 → JPG 마이크로서비스 프록시 (동일 오리진 경유로 CORS 회피)
const targetJpg = process.env.IMAGES_JPG_URL || 'https://images-jpg-service.onrender.com';
app.use([
  '/api/image-to-jpg',
  '/api/batch-convert',
  '/api/progress',
  '/api/download',
  '/api/cancel'
], createProxyMiddleware({
  target: targetJpg,
  changeOrigin: true,
  ws: false,
  xfwd: true,
  proxyTimeout: 600000,
  timeout: 600000,
}));

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
});