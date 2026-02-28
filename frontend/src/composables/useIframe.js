/**
 * Iframe 通信 composable
 * 用于与父系统进行消息通信
 */
import { onMounted, onBeforeUnmount } from 'vue'

const ALLOWED_ORIGINS = [
  // 添加允许的父系统域名
  'http://localhost:8080',
  'http://localhost:3000',
  // 添加生产环境域名
  // 'https://your-company-system.com'
]

function isAllowedOrigin(origin) {
  return ALLOWED_ORIGINS.some(allowed => origin.startsWith(allowed))
}

/**
 * 向父系统发送消息
 * @param {string} type - 消息类型
 * @param {*} data - 消息数据
 */
export function sendMessage(type, data = null) {
  if (window.parent !== window) {
    window.parent.postMessage(
      { type, source: 'comfyui-flow', data },
      '*'
    )
  }
}

/**
 * 发送就绪消息
 */
export function sendReady() {
  sendMessage('ready', {
    timestamp: Date.now()
  })
}

/**
 * 发送路由变化消息
 */
export function sendRouteChange(path) {
  sendMessage('routeChange', { path })
}

/**
 * 发送用户操作消息
 */
export function sendUserAction(action, data = null) {
  sendMessage('userAction', { action, data })
}

/**
 * 发送错误消息
 */
export function sendError(error) {
  sendMessage('error', {
    message: error.message,
    stack: error.stack
  })
}

/**
 * 请求父系统的 token（如果父系统统一管理认证）
 */
export function requestToken() {
  sendMessage('requestToken')
}

/**
 * Iframe 通信 hook
 * @param {Object} callbacks - 回调函数集合
 */
export function useIframe(callbacks = {}) {
  const {
    onToken = null,
    onNavigate = null,
    onMessage = null
  } = callbacks

  function handleMessage(event) {
    // 安全检查：验证消息来源
    if (!isAllowedOrigin(event.origin)) {
      console.warn('[Iframe] Received message from unallowed origin:', event.origin)
      return
    }

    const { type, data } = event.data

    switch (type) {
      case 'token':
        // 父系统传递 token
        if (onToken && data?.token) {
          onToken(data.token)
        }
        break

      case 'navigate':
        // 父系统要求导航到指定路径
        if (onNavigate && data?.path) {
          onNavigate(data.path)
        }
        break

      case 'ping':
        // 心跳检测
        sendMessage('pong')
        break

      default:
        // 自定义消息处理
        if (onMessage) {
          onMessage(type, data)
        }
        break
    }
  }

  onMounted(() => {
    // 检测是否在 iframe 中
    if (window.parent !== window) {
      console.log('[Iframe] Running inside iframe')
      window.addEventListener('message', handleMessage)

      // 通知父系统已就绪
      sendReady()

      // 如果支持从父系统获取 token，则请求
      requestToken()
    }
  })

  onBeforeUnmount(() => {
    window.removeEventListener('message', handleMessage)
  })

  return {
    sendMessage,
    sendRouteChange,
    sendUserAction,
    sendError
  }
}
