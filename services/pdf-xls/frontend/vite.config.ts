import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tsconfigPaths from "vite-tsconfig-paths";
import { traeBadgePlugin } from 'vite-plugin-trae-solo-badge';
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
 
    tsconfigPaths()
  ],
  server: {
    proxy: {
      "/api/pdf-tiff": {
        target: "http://localhost:5008",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/pdf-tiff/, "")
      },
      "/api/pdf-png": {
        target: "http://localhost:5009",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/pdf-png/, "")
      }
    }
  }
})
