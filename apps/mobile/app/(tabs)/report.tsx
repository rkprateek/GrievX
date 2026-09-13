import { StyleSheet, Text, View } from "react-native";

export default function ReportScreen() {
  return <View style={styles.container}><Text style={styles.title}>Report an issue</Text><Text style={styles.body}>Complaint submission is intentionally unavailable until Week 4. This tab establishes the planned navigation location.</Text></View>;
}

const styles = StyleSheet.create({ container: { flex: 1, justifyContent: "center", padding: 24, backgroundColor: "#f5f7fb" }, title: { color: "#102a43", fontSize: 28, fontWeight: "700" }, body: { color: "#52657c", fontSize: 16, lineHeight: 24, marginTop: 16 } });
