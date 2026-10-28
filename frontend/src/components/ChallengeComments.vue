<template>
  <section class="comments">
    <div class="comments-head">
      <div>
        <div class="comments-title">
          <span>讨论区</span>
          <span class="comment-count">{{ total }}</span>
        </div>
        <p class="comments-sub">分享思路、交流工具，请勿直接发布 Flag 或完整答案。</p>
      </div>
      <span class="comments-signal"><i></i>DISCUSSION</span>
    </div>

    <form v-if="auth.isAuthenticated" class="comment-form" @submit.prevent="submit">
      <textarea
        v-model="draft"
        maxlength="1000"
        rows="4"
        placeholder="写下你的想法、踩坑记录或解题提示…（Ctrl + Enter 发布）"
        @keydown.ctrl.enter.prevent="submit"
      />
      <div class="comment-form-foot">
        <span class="comment-rule">{{ draft.length }} / 1000</span>
        <button class="btn primary" type="submit" :disabled="posting || !draft.trim()">
          {{ posting ? '发布中…' : '发布评论' }}
        </button>
      </div>
    </form>

    <div v-else class="comment-login">
      <span>登录后可以参与讨论，与其他选手交流思路。</span>
      <button class="btn" type="button" @click="goLogin">去登录</button>
    </div>

    <p v-if="error" class="comment-error">{{ error }}</p>

    <div v-if="loading" class="comment-empty">正在加载讨论…</div>
    <div v-else-if="comments.length === 0" class="comment-empty">
      还没有评论，来做第一个交流的人。
    </div>
    <div v-else class="comment-list">
      <article v-for="item in comments" :key="item.id" class="comment-item">
        <div class="comment-avatar">{{ item.username.slice(0, 1).toUpperCase() }}</div>
        <div class="comment-body">
          <div class="comment-meta">
            <span class="comment-user">{{ item.username }}</span>
            <span v-if="item.role === 'admin'" class="admin-tag">ADMIN</span>
            <span v-if="item.is_mine" class="mine-tag">我</span>
            <time>{{ formatTime(item.created_at) }}</time>
            <button
              v-if="item.is_mine || auth.user?.role === 'admin'"
              class="comment-delete"
              type="button"
              :disabled="deletingId === item.id"
              @click="remove(item)"
            >{{ deletingId === item.id ? '删除中…' : '删除' }}</button>
          </div>
          <p class="comment-content">{{ item.content }}</p>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { commentsApi, type ChallengeComment, type CommentTarget } from '../api/comments'
import { useAuthStore } from '../stores/auth'
import { parseServerDate } from '../utils/datetime'

const props = defineProps<{
  targetType: CommentTarget
  targetId: number
}>()

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const comments = ref<ChallengeComment[]>([])
const total = ref(0)
const draft = ref('')
const loading = ref(false)
const posting = ref(false)
const deletingId = ref<number | null>(null)
const error = ref('')

