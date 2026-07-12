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

import { api, UpcomingGame } from "../api/client";
import { colors, fonts, spacing } from "../theme";

type Props = NativeStackNavigationProp<Record<string, any>>;

function OddsCell({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.oddsCell}>
      <Text style={styles.oddsLabel}>{label}</Text>
      <Text style={styles.oddsValue}>{value}</Text>
    </View>
  );
}

function PredictionBadge({ pred }: { pred: UpcomingGame["prediction"] }) {
  if (!pred) return null;
  return (
    <View style={styles.predBadge}>
      <Text style={styles.predBadgeLabel}>Fav: {pred.favorite}</Text>
      <Text style={styles.predBadgeValue}>{(pred.favorite_prob * 100).toFixed(0)}%</Text>
      {pred.predicted_total_runs != null && (
        <Text style={styles.predBadgeRuns}>Proy. {pred.predicted_total_runs} carreras</Text>
      )}
    </View>
  );
}

function formatTime(iso: string) {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString("es-US", {
      hour: "2-digit",
      minute: "2-digit",
      timeZoneName: "short",
    });
  } catch {
    return iso;
  }
}

export default function ProximosScreen() {
  const nav = useNavigation<Props>();
  const [games, setGames] = useState<UpcomingGame[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      const data = await api.upcoming();
      setGames(data.games);
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
        <Text style={[fonts.body, { marginTop: 12 }]}>Cargando próximos partidos...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={games}
        keyExtractor={(g) => g.id}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={colors.blue} />
        }
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.card}
            activeOpacity={0.7}
            onPress={() => nav.navigate("PickDetail", { gameId: item.game_id })}
          >
            <View style={styles.cardHeader}>
              <View style={styles.teamsRow}>
                <View style={styles.teamBlock}>
                  <View style={styles.teamRow}>
                    {item.prediction?.favorite === item.away_abbr && <Text style={styles.pickIcon}>✓</Text>}
                    <Text style={item.prediction?.favorite === item.away_abbr ? styles.teamPicked : styles.teamName}>
                      {item.away_team}
                    </Text>
                  </View>
                  <Text style={styles.teamRecord}>{item.away_record}</Text>
                </View>
                <Text style={styles.atSymbol}>@</Text>
                <View style={styles.teamBlock}>
                  <View style={styles.teamRow}>
                    {item.prediction?.favorite === item.home_abbr && <Text style={styles.pickIcon}>✓</Text>}
                    <Text style={item.prediction?.favorite === item.home_abbr ? styles.teamPicked : styles.teamName}>
                      {item.home_team}
                    </Text>
                    <Text style={styles.homeIndicator}>(L)</Text>
                  </View>
                  <Text style={styles.teamRecord}>{item.home_record}</Text>
                </View>
              </View>
              <Text style={styles.gameTime}>{formatTime(item.commence_time)}</Text>
            </View>

            <PredictionBadge pred={item.prediction} />

            {(item.home_streak || item.away_streak || item.weather?.condition) && (
              <View style={styles.contextRow}>
                {item.away_streak && <Text style={styles.streakText}>{item.away_abbr} {item.away_streak}</Text>}
                {item.home_streak && <Text style={styles.streakText}>{item.home_abbr} {item.home_streak}</Text>}
                {item.weather?.condition && (
                  <Text style={styles.weatherText}>{item.weather.condition} {item.weather.temperature ?? ""}°</Text>
                )}
              </View>
            )}

            {item.home_injuries.length > 0 && (
              <View style={styles.injuryRow}>
                <Text style={styles.injuryLabel}>{item.home_abbr} lesiones:</Text>
                {item.home_injuries.slice(0, 2).map((inj, i) => (
                  <Text key={i} style={styles.injuryText} numberOfLines={1}>{inj.description}</Text>
                ))}
              </View>
            )}
            {item.away_injuries.length > 0 && (
              <View style={styles.injuryRow}>
                <Text style={styles.injuryLabel}>{item.away_abbr} lesiones:</Text>
                {item.away_injuries.slice(0, 2).map((inj, i) => (
                  <Text key={i} style={styles.injuryText} numberOfLines={1}>{inj.description}</Text>
                ))}
              </View>
            )}

            <View style={styles.oddsRow}>
              {Object.entries(item.odds.h2h).map(([team, price]) => (
                <OddsCell key={team} label={team.split(" ").pop() ?? team} value={price > 0 ? `+${price}` : `${price}`} />
              ))}
            </View>

            {Object.keys(item.odds.spreads).length > 0 && (
              <View style={styles.oddsRow}>
                {Object.entries(item.odds.spreads).map(([team, data]) => (
                  <OddsCell key={team} label={`Spread ${team.split(" ").pop()}`} value={`${data.point > 0 ? "+" : ""}${data.point} (${data.price > 0 ? "+" : ""}${data.price})`} />
                ))}
              </View>
            )}

            {Object.keys(item.odds.totals).length > 0 && (
              <View style={styles.oddsRow}>
                {Object.entries(item.odds.totals).map(([name, data]) => (
                  <OddsCell key={name} label={name} value={`${data.point} (${data.price > 0 ? "+" : ""}${data.price})`} />
                ))}
              </View>
            )}
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          <View style={styles.emptyBox}>
            <Text style={styles.emptyTitle}>Sin próximos partidos</Text>
            <Text style={styles.emptySub}>No hay juegos programados en los próximos días.</Text>
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
  cardHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 },
  teamsRow: { flexDirection: "row", alignItems: "center", gap: 8, flex: 1 },
  teamRow: { flexDirection: "row", alignItems: "center", gap: 3 },
  teamBlock: { alignItems: "center" },
  teamName: { fontSize: 14, fontWeight: "500", color: colors.textDim },
  teamPicked: { fontSize: 14, fontWeight: "700", color: colors.text },
  pickIcon: { fontSize: 13, color: colors.green, fontWeight: "700" },
  homeIndicator: { fontSize: 9, color: colors.textMuted, marginLeft: 2 },
  atSymbol: { fontSize: 12, color: colors.textMuted },
  teamRecord: { fontSize: 11, color: colors.textMuted, marginTop: 2 },
  gameTime: { fontSize: 11, color: colors.textMuted, backgroundColor: colors.bgCardAlt + "80", paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8 },
  predBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    backgroundColor: colors.blue + "15",
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
    marginBottom: 10,
  },
  predBadgeLabel: { fontSize: 12, color: colors.textDim },
  predBadgeValue: { fontSize: 13, fontWeight: "700", color: colors.blue },
  predBadgeRuns: { fontSize: 11, color: colors.textMuted, marginLeft: "auto" },
  oddsRow: { flexDirection: "row", gap: 8, marginTop: 6, flexWrap: "wrap" },
  oddsCell: {
    backgroundColor: colors.bgCardAlt + "60",
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  oddsLabel: { fontSize: 10, color: colors.textMuted },
  oddsValue: { fontSize: 12, fontWeight: "600", color: colors.text },
  contextRow: {
    flexDirection: "row",
    gap: 8,
    marginBottom: 8,
    flexWrap: "wrap",
  },
  streakText: {
    fontSize: 11,
    color: colors.yellow,
    backgroundColor: colors.yellow + "15",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  weatherText: {
    fontSize: 11,
    color: colors.blue,
    backgroundColor: colors.blue + "15",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  injuryRow: {
    flexDirection: "row",
    gap: 4,
    marginBottom: 4,
    flexWrap: "wrap",
  },
  injuryLabel: {
    fontSize: 10,
    color: colors.red,
    fontWeight: "600",
  },
  injuryText: {
    fontSize: 10,
    color: colors.textMuted,
    flexShrink: 1,
  },
  emptyBox: { alignItems: "center", paddingTop: 60 },
  emptyTitle: { fontSize: 18, fontWeight: "600", color: colors.textDim, marginBottom: 8 },
  emptySub: { fontSize: 14, color: colors.textMuted, textAlign: "center" },
});
