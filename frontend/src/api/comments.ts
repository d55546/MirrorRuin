import { http } from './client'

export type CommentTarget = 'challenge' | 'competition'

export interface ChallengeComment {
  id: number
  username: string
  role: string
  content: string
  created_at: string
  is_mine: boolean
}

export interface CommentList {
  items: ChallengeComment[]
  total: number
}

export const commentsApi = {
  list: (targetType: CommentTarget, targetId: number) =>
    http.get<CommentList>(`/comments/${targetType}/${targetId}`),
  create: (targetType: CommentTarget, targetId: number, content: string) =>
    http.post<ChallengeComment>(`/comments/${targetType}/${targetId}`, { content }),
  remove: (commentId: number) =>
    http.delete<{ success: boolean }>(`/comments/${commentId}`),
}