async function load() {
  if (!props.targetId) return
  loading.value = true
  error.value = ''
  try {
    const result = await commentsApi.list(props.targetType, props.targetId)
    comments.value = result.items
    total.value = result.total
  } catch (e) {
    comments.value = []
    total.value = 0
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

async function submit() {
  if (!auth.isAuthenticated) {
    goLogin()
    return
  }
  const content = draft.value.trim()
  if (!content || posting.value) return
  posting.value = true
  error.value = ''
  try {
    const created = await commentsApi.create(props.targetType, props.targetId, content)
    comments.value.unshift(created)
    total.value += 1
    draft.value = ''
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    posting.value = false
  }
}

async function remove(item: ChallengeComment) {
  if (!window.confirm(`确定删除“${item.username}”的这条评论吗？`)) return
  deletingId.value = item.id
  error.value = ''
  try {
    await commentsApi.remove(item.id)
    comments.value = comments.value.filter((comment) => comment.id !== item.id)
    total.value = Math.max(0, total.value - 1)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    deletingId.value = null
  }
}

function goLogin() {
  router.push({ name: 'login', query: { redirect: route.fullPath } })
}

function formatTime(value: string) {
  const date = parseServerDate(value)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

watch(
  () => [props.targetType, props.targetId],
  () => load(),
)

onMounted(load)
</script>

<style scoped>
.comments {
  margin-top: 30px;
  padding-top: 26px;
  border-top: 1px dashed var(--line2);
}
.comments-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
}
.comments-title {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-strong);
  font-size: 19px;
  font-weight: 800;
}
.comment-count {
  min-width: 25px;
  padding: 2px 8px;
  border: 1px solid rgba(var(--cyan-rgb), 0.42);
  border-radius: 12px;
  color: var(--cyan);
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 400;
  text-align: center;
}
.comments-sub {
  margin-top: 7px;
  color: var(--dim);
  font-size: 12px;
}
.comments-signal {
  display: flex;
  align-items: center;
  gap: 7px;
  color: var(--muted);
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 1.3px;
  white-space: nowrap;
}
.comments-signal i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 9px rgba(var(--green-rgb), 0.8);
}
.comment-form {
  margin-bottom: 20px;
}
.comment-form textarea {
  display: block;
  width: 100%;
  min-height: 98px;
  padding: 13px 15px;
  resize: vertical;
  border: 1px solid var(--line2);
  border-radius: 7px;
  outline: none;
  background: var(--field-bg);
  color: var(--text);
  font: inherit;
  font-size: 14px;
  line-height: 1.7;
  transition: 0.15s;
}
.comment-form textarea::placeholder {
  color: var(--dim);
}
.comment-form textarea:focus {
  border-color: var(--green);
  box-shadow: 0 0 0 3px rgba(var(--green-rgb), 0.08);
}
.comment-form-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 9px;
}
.comment-rule {
  color: var(--dim);
  font-family: var(--mono);
  font-size: 11px;
}
.comment-form-foot .btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.comment-login {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
  padding: 14px 16px;
  border: 1px dashed var(--line2);
  border-radius: 7px;
  color: var(--muted);
  font-size: 13px;
}
.comment-login .btn {
  flex-shrink: 0;
}
.comment-error {
  margin-bottom: 14px;
  padding: 9px 12px;
  border: 1px solid rgba(var(--red-rgb), 0.38);
  border-radius: 6px;
  background: rgba(var(--red-rgb), 0.07);
  color: var(--red);
  font-size: 12px;
}
.comment-empty {
  padding: 28px 0 10px;
  color: var(--dim);
  font-size: 13px;
  text-align: center;
}
.comment-list {
  display: flex;
  flex-direction: column;
}
.comment-item {
  display: flex;
  gap: 12px;
  padding: 18px 0;
  border-top: 1px solid var(--line);
}
.comment-item:first-child {
  border-top: 0;
}
.comment-avatar {
  display: grid;
  flex: 0 0 34px;
  place-items: center;
  width: 34px;
  height: 34px;
  border: 1px solid rgba(var(--green-rgb), 0.45);
  border-radius: 50%;
  background: rgba(var(--green-rgb), 0.08);
  color: var(--green);
  font-family: var(--mono);
  font-size: 13px;
  font-weight: 700;
}
.comment-body {
  min-width: 0;
  flex: 1;
}
.comment-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 7px;
}
.comment-user {
  color: var(--text-strong);
  font-size: 13px;
  font-weight: 700;
}
.admin-tag,
.mine-tag {
  padding: 1px 5px;
  border-radius: 3px;
  font-family: var(--mono);
  font-size: 9px;
  font-weight: 700;
}
.admin-tag {
  border: 1px solid rgba(var(--amber-rgb), 0.45);
  color: var(--amber);
}
.mine-tag {
  border: 1px solid rgba(var(--cyan-rgb), 0.4);
  color: var(--cyan);
}
.comment-meta time {
  color: var(--dim);
  font-family: var(--mono);
  font-size: 10px;
}
.comment-delete {
  margin-left: auto;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--dim);
  font-size: 11px;
  cursor: pointer;
}
.comment-delete:hover {
  color: var(--red);
}
.comment-delete:disabled {
  opacity: 0.5;
  cursor: wait;
}
.comment-content {
  margin-top: 7px;
  color: var(--text);
  font-size: 14px;
  line-height: 1.75;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
}
@media (max-width: 760px) {
  .comments-head {
    flex-direction: column;
    gap: 10px;
  }
  .comments-signal {
    display: none;
  }
  .comment-login {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
