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

import { api, Pick } from "../api/client";
import { colors, fonts, spacing } from "../theme";

type Props = NativeStackNavigationProp<Record<string, any>>;

function EdgeBadge({ edge }: { edge: number | null }) {
  if (edge == null) return null;
  const color = edge > 0.05 ? colors.green : edge > 0.02 ? colors.yellow : colors.red;
  return (
    <View style={[styles.edgeBadge, { backgroundColor: color + "20" }]}>
      <Text style={[styles.edgeText, { color }]}>{(edge * 100).toFixed(1)}%</Text>
    </View>
  );
}

function ConfidenceDot({ confidence }: { confidence: string | null }) {
  const dotColor =
    confidence === "high" ? colors.green : confidence === "medium" ? colors.yellow : colors.textMuted;
  return <View style={[styles.confidenceDot, { backgroundColor: dotColor }]} />;
}

export default function DashboardScreen() {
  const nav = useNavigation<Props>();
  const [picks, setPicks] = useState<Pick[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      const data = await api.picksOfDay();
      setPicks(data.picks);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.blue} />
        <Text style={[fonts.body, { marginTop: 12 }]}>Cargando picks...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={picks}
        keyExtractor={(p) => `${p.prediction_id}`}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => load(true)}
            tintColor={colors.blue}
          />
        }
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.card}
            activeOpacity={0.7}
            onPress={() => nav.navigate("PickDetail", { gameId: item.game_id })}
          >
            <View style={styles.cardTop}>
              <View style={styles.teams}>
                <Text style={styles.awayTeam}>{item.away_team}</Text>
                <Text style={styles.atSymbol}>@</Text>
                <Text style={styles.homeTeam}>{item.home_team}</Text>
              </View>
              <EdgeBadge edge={item.edge} />
            </View>

            <View style={styles.cardBody}>
              <ConfidenceDot confidence={item.confidence} />
              <Text style={styles.selection} numberOfLines={1}>
                {item.selection}
              </Text>
              <Text style={styles.market}>{item.market}</Text>
            </View>

            <View style={styles.cardFooter}>
              <Text style={styles.probLabel}>
                Modelo: <Text style={styles.probValue}>{(item.model_probability * 100).toFixed(0)}%</Text>
              </Text>
              {item.market_probability != null && (
                <Text style={styles.probLabel}>
                  Mercado: <Text style={styles.probValue}>{(item.market_probability * 100).toFixed(0)}%</Text>
                </Text>
              )}
            </View>
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          <View style={styles.emptyBox}>
            <Text style={styles.emptyTitle}>Sin picks hoy</Text>
            <Text style={styles.emptySub}>
              No hay predicciones disponibles para hoy. Vuelve más tarde.
            </Text>
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
  cardTop: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 10 },
  teams: { flexDirection: "row", alignItems: "center", gap: 6 },
  awayTeam: { fontSize: 15, fontWeight: "600", color: colors.textDim },
  atSymbol: { fontSize: 12, color: colors.textMuted },
  homeTeam: { fontSize: 15, fontWeight: "700", color: colors.text },
  edgeBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 20 },
  edgeText: { fontSize: 13, fontWeight: "700" },
  cardBody: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 10 },
  confidenceDot: { width: 8, height: 8, borderRadius: 4 },
  selection: { flex: 1, fontSize: 14, fontWeight: "500", color: colors.text },
  market: { fontSize: 11, color: colors.textMuted, backgroundColor: colors.bgCardAlt + "80", paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 },
  cardFooter: { flexDirection: "row", gap: 16, borderTopWidth: 1, borderTopColor: colors.border, paddingTop: 10 },
  probLabel: { fontSize: 12, color: colors.textMuted },
  probValue: { color: colors.textDim, fontWeight: "600" },
  emptyBox: { alignItems: "center", paddingTop: 60 },
  emptyTitle: { fontSize: 18, fontWeight: "600", color: colors.textDim, marginBottom: 8 },
  emptySub: { fontSize: 14, color: colors.textMuted, textAlign: "center" },
});
