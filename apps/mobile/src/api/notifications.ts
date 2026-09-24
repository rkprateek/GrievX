import { apiRequest } from "./client";

export type Notification = {
  id: string;
  type: string;
  title: string;
  message: string;
  complaint_id?: string | null;
  read_at?: string | null;
  created_at: string;
};

export function getNotifications(unreadOnly = false) {
  return apiRequest<Notification[]>(`/notifications?limit=100&unread_only=${unreadOnly}`);
}

export function getUnreadNotificationCount() {
  return apiRequest<{ count: number }>("/notifications/unread-count");
}

export function markNotificationRead(id: string) {
  return apiRequest<Notification>(`/notifications/${encodeURIComponent(id)}/read`, { method: "PATCH" });
}
