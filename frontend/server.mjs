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