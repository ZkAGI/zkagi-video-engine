import React from "react";
import { AbsoluteFill } from "remotion";

export const BottomGradient: React.FC<{ intensity?: number }> = ({ intensity = 0.65 }) => (
  <AbsoluteFill style={{ zIndex: 40 }}>
    <div style={{
      position: "absolute", width: "100%", height: "100%",
      background: `linear-gradient(180deg, transparent 0%, transparent 55%, rgba(0,0,0,${intensity * 0.3}) 75%, rgba(0,0,0,${intensity}) 100%)`,
    }} />
  </AbsoluteFill>
);
