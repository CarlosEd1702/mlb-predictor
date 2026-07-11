import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useRoute } from "@react-navigation/native";
import type { RouteProp } from "@react-navigation/native";

import { api, GameDetail } from "../api/client";
import { colors, fonts, spacing } from "../theme";

type RouteParams = { PickDetail: { gameId: number } };

function ProbBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <View style={styles.probBarRow}>
      <Text style={styles.probBarLabel}>{label}</Text>
      <View style={styles.probBarBg}>
        <View style={[styles.probBarFill, { width: `${value * 100}%`, backgroundColor: color }]} />
      </View>
      <Text style={[styles.probBarValue, { color }]}>{(value * 100).toFixed(0)}%</Text>
    </View>
  );
}

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
        <ActivityIndicator size="large" color={colors.blue} />
      </View>
    );
  }

  if (!detail) {
    return (
      <View style={styles.center}>
        <Text style={{ color: colors.red, fontSize: 16 }}>Error al cargar</Text>
      </View>
    );
  }

  const { game, predictions } = detail;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scroll}>
      <View style={styles.headerCard}>
        <Text style={styles.awayTeam}>{game.away_team}</Text>
        <Text style={styles.vsText}>@</Text>
        <Text style={styles.homeTeam}>{game.home_team}</Text>
        <View style={styles.metaRow}>
          <Text style={styles.meta}>{game.park || "Estadio N/A"}</Text>
          <Text style={styles.metaSep}>•</Text>
          <Text style={styles.meta}>{game.date}</Text>
        </View>
        <View style={styles.statusBadge}>
          <Text style={styles.statusText}>{game.status}</Text>
        </View>
        {game.home_score != null && (
          <View style={styles.scoreRow}>
            <Text style={styles.score}>{game.away_score}</Text>
            <Text style={styles.scoreDash}>-</Text>
            <Text style={styles.score}>{game.home_score}</Text>
          </View>
        )}
      </View>

      <Text style={styles.sectionTitle}>Predicciones</Text>
      {predictions.length === 0 ? (
        <Text style={styles.noData}>Sin predicciones para este partido</Text>
      ) : (
        predictions.map((p) => (
          <View key={p.id} style={styles.predCard}>
            <View style={styles.predHeader}>
              <Text style={styles.predMarket}>{p.market}</Text>
              {p.edge != null && (
                <Text style={[styles.predEdge, { color: p.edge > 0 ? colors.green : colors.red }]}>
                  Edge: {(p.edge * 100).toFixed(1)}%
                </Text>
              )}
            </View>
            <Text style={styles.predSelection}>{p.selection}</Text>
            <ProbBar label="Modelo" value={p.model_probability} color={colors.blue} />
          </View>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  center: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: colors.bg },
  scroll: { padding: spacing.lg, paddingBottom: 32 },
  headerCard: {
    backgroundColor: colors.bgCard,
    borderRadius: 14,
    padding: spacing.xl,
    alignItems: "center",
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  awayTeam: { fontSize: 20, fontWeight: "600", color: colors.textDim },
  vsText: { fontSize: 16, color: colors.textMuted, marginVertical: 2 },
  homeTeam: { fontSize: 24, fontWeight: "bold", color: colors.text },
  metaRow: { flexDirection: "row", alignItems: "center", marginTop: 10, gap: 6 },
  meta: { fontSize: 13, color: colors.textMuted },
  metaSep: { fontSize: 13, color: colors.textMuted },
  statusBadge: {
    marginTop: 10,
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 20,
    backgroundColor: colors.blue + "20",
  },
  statusText: { fontSize: 12, fontWeight: "600", color: colors.blue },
  scoreRow: { flexDirection: "row", alignItems: "center", gap: 10, marginTop: 12 },
  score: { fontSize: 28, fontWeight: "bold", color: colors.text },
  scoreDash: { fontSize: 28, fontWeight: "300", color: colors.textMuted },
  sectionTitle: { fontSize: 18, fontWeight: "600", color: colors.text, marginBottom: 12 },
  predCard: {
    backgroundColor: colors.bgCard,
    borderRadius: 12,
    padding: spacing.lg,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  predHeader: { flexDirection: "row", justifyContent: "space-between", marginBottom: 8 },
  predMarket: { fontSize: 14, fontWeight: "600", color: colors.blue },
  predEdge: { fontSize: 13, fontWeight: "700" },
  predSelection: { fontSize: 15, color: colors.text, marginBottom: 12 },
  probBarRow: { flexDirection: "row", alignItems: "center", gap: 8, marginTop: 6 },
  probBarLabel: { fontSize: 12, color: colors.textMuted, width: 50 },
  probBarBg: { flex: 1, height: 6, backgroundColor: colors.bg, borderRadius: 3, overflow: "hidden" },
  probBarFill: { height: "100%", borderRadius: 3 },
  probBarValue: { fontSize: 12, fontWeight: "600", width: 36, textAlign: "right" },
  noData: { color: colors.textMuted, textAlign: "center", paddingVertical: 20 },
});
