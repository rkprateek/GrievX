import { StyleSheet, Text, View } from "react-native";

export default function HomeScreen() {
  return <View style={styles.container}><Text style={styles.eyebrow}>WEEK 2 FOUNDATION</Text><Text style={styles.title}>Welcome to GrievX</Text><Text style={styles.body}>The mobile shell, navigation, and API configuration are ready. Secure sign-in and complaint reporting will be added in their scheduled weeks.</Text></View>;
}

const styles = StyleSheet.create({ container: { flex: 1, justifyContent: "center", padding: 24, backgroundColor: "#f5f7fb" }, eyebrow: { color: "#1267a8", fontSize: 12, fontWeight: "700", letterSpacing: 1 }, title: { color: "#102a43", fontSize: 32, fontWeight: "700", marginTop: 8 }, body: { color: "#52657c", fontSize: 16, lineHeight: 24, marginTop: 16 } });
