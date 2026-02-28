import axios from 'axios'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 20000
})

const pendingRequests = new Map()
const recentRequests = new Map()
const DUPLICATE_GAP_MS = 800

function stableStringify(value) {
  if (value === null || value === undefined) {
    return ''
  }
  if (value instanceof FormData) {
    const entries = []
    value.forEach((item, key) => {
      if (item instanceof File) {
        entries.push([key, `${item.name}:${item.size}:${item.type}`])
      } else {
        entries.push([key, String(item)])
      }
    })
    return JSON.stringify(entries)
  }
  const normalize = (input) => {
    if (input === null || input === undefined) return null
    if (typeof input === 'string' || typeof input === 'number' || typeof input === 'boolean') {
      return input
    }
    if (input instanceof Date) return input.toISOString()
    if (input instanceof File) return `${input.name}:${input.size}:${input.type}`
    if (Array.isArray(input)) return input.map((item) => normalize(item))
    if (typeof input === 'object') {
      const output = {}
      Object.keys(input)
        .sort()
        .forEach((key) => {
          output[key] = normalize(input[key])
        })
      return output
    }
    return String(input)
  }

  return JSON.stringify(normalize(value))
}

function buildRequestKey(config) {
  const method = String(config?.method || 'get').toLowerCase()
  const baseURL = String(config?.baseURL || '')
  const url = String(config?.url || '')
  const params = stableStringify(config?.params)
  const data = stableStringify(config?.data)
  return `${method}|${baseURL}|${url}|${params}|${data}`
}

function createDuplicateRequestError(config) {
  const error = new Error('Duplicate request blocked')
  error.name = 'DuplicateRequestError'
  error.isDuplicateRequest = true
  error.config = config
  return error
}

function releaseRequest(config) {
  const key = config?.__requestKey
  if (!key) return
  pendingRequests.delete(key)
  recentRequests.set(key, Date.now())
}

export function isDuplicateRequestError(error) {
  return Boolean(error?.isDuplicateRequest || error?.name === 'DuplicateRequestError')
}

http.interceptors.request.use((config) => {
  const requestKey = buildRequestKey(config)
  const now = Date.now()
  const recentAt = recentRequests.get(requestKey)

  if (pendingRequests.has(requestKey)) {
    return Promise.reject(createDuplicateRequestError(config))
  }
  if (recentAt && now - recentAt < DUPLICATE_GAP_MS) {
    return Promise.reject(createDuplicateRequestError(config))
  }

  config.__requestKey = requestKey
  pendingRequests.set(requestKey, now)

  const token = localStorage.getItem('task_manager_token') || ''
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => {
    releaseRequest(response.config)
    return response
  },
  (error) => {
    releaseRequest(error?.config)
    if (isDuplicateRequestError(error)) {
      return Promise.reject(error)
    }
    if (error?.response?.status === 401) {
      localStorage.removeItem('task_manager_token')
      localStorage.removeItem('task_manager_username')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// iframe 模式下的 token 管理
let iframeToken = null

export function setIframeToken(token) {
  iframeToken = token
}

export function getIframeToken() {
  return iframeToken
}

export function clearIframeToken() {
  iframeToken = null
}

http.interceptors.request.use((config) => {
  const requestKey = buildRequestKey(config)
  const now = Date.now()
  const recentAt = recentRequests.get(requestKey)

  if (pendingRequests.has(requestKey)) {
    return Promise.reject(createDuplicateRequestError(config))
  }
  if (recentAt && now - recentAt < DUPLICATE_GAP_MS) {
    return Promise.reject(createDuplicateRequestError(config))
  }

  config.__requestKey = requestKey
  pendingRequests.set(requestKey, now)

  // 优先使用 iframe token，其次使用 localStorage
  const token = iframeToken || localStorage.getItem('task_manager_token') || ''
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default http
