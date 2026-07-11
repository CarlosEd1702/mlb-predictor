import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";

import { api, GameSummary } from "../api/client";
import { colors, fonts, spacing } from "../theme";

type Props = NativeStackNavigationProp<Record<string, any>>;

function StatusBadge({ status }: { status: string }) {
  const color =
    status === "final" ? colors.green : status === "live" ? colors.red : colors.textMuted;
  const label = status === "scheduled" ? "Programado" : status === "final" ? "Finalizado" : "En vivo";
  return (
    <View style={[styles.statusBadge, { backgroundColor: color + "20" }]}>
      <Text style={[styles.statusText, { color }]}>{label}</Text>
    </View>
  );
}

export default function CalendarScreen() {
  const nav = useNavigation<Props>();
  const [games, setGames] = useState<GameSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split("T")[0]);

  const load = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      const data = await api.gamesForDate(selectedDate);
      setGames(data.games);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedDate]);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.blue} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={games}
        keyExtractor={(g) => `${g.id}`}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={colors.blue} />
        }
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.card}
            activeOpacity={0.7}
            onPress={() => nav.navigate("PickDetail", { gameId: item.id })}
          >
            <View style={styles.cardTop}>
              <View style={styles.teams}>
                <Text style={styles.awayTeam}>{item.away_team}</Text>
                <Text style={styles.atSymbol}>@</Text>
                <Text style={styles.homeTeam}>{item.home_team}</Text>
              </View>
              <StatusBadge status={item.status} />
            </View>
            {(item.status === "final" && item.home_score != null) && (
              <View style={styles.scoreRow}>
                <Text style={styles.score}>{item.away_score}</Text>
                <Text style={styles.scoreDash}>-</Text>
                <Text style={styles.score}>{item.home_score}</Text>
              </View>
            )}
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          <View style={styles.emptyBox}>
            <Text style={styles.emptyTitle}>Sin partidos</Text>
            <Text style={styles.emptySub}>No hay partidos programados para esta fecha.</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  center: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: colors.bg },
  list: { padding: spacing.lg, paddingBottom: 32 },
  card: {
    backgroundColor: colors.bgCard,
    borderRadius: 14,
    padding: spacing.lg,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardTop: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  teams: { flexDirection: "row", alignItems: "center", gap: 6 },
  awayTeam: { fontSize: 15, fontWeight: "600", color: colors.textDim },
  atSymbol: { fontSize: 12, color: colors.textMuted },
  homeTeam: { fontSize: 15, fontWeight: "700", color: colors.text },
  statusBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 20 },
  statusText: { fontSize: 12, fontWeight: "600" },
  scoreRow: { flexDirection: "row", justifyContent: "center", gap: 8, marginTop: 10 },
  score: { fontSize: 22, fontWeight: "700", color: colors.text },
  scoreDash: { fontSize: 22, fontWeight: "300", color: colors.textMuted },
  emptyBox: { alignItems: "center", paddingTop: 60 },
  emptyTitle: { fontSize: 18, fontWeight: "600", color: colors.textDim, marginBottom: 8 },
  emptySub: { fontSize: 14, color: colors.textMuted, textAlign: "center" },
});
