import { useState } from "react";
import { Alert, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useRouter } from "expo-router";

import { apiRequest } from "../src/api/client";
import { saveToken } from "../src/auth/storage";

type AuthResponse = { access_token: string };

export default function RegisterScreen() {
  const router = useRouter();
  const [fullName, setFullName] = useState(""); const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [busy, setBusy] = useState(false);
  async function register() {
    setBusy(true);
    try {
      const data = await apiRequest<AuthResponse>("/auth/register", { method:"POST", body:JSON.stringify({full_name:fullName,email,password}) });
      await saveToken(data.access_token); router.replace("/(tabs)");
    } catch (error) { Alert.alert("Registration failed", error instanceof Error ? error.message : "Try again"); }
    finally { setBusy(false); }
  }
  return <View style={styles.container}><Text style={styles.title}>Create account</Text><TextInput style={styles.input} placeholder="Full name" value={fullName} onChangeText={setFullName}/><TextInput style={styles.input} autoCapitalize="none" keyboardType="email-address" placeholder="College email" value={email} onChangeText={setEmail}/><TextInput style={styles.input} secureTextEntry placeholder="Password (8+ characters)" value={password} onChangeText={setPassword}/><Pressable style={styles.button} disabled={busy} onPress={register}><Text style={styles.buttonText}>{busy ? "Creating…" : "Register"}</Text></Pressable><Pressable onPress={()=>router.replace("/login")}><Text style={styles.link}>Back to sign in</Text></Pressable></View>;
}
const styles=StyleSheet.create({container:{flex:1,padding:24,justifyContent:"center",gap:14,backgroundColor:"#f7f8fa"},title:{fontSize:30,fontWeight:"800",marginBottom:10},input:{backgroundColor:"white",borderWidth:1,borderColor:"#ddd",borderRadius:10,padding:14},button:{backgroundColor:"#111827",padding:15,borderRadius:10,alignItems:"center"},buttonText:{color:"white",fontWeight:"700"},link:{textAlign:"center",fontWeight:"600"}});
