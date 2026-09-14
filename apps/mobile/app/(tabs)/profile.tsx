import { useEffect, useState } from "react";
import { Alert, Pressable, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";

import { apiRequest } from "../../src/api/client";
import { clearToken } from "../../src/auth/storage";

type User = { full_name:string; email:string; role:string; department:string|null };

export default function ProfileScreen() {
  const router = useRouter(); const [user,setUser]=useState<User|null>(null);
  useEffect(()=>{ apiRequest<User>("/auth/me").then(setUser).catch(()=>router.replace("/login")); },[router]);
  async function logout(){ try { await apiRequest<void>("/auth/logout",{method:"POST"}); } catch {} await clearToken(); router.replace("/login"); }
  if(!user) return <View style={styles.container}><Text>Loading…</Text></View>;
  return <View style={styles.container}><Text style={styles.title}>Profile</Text><Text style={styles.label}>Name</Text><Text style={styles.value}>{user.full_name}</Text><Text style={styles.label}>Email</Text><Text style={styles.value}>{user.email}</Text><Text style={styles.label}>Role</Text><Text style={styles.value}>{user.role}</Text>{user.department&&<><Text style={styles.label}>Department</Text><Text style={styles.value}>{user.department}</Text></>}<Pressable style={styles.button} onPress={()=>Alert.alert("Sign out?","You will need to sign in again.", [{text:"Cancel",style:"cancel"},{text:"Sign out",onPress:logout}] )}><Text style={styles.buttonText}>Sign out</Text></Pressable></View>;
}
const styles=StyleSheet.create({container:{flex:1,padding:24,justifyContent:"center",backgroundColor:"#f5f7fb"},title:{fontSize:28,fontWeight:"700",marginBottom:20},label:{fontSize:13,color:"#52657c",marginTop:12},value:{fontSize:17,fontWeight:"600",marginTop:3},button:{marginTop:30,backgroundColor:"#b42318",padding:15,borderRadius:10,alignItems:"center"},buttonText:{color:"white",fontWeight:"700"}});
