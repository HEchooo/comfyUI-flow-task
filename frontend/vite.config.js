import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  base: '/comfyui-flow/', // 子路径部署，改为你的实际路径
  server: {
    port: 5173,
    host: true,
    // 开发环境也使用 base 路径
    origin: 'http://localhost:5173/comfyui-flow/'
  },
  build: {
    // 生成 sourcemap 方便调试
    sourcemap: true,
    // 提高 chunk 限制警告
    chunkSizeWarningLimit: 1000
  }
})
