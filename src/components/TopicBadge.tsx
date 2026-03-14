import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";

export const TopicBadge: React.FC<{
  label: string;
  color: string;
  durationInFrames: number;
}> = ({ label, color, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enterSpring = spring({ frame, fps, config: { damping: 20, mass: 0.4, stiffness: 160 } });
  const slideX = interpolate(enterSpring, [0, 1], [-60, 0]);
  const opacity = interpolate(enterSpring, [0, 1], [0, 1]);
  const exitOp = interpolate(frame, [durationInFrames - 8, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <div style={{
      position: "absolute", top: 28, left: 28,
      transform: `translateX(${slideX}px)`, opacity: opacity * exitOp, zIndex: 55,
    }}>
      <div style={{
        background: `${color}30`, border: `1px solid ${color}60`,
        padding: "4px 14px", borderRadius: 6, backdropFilter: "blur(8px)",
      }}>
        <span style={{
          color, fontSize: 14, fontWeight: 700,
          fontFamily: "'Inter', sans-serif", textTransform: "uppercase", letterSpacing: 1.5,
        }}>{label}</span>
      </div>
    </div>
  );
};
