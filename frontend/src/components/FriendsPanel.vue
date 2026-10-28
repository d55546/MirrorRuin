<template>
  <section class="social-panel">
    <header class="social-head">
      <div>
        <div class="social-title">
          <span>好友与聊天</span>
          <span v-if="overview.unread_count" class="unread-badge">{{ overview.unread_count }}</span>
        </div>
        <p>添加其他选手为好友，成为好友后可以互相发送私信。</p>
      </div>
      <span class="social-signal"><i></i>SECURE CHAT</span>
    </header>

    <p v-if="actionError" class="notice err">{{ actionError }}</p>
    <p v-else-if="actionMsg" class="notice ok">{{ actionMsg }}</p>

    <div class="social-grid">
      <aside class="social-side">
        <ElForm class="user-search" :inline="true" @submit.prevent="searchUsers">
          <ElFormItem class="search-field">
            <ElInput
              v-model.trim="searchQuery"
              maxlength="50"
              clearable
              placeholder="输入用户名搜索"
              aria-label="搜索用户"
            />
          </ElFormItem>
          <ElFormItem class="search-action">
            <ElButton
              type="primary"
              native-type="submit"
              :loading="searching"
              :disabled="!searchQuery"
            >搜索</ElButton>
          </ElFormItem>
        </ElForm>

        <div v-if="searchResults.length" class="search-results">
          <div v-for="user in searchResults" :key="user.id" class="person-row">
            <span class="mini-avatar">{{ user.username.slice(0, 1).toUpperCase() }}</span>
            <span class="person-name">{{ user.username }}</span>
            <button
              class="mini-btn"
              type="button"
              :disabled="busyKey === `add-${user.id}` || !!relationState(user)"
              @click="addFriend(user)"
            >{{ relationState(user) || (busyKey === `add-${user.id}` ? '发送中…' : '加好友') }}</button>
          </div>
        </div>

        <section v-if="overview.incoming.length" class="relation-section">
          <div class="section-label">
            收到的好友申请
            <span>{{ overview.incoming.length }}</span>
          </div>
          <div v-for="request in overview.incoming" :key="request.id" class="request-row">
            <span class="mini-avatar amber">{{ request.user.username.slice(0, 1).toUpperCase() }}</span>
            <span class="person-name">{{ request.user.username }}</span>
            <button
              class="mini-btn accept"
              type="button"
              :disabled="busyKey === `accept-${request.id}`"
              @click="acceptRequest(request)"
            >接受</button>
            <button
              class="icon-btn"
              type="button"
              title="拒绝"
              :disabled="busyKey === `reject-${request.id}`"
              @click="deleteRequest(request)"
            >×</button>
          </div>
        </section>

        <section v-if="overview.outgoing.length" class="relation-section">
          <div class="section-label">已发送的申请</div>
          <div v-for="request in overview.outgoing" :key="request.id" class="request-row">
            <span class="mini-avatar dim">{{ request.user.username.slice(0, 1).toUpperCase() }}</span>
            <span class="person-name">{{ request.user.username }}</span>
            <button
              class="mini-btn ghost"
              type="button"
              :disabled="busyKey === `cancel-${request.id}`"
              @click="deleteRequest(request)"
            >撤回</button>
          </div>
        </section>

        <div class="friend-list">
          <div class="section-label">
            我的好友
            <span>{{ overview.friends.length }}</span>
          </div>
          <div v-if="loading" class="side-empty">正在加载好友…</div>
          <div v-else-if="overview.friends.length === 0" class="side-empty">
            还没有好友，搜索用户名发送申请吧。
          </div>
          <button
            v-for="friend in overview.friends"
            :key="friend.id"
            class="friend-item"
            :class="{ active: selectedId === friend.id }"
            type="button"
            @click="selectFriend(friend.id)"
          >
            <span class="mini-avatar">{{ friend.username.slice(0, 1).toUpperCase() }}</span>
            <span class="friend-copy">
              <span class="person-name">{{ friend.username }}</span>
              <small>{{ friend.last_message || '开始交流' }}</small>
            </span>
            <span v-if="friend.unread_count" class="friend-unread">{{ friend.unread_count }}</span>
          </button>
        </div>
      </aside>

      <section class="chat-box">
        <template v-if="selectedFriend">
          <header class="chat-head">
            <div class="chat-person">
              <span class="chat-avatar">{{ selectedFriend.username.slice(0, 1).toUpperCase() }}</span>
              <div>
                <strong>{{ selectedFriend.username }}</strong>
                <small v-if="selectedFriend.role === 'admin'">管理员</small>
                <small v-else>选手</small>
              </div>
            </div>
            <button class="mini-btn ghost" type="button" @click="removeFriend(selectedFriend)">
              删除好友
            </button>
          </header>

          <div ref="messagesRef" class="messages">
            <div v-if="messagesLoading && messages.length === 0" class="chat-empty">正在加载消息…</div>
            <div v-else-if="messages.length === 0" class="chat-empty">
              你们已经成为好友，发送第一条消息吧。
            </div>
            <div
              v-for="message in messages"
              :key="message.id"
              class="message-row"
              :class="{ mine: message.is_mine }"
            >
              <span
                class="message-avatar"
                :class="message.is_mine ? 'mine' : 'friend'"
              >{{ senderInitial(message) }}</span>
              <div class="message-stack">
                <span class="message-sender">
                  {{ senderName(message) }}
                  <em class="sender-role">{{ message.is_mine ? '我' : '对方' }}</em>
                </span>
                <div class="bubble">
                  <p>{{ message.content }}</p>
                  <time>{{ formatTime(message.created_at) }}</time>
                </div>
              </div>
            </div>
          </div>

          <ElForm class="message-form" @submit.prevent="sendMessage">
            <ElFormItem class="message-field">
              <ElInput
                v-model="messageDraft"
                type="textarea"
                maxlength="2000"
                show-word-limit
                :autosize="{ minRows: 2, maxRows: 5 }"
                placeholder="输入私信，Enter 发送，Shift + Enter 换行"
                @keydown.enter="handleEnterSend"
              />
            </ElFormItem>
            <div class="message-actions">
              <span>Enter 发送 · Shift + Enter 换行</span>
              <ElButton
                type="primary"
                native-type="submit"
                :loading="sending"
                :disabled="!messageDraft.trim()"
              >发送</ElButton>
            </div>
          </ElForm>
        </template>

        <div v-else class="chat-placeholder">
          <div class="placeholder-icon">@</div>
          <strong>选择一位好友开始聊天</strong>
          <span>好友之间的私信仅双方可见。</span>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElButton, ElForm, ElFormItem, ElInput } from 'element-plus'
