<template>
  <div class="app">
    <header class="topbar">
      <div class="in">
        <router-link to="/" class="brand">
          <span class="sh"></span>CYBERRANGE
        </router-link>
        <nav class="nav">
          <router-link to="/overview">总览</router-link>
          <router-link to="/challenges">题库</router-link>
          <router-link to="/traffic">流量分析</router-link>
          <router-link to="/leaderboard">排行榜</router-link>
          <router-link to="/announcements">公告</router-link>
          <router-link to="/knowledge">知识</router-link>
        </nav>
        <div class="top-actions">
          <ThemeToggle />
          <template v-if="auth.isAuthenticated && auth.user">
            <div ref="notifRef" class="notif-wrap">
              <button
                class="notif-btn"
                type="button"
                :aria-label="unreadCount ? `通知，${unreadCount} 条未读` : '通知'"
                @click.stop="toggleNotifications"
              >
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" aria-hidden="true">
                  <path
                    d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"
                    stroke="currentColor"
                    stroke-width="1.8"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                  <path
                    d="M10 21h4"
                    stroke="currentColor"
                    stroke-width="1.8"
                    stroke-linecap="round"
                  />
                </svg>
                <span v-if="unreadCount" class="notif-badge">
                  {{ unreadCount > 99 ? '99+' : unreadCount }}
                </span>
              </button>

              <div v-if="notifOpen" class="notif-panel" @click.stop>
                <div class="notif-head">
                  <div>
                    <span class="notif-heading">通知</span>
                    <span v-if="unreadCount" class="notif-unread">{{ unreadCount }} 未读</span>
                  </div>
                  <button
                    v-if="unreadCount"
                    class="read-all"
                    type="button"
                    @click="markAllRead"
                  >全部已读</button>
                </div>

                <div class="notif-list">
                  <div v-if="notifLoading && notifications.length === 0" class="notif-empty">
                    正在读取通知…
                  </div>
                  <div v-else-if="notifications.length === 0" class="notif-empty">
                    暂无通知
                  </div>
                  <div
                    v-for="item in notifications"
                    :key="item.id"
                    class="notif-item"
                    :class="{ unread: !item.is_read }"
                    role="button"
                    tabindex="0"
                    @click="openNotification(item)"
                    @keyup.enter="openNotification(item)"
                  >
                    <div class="notif-item-top">
                      <span class="notif-dot" :class="{ on: !item.is_read }"></span>
                      <span class="notif-item-title">{{ item.title }}</span>
                      <time>{{ formatNoticeTime(item.created_at) }}</time>
                    </div>
                    <p>{{ item.content }}</p>
                  </div>
                </div>
              </div>
            </div>

            <router-link :to="auth.user.role === 'admin' ? '/admin' : '/profile'">
              <button class="btn" :class="{ alert: auth.user.role === 'admin' }">
                {{ auth.user.role === 'admin' ? 'ADMIN' : auth.user.username }}
              </button>
            </router-link>
            <div ref="accountRef" class="account-wrap">
              <button class="btn account-trigger" type="button" @click.stop="accountOpen = !accountOpen">
                切换账号
              </button>
              <div v-if="accountOpen" class="account-panel" @click.stop>
                <div class="account-head">
                  <span>已登录账号</span>
                  <small>各标签页独立保持</small>
                </div>
                <div class="account-current">
                  <span class="account-dot"></span>
                  <span>{{ auth.user.username }}</span>
                  <small>当前标签页</small>
                </div>
                <button
                  v-for="account in otherAccounts"
                  :key="account.token"
                  class="account-item"
                  type="button"
                  :disabled="accountSwitching === account.token"
                  @click="switchToAccount(account)"
                >
                  <span>{{ account.username }}</span>
                  <small>{{ accountSwitching === account.token ? '切换中…' : '切换' }}</small>
                </button>
                <div v-if="otherAccounts.length === 0" class="account-empty">
                  暂无其他已登录账号
                </div>
                <button class="account-login" type="button" @click="loginAnotherAccount">
                  + 登录其他账号
                </button>
              </div>
            </div>
            <button class="btn" @click="onLogout">退出</button>
          </template>
          <template v-else>
            <router-link to="/login"><button class="btn alert">登录 / 注册</button></router-link>
          </template>
        </div>
      </div>
    </header>

    <main class="container">
      <router-view :key="route.fullPath" />
    </main>

    <footer class="status-bar">
      <span>mode: <span class="ok">online</span></span>
      <span>CYBERRANGE · phase 1 · challenge & score</span>
      <span class="warn">⚡ red-alert ready</span>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { notificationsApi, type NotificationItem } from '../api/notifications'
