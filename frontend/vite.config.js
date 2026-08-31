// Vite 配置文件
// 作用：
// 1. 启用 Vue3 插件
// 2. 配置开发代理，解决前后端联调跨域问题

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      dts: false,
      resolvers: [ElementPlusResolver()]
    }),
    Components({
      dts: false,
      resolvers: [ElementPlusResolver({ importStyle: 'css' })]
    })
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return

          if (id.includes('element-plus')) {
            return 'vendor-element-plus'
          }

          if (id.includes('vue-router')) {
            return 'vendor-router'
          }

          if (id.includes('axios')) {
            return 'vendor-axios'
          }

          if (id.includes('/node_modules/echarts/') || id.includes('/node_modules/zrender/')) {
            return
          }

          return 'vendor-misc'
        }
      }
    }
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      // 所有 /api 请求都转发到 Flask 服务
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      // 上传图片访问同样转发到 Flask
      '/uploads': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})
