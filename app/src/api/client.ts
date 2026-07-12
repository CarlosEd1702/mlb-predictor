const API_BASE = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000/api/v1";

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

export interface InjuryItem {
  type: string;
  description: string;
  date: string;
}

export interface UpcomingGame {
  id: string;
  game_id: number;
  commence_time: string;
  home_team: string;
  away_team: string;
  home_abbr: string;
  away_abbr: string;
  home_record: string;
  away_record: string;
  home_streak: string;
  away_streak: string;
  weather: {
    condition: string;
    temperature: string | number | null;
    wind: string;
  };
  home_injuries: InjuryItem[];
  away_injuries: InjuryItem[];
  odds: {
    h2h: Record<string, number>;
    spreads: Record<string, { price: number; point: number | null }>;
    totals: Record<string, { price: number; point: number | null }>;
  };
  prediction: {
    home_win_prob: number;
    away_win_prob: number;
    favorite: string;
    favorite_prob: number;
    predicted_total_runs?: number;
  } | null;
}

export interface CalibrationBin {
  bucket: number;
  bin_min: number;
  bin_max: number;
  bin_mid: number;
  total: number;
  wins: number;
  losses: number;
  win_rate: number;
  error: number;
}

export interface CalibrationData {
  bins: CalibrationBin[];
  mse: number;
  total_picks: number;
}

export interface ErrorBreakdown {
  by_market: Array<{
    market: string;
    total: number;
    wins: number;
    losses: number;
    win_rate: number;
    avg_prob: number;
    avg_edge: number;
  }>;
  by_team: Array<{
    team: string;
    total: number;
    wins: number;
    win_rate: number;
  }>;
}

export interface GameResult {
  game_id: number;
  home_team: string;
  away_team: string;
  home_score: number | null;
  away_score: number | null;
  status: string;
  prediction: {
    id: number;
    market: string;
    selection: string;
    model_probability: number;
    edge: number | null;
  };
  result: {
    won: boolean | null;
    actual_value: number | null;
    clv: number | null;
  };
}

export interface DailyAccuracy {
  date: string;
  total_picks: number;
  wins: number;
  losses: number;
  accuracy: number;
}

export interface SchedulerJobStatus {
  id: string;
  next_run_time: string | null;
}

export interface MonitorData {
  last_retrain: {
    version_label: string;
    training_date: string;
    accuracy: number | null;
    samples: number;
  } | null;
  last_results_pull: string | null;
  daily_accuracy: DailyAccuracy[];
  pending_picks: number;
  scheduler_jobs: SchedulerJobStatus[];
}

export interface ModelVersionInfo {
  id: number;
  version_label: string;
  market: string;
  training_date: string;
  training_samples: number;
  metrics: Record<string, number>;
  feature_importance: Record<string, number> | null;
  parent_version: string | null;
  is_active: boolean;
}

export const api = {
  health: () => fetchJSON<{ status: string; timestamp: string }>("/health"),

  picksOfDay: () => fetchJSON<{ date: string; picks: Pick[] }>("/predicciones/hoy"),

  gameDetail: (id: number) => fetchJSON<GameDetail>(`/partido/${id}`),

  gamesForDate: (date: string) =>
    fetchJSON<{ date: string; games: GameSummary[] }>(`/partidos?fecha=${date}`),

  upcoming: () => fetchJSON<{ games: UpcomingGame[] }>("/proximos"),

  history: (tipo?: string) => {
    const qs = tipo ? `?tipo=${tipo}` : "";
    return fetchJSON<HistorySummary>(`/historial${qs}`);
  },

  historyByType: (tipo: string) =>
    fetchJSON<HistorySummary & { prop_type: string }>(`/historial/${tipo}`),

  resultados: (fecha?: string) => {
    const qs = fecha ? `?fecha=${fecha}` : "";
    return fetchJSON<{ date: string; results: GameResult[] }>(`/resultados${qs}`);
  },

  calibration: () => fetchJSON<CalibrationData>("/analytics/calibration"),

  errorBreakdown: () => fetchJSON<ErrorBreakdown>("/analytics/errors"),

  modelos: () => fetchJSON<{ versions: ModelVersionInfo[] }>("/modelos"),

  monitor: () => fetchJSON<MonitorData>("/monitor"),
};