import ThemeToggle from '../components/ThemeToggle.vue'
import { useAuthStore } from '../stores/auth'
import { parseServerDate } from '../utils/datetime'
import type { SavedSession } from '../utils/authSession'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const notifRef = ref<HTMLElement | null>(null)
const notifOpen = ref(false)
const accountRef = ref<HTMLElement | null>(null)
const accountOpen = ref(false)
const accountSwitching = ref('')
const notifLoading = ref(false)
const notifications = ref<NotificationItem[]>([])
const unreadCount = computed(() => notifications.value.filter((item) => !item.is_read).length)
const otherAccounts = computed(() =>
  auth.savedAccounts.filter((account) => account.token !== auth.token),
)
let pollTimer: ReturnType<typeof setInterval> | undefined

async function loadNotifications() {
  if (!auth.isAuthenticated) return
  notifLoading.value = true
  try {
    notifications.value = await notificationsApi.list()
  } catch {
    // 通知加载失败不阻断页面使用；下一轮轮询会重试。
  } finally {
    notifLoading.value = false
  }
}

function toggleNotifications() {
  notifOpen.value = !notifOpen.value
  if (notifOpen.value) loadNotifications()
}

function closeOnOutside(event: MouseEvent) {
  const target = event.target as Node
  if (notifOpen.value && notifRef.value && !notifRef.value.contains(target)) {
    notifOpen.value = false
  }
  if (accountOpen.value && accountRef.value && !accountRef.value.contains(target)) {
    accountOpen.value = false
  }
}

async function markAllRead() {
  if (!unreadCount.value) return
  try {
    await notificationsApi.markAllRead()
    notifications.value.forEach((item) => { item.is_read = true })
  } catch {
    // 保持当前未读状态，等待用户重试。
  }
}

async function openNotification(item: NotificationItem) {
  if (!item.is_read) {
    try {
      await notificationsApi.markRead(item.id)
      item.is_read = true
    } catch {
      // 跳转不受标记已读失败影响。
    }
  }
  notifOpen.value = false
  if (auth.user?.role === 'admin' && item.type === 'challenge_submitted') {
    router.push({ name: 'admin', query: { section: 'review' } })
  } else if (item.type === 'announcement_published' && item.related_article_id) {
    router.push(`/article/${item.related_article_id}`)
  }
}

