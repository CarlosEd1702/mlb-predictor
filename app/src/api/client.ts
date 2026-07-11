const API_BASE = process.env.EXPO_PUBLIC_API_URL || "http://127.0.0.1:8001/api/v1";

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export interface Pick {
  prediction_id: number;
  game_id: number;
  home_team: string;
  away_team: string;
  game_date: string;
  market: string;
  selection: string;
  model_probability: number;
  market_probability: number | null;
  edge: number | null;
  confidence: string | null;
}

export interface GameDetail {
  game: {
    id: number;
    date: string;
    home_team: string;
    away_team: string;
    park: string | null;
    home_score: number | null;
    away_score: number | null;
    status: string;
  };
  predictions: Array<{
    id: number;
    market: string;
    selection: string;
    model_probability: number;
    edge: number | null;
  }>;
}

export interface HistorySummary {
  total_picks: number;
  wins: number;
  losses: number;
  pushes: number;
  accuracy: number;
}

export interface GameSummary {
  id: number;
  home_team: string;
  away_team: string;
  game_date: string;
  status: string;
  home_score: number | null;
  away_score: number | null;
}

export const api = {
  health: () => fetchJSON<{ status: string; timestamp: string }>("/health"),

  picksOfDay: () => fetchJSON<{ date: string; picks: Pick[] }>("/predicciones/hoy"),

  gameDetail: (id: number) => fetchJSON<GameDetail>(`/partido/${id}`),

  gamesForDate: (date: string) =>
    fetchJSON<{ date: string; games: GameSummary[] }>(`/partidos?fecha=${date}`),

  history: (tipo?: string) => {
    const qs = tipo ? `?tipo=${tipo}` : "";
    return fetchJSON<HistorySummary>(`/historial${qs}`);
  },

  historyByType: (tipo: string) =>
    fetchJSON<HistorySummary & { prop_type: string }>(`/historial/${tipo}`),
};