import 'element-plus/es/components/button/style/css'
import 'element-plus/es/components/form/style/css'
import 'element-plus/es/components/form-item/style/css'
import 'element-plus/es/components/input/style/css'
import {
  socialApi,
  type DirectMessage,
  type Friend,
  type FriendRequest,
  type SocialOverview,
  type SocialUser,
} from '../api/social'
import { useAuthStore } from '../stores/auth'
import { parseServerDate } from '../utils/datetime'

const auth = useAuthStore()

const emptyOverview = (): SocialOverview => ({
  friends: [],
  incoming: [],
  outgoing: [],
  unread_count: 0,
})

const overview = ref<SocialOverview>(emptyOverview())
const loading = ref(true)
const searchQuery = ref('')
const searching = ref(false)
const searchResults = ref<SocialUser[]>([])
const busyKey = ref('')
const actionError = ref('')
const actionMsg = ref('')
const selectedId = ref<number | null>(null)
const messages = ref<DirectMessage[]>([])
const messagesLoading = ref(false)
const sending = ref(false)
const messageDraft = ref('')
const messagesRef = ref<HTMLElement | null>(null)
let overviewTimer: ReturnType<typeof setInterval> | undefined
let messageTimer: ReturnType<typeof setInterval> | undefined
let pollingMessages = false

