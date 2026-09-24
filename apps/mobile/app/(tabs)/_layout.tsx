import { useEffect, useState } from "react";
import { Tabs, useRouter } from "expo-router";
import { getToken } from "../../src/auth/storage";

export default function TabLayout() {
  const router = useRouter(); const [ready,setReady]=useState(false);
  useEffect(()=>{ getToken().then(token=>{ if(!token) router.replace("/login"); else setReady(true); }); },[router]);
  if(!ready) return null;
  return <Tabs screenOptions={{ headerStyle:{backgroundColor:"#102a43"}, headerTintColor:"#ffffff", tabBarActiveTintColor:"#1267a8" }}>
    <Tabs.Screen name="index" options={{title:"Home"}} />
    <Tabs.Screen name="report" options={{title:"Report"}} />
    <Tabs.Screen name="notifications" options={{title:"Notifications"}} />
    <Tabs.Screen name="profile" options={{title:"Profile"}} />
  </Tabs>;
}
