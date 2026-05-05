import { reactive } from "vue";

export interface Notification {
  id: number;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
}


const notifications = reactive<Notification[]>([]);

let id = 0;

export function useNotifications() {
  function show(message: string, type: Notification["type"] = "info", duration = 3000) {
    const notification = {
      id: id++,
      message,
      type,
    };

    notifications.push(notification);

    setTimeout(() => {
      remove(notification.id);
    }, duration);
  }

  function remove(notificationId: number) {
    const index = notifications.findIndex(n => n.id === notificationId);
    if (index !== -1) notifications.splice(index, 1);
  }

  return {
    notifications,
    show,
    remove,
    success: (msg: string) => show(msg, "success"),
    error: (msg: string) => show(msg, "error"),
    warning: (msg: string) => show(msg, "warning"),
    info: (msg: string) => show(msg, "info"),
  };
}