const selectedFriend = computed(
  () => overview.value.friends.find((friend) => friend.id === selectedId.value) ?? null,
)

function relationState(user: SocialUser): string {
  if (overview.value.friends.some((friend) => friend.id === user.id)) return '已是好友'
  if (overview.value.incoming.some((request) => request.user.id === user.id)) return '待接受'
  if (overview.value.outgoing.some((request) => request.user.id === user.id)) return '已申请'
  return ''
}

function setNotice(message: string, ok: boolean) {
  actionMsg.value = ok ? message : ''
  actionError.value = ok ? '' : message
}

async function loadOverview(silent = false) {
  if (!silent) loading.value = true
  try {
    overview.value = await socialApi.overview()
    if (selectedId.value && !selectedFriend.value) {
      selectedId.value = null
      messages.value = []
    }
    if (!selectedId.value && overview.value.friends.length) {
      selectFriend(overview.value.friends[0].id)
    }
  } catch (e) {
    if (!silent) setNotice((e as Error).message, false)
  } finally {
    loading.value = false
  }
}

async function searchUsers() {
  const query = searchQuery.value.trim()
  if (!query) return
  searching.value = true
  actionError.value = ''
  try {
    searchResults.value = await socialApi.search(query)
    if (searchResults.value.length === 0) setNotice('没有找到匹配的用户', false)
  } catch (e) {
    searchResults.value = []
    setNotice((e as Error).message, false)
  } finally {
    searching.value = false
  }
}

async function addFriend(user: SocialUser) {
  busyKey.value = `add-${user.id}`
  try {
    await socialApi.sendRequest(user.username)
    await loadOverview(true)
    setNotice(`已向 ${user.username} 发送好友申请`, true)
  } catch (e) {
    setNotice((e as Error).message, false)
  } finally {
    busyKey.value = ''
  }
}

async function acceptRequest(request: FriendRequest) {
  busyKey.value = `accept-${request.id}`
  try {
    await socialApi.acceptRequest(request.id)
    await loadOverview(true)
    setNotice(`已与 ${request.user.username} 成为好友`, true)
  } catch (e) {
    setNotice((e as Error).message, false)
  } finally {
    busyKey.value = ''
  }
}

async function deleteRequest(request: FriendRequest) {
  const action = overview.value.outgoing.some((item) => item.id === request.id) ? '撤回' : '拒绝'
  if (!window.confirm(`确定${action}对 ${request.user.username} 的好友申请吗？`)) return
  busyKey.value = `${action === '撤回' ? 'cancel' : 'reject'}-${request.id}`
  try {
    await socialApi.deleteRequest(request.id)
    await loadOverview(true)
    setNotice(`已${action}该申请`, true)
  } catch (e) {
    setNotice((e as Error).message, false)
  } finally {
    busyKey.value = ''
  }
}

async function removeFriend(friend: Friend) {
  if (!window.confirm(`确定删除好友 ${friend.username} 吗？双方的聊天记录也会被清除。`)) return
  busyKey.value = `remove-${friend.id}`
  try {
    await socialApi.removeFriend(friend.id)
    selectedId.value = null
    messages.value = []
    await loadOverview(true)
    setNotice(`已删除好友 ${friend.username}`, true)
  } catch (e) {
    setNotice((e as Error).message, false)
  } finally {
    busyKey.value = ''
  }
}

async function selectFriend(friendId: number) {
  selectedId.value = friendId
  messages.value = []
  await loadMessages(false)
}

