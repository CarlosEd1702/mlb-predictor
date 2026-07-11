export const colors = {
  bg: "#0f172a",
  bgCard: "#1e293b",
  bgCardAlt: "#334155",
  text: "#f8fafc",
  textDim: "#94a3b8",
  textMuted: "#64748b",
  green: "#22c55e",
  red: "#ef4444",
  yellow: "#eab308",
  blue: "#3b82f6",
  border: "#334155",
};

export const spacing = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
};

export const fonts = {
  title: { fontSize: 24, fontWeight: "bold" as const, color: colors.text },
  subtitle: { fontSize: 18, fontWeight: "600" as const, color: colors.text },
  body: { fontSize: 14, color: colors.textDim },
  small: { fontSize: 12, color: colors.textMuted },
};
