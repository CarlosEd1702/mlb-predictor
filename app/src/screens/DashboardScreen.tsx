import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";

import { api, Pick } from "../api/client";

type RootStackParamList = {
  Dashboard: undefined;
  PickDetail: { gameId: number };
  History: undefined;
};

export default function DashboardScreen() {
  const nav = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const [picks, setPicks] = useState<Pick[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .picksOfDay()
      .then((d) => setPicks(d.picks))
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Picks del Día</Text>
      <FlatList
        data={picks}
        keyExtractor={(p) => `${p.prediction_id}`}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.card}
            onPress={() => nav.navigate("PickDetail", { gameId: item.game_id })}
          >
            <View style={styles.cardHeader}>
              <Text style={styles.matchup}>
                {item.away_team} @ {item.home_team}
              </Text>
              <Text style={styles.edge}>
                {item.edge != null ? `${(item.edge * 100).toFixed(1)}%` : "--"}
              </Text>
            </View>
            <Text style={styles.selection}>{item.selection}</Text>
            <Text style={styles.market}>{item.market}</Text>
            <View style={styles.probRow}>
              <Text style={styles.prob}>Modelo: {(item.model_probability * 100).toFixed(0)}%</Text>
              {item.market_probability != null && (
                <Text style={styles.prob}>
                  Mercado: {(item.market_probability * 100).toFixed(0)}%
                </Text>
              )}
            </View>
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          <Text style={styles.empty}>No hay picks disponibles para hoy</Text>
        }
      />
      <TouchableOpacity
        style={styles.historyBtn}
        onPress={() => nav.navigate("History")}
      >
        <Text style={styles.historyBtnText}>Ver Historial</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: "#0f172a" },
  center: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: "#0f172a" },
  title: { fontSize: 24, fontWeight: "bold", color: "#f8fafc", marginBottom: 16 },
  card: {
    backgroundColor: "#1e293b",
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  cardHeader: { flexDirection: "row", justifyContent: "space-between", marginBottom: 8 },
  matchup: { fontSize: 16, fontWeight: "600", color: "#f8fafc" },
  edge: { fontSize: 16, fontWeight: "bold", color: "#22c55e" },
  selection: { fontSize: 14, color: "#94a3b8", marginBottom: 4 },
  market: { fontSize: 12, color: "#64748b", marginBottom: 8 },
  probRow: { flexDirection: "row", gap: 16 },
  prob: { fontSize: 12, color: "#94a3b8" },
  empty: { color: "#64748b", textAlign: "center", marginTop: 40 },
  historyBtn: {
    backgroundColor: "#334155",
    borderRadius: 8,
    padding: 14,
    alignItems: "center",
    marginTop: 8,
  },
  historyBtnText: { color: "#f8fafc", fontWeight: "600" },
});