async function loadMessages(silent: boolean) {
  const friendId = selectedId.value
  if (!friendId || (silent && pollingMessages)) return
  pollingMessages = true
  if (!silent) messagesLoading.value = true
  try {
    const result = await socialApi.messages(friendId)
    if (selectedId.value !== friendId) return
    const grew = result.items.length !== messages.value.length
    messages.value = result.items
    const friend = overview.value.friends.find((item) => item.id === friendId)
    if (friend) friend.unread_count = 0
    overview.value.unread_count = overview.value.friends.reduce(
      (sum, item) => sum + item.unread_count,
      0,
    )
    if (grew) await nextTick(() => scrollToBottom())
  } catch (e) {
    if (!silent) setNotice((e as Error).message, false)
  } finally {
    pollingMessages = false
    if (!silent) messagesLoading.value = false
  }
}

function handleEnterSend(event: Event | KeyboardEvent) {
  if (!(event instanceof KeyboardEvent)) return
  if (event.isComposing || event.keyCode === 229 || event.shiftKey || event.altKey) return
  event.preventDefault()
  void sendMessage()
}

async function sendMessage() {
  const friendId = selectedId.value
  const content = messageDraft.value.trim()
  if (!friendId || !content || sending.value) return
  sending.value = true
  try {
    const created = await socialApi.sendMessage(friendId, content)
    messages.value.push(created)
    messageDraft.value = ''
    setNotice('', true)
    await nextTick(() => scrollToBottom())
    await loadOverview(true)
  } catch (e) {
    setNotice((e as Error).message, false)
  } finally {
    sending.value = false
  }
}

function scrollToBottom() {
  if (!messagesRef.value) return
  messagesRef.value.scrollTop = messagesRef.value.scrollHeight
}

function senderName(message: DirectMessage) {
  return message.is_mine ? auth.user?.username || '我' : selectedFriend.value?.username || ''
}

function senderInitial(message: DirectMessage) {
  return senderName(message).slice(0, 1).toUpperCase()
}

