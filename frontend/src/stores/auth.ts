import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { authApi, type User } from '../api/auth'
import {
  clearActiveToken,
  forgetSession,
  getActiveToken,
  readSavedSessions,
  rememberSession,
  setActiveToken,
  type SavedSession,
} from '../utils/authSession'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(getActiveToken())
  const user = ref<User | null>(null)
  const savedAccounts = ref<SavedSession[]>(readSavedSessions())

  const isAuthenticated = computed(() => !!token.value)

  function saveCurrentAccount(activeToken: string, account: User) {
    savedAccounts.value = rememberSession(activeToken, account.username)
  }

  function activateToken(activeToken: string) {
    setActiveToken(activeToken)
    token.value = activeToken
  }

  async function login(username: string, password: string) {
    const res = await authApi.login(username, password)
    activateToken(res.access_token)
    user.value = await authApi.me()
    saveCurrentAccount(res.access_token, user.value)
  }

  async function register(username: string, email: string, password: string) {
    await authApi.register(username, email, password)
    await login(username, password)
  }

  async function fetchMe() {
    if (!token.value) return
    const activeToken = token.value
    try {
      user.value = await authApi.me()
      saveCurrentAccount(activeToken, user.value)
    } catch {
      logout()
    }
  }

  async function switchAccount(nextToken: string) {
    if (!nextToken || nextToken === token.value) return
    const previousToken = token.value
    const previousUser = user.value
    activateToken(nextToken)
    try {
      user.value = await authApi.me()
      saveCurrentAccount(nextToken, user.value)
    } catch (error) {
      savedAccounts.value = forgetSession(nextToken)
      if (previousToken) {
        activateToken(previousToken)
        user.value = previousUser
      } else {
        logout()
      }
      throw error
    }
  }

  function logout() {
    savedAccounts.value = forgetSession(token.value)
    clearActiveToken()
    token.value = null
    user.value = null
  }

  return {
    token,
    user,
    savedAccounts,
    isAuthenticated,
    login,
    register,
    fetchMe,
    switchAccount,
    logout,
  }
})
