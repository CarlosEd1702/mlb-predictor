import React from "react";
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

import { ModelVersionInfo } from "../api/client";
import { colors, fonts, spacing } from "../theme";

interface Props {
  versions: ModelVersionInfo[];
  loading: boolean;
  refreshing: boolean;
  onRefresh: () => void;
}

function formatDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString("es-MX", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function MetricRow({ label, value, goodDir }: { label: string; value: number; goodDir?: "up" | "down" }) {
  const formatted = label === "accuracy"
    ? `${(value * 100).toFixed(1)}%`
    : label === "brier_score" || label === "log_loss" || label === "calibration_error"
    ? value.toFixed(4)
    : label === "rmse" || label === "mae"
    ? value.toFixed(2)
    : value.toFixed(4);

  const isGood =
    goodDir === "up"
      ? value > 0.5
      : goodDir === "down"
      ? value < 0.3
      : null;

  return (
    <View style={styles.metricRow}>
      <Text style={styles.metricLabel}>{label.replace(/_/g, " ")}</Text>
      <Text style={[styles.metricValue, isGood != null && { color: isGood ? colors.green : colors.red }]}>
        {formatted}
      </Text>
    </View>
  );
}

export default function ModelsTab({ versions, loading, refreshing, onRefresh }: Props) {
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
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.blue} />
      }
    >
      {versions.length === 0 ? (
        <Text style={styles.emptyText}>No hay versiones de modelo registradas.</Text>
      ) : (
        versions.map((v) => (
          <View key={v.id} style={[styles.card, v.is_active && styles.cardActive]}>
            <View style={styles.cardHeader}>
              <View style={styles.cardHeaderLeft}>
                {v.is_active && (
                  <View style={styles.activeBadge}>
                    <Text style={styles.activeBadgeText}>ACTIVO</Text>
                  </View>
                )}
                <Text style={styles.versionLabel}>{v.version_label}</Text>
              </View>
              <Text style={styles.marketChip}>{v.market === "h2h" ? "Moneyline" : v.market === "totals" ? "Totales" : v.market}</Text>
            </View>

            <Text style={styles.dateText}>{formatDate(v.training_date)}</Text>

            <View style={styles.metricsContainer}>
              {v.metrics?.accuracy != null && <MetricRow label="accuracy" value={v.metrics.accuracy} goodDir="up" />}
              {v.metrics?.log_loss != null && <MetricRow label="log_loss" value={v.metrics.log_loss} goodDir="down" />}
              {v.metrics?.brier_score != null && <MetricRow label="brier_score" value={v.metrics.brier_score} goodDir="down" />}
              {v.metrics?.calibration_error != null && <MetricRow label="calibration_error" value={v.metrics.calibration_error} goodDir="down" />}
              {v.metrics?.rmse != null && <MetricRow label="rmse" value={v.metrics.rmse} goodDir="down" />}
              {v.metrics?.mae != null && <MetricRow label="mae" value={v.metrics.mae} goodDir="down" />}
            </View>

            <View style={styles.footer}>
              <Text style={styles.samplesText}>{v.training_samples} muestras</Text>
              {v.parent_version && (
                <Text style={styles.parentText}>desde {v.parent_version}</Text>
              )}
            </View>
          </View>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  scroll: { paddingBottom: 32 },
  emptyText: { color: colors.textMuted, textAlign: "center", paddingVertical: 40, fontSize: 14 },
  card: {
    backgroundColor: colors.bgCard,
    borderRadius: 12,
    padding: spacing.lg,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardActive: {
    borderColor: colors.green,
    backgroundColor: colors.green + "08",
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 6,
  },
  cardHeaderLeft: { flexDirection: "row", alignItems: "center", gap: 8 },
  activeBadge: {
    backgroundColor: colors.green + "20",
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  activeBadgeText: {
    fontSize: 10,
    fontWeight: "700",
    color: colors.green,
    letterSpacing: 1,
  },
  versionLabel: { fontSize: 17, fontWeight: "bold", color: colors.text },
  marketChip: {
    fontSize: 11,
    color: colors.blue,
    backgroundColor: colors.blue + "18",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
    fontWeight: "600",
  },
  dateText: { fontSize: 12, color: colors.textMuted, marginBottom: 12 },
  metricsContainer: {
    backgroundColor: colors.bg,
    borderRadius: 8,
    padding: spacing.sm,
    marginBottom: 10,
  },
  metricRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 3,
  },
  metricLabel: { fontSize: 12, color: colors.textDim, textTransform: "capitalize" },
  metricValue: { fontSize: 13, fontWeight: "600", color: colors.text },
  footer: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  samplesText: { fontSize: 12, color: colors.textMuted },
  parentText: { fontSize: 11, color: colors.textMuted, fontStyle: "italic" },
});
