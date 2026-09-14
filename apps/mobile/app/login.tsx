import { useState } from "react";
import { Alert, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useRouter } from "expo-router";

import { apiRequest } from "../src/api/client";
import { saveToken } from "../src/auth/storage";

type AuthResponse = { access_token: string; user: { role: string } };

export default function LoginScreen() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  async function login() {
    setBusy(true);
    try {
      const data = await apiRequest<AuthResponse>("/auth/login", {
        method: "POST", body: JSON.stringify({ email, password }),
      });
      await saveToken(data.access_token);
      router.replace("/(tabs)");
    } catch (error) { Alert.alert("Login failed", error instanceof Error ? error.message : "Try again"); }
    finally { setBusy(false); }
  }

  return <View style={styles.container}><Text style={styles.title}>GrievX</Text><Text style={styles.subtitle}>Student sign in</Text>
    <TextInput style={styles.input} autoCapitalize="none" keyboardType="email-address" placeholder="College email" value={email} onChangeText={setEmail}/>
    <TextInput style={styles.input} secureTextEntry placeholder="Password" value={password} onChangeText={setPassword}/>
    <Pressable style={styles.button} disabled={busy} onPress={login}><Text style={styles.buttonText}>{busy ? "Signing in…" : "Sign in"}</Text></Pressable>
    <Pressable onPress={() => router.push("/register")}><Text style={styles.link}>Create student account</Text></Pressable>
  </View>;
}

const styles = StyleSheet.create({ container:{flex:1,padding:24,justifyContent:"center",gap:14,backgroundColor:"#f7f8fa"}, title:{fontSize:36,fontWeight:"800"}, subtitle:{fontSize:18,marginBottom:12}, input:{backgroundColor:"white",borderWidth:1,borderColor:"#ddd",borderRadius:10,padding:14}, button:{backgroundColor:"#111827",padding:15,borderRadius:10,alignItems:"center"},buttonText:{color:"white",fontWeight:"700"},link:{textAlign:"center",marginTop:10,fontWeight:"600"} });
