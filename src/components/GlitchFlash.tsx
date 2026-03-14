import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";

export const GlitchFlash: React.FC<{ color?: string }> = ({ color = "#06B6D4" }) => {
  const frame = useCurrentFrame();
  if (frame > 8) return null;

  const flash1 = frame < 2 ? 0.7 : 0;
  const flash2 = frame >= 3 && frame < 5 ? 0.4 : 0;
  const scanline = frame >= 2 && frame < 6 ? 0.3 : 0;

  return (
    <AbsoluteFill style={{ zIndex: 200 }}>
      <div style={{
        position: "absolute", width: "100%", height: "100%",
        backgroundColor: color, opacity: flash1 + flash2,
      }} />
      {scanline > 0 && (
        <div style={{
          position: "absolute", width: "100%", height: "100%",
          background: `repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,${scanline}) 2px, rgba(0,0,0,${scanline}) 4px)`,
        }} />
      )}
    </AbsoluteFill>
  );
};
