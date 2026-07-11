import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

import { api, HistorySummary } from "../api/client";
import { colors, fonts, spacing } from "../theme";

const PROP_TYPES = [
  { label: "Todos", value: null },
  { label: "Moneyline", value: "h2h" },
  { label: "Totales", value: "totals" },
  { label: "Spread", value: "spreads" },
  { label: "Strikeouts", value: "player_strikeouts" },
];

export default function HistoryScreen() {
  const [history, setHistory] = useState<HistorySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedType, setSelectedType] = useState<string | null>(null);

  const load = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      const data = selectedType
        ? await api.historyByType(selectedType)
        : await api.history();
      setHistory(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedType]);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.blue} />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scroll}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={colors.blue} />
      }
    >
      <Text style={styles.title}>Historial</Text>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterRow}>
        {PROP_TYPES.map((pt) => (
          <TouchableOpacity
            key={pt.label}
            style={[
              styles.filterChip,
              selectedType === pt.value && styles.filterChipActive,
            ]}
            onPress={() => setSelectedType(pt.value)}
          >
            <Text
              style={[
                styles.filterChipText,
                selectedType === pt.value && styles.filterChipTextActive,
              ]}
            >
              {pt.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {history && (
        <View style={styles.summaryCard}>
          <View style={styles.statRow}>
            <View style={styles.stat}>
              <Text style={styles.statValue}>{history.total_picks}</Text>
              <Text style={styles.statLabel}>Picks</Text>
            </View>
            <View style={styles.divider} />
            <View style={styles.stat}>
              <Text style={[styles.statValue, { color: colors.green }]}>{history.wins}</Text>
              <Text style={styles.statLabel}>Ganados</Text>
            </View>
            <View style={styles.divider} />
            <View style={styles.stat}>
              <Text style={[styles.statValue, { color: colors.red }]}>{history.losses}</Text>
              <Text style={styles.statLabel}>Perdidos</Text>
            </View>
          </View>
          <View style={styles.accuracyRow}>
            <Text style={styles.accuracyLabel}>Accuracy</Text>
            <Text style={styles.accuracyValue}>
              {history.total_picks > 0 ? (history.accuracy * 100).toFixed(1) : "---"}%
            </Text>
          </View>
          <View style={styles.progressBg}>
            <View
              style={[
                styles.progressFill,
                {
                  width: history.total_picks > 0 ? `${history.accuracy * 100}%` : "0%",
                  backgroundColor:
                    history.accuracy > 0.55 ? colors.green : history.accuracy > 0.45 ? colors.yellow : colors.red,
                },
              ]}
            />
          </View>
        </View>
      )}

      {selectedType && history && history.total_picks > 0 && (
        <View style={styles.infoCard}>
          <Text style={styles.infoText}>
            Mostrando resultados para: <Text style={{ fontWeight: "700", color: colors.text }}>{selectedType}</Text>
          </Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  center: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: colors.bg },
  scroll: { padding: spacing.lg, paddingBottom: 32 },
  title: { fontSize: 24, fontWeight: "bold", color: colors.text, marginBottom: 16 },
  filterRow: { marginBottom: 20, flexDirection: "row" },
  filterChip: {
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 20,
    backgroundColor: colors.bgCard,
    marginRight: 8,
    borderWidth: 1,
    borderColor: colors.border,
  },
  filterChipActive: { backgroundColor: colors.blue + "30", borderColor: colors.blue },
  filterChipText: { fontSize: 13, color: colors.textDim },
  filterChipTextActive: { color: colors.blue, fontWeight: "600" },
  summaryCard: {
    backgroundColor: colors.bgCard,
    borderRadius: 14,
    padding: spacing.xl,
    borderWidth: 1,
    borderColor: colors.border,
  },
  statRow: { flexDirection: "row", justifyContent: "space-around", marginBottom: 20 },
  stat: { alignItems: "center" },
  statValue: { fontSize: 32, fontWeight: "bold", color: colors.text, marginBottom: 4 },
  statLabel: { fontSize: 12, color: colors.textMuted, textTransform: "uppercase", letterSpacing: 1 },
  divider: { width: 1, backgroundColor: colors.border },
  accuracyRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  accuracyLabel: { fontSize: 14, color: colors.textDim, fontWeight: "500" },
  accuracyValue: { fontSize: 20, fontWeight: "bold", color: colors.text },
  progressBg: { height: 6, backgroundColor: colors.bg, borderRadius: 3, overflow: "hidden" },
  progressFill: { height: "100%", borderRadius: 3 },
  infoCard: {
    backgroundColor: colors.bgCardAlt + "80",
    borderRadius: 10,
    padding: spacing.lg,
    marginTop: spacing.lg,
  },
  infoText: { fontSize: 13, color: colors.textDim, textAlign: "center" },
});
