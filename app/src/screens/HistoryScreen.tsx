import React, { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import { api, HistorySummary } from "../api/client";

const PROP_TYPES = [
  { label: "Todos", value: undefined },
  { label: "Moneyline", value: "h2h" },
  { label: "Totales", value: "totals" },
  { label: "Spread", value: "spreads" },
  { label: "Strikeouts", value: "player_strikeouts" },
];

export default function HistoryScreen() {
  const [history, setHistory] = useState<HistorySummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .history()
      .then(setHistory)
      .catch(console.error)
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
      <Text style={styles.title}>Historial de Efectividad</Text>

      {history && (
        <View style={styles.summaryCard}>
          <View style={styles.statRow}>
            <View style={styles.stat}>
              <Text style={styles.statValue}>{history.total_picks}</Text>
              <Text style={styles.statLabel}>Total</Text>
            </View>
            <View style={styles.stat}>
              <Text style={[styles.statValue, { color: "#22c55e" }]}>{history.wins}</Text>
              <Text style={styles.statLabel}>Ganados</Text>
            </View>
            <View style={styles.stat}>
              <Text style={[styles.statValue, { color: "#ef4444" }]}>{history.losses}</Text>
              <Text style={styles.statLabel}>Perdidos</Text>
            </View>
          </View>
          <Text style={styles.accuracy}>
            Accuracy: {history.total_picks > 0 ? (history.accuracy * 100).toFixed(1) : "N/A"}%
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: "#0f172a" },
  center: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: "#0f172a" },
  title: { fontSize: 24, fontWeight: "bold", color: "#f8fafc", marginBottom: 16 },
  summaryCard: {
    backgroundColor: "#1e293b",
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
  },
  statRow: { flexDirection: "row", justifyContent: "space-around", marginBottom: 16 },
  stat: { alignItems: "center" },
  statValue: { fontSize: 28, fontWeight: "bold", color: "#f8fafc" },
  statLabel: { fontSize: 12, color: "#64748b", marginTop: 4 },
  accuracy: { fontSize: 18, fontWeight: "600", color: "#f8fafc", textAlign: "center" },
});
