import React from "react";
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { MonitorData, DailyAccuracy } from "../api/client";
import { colors, spacing } from "../theme";

interface Props {
  data: MonitorData | null;
  loading: boolean;
  refreshing: boolean;
  onRefresh: () => void;
}

function formatDateTime(iso: string | null) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("es-MX", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function AlertBox({ text, type }: { text: string; type: "warn" | "ok" | "info" }) {
  const bg = type === "warn" ? colors.red + "15" : type === "ok" ? colors.green + "15" : colors.blue + "15";
  const fg = type === "warn" ? colors.red : type === "ok" ? colors.green : colors.blue;
  return (
    <View style={[styles.alertBox, { backgroundColor: bg, borderColor: fg + "40" }]}>
      <Text style={[styles.alertText, { color: fg }]}>{text}</Text>
    </View>
  );
}

function AccuracyBar({ day, maxPicks }: { day: DailyAccuracy; maxPicks: number }) {
  const barWidth = maxPicks > 0 ? (day.total_picks / maxPicks) * 100 : 0;
  const barColor = day.accuracy > 0.55 ? colors.green : day.accuracy > 0.45 ? colors.yellow : colors.red;
  const shortDate = new Date(day.date + "T12:00:00").toLocaleDateString("es-MX", { day: "2-digit", month: "2-digit" });
  return (
    <View style={styles.accRow}>
      <Text style={styles.accDate}>{shortDate}</Text>
      <View style={styles.accBarBg}>
        <View style={[styles.accBarFill, { width: `${barWidth}%`, backgroundColor: barColor }]} />
      </View>
      <Text style={[styles.accPct, { color: barColor }]}>{(day.accuracy * 100).toFixed(0)}%</Text>
      <Text style={styles.accN}>{day.wins}/{day.total_picks}</Text>
    </View>
  );
}

export default function MonitorTab({ data, loading, refreshing, onRefresh }: Props) {
  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.blue} />
      </View>
    );
  }

  if (!data) {
    return (
      <View style={styles.center}>
        <Text style={styles.emptyText}>No hay datos de monitoreo.</Text>
      </View>
    );
  }

  const lastRetrain = data.last_retrain;
  const lastResult = data.last_results_pull;
  const maxPicks = Math.max(...data.daily_accuracy.map((d) => d.total_picks), 1);

  const needsAttention =
    (lastRetrain && lastRetrain.accuracy != null && lastRetrain.accuracy < 0.5) ||
    data.pending_picks > 50;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scroll}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.blue} />
      }
    >
      {needsAttention && (
        <AlertBox
          text="El modelo necesita atención — accuracy baja o hay picks pendientes."
          type="warn"
        />
      )}

      <Text style={styles.sectionTitle}>Sistema</Text>
      <View style={styles.card}>
        <StatusRow label="Retrain" value={lastRetrain ? `${lastRetrain.version_label} (${formatDateTime(lastRetrain.training_date)})` : "Nunca"} />
        <StatusRow label="Resultados" value={formatDateTime(lastResult)} />
        <StatusRow label="Picks pendientes" value={String(data.pending_picks)} />
      </View>

      {lastRetrain && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Último retrain</Text>
          <View style={styles.metricsGrid}>
            <View style={styles.metricBox}>
              <Text style={styles.metricValue}>{lastRetrain.version_label}</Text>
              <Text style={styles.metricLabel}>Versión</Text>
            </View>
            <View style={styles.metricBox}>
              <Text style={styles.metricValue}>{lastRetrain.samples}</Text>
              <Text style={styles.metricLabel}>Muestras</Text>
            </View>
            <View style={styles.metricBox}>
              <Text style={[styles.metricValue, { color: lastRetrain.accuracy != null && lastRetrain.accuracy > 0.55 ? colors.green : colors.red }]}>
                {lastRetrain.accuracy != null ? `${(lastRetrain.accuracy * 100).toFixed(1)}%` : "—"}
              </Text>
              <Text style={styles.metricLabel}>Accuracy</Text>
            </View>
          </View>
        </View>
      )}

      <Text style={styles.sectionTitle}>Scheduler</Text>
      <View style={styles.card}>
        {data.scheduler_jobs.length === 0 ? (
          <Text style={styles.emptyText}>No hay jobs activos</Text>
        ) : (
          data.scheduler_jobs.map((j) => (
            <View key={j.id} style={styles.jobRow}>
              <View style={[styles.jobDot, j.next_run_time ? styles.jobDotActive : styles.jobDotInactive]} />
              <Text style={styles.jobId}>{j.id}</Text>
              <Text style={styles.jobNext}>{j.next_run_time ? formatDateTime(j.next_run_time) : "detenido"}</Text>
            </View>
          ))
        )}
      </View>

      <Text style={styles.sectionTitle}>Accuracy diaria (14 días)</Text>
      {data.daily_accuracy.length === 0 ? (
        <Text style={styles.emptyText}>Sin datos de resultados aún.</Text>
      ) : (
        <View style={styles.card}>
          {data.daily_accuracy.map((d) => (
            <AccuracyBar key={d.date} day={d} maxPicks={maxPicks} />
          ))}
        </View>
      )}
    </ScrollView>
  );
}

function StatusRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.statusRow}>
      <Text style={styles.statusLabel}>{label}</Text>
      <Text style={styles.statusValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  scroll: { paddingBottom: 32 },
  emptyText: { color: colors.textMuted, textAlign: "center", paddingVertical: 20, fontSize: 13 },
  sectionTitle: { fontSize: 15, fontWeight: "600", color: colors.text, marginBottom: 8, marginTop: 4 },
  card: {
    backgroundColor: colors.bgCard,
    borderRadius: 12,
    padding: spacing.lg,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardTitle: { fontSize: 13, fontWeight: "600", color: colors.textDim, marginBottom: 8, textTransform: "uppercase", letterSpacing: 0.5 },
  alertBox: {
    borderRadius: 10,
    padding: spacing.md,
    marginBottom: spacing.md,
    borderWidth: 1,
  },
  alertText: { fontSize: 13, fontWeight: "500" },
  statusRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 5,
    borderBottomWidth: 1,
    borderBottomColor: colors.border + "60",
  },
  statusLabel: { fontSize: 13, color: colors.textDim },
  statusValue: { fontSize: 13, color: colors.text, fontWeight: "500" },
  metricsGrid: { flexDirection: "row", justifyContent: "space-around" },
  metricBox: { alignItems: "center", gap: 4 },
  metricValue: { fontSize: 22, fontWeight: "bold", color: colors.text },
  metricLabel: { fontSize: 11, color: colors.textMuted, textTransform: "uppercase" },
  jobRow: { flexDirection: "row", alignItems: "center", gap: 8, paddingVertical: 5 },
  jobDot: { width: 8, height: 8, borderRadius: 4 },
  jobDotActive: { backgroundColor: colors.green },
  jobDotInactive: { backgroundColor: colors.red },
  jobId: { fontSize: 13, color: colors.text, flex: 1, textTransform: "capitalize" },
  jobNext: { fontSize: 11, color: colors.textMuted },
  accRow: { flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 4 },
  accDate: { fontSize: 11, color: colors.textMuted, width: 40 },
  accBarBg: {
    flex: 1,
    height: 8,
    backgroundColor: colors.bgCardAlt || colors.bg,
    borderRadius: 4,
    overflow: "hidden",
  },
  accBarFill: { height: "100%", borderRadius: 4 },
  accPct: { fontSize: 12, fontWeight: "700", width: 36, textAlign: "right" },
  accN: { fontSize: 10, color: colors.textMuted, width: 32, textAlign: "right" },
});
