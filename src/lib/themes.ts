export interface Theme {
  background: string;
  backgroundGradient: string;
  textPrimary: string;
  subtitleBg: string;
  subtitleText: string;
  accentColor: string;
  watermarkColor: string;
  nameBadgeBg: string;
  nameBadgeText: string;
}

export const THEMES: Record<string, Theme> = {
  "zkagi-brand": {
    background: "#0a0a1a",
    backgroundGradient: "linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 50%, #0a1a2e 100%)",
    textPrimary: "#FFFFFF",
    subtitleBg: "rgba(10,10,26,0.85)",
    subtitleText: "#FFFFFF",
    accentColor: "#7C3AED",
    watermarkColor: "rgba(124,58,237,0.3)",
    nameBadgeBg: "rgba(124,58,237,0.2)",
    nameBadgeText: "#A78BFA",
  },
  pawpad: {
    background: "#0f172a",
    backgroundGradient: "linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0c4a6e 100%)",
    textPrimary: "#FFFFFF",
    subtitleBg: "rgba(15,23,42,0.85)",
    subtitleText: "#FFFFFF",
    accentColor: "#06B6D4",
    watermarkColor: "rgba(6,182,212,0.3)",
    nameBadgeBg: "rgba(6,182,212,0.2)",
    nameBadgeText: "#38BDF8",
  },
  dark: {
    background: "#111111",
    backgroundGradient: "linear-gradient(135deg, #111 0%, #1a1a2e 100%)",
    textPrimary: "#FFFFFF",
    subtitleBg: "rgba(0,0,0,0.8)",
    subtitleText: "#FFFFFF",
    accentColor: "#8B5CF6",
    watermarkColor: "rgba(139,92,246,0.2)",
    nameBadgeBg: "rgba(255,255,255,0.1)",
    nameBadgeText: "#D1D5DB",
  },
  light: {
    background: "#FAFAFA",
    backgroundGradient: "linear-gradient(135deg, #FAFAFA 0%, #E0E7FF 100%)",
    textPrimary: "#111827",
    subtitleBg: "rgba(255,255,255,0.9)",
    subtitleText: "#111827",
    accentColor: "#7C3AED",
    watermarkColor: "rgba(124,58,237,0.15)",
    nameBadgeBg: "rgba(124,58,237,0.1)",
    nameBadgeText: "#7C3AED",
  },
};

export const getTheme = (name: string): Theme => THEMES[name] || THEMES["zkagi-brand"];
