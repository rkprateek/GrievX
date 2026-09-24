import { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";

import { getNotifications, markNotificationRead, Notification } from "../../src/api/notifications";
import { getToken } from "../../src/auth/storage";
import { environment } from "../../src/config/environment";

function websocketUrl(token: string) {
  const base = environment.apiBaseUrl.replace(/^http/, "ws");
  return `${base}/ws/notifications?token=${encodeURIComponent(token)}`;
}

export default function NotificationsScreen() {
  const router = useRouter();
  const [items, setItems] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      setItems(await getNotifications());
    } catch {
      // The tab layout handles session routing.
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { void load(); }, [load]));

  useEffect(() => {
    let socket: WebSocket | undefined;
    let cancelled = false;

    (async () => {
      const token = await getToken();
      if (!token || cancelled) return;
      socket = new WebSocket(websocketUrl(token));
      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.event === "notification" && message.notification) {
            setItems((current) => [message.notification as Notification, ...current.filter((item) => item.id !== message.notification.id)]);
          }
        } catch {
          // Ignore malformed real-time payloads.
        }
      };
      socket.onerror = () => undefined;
    })();

    return () => {
      cancelled = true;
      socket?.close();
    };
  }, []);

  async function openNotification(item: Notification) {
    if (!item.read_at) {
      try {
        const updated = await markNotificationRead(item.id);
        setItems((current) => current.map((entry) => entry.id === item.id ? updated : entry));
      } catch {
        // Keep the notification visible even if marking read fails.
      }
    }
    if (item.complaint_id) router.push("/(tabs)/report");
  }

  return (
    <View style={styles.screen}>
      <View style={styles.header}>
        <Text style={styles.title}>Notifications</Text>
        <Text style={styles.subtitle}>Live updates for your complaints</Text>
      </View>
      {loading ? <ActivityIndicator style={styles.loader} /> : (
        <FlatList
          data={items}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          ListEmptyComponent={<Text style={styles.empty}>No notifications yet.</Text>}
          renderItem={({ item }) => (
            <Pressable style={[styles.card, !item.read_at && styles.unread]} onPress={() => void openNotification(item)}>
              <View style={styles.row}>
                <Text style={styles.cardTitle}>{item.title}</Text>
                {!item.read_at && <View style={styles.dot} />}
              </View>
              <Text style={styles.message}>{item.message}</Text>
              {item.complaint_id && <Text style={styles.complaint}>{item.complaint_id}</Text>}
              <Text style={styles.time}>{new Date(item.created_at).toLocaleString()}</Text>
            </Pressable>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: "#f5f7fb" },
  header: { padding: 20, paddingBottom: 10 },
  title: { color: "#102a43", fontSize: 28, fontWeight: "700" },
  subtitle: { color: "#66778d", marginTop: 4 },
  loader: { marginTop: 30 },
  list: { padding: 20, gap: 10 },
  card: { backgroundColor: "#fff", borderRadius: 12, padding: 15, borderWidth: 1, borderColor: "#dce6f0", gap: 7 },
  unread: { borderColor: "#8bb7d8" },
  row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  cardTitle: { color: "#183b5d", fontWeight: "800", fontSize: 15 },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: "#1769aa" },
  message: { color: "#40566f", lineHeight: 20 },
  complaint: { color: "#1769aa", fontWeight: "700", fontSize: 12 },
  time: { color: "#8996a5", fontSize: 10 },
  empty: { textAlign: "center", color: "#7d8b9a", marginTop: 30 },
});
