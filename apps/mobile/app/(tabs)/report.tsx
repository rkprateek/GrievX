import * as ImagePicker from "expo-image-picker";
import * as Location from "expo-location";
import { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, Alert, Image, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useFocusEffect } from "expo-router";

import { getComplaint, getComplaints, Complaint, submitComplaint } from "../../src/api/complaints";
import { openNotificationSocket } from "../../src/api/client";

export default function ReportScreen() {
  const [description, setDescription] = useState("");
  const [image, setImage] = useState<{ uri: string; name: string; type: string } | undefined>();
  const [location, setLocation] = useState<Location.LocationObject | undefined>();
  const [locationLabel, setLocationLabel] = useState("");
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [selected, setSelected] = useState<Complaint | undefined>();
  const [busy, setBusy] = useState(false);

  const loadHistory = useCallback(async () => {
    try { setComplaints(await getComplaints()); } catch { /* auth/session errors are handled by the login flow */ }
  }, []);
  useFocusEffect(useCallback(() => { void loadHistory(); }, [loadHistory]));

  useEffect(() => {
    let closeSocket = () => {};
    let active = true;
    void openNotificationSocket((message) => {
      if (!active || typeof message !== "object" || message === null) return;
      const event = message as { type?: string; complaint_id?: string | null };
      if (event.type === "notification") void loadHistory();
    }).then((close) => {
      if (active) closeSocket = close;
      else close();
    });
    return () => {
      active = false;
      closeSocket();
    };
  }, [loadHistory]);

  async function captureImage() {
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (!permission.granted) return Alert.alert("Camera permission required", "Allow camera access to capture evidence.");
    const result = await ImagePicker.launchCameraAsync({ mediaTypes: ["images"], quality: 0.8 });
    if (!result.canceled) {
      const asset = result.assets[0];
      setImage({ uri: asset.uri, name: asset.fileName ?? `complaint-${Date.now()}.jpg`, type: asset.mimeType ?? "image/jpeg" });
    }
  }

  async function selectImage() {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) return Alert.alert("Photo permission required", "Allow photo access to select evidence.");
    const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ["images"], quality: 0.8 });
    if (!result.canceled) {
      const asset = result.assets[0];
      setImage({ uri: asset.uri, name: asset.fileName ?? `complaint-${Date.now()}.jpg`, type: asset.mimeType ?? "image/jpeg" });
    }
  }

  async function captureLocation() {
    const permission = await Location.requestForegroundPermissionsAsync();
    if (permission.status !== "granted") return Alert.alert("Location permission required", "Allow location access to attach the campus location.");
    try {
      setLocation(await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced }));
    } catch {
      Alert.alert("Location unavailable", "Try again where GPS is available.");
    }
  }

  async function submit() {
    if (description.trim().length < 10) return Alert.alert("Description required", "Enter at least 10 characters describing the issue.");
    if (!location) return Alert.alert("Location required", "Capture your campus location before submitting.");
    setBusy(true);
    try {
      const created = await submitComplaint({
        description, latitude: location.coords.latitude, longitude: location.coords.longitude,
        locationLabel, image,
      });
      setDescription(""); setImage(undefined); setLocation(undefined); setLocationLabel(""); setSelected(created);
      await loadHistory();
      Alert.alert("Complaint submitted", `Your complaint ID is ${created.id}`);
    } catch (error) {
      Alert.alert("Submission failed", error instanceof Error ? error.message : "Please try again.");
    } finally { setBusy(false); }
  }

  async function openComplaint(id: string) {
    try { setSelected(await getComplaint(id)); } catch (error) { Alert.alert("Unable to load", error instanceof Error ? error.message : "Please try again."); }
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Report an issue</Text>
      <Text style={styles.subtitle}>Describe the problem, attach evidence, and capture its campus location.</Text>
      <TextInput style={[styles.input, styles.textarea]} multiline maxLength={5000} placeholder="What happened?" value={description} onChangeText={setDescription} />
      <View style={styles.row}>
        <Pressable style={styles.secondary} onPress={captureImage}><Text style={styles.secondaryText}>Take photo</Text></Pressable>
        <Pressable style={styles.secondary} onPress={selectImage}><Text style={styles.secondaryText}>Choose photo</Text></Pressable>
      </View>
      {image && <Image source={{ uri: image.uri }} style={styles.preview} />}
      <Pressable style={styles.secondary} onPress={captureLocation}><Text style={styles.secondaryText}>{location ? "Location captured ✓" : "Capture campus location"}</Text></Pressable>
      {location && <Text style={styles.location}>{location.coords.latitude.toFixed(5)}, {location.coords.longitude.toFixed(5)}</Text>}
      <TextInput style={styles.input} placeholder="Location label (optional)" value={locationLabel} onChangeText={setLocationLabel} maxLength={255} />
      <Pressable style={[styles.submit, busy && styles.disabled]} disabled={busy} onPress={submit}>{busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.submitText}>Submit complaint</Text>}</Pressable>
      {selected && <View style={styles.detail}>
        <Text style={styles.detailTitle}>{selected.id}</Text>
        <Text style={styles.currentStatus}>Current status: {selected.status}</Text>
        <Text>{selected.description}</Text>
        <Text style={styles.timelineTitle}>Status timeline</Text>
        {selected.history.map((item, index) => (
          <View key={`${item.created_at}-${index}`} style={styles.timelineRow}>
            <View style={styles.dot} />
            <View style={{ flex: 1 }}>
              <Text style={styles.timelineStatus}>{item.from_status ? `${item.from_status} → ${item.to_status}` : item.to_status}</Text>
              <Text style={styles.muted}>{new Date(item.created_at).toLocaleString()}</Text>
            </View>
          </View>
        ))}
      </View>}
      <Text style={styles.historyTitle}>Complaint history</Text>
      {complaints.length === 0 ? <Text style={styles.muted}>No complaints submitted yet.</Text> : complaints.map((item) => <Pressable key={item.id} style={styles.card} onPress={() => openComplaint(item.id)}><Text style={styles.cardTitle}>{item.id}</Text><Text numberOfLines={2}>{item.description}</Text><Text style={styles.muted}>{item.status}</Text></Pressable>)}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, gap: 12, backgroundColor: "#f5f7fb" }, title: { color: "#102a43", fontSize: 28, fontWeight: "700" }, subtitle: { color: "#52657c", lineHeight: 21 }, input: { backgroundColor: "#fff", borderWidth: 1, borderColor: "#d9e2ec", borderRadius: 10, padding: 13, fontSize: 16 }, textarea: { minHeight: 130, textAlignVertical: "top" }, row: { flexDirection: "row", gap: 10 }, secondary: { flex: 1, borderWidth: 1, borderColor: "#1267a8", borderRadius: 10, padding: 13, alignItems: "center", backgroundColor: "#fff" }, secondaryText: { color: "#1267a8", fontWeight: "700" }, preview: { width: "100%", height: 190, borderRadius: 10 }, location: { color: "#1f6f4a" }, submit: { borderRadius: 10, padding: 15, alignItems: "center", backgroundColor: "#1267a8" }, disabled: { opacity: 0.6 }, submitText: { color: "#fff", fontWeight: "700", fontSize: 16 }, historyTitle: { marginTop: 12, color: "#102a43", fontSize: 21, fontWeight: "700" }, card: { backgroundColor: "#fff", borderRadius: 10, padding: 14, gap: 5 }, cardTitle: { color: "#1267a8", fontWeight: "700" }, detail: { backgroundColor: "#fff", borderRadius: 10, padding: 15, gap: 6 }, detailTitle: { color: "#102a43", fontSize: 20, fontWeight: "700" }, currentStatus: { color: "#1267a8", fontWeight: "800" }, timelineTitle: { marginTop: 8, color: "#102a43", fontSize: 16, fontWeight: "800" }, timelineRow: { flexDirection: "row", gap: 10, paddingVertical: 7 }, dot: { width: 10, height: 10, borderRadius: 5, backgroundColor: "#1267a8", marginTop: 4 }, timelineStatus: { color: "#30445f", fontWeight: "700" }, muted: { color: "#6b7c93" },
});
