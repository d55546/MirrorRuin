import { getActiveToken } from '../utils/authSession'

const API = ((import.meta.env.VITE_API_BASE as string | undefined)?.trim() || '/api').replace(
  /\/$/,
  '',
)
const REQUEST_TIMEOUT_MS = 15_000

function errorDetail(detail: unknown): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item && typeof item === 'object' && 'msg' in item) return String(item.msg)
        return String(item)
      })
      .join('；')
  }
  if (detail && typeof detail === 'object' && 'message' in detail) {
    return String(detail.message)
  }
  return ''
}

async function responseError(res: Response): Promise<string> {
  let detail = ''
  try {
    const data = await res.json()
    detail = errorDetail(data?.detail ?? data?.message)
  } catch {
    // 非 JSON 错误响应使用状态码提示。
  }

  if ([500, 502, 503, 504].includes(res.status) && !detail) {
    return `后端服务异常（HTTP ${res.status}），请确认后端已启动后重试。`
  }
  return detail || `请求失败（HTTP ${res.status}）`
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getActiveToken()
  const headers = new Headers(options.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)

  let res: Response
  try {
    res = await fetch(`${API}${path}`, {
      ...options,
      headers,
      signal: options.signal ?? controller.signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('请求超时，请检查网络连接后重试。')
    }
    console.error(`[API] 无法访问 ${API}${path}`, error)
    throw new Error(
      '无法连接后端服务。请确认后端已启动（默认 8000 端口）后重试。',
    )
  } finally {
    window.clearTimeout(timeout)
  }

  if (!res.ok) {
    throw new Error(await responseError(res))
  }
  if (res.status === 204) {
    return undefined as T
  }
  return res.json() as Promise<T>
}

export const http = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  postForm: <T>(path: string, body: FormData) =>
    request<T>(path, { method: 'POST', body }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: <T = void>(path: string, body?: unknown) =>
    request<T>(path, { method: 'DELETE', body: body ? JSON.stringify(body) : undefined }),
}
