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
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          // React 관련 라이브러리들을 별도 청크로 분리
          'react-vendor': ['react', 'react-dom'],
          // React Router 관련
          'router': ['react-router-dom'],
          // UI 라이브러리들
          'ui-vendor': ['lucide-react'],
          // 유틸리티 라이브러리들
          'utils': ['clsx', 'tailwind-merge'],
          // Supabase 관련
          'supabase': ['@supabase/supabase-js'],
          // PDF 관련
          'pdf': ['pdfjs-dist'],
          // 상태 관리
          'state': ['zustand']
        }
      }
    }
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
      "/api/image-to-jpg": {
        target: "https://popular-77-srwb.onrender.com",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/image-to-jpg/, "/api/image-to-jpg")
      },
      "/api/images-webp": {
        target: "http://localhost:5000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/images-webp/, "/convert")
      },
      "/api/images-png": {
        target: "http://localhost:5001",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/images-png/, "/api/images-png")
      }
    }
  }
})
