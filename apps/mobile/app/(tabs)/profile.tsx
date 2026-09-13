import { StyleSheet, Text, View } from "react-native";

export default function ProfileScreen() {
  return <View style={styles.container}><Text style={styles.title}>Profile</Text><Text style={styles.body}>Authentication is not implemented in Week 2. This screen is a navigation placeholder only.</Text></View>;
}

const styles = StyleSheet.create({ container: { flex: 1, justifyContent: "center", padding: 24, backgroundColor: "#f5f7fb" }, title: { color: "#102a43", fontSize: 28, fontWeight: "700" }, body: { color: "#52657c", fontSize: 16, lineHeight: 24, marginTop: 16 } });
