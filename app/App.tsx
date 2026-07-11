import { StatusBar } from "expo-status-bar";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { Text, View } from "react-native";

import DashboardScreen from "./src/screens/DashboardScreen";
import CalendarScreen from "./src/screens/CalendarScreen";
import HistoryScreen from "./src/screens/HistoryScreen";
import PickDetailScreen from "./src/screens/PickDetailScreen";
import { colors } from "./src/theme";

export type RootStackParamList = {
  MainTabs: undefined;
  PickDetail: { gameId: number };
  History: undefined;
};

export type TabParamList = {
  DashboardTab: undefined;
  CalendarTab: undefined;
  HistoryTab: undefined;
};

const RootStack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<TabParamList>();

function TabIcon({ label }: { label: string }) {
  const icons: Record<string, string> = {
    "Hoy": "📊",
    "Partidos": "📅",
    "Historial": "📈",
  };
  return (
    <View style={{ alignItems: "center" }}>
      <Text style={{ fontSize: 20 }}>{icons[label] || "📊"}</Text>
    </View>
  );
}

function TabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerStyle: { backgroundColor: colors.bgCard },
        headerTintColor: colors.text,
        headerTitleStyle: { fontWeight: "600" },
        tabBarStyle: {
          backgroundColor: colors.bgCard,
          borderTopColor: colors.border,
          borderTopWidth: 1,
          paddingBottom: 4,
          height: 56,
        },
        tabBarActiveTintColor: colors.blue,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarLabelStyle: { fontSize: 11, fontWeight: "600" },
        tabBarIcon: () => {
          const labels: Record<string, string> = {
            DashboardTab: "Hoy",
            CalendarTab: "Partidos",
            HistoryTab: "Historial",
          };
          return <TabIcon label={labels[route.name]} />;
        },
      })}
    >
      <Tab.Screen
        name="DashboardTab"
        component={DashboardScreen}
        options={{ title: "Picks de Hoy", tabBarLabel: "Hoy" }}
      />
      <Tab.Screen
        name="CalendarTab"
        component={CalendarScreen}
        options={{ title: "Partidos", tabBarLabel: "Partidos" }}
      />
      <Tab.Screen
        name="HistoryTab"
        component={HistoryScreen}
        options={{ title: "Historial", tabBarLabel: "Historial" }}
      />
    </Tab.Navigator>
  );
}

export default function App() {
  return (
    <NavigationContainer>
      <RootStack.Navigator
        screenOptions={{
          headerStyle: { backgroundColor: colors.bgCard },
          headerTintColor: colors.text,
          headerTitleStyle: { fontWeight: "600" },
        }}
      >
        <RootStack.Screen
          name="MainTabs"
          component={TabNavigator}
          options={{ headerShown: false }}
        />
        <RootStack.Screen
          name="PickDetail"
          component={PickDetailScreen}
          options={{ title: "Detalle del Partido" }}
        />
      </RootStack.Navigator>
      <StatusBar style="light" />
    </NavigationContainer>
  );
}
