import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";

export const CtaUrl: React.FC<{
  url: string;
  color: string;
  triggerFrame: number;
  durationInFrames: number;
}> = ({ url, color, triggerFrame, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const localFrame = frame - triggerFrame;
  if (localFrame < 0) return null;

  const popSpring = spring({ frame: localFrame, fps, config: { damping: 10, mass: 0.5, stiffness: 120 } });
  const scale = interpolate(popSpring, [0, 1], [0.3, 1]);
  const opacity = interpolate(popSpring, [0, 1], [0, 1]);
  const glowPulse = Math.sin(localFrame * 0.15) * 0.3 + 0.7;
  const exitOp = interpolate(frame, [durationInFrames - 15, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <div style={{
      position: "absolute", top: "35%", left: "50%",
      transform: `translateX(-50%) scale(${scale})`, opacity: opacity * exitOp, zIndex: 60,
    }}>
      <div style={{
        background: `${color}20`, border: `2px solid ${color}90`,
        padding: "12px 36px", borderRadius: 14, backdropFilter: "blur(12px)",
        boxShadow: `0 0 ${30 * glowPulse}px ${color}40, 0 0 ${60 * glowPulse}px ${color}20`,
      }}>
        <span style={{
          color: "#FFFFFF", fontSize: 28, fontWeight: 800,
          fontFamily: "'Inter', sans-serif", letterSpacing: 1,
          textShadow: `0 0 12px ${color}60`,
        }}>{url}</span>
      </div>
    </div>
  );
};
