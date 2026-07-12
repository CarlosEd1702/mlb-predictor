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

import { api, HistorySummary, CalibrationData, ErrorBreakdown, GameResult, ModelVersionInfo, MonitorData } from "../api/client";
import ModelsTab from "./ModelsTab";
import MonitorTab from "./MonitorTab";
import { colors, fonts, spacing } from "../theme";

type Tab = "resumen" | "calibracion" | "errores" | "resultados" | "modelos" | "monitor";
const TABS: { key: Tab; label: string }[] = [
  { key: "resumen", label: "Resumen" },
  { key: "calibracion", label: "Calibración" },
  { key: "errores", label: "Errores" },
  { key: "resultados", label: "Resultados" },
  { key: "modelos", label: "Modelos" },
  { key: "monitor", label: "Monitor" },
];

const PROP_TYPES = [
  { label: "Todos", value: null },
  { label: "Moneyline", value: "h2h" },
  { label: "Totales", value: "totals" },
  { label: "Spread", value: "spreads" },
  { label: "Strikeouts", value: "player_strikeouts" },
];

function ProbBar({ pct, color }: { pct: number; color: string }) {
  return (
    <View style={styles.probBarBg}>
      <View style={[styles.probBarFill, { width: `${Math.min(pct * 100, 100)}%`, backgroundColor: color }]} />
    </View>
  );
}

