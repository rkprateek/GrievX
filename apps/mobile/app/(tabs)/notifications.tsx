import { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useFocusEffect } from "expo-router";

import { getNotifications, markNotificationRead, NotificationItem } from "../../src/api/complaints";
import { openNotificationSocket } from "../../src/api/client";

export default function NotificationsScreen() {
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [unread, setUnread] = useState(0);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const result = await getNotifications();
      setItems(result.items);
      setUnread(result.unread_count);
    } catch {
      // Session errors are handled by the authenticated app shell.
    }
  }, []);

  useFocusEffect(useCallback(() => { void load(); }, [load]));

  useEffect(() => {
    let closeSocket = () => {};
    let active = true;
    void openNotificationSocket((message) => {
      if (!active || typeof message !== "object" || message === null) return;
      const event = message as { type?: string };
      if (event.type === "notification") void load();
    }).then((close) => {
      if (active) closeSocket = close;
      else close();
    });
    return () => {
      active = false;
      closeSocket();
    };
  }, [load]);

  async function markRead(id: string) {
    setBusy(true);
    try {
      await markNotificationRead(id);
      await load();
    } finally {
      setBusy(false);
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Notifications</Text>
      <Text style={styles.subtitle}>{unread ? `${unread} unread update${unread === 1 ? "" : "s"}` : "You're all caught up."}</Text>
      {items.length === 0 && <Text style={styles.empty}>No notifications yet.</Text>}
      {items.map((item) => (
        <Pressable
          key={item.id}
          style={[styles.card, !item.is_read && styles.unreadCard]}
          disabled={busy || item.is_read}
          onPress={() => void markRead(item.id)}
        >
          <View style={styles.row}>
            <View style={styles.dot} />
            <View style={{ flex: 1 }}>
              <Text style={styles.cardTitle}>{item.title}</Text>
              <Text style={styles.body}>{item.body}</Text>
              {item.complaint_id && <Text style={styles.complaint}>{item.complaint_id}</Text>}
              <Text style={styles.time}>{new Date(item.created_at).toLocaleString()}</Text>
            </View>
          </View>
          {!item.is_read && <Text style={styles.mark}>Tap to mark as read</Text>}
        </Pressable>
      ))}
      {busy && <ActivityIndicator />}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, gap: 12, backgroundColor: "#f5f7fb", flexGrow: 1 },
  title: { color: "#102a43", fontSize: 28, fontWeight: "700" },
  subtitle: { color: "#52657c", marginBottom: 5 },
  empty: { color: "#7a899b", paddingVertical: 30, textAlign: "center" },
  card: { backgroundColor: "#fff", borderRadius: 12, padding: 15, borderWidth: 1, borderColor: "#dce6f0" },
  unreadCard: { borderColor: "#8db8d9" },
  row: { flexDirection: "row", gap: 10 },
  dot: { width: 9, height: 9, borderRadius: 5, backgroundColor: "#1267a8", marginTop: 5 },
  cardTitle: { color: "#213b58", fontWeight: "800", fontSize: 15 },
  body: { color: "#52657c", marginTop: 5, lineHeight: 20 },
  complaint: { color: "#1267a8", fontWeight: "800", marginTop: 6 },
  time: { color: "#8a98a8", fontSize: 10, marginTop: 7 },
  mark: { color: "#1267a8", fontSize: 10, fontWeight: "700", marginTop: 10 },
});
