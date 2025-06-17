import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // 讓容器可以從外部存取
    host: '0.0.0.0',
    port: 5173,
    // 設定代理，將所有 /api 開頭的請求轉發到後端服務
    proxy: {
      '/api': {
        // 'http://backend:5000' 是後端服務在 Docker Compose 中的名稱和端口
        target: 'http://backend:5000',
        // 更改來源，以便後端可以正確接收請求
        changeOrigin: true,
      },
    },
  },
})
