import React, { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { useRoute } from "@react-navigation/native";
import type { RouteProp } from "@react-navigation/native";

import { api, GameDetail } from "../api/client";

type RouteParams = { PickDetail: { gameId: number } };

export default function PickDetailScreen() {
  const route = useRoute<RouteProp<RouteParams, "PickDetail">>();
  const [detail, setDetail] = useState<GameDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .gameDetail(route.params.gameId)
      .then(setDetail)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [route.params.gameId]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  if (!detail) {
    return (
      <View style={styles.center}>
        <Text style={styles.error}>Error al cargar el partido</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.matchup}>
        {detail.game.away_team} @ {detail.game.home_team}
      </Text>
      <Text style={styles.info}>Fecha: {detail.game.date}</Text>
      <Text style={styles.info}>Parque: {detail.game.park || "N/A"}</Text>
      <Text style={styles.info}>Estado: {detail.game.status}</Text>

      <Text style={styles.sectionTitle}>Predicciones</Text>
      {detail.predictions.map((p) => (
        <View key={p.id} style={styles.predCard}>
          <Text style={styles.market}>{p.market}</Text>
          <Text style={styles.selection}>{p.selection}</Text>
          <Text style={styles.prob}>Probabilidad: {(p.model_probability * 100).toFixed(1)}%</Text>
          {p.edge != null && (
            <Text style={[styles.edge, p.edge > 0 ? styles.positive : styles.negative]}>
              Edge: {(p.edge * 100).toFixed(1)}%
            </Text>
          )}
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: "#0f172a" },
  center: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: "#0f172a" },
  matchup: { fontSize: 22, fontWeight: "bold", color: "#f8fafc", marginBottom: 8 },
  info: { fontSize: 14, color: "#94a3b8", marginBottom: 4 },
  sectionTitle: { fontSize: 18, fontWeight: "600", color: "#f8fafc", marginTop: 20, marginBottom: 12 },
  predCard: {
    backgroundColor: "#1e293b",
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
  },
  market: { fontSize: 14, fontWeight: "600", color: "#f8fafc", marginBottom: 4 },
  selection: { fontSize: 14, color: "#94a3b8", marginBottom: 4 },
  prob: { fontSize: 12, color: "#64748b" },
  edge: { fontSize: 12, marginTop: 2, fontWeight: "600" },
  positive: { color: "#22c55e" },
  negative: { color: "#ef4444" },
  error: { color: "#ef4444", fontSize: 16 },
});
