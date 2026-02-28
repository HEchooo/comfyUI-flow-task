# ComfyUI Flow Iframe 集成指南

本文档说明如何将 ComfyUI Flow 应用通过 iframe 嵌入到公司管理系统中。

## 部署步骤

### 1. 修改部署路径

编辑 `frontend/vite.config.js`，修改 `base` 路径为你的实际部署路径：

```javascript
export default defineConfig({
  base: '/comfyui-flow/', // 改为你的实际路径
  // ...
})
```

### 2. 配置允许的父系统域名

编辑 `frontend/src/composables/useIframe.js`，添加你的公司管理系统域名：

```javascript
const ALLOWED_ORIGINS = [
  'http://localhost:8080',  // 开发环境
  'http://localhost:3000',
  'https://your-company-system.com',  // 生产环境
]
```

### 3. 构建前端

```bash
cd frontend
npm run build
```

构建产物在 `frontend/dist/` 目录，将整个目录部署到你的服务器 `/comfyui-flow/` 路径下。

### 4. 后端部署

后端服务独立部署，确保 CORS 配置允许父系统域名的跨域请求。

编辑 `backend/app/core/config.py`：

```python
CORS_ORIGINS: List[str] = [
    "http://localhost:8080",
    "http://localhost:3000",
    "https://your-company-system.com",
    "http://localhost:5173",  # 开发环境
]
```

## 父系统集成代码

### Vue 2/3 集成示例

```vue
<template>
  <div class="comfyui-flow-container">
    <iframe
      ref="iframeRef"
      :src="iframeSrc"
      class="comfyui-flow-iframe"
      @load="onIframeLoad"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const iframeRef = ref(null)
const iframeSrc = '/comfyui-flow/'  // 你的部署路径
const token = ref('your-auth-token') // 从你的系统获取的 token

// 发送 token 到 iframe
function sendToken() {
  if (iframeRef.value?.contentWindow) {
    iframeRef.value.contentWindow.postMessage({
      type: 'token',
      data: { token: token.value }
    }, '*')
  }
}

// iframe 加载完成
function onIframeLoad() {
  console.log('ComfyUI Flow iframe loaded')
  sendToken()
}

// 监听来自 iframe 的消息
function handleMessage(event) {
  // 安全检查：验证消息来源
  if (!event.origin.includes('your-domain.com')) {
    return
  }

  const { type, source, data } = event.data

  // 只处理来自 ComfyUI Flow 的消息
  if (source !== 'comfyui-flow') return

  switch (type) {
    case 'ready':
      console.log('ComfyUI Flow is ready')
      sendToken()
      break

    case 'routeChange':
      console.log('Route changed to:', data.path)
      // 可以在这里更新父系统的状态
      break

    case 'requestToken':
      // iframe 请求 token
      sendToken()
      break

    case 'requestAuth':
      // iframe 需要认证，可以跳转到登录页
      console.log('ComfyUI Flow requires authentication')
      break

    case 'userAction':
      console.log('User action:', data.action)
      // 处理用户操作统计等
      break

    case 'error':
      console.error('ComfyUI Flow error:', data.message)
      break
  }
}

// 控制导航到指定路径
function navigateTo(path) {
  if (iframeRef.value?.contentWindow) {
    iframeRef.value.contentWindow.postMessage({
      type: 'navigate',
      data: { path }
    }, '*')
  }
}

onMounted(() => {
  window.addEventListener('message', handleMessage)
})

onBeforeUnmount(() => {
  window.removeEventListener('message', handleMessage)
})
</script>

<style scoped>
.comfyui-flow-container {
  width: 100%;
  height: calc(100vh - 64px); /* 减去父系统导航栏高度 */
  overflow: hidden;
}

.comfyui-flow-iframe {
  width: 100%;
  height: 100%;
  border: none;
}
</style>
```

### 纯 HTML/JS 集成示例

```html
<!DOCTYPE html>
<html>
<head>
  <title>ComfyUI Flow 集成</title>
  <style>
    .iframe-container {
      width: 100%;
      height: calc(100vh - 64px);
      overflow: hidden;
    }
    .iframe-container iframe {
      width: 100%;
      height: 100%;
      border: none;
    }
  </style>
</head>
<body>
  <div class="iframe-container">
    <iframe id="comfyui-flow" src="/comfyui-flow/"></iframe>
  </div>

  <script>
    const iframe = document.getElementById('comfyui-flow');
    const token = 'your-auth-token'; // 从你的系统获取

    // 发送 token
    function sendToken() {
      iframe.contentWindow.postMessage({
        type: 'token',
        data: { token }
      }, '*');
    }

    // 监听消息
    window.addEventListener('message', (event) => {
      const { type, source, data } = event.data;
      if (source !== 'comfyui-flow') return;

      switch (type) {
        case 'ready':
          sendToken();
          break;
        case 'requestToken':
          sendToken();
          break;
      }
    });
  </script>
</body>
</html>
```

## 消息协议

### 父系统 → ComfyUI Flow

| 类型 | 说明 | 数据结构 |
|------|------|----------|
| `token` | 传递认证 token | `{ token: string }` |
| `navigate` | 导航到指定路径 | `{ path: string }` |
| `ping` | 心跳检测 | 无 |

### ComfyUI Flow → 父系统

| 类型 | 说明 | 数据结构 |
|------|------|----------|
| `ready` | iframe 已就绪 | `{ timestamp: number }` |
| `routeChange` | 路由变化 | `{ path: string }` |
| `requestToken` | 请求 token | 无 |
| `requestAuth` | 请求认证 | 无 |
| `userAction` | 用户操作 | `{ action: string, data: any }` |
| `error` | 错误信息 | `{ message: string, stack: string }` |
| `pong` | 心跳响应 | 无 |

## 注意事项

1. **安全**：务必在 `ALLOWED_ORIGINS` 中配置正确的父系统域名
2. **Token 管理**：建议父系统统一管理认证，token 过期时自动刷新
3. **响应式**：iframe 高度需要根据父系统布局调整
4. **跨域**：确保后端 CORS 配置正确
5. **开发环境**：开发时需要配置代理，确保前后端通信正常
