export interface SavedSession {
  token: string
  username: string
}

const ACTIVE_TOKEN_KEY = 'cr_active_token'
const LEGACY_TOKEN_KEY = 'cr_token'
const SAVED_SESSIONS_KEY = 'cr_saved_sessions'

function readJson(value: string | null): unknown {
  if (!value) return null
  try {
    return JSON.parse(value)
  } catch {
    return null
  }
}

export function getActiveToken(): string | null {
  const tabToken = sessionStorage.getItem(ACTIVE_TOKEN_KEY)
  if (tabToken) return tabToken

  const legacyToken = localStorage.getItem(LEGACY_TOKEN_KEY)
  if (legacyToken) {
    sessionStorage.setItem(ACTIVE_TOKEN_KEY, legacyToken)
    localStorage.removeItem(LEGACY_TOKEN_KEY)
    return legacyToken
  }
  return null
}

export function setActiveToken(token: string): void {
  sessionStorage.setItem(ACTIVE_TOKEN_KEY, token)
  localStorage.removeItem(LEGACY_TOKEN_KEY)
}

export function clearActiveToken(): void {
  sessionStorage.removeItem(ACTIVE_TOKEN_KEY)
  localStorage.removeItem(LEGACY_TOKEN_KEY)
}

export function readSavedSessions(): SavedSession[] {
  const value = readJson(localStorage.getItem(SAVED_SESSIONS_KEY))
  if (!Array.isArray(value)) return []
  return value.filter(
    (item): item is SavedSession =>
      !!item &&
      typeof item === 'object' &&
      typeof item.token === 'string' &&
      typeof item.username === 'string',
  )
}

export function rememberSession(token: string, username: string): SavedSession[] {
  const normalized = username.trim().toLowerCase()
  const sessions = readSavedSessions().filter(
    (item) =>
      item.token !== token && item.username.trim().toLowerCase() !== normalized,
  )
  const next = [{ token, username }, ...sessions].slice(0, 20)
  localStorage.setItem(SAVED_SESSIONS_KEY, JSON.stringify(next))
  return next
}

export function forgetSession(token: string | null): SavedSession[] {
  const next = readSavedSessions().filter((item) => item.token !== token)
  localStorage.setItem(SAVED_SESSIONS_KEY, JSON.stringify(next))
  return next
}
