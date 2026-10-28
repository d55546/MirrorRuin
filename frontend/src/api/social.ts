import { http } from './client'

export interface SocialUser {
  id: number
  username: string
  role: string
}

export interface Friend extends SocialUser {
  last_message: string | null
  last_message_at: string | null
  unread_count: number
}

export interface FriendRequest {
  id: number
  user: SocialUser
  created_at: string
}

export interface SocialOverview {
  friends: Friend[]
  incoming: FriendRequest[]
  outgoing: FriendRequest[]
  unread_count: number
}

export interface DirectMessage {
  id: number
  sender_id: number
  receiver_id: number
  content: string
  is_read: boolean
  created_at: string
  is_mine: boolean
}

export interface DirectMessageList {
  friend: SocialUser
  items: DirectMessage[]
  total: number
}

export const socialApi = {
  search: (query: string) => {
    const params = new URLSearchParams({ q: query })
    return http.get<SocialUser[]>(`/social/search?${params.toString()}`)
  },
  overview: () => http.get<SocialOverview>('/social/overview'),
  sendRequest: (username: string) =>
    http.post<FriendRequest>('/social/requests', { username }),
  acceptRequest: (id: number) =>
    http.post<{ success: boolean }>(`/social/requests/${id}/accept`, {}),
  deleteRequest: (id: number) =>
    http.delete<{ success: boolean }>(`/social/requests/${id}`),
  removeFriend: (friendId: number) =>
    http.delete<{ success: boolean }>(`/social/friends/${friendId}`),
  messages: (friendId: number) =>
    http.get<DirectMessageList>(`/social/messages/${friendId}`),
  sendMessage: (friendId: number, content: string) =>
    http.post<DirectMessage>(`/social/messages/${friendId}`, { content }),
}
