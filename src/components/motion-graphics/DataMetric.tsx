import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

export interface DataMetricProps {
  /** e.g. "$140B" */
  value: string;
  /** e.g. "Lost to crypto hacks since 2017" */
  label: string;
  /** Optional sub-label */
  sublabel?: string;
  accentColor?: string;
  durationInFrames: number;
}

export const DataMetric: React.FC<DataMetricProps> = ({
  value,
  label,
  sublabel,
  accentColor = "#7C3AED",
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Number counts up with easing
  const countSpring = spring({ frame, fps, config: { damping: 30, mass: 1.0, stiffness: 60 } });

  // Parse the numeric portion for counter animation
  const match = value.match(/^([^0-9]*)([0-9,.]+)(.*)$/);
  let displayValue = value;
  if (match) {
    const prefix = match[1];
    const num = parseFloat(match[2].replace(/,/g, ""));
    const suffix = match[3];
    const current = num * countSpring;

    // Preserve decimal formatting
    if (match[2].includes(".")) {
      const decimals = match[2].split(".")[1].length;
      displayValue = `${prefix}${current.toFixed(decimals)}${suffix}`;
    } else {
      displayValue = `${prefix}${Math.round(current).toLocaleString()}${suffix}`;
    }

    if (countSpring > 0.98) displayValue = value;
  }

  // Value scale pop
  const valueSpring = spring({ frame, fps, config: { damping: 12, mass: 0.5, stiffness: 150 } });
  const valueScale = interpolate(valueSpring, [0, 1], [0.5, 1]);
  const valueOp = interpolate(valueSpring, [0, 1], [0, 1]);

  // Label slides in from bottom
  const labelSpring = spring({ frame: Math.max(0, frame - 15), fps, config: { damping: 16, mass: 0.5, stiffness: 140 } });
  const labelY = interpolate(labelSpring, [0, 1], [30, 0]);
  const labelOp = interpolate(labelSpring, [0, 1], [0, 1]);

  // Sublabel fades in
  const subSpring = spring({ frame: Math.max(0, frame - 25), fps, config: { damping: 18, mass: 0.6, stiffness: 120 } });
  const subOp = interpolate(subSpring, [0, 1], [0, 1]);

  // Decorative line expands
  const lineSpring = spring({ frame: Math.max(0, frame - 8), fps, config: { damping: 20, mass: 0.4, stiffness: 120 } });
  const lineWidth = interpolate(lineSpring, [0, 1], [0, 200]);

  // Exit
  const exitOp = interpolate(frame, [durationInFrames - 15, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        background: "linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 50%, #0a1a2e 100%)",
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 20,
          opacity: exitOp,
        }}
      >
        {/* Big number */}
        <div
          style={{
            fontFamily: "'Inter', sans-serif",
            fontSize: 120,
            fontWeight: 900,
            color: "#FFFFFF",
            transform: `scale(${valueScale})`,
            opacity: valueOp,
            textShadow: `0 0 30px ${accentColor}40`,
            letterSpacing: -3,
          }}
        >
          {displayValue}
        </div>

        {/* Decorative line */}
        <div
          style={{
            width: lineWidth,
            height: 3,
            background: `linear-gradient(90deg, transparent, ${accentColor}, transparent)`,
            borderRadius: 2,
          }}
        />

        {/* Label */}
        <div
          style={{
            fontFamily: "'Inter', sans-serif",
            fontSize: 32,
            fontWeight: 500,
            color: "rgba(255,255,255,0.8)",
            transform: `translateY(${labelY}px)`,
            opacity: labelOp,
            maxWidth: 800,
            textAlign: "center",
            lineHeight: 1.4,
          }}
        >
          {label}
        </div>

        {/* Sublabel */}
        {sublabel && (
          <div
            style={{
              fontFamily: "'Inter', sans-serif",
              fontSize: 22,
              fontWeight: 400,
              color: accentColor,
              opacity: subOp,
              marginTop: 4,
            }}
          >
            {sublabel}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