function formatNoticeTime(value: string) {
  const d = parseServerDate(value)
  return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

watch(
  () => auth.isAuthenticated,
  (authenticated) => {
    if (authenticated) {
      loadNotifications()
    } else {
      notifications.value = []
      notifOpen.value = false
    }
  },
  { immediate: true },
)

onMounted(() => {
  document.addEventListener('click', closeOnOutside)
  pollTimer = setInterval(loadNotifications, 30000)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', closeOnOutside)
  if (pollTimer) clearInterval(pollTimer)
})

async function switchToAccount(account: SavedSession) {
  if (accountSwitching.value) return
  accountSwitching.value = account.token
  try {
    await auth.switchAccount(account.token)
    accountOpen.value = false
    notifications.value = []
    await loadNotifications()
    await router.push('/profile')
  } catch (e) {
    window.alert(`账号切换失败：${(e as Error).message}`)
  } finally {
    accountSwitching.value = ''
  }
}

function loginAnotherAccount() {
  accountOpen.value = false
  router.push({
    name: 'login',
    query: { switch: '1', redirect: route.fullPath },
  })
}

function onLogout() {
  auth.logout()
  accountOpen.value = false
  router.push('/')
}
</script>

<style scoped>
.notif-wrap {
  position: relative;
}
.notif-btn {
  position: relative;
  display: grid;
  place-items: center;
  width: 36px;
  height: 34px;
  padding: 0;
  border: 1px solid var(--line2);
  border-radius: 6px;
  background: var(--panel);
  color: var(--muted);
  cursor: pointer;
  transition: 0.15s;
}
.notif-btn:hover {
  border-color: var(--green);
  color: var(--green);
}
.notif-badge {
  position: absolute;
  top: -5px;
  right: -5px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 8px;
  background: var(--red);
  color: #fff;
  font-family: var(--mono);
  font-size: 9px;
  font-weight: 700;
  line-height: 16px;
  text-align: center;
  box-shadow: 0 0 8px rgba(var(--red-rgb), 0.55);
}
.notif-panel {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  z-index: 120;
  width: 360px;
  max-width: calc(100vw - 32px);
  overflow: hidden;
  border: 1px solid var(--line2);
  border-radius: 8px;
  background: var(--panel);
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.48);
}
.notif-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--line);
}
.notif-heading {
  color: var(--text-strong);
  font-size: 14px;
  font-weight: 800;
}
.notif-unread {
  margin-left: 8px;
  color: var(--red);
  font-family: var(--mono);
  font-size: 11px;
}
.read-all {
  padding: 3px 8px;
  border: 1px solid var(--line2);
  border-radius: 4px;
  background: transparent;
  color: var(--muted);
  font-size: 11px;
  cursor: pointer;
}
.read-all:hover {
  border-color: var(--green);
  color: var(--green);
}
.notif-list {
  max-height: 390px;
  overflow-y: auto;
}
.notif-item {
  display: block;
  width: 100%;
  padding: 12px 14px;
  border: 0;
  border-top: 1px solid var(--line);
  background: transparent;
  color: var(--text);
  text-align: left;
  cursor: pointer;
}
.notif-item:first-child {
  border-top: none;
}
.notif-item:hover {
  background: rgba(var(--green-rgb), 0.04);
}
.notif-item.unread {
  background: rgba(var(--green-rgb), 0.035);
}
.notif-item-top {
  display: flex;
  align-items: center;
  gap: 7px;
}
.notif-dot {
  flex-shrink: 0;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: transparent;
}
.notif-dot.on {
  background: var(--green);
  box-shadow: 0 0 7px rgba(var(--green-rgb), 0.8);
}
.notif-item-title {
  flex: 1;
  overflow: hidden;
  color: var(--text-strong);
  font-size: 13px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.notif-item-top time {
  flex-shrink: 0;
  color: var(--dim);
  font-family: var(--mono);
  font-size: 10px;
}
.notif-item p {
  display: -webkit-box;
  overflow: hidden;
  margin: 5px 0 0 12px;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.55;
  overflow-wrap: anywhere;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}
.notif-empty {
  padding: 34px 14px;
  color: var(--dim);
  font-size: 12px;
  text-align: center;
}

.account-wrap {
  position: relative;
}
.account-trigger {
  white-space: nowrap;
}
.account-panel {
  position: absolute;
  top: calc(100% + 9px);
  right: 0;
  z-index: 130;
  width: 238px;
  overflow: hidden;
  border: 1px solid var(--line2);
  border-radius: 8px;
  background: var(--panel);
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.48);
}
.account-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 11px 13px;
  border-bottom: 1px solid var(--line);
  color: var(--text-strong);
  font-size: 12px;
  font-weight: 700;
}
.account-head small,
.account-current small,
.account-item small {
  color: var(--dim);
  font-size: 9px;
  font-weight: 400;
}
.account-current,
.account-item {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 8px;
  padding: 10px 13px;
  border: 0;
  border-bottom: 1px solid var(--line);
  background: transparent;
  color: var(--text);
  font-size: 12px;
  text-align: left;
}
.account-current {
  color: var(--green);
}
.account-current small {
  margin-left: auto;
}
.account-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 8px rgba(var(--green-rgb), 0.75);
}
.account-item {
  cursor: pointer;
}
.account-item:hover:not(:disabled) {
  background: rgba(var(--green-rgb), 0.06);
  color: var(--green);
}
.account-item:disabled {
  opacity: 0.6;
  cursor: wait;
}
.account-item span {
  flex: 1;
}
.account-empty {
  padding: 15px 13px;
  border-bottom: 1px solid var(--line);
  color: var(--dim);
  font-size: 11px;
  text-align: center;
}
.account-login {
  width: 100%;
  padding: 11px 13px;
  border: 0;
  background: rgba(var(--green-rgb), 0.05);
  color: var(--green);
  font-size: 12px;
  font-weight: 700;
  text-align: left;
  cursor: pointer;
}
.account-login:hover {
  background: rgba(var(--green-rgb), 0.1);
}

</style>