export default function HistoryScreen() {
  const [tab, setTab] = useState<Tab>("resumen");
  const [history, setHistory] = useState<HistorySummary | null>(null);
  const [calibration, setCalibration] = useState<CalibrationData | null>(null);
  const [errors, setErrors] = useState<ErrorBreakdown | null>(null);
  const [results, setResults] = useState<GameResult[]>([]);
  const [models, setModels] = useState<ModelVersionInfo[]>([]);
  const [monitorData, setMonitorData] = useState<MonitorData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedType, setSelectedType] = useState<string | null>(null);

  const load = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      setLoading(true);
      const [h, c, e, r, m, mon] = await Promise.all([
        selectedType ? api.historyByType(selectedType) : api.history(),
        api.calibration(),
        api.errorBreakdown(),
        api.resultados(),
        api.modelos(),
        api.monitor(),
      ]);
      setHistory(h);
      setCalibration(c);
      setErrors(e);
      setResults(r.results);
      setModels(m.versions);
      setMonitorData(mon);
    } catch (err) {
      console.error(err);
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
        {TABS.map((t) => (
          <TouchableOpacity
            key={t.key}
            style={[styles.filterChip, tab === t.key && styles.filterChipActive]}
            onPress={() => setTab(t.key)}
          >
            <Text style={[styles.filterChipText, tab === t.key && styles.filterChipTextActive]}>
              {t.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {tab === "resumen" && (
        <>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterRow}>
            {PROP_TYPES.map((pt) => (
              <TouchableOpacity
                key={pt.label}
                style={[styles.filterChip, selectedType === pt.value && styles.filterChipActive]}
                onPress={() => setSelectedType(pt.value)}
              >
                <Text style={[styles.filterChipText, selectedType === pt.value && styles.filterChipTextActive]}>
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
        </>
      )}

      {tab === "calibracion" && calibration && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            Calibración ({calibration.total_picks} picks, MSE: {calibration.mse})
          </Text>
          {calibration.bins.map((b) => (
            <View key={b.bucket} style={styles.calRow}>
              <View style={styles.calLabel}>
                <Text style={styles.calLabelText}>
                  {b.bin_min.toFixed(0)}-{b.bin_max.toFixed(0)}%
                </Text>
              </View>
              <View style={styles.calBars}>
                <ProbBar pct={b.win_rate} color={colors.blue} />
                <View style={styles.calMarker} />
              </View>
              <View style={styles.calStats}>
                <Text style={[styles.calPct, { color: Math.abs(b.error) < 0.05 ? colors.green : colors.yellow }]}>
                  {(b.win_rate * 100).toFixed(0)}%
                </Text>
                <Text style={styles.calN}>{b.total}</Text>
              </View>
            </View>
          ))}
          <Text style={styles.helpText}>
            Cada barra muestra el % real de aciertos para ese rango de probabilidad predicho. Una barra cerca de la línea punteada = bien calibrado.
          </Text>
        </View>
      )}

      {tab === "errores" && errors && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Por Mercado</Text>
          {errors.by_market.map((m) => (
            <View key={m.market} style={styles.errorCard}>
              <View style={styles.errorHeader}>
                <Text style={styles.errorMarket}>{m.market}</Text>
                <Text style={[styles.errorPct, { color: m.win_rate > 0.5 ? colors.green : colors.red }]}>
                  {(m.win_rate * 100).toFixed(1)}%
                </Text>
              </View>
              <Text style={styles.errorMeta}>
                {m.wins}W {m.losses}L · Prob prom: {(m.avg_prob * 100).toFixed(0)}%
              </Text>
              <ProbBar pct={m.win_rate} color={m.win_rate > 0.5 ? colors.green : colors.red} />
            </View>
          ))}

          <Text style={[styles.sectionTitle, { marginTop: 20 }]}>Por Equipo (ML)</Text>
          {errors.by_team.map((t) => (
            <View key={t.team} style={styles.teamRow}>
              <Text style={styles.teamName}>{t.team}</Text>
              <Text style={[styles.teamPct, { color: t.win_rate > 0.5 ? colors.green : colors.red }]}>
                {(t.win_rate * 100).toFixed(1)}%
              </Text>
              <Text style={styles.teamN}>{t.total} picks</Text>
            </View>
          ))}
        </View>
      )}

      {tab === "monitor" && (
        <MonitorTab
          data={monitorData}
          loading={loading}
          refreshing={refreshing}
          onRefresh={() => load(true)}
        />
      )}

      {tab === "modelos" && (
        <ModelsTab
          versions={models}
          loading={loading}
          refreshing={refreshing}
          onRefresh={() => load(true)}
        />
      )}

      {tab === "resultados" && (
        <View style={styles.section}>
          {results.length === 0 ? (
            <Text style={styles.emptyText}>No hay resultados registrados para hoy.</Text>
          ) : (
            results.map((r) => (
              <View key={r.game_id} style={styles.resultCard}>
                <View style={styles.resultHeader}>
                  <Text style={styles.resultTeams}>
                    {r.away_team} @ {r.home_team}
                  </Text>
                  {r.result.won != null && (
                    <View style={[styles.resultBadge, { backgroundColor: (r.result.won ? colors.green : colors.red) + "20" }]}>
                      <Text style={[styles.resultBadgeText, { color: r.result.won ? colors.green : colors.red }]}>
                        {r.result.won ? "GANADA" : "PERDIDA"}
                      </Text>
                    </View>
                  )}
                </View>
                <Text style={styles.resultScore}>
                  {r.away_score ?? "?"} - {r.home_score ?? "?"}
                </Text>
                <Text style={styles.resultPick}>
                  {r.prediction.selection} ({(r.prediction.model_probability * 100).toFixed(0)}%)
                </Text>
              </View>
            ))
          )}
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
  accuracyRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 10 },
  accuracyLabel: { fontSize: 14, color: colors.textDim, fontWeight: "500" },
  accuracyValue: { fontSize: 20, fontWeight: "bold", color: colors.text },
  progressBg: { height: 6, backgroundColor: colors.bg, borderRadius: 3, overflow: "hidden" },
  progressFill: { height: "100%", borderRadius: 3 },
  section: { marginTop: 4 },
  sectionTitle: { fontSize: 16, fontWeight: "600", color: colors.text, marginBottom: 12 },
  helpText: { fontSize: 12, color: colors.textMuted, marginTop: 12, lineHeight: 18 },
  calRow: { flexDirection: "row", alignItems: "center", marginBottom: 8, gap: 8 },
  calLabel: { width: 50 },
  calLabelText: { fontSize: 11, color: colors.textMuted },
  calBars: { flex: 1, position: "relative", height: 14, justifyContent: "center" },
  probBarBg: { height: 8, backgroundColor: colors.bgCardAlt, borderRadius: 4, overflow: "hidden" },
  probBarFill: { height: "100%", borderRadius: 4 },
  calMarker: { position: "absolute", left: "50%", top: -2, width: 2, height: 18, backgroundColor: colors.textMuted + "60", borderRadius: 1 },
  calStats: { width: 60, alignItems: "flex-end" },
  calPct: { fontSize: 13, fontWeight: "700" },
  calN: { fontSize: 10, color: colors.textMuted },
  errorCard: {
    backgroundColor: colors.bgCard,
    borderRadius: 10,
    padding: spacing.md,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  errorHeader: { flexDirection: "row", justifyContent: "space-between", marginBottom: 4 },
  errorMarket: { fontSize: 14, fontWeight: "600", color: colors.text },
  errorPct: { fontSize: 14, fontWeight: "700" },
  errorMeta: { fontSize: 11, color: colors.textMuted, marginBottom: 6 },
  teamRow: { flexDirection: "row", alignItems: "center", gap: 10, marginBottom: 6, paddingHorizontal: 4 },
  teamName: { fontSize: 13, fontWeight: "500", color: colors.textDim, width: 60 },
  teamPct: { fontSize: 13, fontWeight: "700", width: 50 },
  teamN: { fontSize: 11, color: colors.textMuted },
  emptyText: { color: colors.textMuted, textAlign: "center", paddingVertical: 40, fontSize: 14 },
  resultCard: {
    backgroundColor: colors.bgCard,
    borderRadius: 12,
    padding: spacing.lg,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  resultHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 6 },
  resultTeams: { fontSize: 14, fontWeight: "600", color: colors.text },
  resultBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 12 },
  resultBadgeText: { fontSize: 11, fontWeight: "700" },
  resultScore: { fontSize: 22, fontWeight: "bold", color: colors.text, marginBottom: 4 },
  resultPick: { fontSize: 12, color: colors.textMuted },
});
