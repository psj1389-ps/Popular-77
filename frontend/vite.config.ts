import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tsconfigPaths from "vite-tsconfig-paths";
import { traeBadgePlugin } from 'vite-plugin-trae-solo-badge';
import sitemap from 'vite-plugin-sitemap';
import path from "path";

// https://vite.dev/config/
export default defineConfig({
  build: {
    sourcemap: 'hidden',
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src")
    }
  },
  plugins: [
    react({
      babel: {
        plugins: [
          'react-dev-locator',
        ],
      },
    }),
 
    tsconfigPaths(),
    sitemap({
      hostname: 'https://77-tools.xyz',
      dynamicRoutes: [
        '/',
        '/tools/pdf-doc',
        '/tools/pdf-jpg',
        '/tools/pdf-ai',
        '/tools/pdf-bmp',
        '/tools/pdf-gif',
        '/tools/pdf-png',
        '/tools/pdf-pptx',
        '/tools/pdf-svg',
        '/tools/pdf-tiff',
        '/tools/pdf-xls'
      ]
    })
  ],
  server: {
    proxy: {
      "/api/pdf-doc": {
        target: "http://localhost:10000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/pdf-doc/, "")
      },
      "/api/pdf-pptx": {
        target: "http://localhost:10000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/pdf-pptx/, "")
      },
      "/api/pdf-xls": {
        target: "http://localhost:10000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/pdf-xls/, "")
      },
      "/api/pdf-tiff": {
        target: "http://localhost:5008",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/pdf-tiff/, "")
      },
      "/api/pdf-png": {
        target: "http://localhost:5009",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/pdf-png/, "")
      },
      "/api/pdf-image": {
        target: "http://localhost:5000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/pdf-image/, "")
      },

    }
  }
})