function formatTime(value: string) {
  return parseServerDate(value).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

onMounted(async () => {
  await loadOverview()
  overviewTimer = setInterval(() => loadOverview(true), 10_000)
  messageTimer = setInterval(() => loadMessages(true), 4_000)
})

onBeforeUnmount(() => {
  if (overviewTimer) clearInterval(overviewTimer)
  if (messageTimer) clearInterval(messageTimer)
})
</script>

<style scoped>
.social-panel {
  --el-color-primary: var(--green);
  --el-color-primary-light-3: var(--green);
  --el-color-primary-light-5: rgba(var(--green-rgb), 0.55);
  --el-color-primary-light-7: rgba(var(--green-rgb), 0.28);
  --el-color-primary-light-9: rgba(var(--green-rgb), 0.09);
  --el-bg-color: var(--panel);
  --el-fill-color-blank: var(--field-bg);
  --el-text-color-regular: var(--text);
  --el-text-color-placeholder: var(--dim);
  --el-border-color: var(--line2);
  --el-border-color-light: var(--line);
  --el-border-color-hover: var(--green);
  --el-font-family: var(--sans);
  padding: 22px 24px 24px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--panel);
}
.social-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding-bottom: 17px;
  border-bottom: 1px solid var(--line);
}
.social-title {
  display: flex;
  align-items: center;
  gap: 9px;
  color: var(--text-strong);
  font-size: 17px;
  font-weight: 800;
}
.social-head p {
  margin-top: 6px;
  color: var(--dim);
  font-size: 12px;
}
.unread-badge {
  min-width: 20px;
  padding: 1px 6px;
  border-radius: 10px;
  background: var(--red);
  color: #fff;
  font-family: var(--mono);
  font-size: 10px;
  text-align: center;
}
.social-signal {
  display: flex;
  align-items: center;
  gap: 7px;
  color: var(--muted);
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 1px;
  white-space: nowrap;
}
.social-signal i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 9px rgba(var(--green-rgb), 0.8);
}
.notice {
  margin-top: 13px;
  padding: 8px 11px;
  border-radius: 5px;
  font-size: 12px;
}
.notice.ok {
  border: 1px solid rgba(var(--green-rgb), 0.25);
  background: rgba(var(--green-rgb), 0.06);
  color: var(--green);
}
.notice.err {
  border: 1px solid rgba(var(--red-rgb), 0.35);
  background: rgba(var(--red-rgb), 0.07);
  color: var(--red);
}
.social-grid {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  min-height: 500px;
  margin-top: 18px;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 8px;
}
.social-side {
  min-width: 0;
  padding: 13px;
  border-right: 1px solid var(--line);
  background: var(--panel2);
}
.user-search {
  display: flex;
  width: 100%;
  gap: 7px;
}
.user-search :deep(.el-form-item) {
  min-width: 0;
  margin: 0;
}
.user-search .search-field {
  flex: 1;
}
.user-search .search-field :deep(.el-form-item__content) {
  min-width: 0;
}
.user-search :deep(.el-input__wrapper) {
  min-height: 33px;
  padding: 0 10px;
  border-radius: 5px;
  background: var(--field-bg);
  box-shadow: 0 0 0 1px var(--line2) inset;
  transition: 0.15s ease;
}
.user-search :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--muted) inset;
}
.user-search :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    0 0 0 1px var(--green) inset,
    0 0 0 3px rgba(var(--green-rgb), 0.1);
}
.user-search :deep(.el-input__inner) {
  color: var(--text);
  font-size: 12px;
}
.user-search :deep(.el-input__inner::placeholder) {
  color: var(--dim);
}
.user-search :deep(.el-input__clear) {
  color: var(--dim);
}
.user-search :deep(.el-button) {
  min-height: 33px;
  padding: 6px 11px;
  border-radius: 5px;
  font-size: 12px;
}
.search-results,
.relation-section {
  margin-top: 11px;
  padding: 8px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel);
}
.person-row,
.request-row {
  display: flex;
  align-items: center;
  gap: 7px;
  min-height: 34px;
}
.person-row + .person-row,
.request-row + .request-row {
  margin-top: 5px;
}
.mini-avatar {
  display: grid;
  flex: 0 0 25px;
  place-items: center;
  width: 25px;
  height: 25px;
  border: 1px solid rgba(var(--green-rgb), 0.35);
  border-radius: 50%;
  background: rgba(var(--green-rgb), 0.08);
  color: var(--green);
  font-family: var(--mono);
  font-size: 10px;
  font-weight: 700;
}
.mini-avatar.amber {
  border-color: rgba(var(--amber-rgb), 0.4);
  background: rgba(var(--amber-rgb), 0.08);
  color: var(--amber);
}
.mini-avatar.dim {
  border-color: var(--line2);
  background: transparent;
  color: var(--dim);
}
.person-name {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  color: var(--text);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.mini-btn {
  flex-shrink: 0;
  padding: 3px 7px;
  border: 1px solid var(--line2);
  border-radius: 4px;
  background: transparent;
  color: var(--muted);
  font-size: 10px;
  cursor: pointer;
}
.mini-btn:hover:not(:disabled),
.mini-btn.accept {
  border-color: var(--green);
  color: var(--green);
}
.mini-btn.ghost {
  color: var(--dim);
}
.mini-btn:disabled {
  opacity: 0.52;
  cursor: wait;
}
.icon-btn {
  width: 20px;
  height: 20px;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--dim);
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
}
.icon-btn:hover {
  color: var(--red);
}
.section-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 5px 2px 9px;
  color: var(--muted);
  font-size: 10px;
  letter-spacing: 0.5px;
}
.section-label span {
  color: var(--cyan);
  font-family: var(--mono);
}
.friend-list {
  margin-top: 15px;
}
.friend-item {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 8px;
  padding: 7px;
  border: 1px solid transparent;
  border-radius: 5px;
  background: transparent;
  text-align: left;
  cursor: pointer;
}
.friend-item:hover {
  background: rgba(var(--green-rgb), 0.04);
}
.friend-item.active {
  border-color: rgba(var(--green-rgb), 0.24);
  background: rgba(var(--green-rgb), 0.07);
}
.friend-copy {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 2px;
}
.friend-copy small {
  overflow: hidden;
  color: var(--dim);
  font-size: 9px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.friend-unread {
  min-width: 17px;
  height: 17px;
  padding: 0 4px;
  border-radius: 9px;
  background: var(--red);
  color: #fff;
  font-family: var(--mono);
  font-size: 9px;
  line-height: 17px;
  text-align: center;
}
.side-empty {
  padding: 14px 8px;
  color: var(--dim);
  font-size: 11px;
  line-height: 1.6;
  text-align: center;
}
.chat-box {
  display: flex;
  min-width: 0;
  flex-direction: column;
  background: var(--field-soft);
}
.chat-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 17px;
  border-bottom: 1px solid var(--line);
  background: var(--panel);
}
.chat-person {
  display: flex;
  align-items: center;
  gap: 10px;
}
.chat-avatar {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--green), var(--cyan));
  color: var(--on-accent);
  font-family: var(--mono);
  font-size: 13px;
  font-weight: 800;
}
.chat-person div {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.chat-person strong {
  color: var(--text-strong);
  font-size: 13px;
}
.chat-person small {
  color: var(--dim);
  font-size: 10px;
}
.messages {
  min-height: 0;
  flex: 1;
  padding: 17px;
  overflow-y: auto;
}
.chat-empty {
  padding: 90px 20px;
  color: var(--dim);
  font-size: 12px;
  line-height: 1.8;
  text-align: center;
}
.message-row {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  margin-bottom: 15px;
  justify-content: flex-start;
}
.message-row.mine {
  flex-direction: row-reverse;
}
.message-avatar {
  display: grid;
  flex: 0 0 32px;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 800;
}
.message-avatar.friend {
  border: 1px solid rgba(var(--cyan-rgb), 0.38);
  background: rgba(var(--cyan-rgb), 0.09);
  color: var(--cyan);
}
.message-avatar.mine {
  border: 1px solid rgba(var(--green-rgb), 0.42);
  background: rgba(var(--green-rgb), 0.11);
  color: var(--green);
}
.message-stack {
  display: flex;
  max-width: min(76%, 520px);
  align-items: flex-start;
  flex-direction: column;
}
.message-row.mine .message-stack {
  align-items: flex-end;
}
.message-sender {
  display: flex;
  align-items: center;
  gap: 5px;
  margin: 0 5px 4px;
  color: var(--muted);
  font-size: 10px;
}
.message-row.mine .message-sender {
  flex-direction: row-reverse;
  color: var(--green);
}
.sender-role {
  padding: 1px 4px;
  border: 1px solid var(--line2);
  border-radius: 3px;
  color: var(--dim);
  font-family: var(--mono);
  font-size: 8px;
  font-style: normal;
  line-height: 1.2;
}
.message-row.mine .sender-role {
  border-color: rgba(var(--green-rgb), 0.42);
  color: var(--green);
}
.bubble {
  position: relative;
  max-width: 100%;
  padding: 9px 12px;
  border: 1px solid var(--line2);
  border-radius: 4px 12px 12px 12px;
  background: var(--panel2);
  box-shadow: 0 5px 14px rgba(0, 0, 0, 0.12);
}
.message-row:not(.mine) .bubble::before {
  content: '';
  position: absolute;
  top: 12px;
  left: -6px;
  border-top: 5px solid transparent;
  border-right: 6px solid var(--panel2);
  border-bottom: 5px solid transparent;
}
.message-row.mine .bubble {
  border-color: var(--green);
  border-radius: 12px 4px 12px 12px;
  background: var(--green);
  box-shadow: 0 0 18px rgba(var(--green-rgb), 0.18);
}
.message-row.mine .bubble::after {
  content: '';
  position: absolute;
  top: 12px;
  right: -6px;
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
  border-left: 6px solid var(--green);
}
.bubble p {
  color: var(--text);
  font-size: 13px;
  line-height: 1.65;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
}
.message-row.mine .bubble p {
  color: var(--on-accent);
  font-weight: 600;
}
.bubble time {
  display: block;
  margin-top: 5px;
  color: var(--dim);
  font-family: var(--mono);
  font-size: 9px;
  text-align: right;
}
.message-row.mine .bubble time {
  color: rgba(6, 38, 26, 0.64);
}
.message-form {
  padding: 11px 14px 13px;
  border-top: 1px solid var(--line);
  background: var(--panel);
}
.message-form :deep(.el-form-item) {
  margin-bottom: 0;
}
.message-form :deep(.el-textarea__inner) {
  min-height: 54px !important;
  padding: 9px 11px 24px;
  border-radius: 6px;
  background: var(--field-bg);
  box-shadow: 0 0 0 1px var(--line2) inset;
  color: var(--text);
  font-family: var(--sans);
  font-size: 13px;
  line-height: 1.65;
  transition: 0.15s ease;
}
.message-form :deep(.el-textarea__inner:hover) {
  box-shadow: 0 0 0 1px var(--muted) inset;
}
.message-form :deep(.el-textarea__inner:focus) {
  box-shadow:
    0 0 0 1px var(--green) inset,
    0 0 0 3px rgba(var(--green-rgb), 0.1);
}
.message-form :deep(.el-textarea__inner::placeholder) {
  color: var(--dim);
}
.message-form :deep(.el-input__count) {
  right: 12px;
  bottom: 6px;
  background: transparent;
  color: var(--dim);
  font-family: var(--mono);
  font-size: 9px;
}
.message-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}
.message-actions span {
  color: var(--dim);
  font-family: var(--mono);
  font-size: 10px;
}
.message-actions :deep(.el-button) {
  min-width: 74px;
  padding: 7px 18px;
  border-radius: 5px;
  font-size: 12px;
  font-weight: 700;
}
.social-panel :deep(.el-button--primary) {
  --el-button-bg-color: var(--green);
  --el-button-border-color: var(--green);
  --el-button-hover-bg-color: var(--green);
  --el-button-hover-border-color: var(--green);
  --el-button-active-bg-color: var(--green);
  --el-button-active-border-color: var(--green);
  --el-button-text-color: var(--on-accent);
  --el-button-hover-text-color: var(--on-accent);
  --el-button-active-text-color: var(--on-accent);
  box-shadow: 0 0 12px rgba(var(--green-rgb), 0.18);
}
.social-panel :deep(.el-button--primary:hover) {
  filter: brightness(1.08);
}
.social-panel :deep(.el-button--primary.is-disabled) {
  --el-button-disabled-bg-color: rgba(var(--green-rgb), 0.34);
  --el-button-disabled-border-color: transparent;
  --el-button-disabled-text-color: rgba(6, 38, 26, 0.65);
  box-shadow: none;
  filter: none;
}
.chat-placeholder {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 8px;
  color: var(--dim);
  text-align: center;
}
.placeholder-icon {
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  margin-bottom: 5px;
  border: 1px solid var(--line2);
  border-radius: 50%;
  color: var(--green);
  font-family: var(--mono);
  font-size: 24px;
}
.chat-placeholder strong {
  color: var(--muted);
  font-size: 14px;
}
.chat-placeholder span {
  font-size: 11px;
}
@media (max-width: 900px) {
  .social-grid {
    grid-template-columns: 1fr;
  }
  .social-side {
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }
  .chat-box {
    min-height: 440px;
  }
  .social-head {
    flex-direction: column;
    gap: 8px;
  }
  .social-signal {
    display: none;
  }
}
</style>
