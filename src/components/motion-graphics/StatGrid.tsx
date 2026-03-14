import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

export interface StatItem {
  value: string;
  label: string;
}

export interface StatGridProps {
  /** Optional title above the grid */
  title?: string;
  /** 2-4 stat items */
  stats: StatItem[];
  accentColor?: string;
  durationInFrames: number;
}

export const StatGrid: React.FC<StatGridProps> = ({
  title,
  stats,
  accentColor = "#7C3AED",
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Title entry
  const titleSpring = spring({ frame, fps, config: { damping: 16, mass: 0.5, stiffness: 140 } });
  const titleOp = interpolate(titleSpring, [0, 1], [0, 1]);
  const titleY = interpolate(titleSpring, [0, 1], [-20, 0]);

  // Exit
  const exitOp = interpolate(frame, [durationInFrames - 15, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const columns = stats.length <= 2 ? stats.length : stats.length <= 4 ? 2 : 3;

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
          gap: 40,
          opacity: exitOp,
        }}
      >
        {/* Title */}
        {title && (
          <div
            style={{
              fontFamily: "'Inter', sans-serif",
              fontSize: 40,
              fontWeight: 700,
              color: "#FFFFFF",
              opacity: titleOp,
              transform: `translateY(${titleY}px)`,
              textAlign: "center",
            }}
          >
            {title}
          </div>
        )}

        {/* Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: `repeat(${columns}, 1fr)`,
            gap: 28,
          }}
        >
          {stats.map((stat, i) => {
            const cardSpring = spring({
              frame: Math.max(0, frame - 8 - i * 6),
              fps,
              config: { damping: 12, mass: 0.4, stiffness: 160 },
            });
            const cardScale = interpolate(cardSpring, [0, 1], [0.5, 1]);
            const cardOp = interpolate(cardSpring, [0, 1], [0, 1]);

            // Count up animation for value
            const countSpring = spring({
              frame: Math.max(0, frame - 8 - i * 6),
              fps,
              config: { damping: 30, mass: 1.0, stiffness: 60 },
            });

            const numMatch = stat.value.match(/^([^0-9]*)([0-9,.]+)(.*)$/);
            let displayValue = stat.value;
            if (numMatch) {
              const prefix = numMatch[1];
              const num = parseFloat(numMatch[2].replace(/,/g, ""));
              const suffix = numMatch[3];
              const current = num * countSpring;
              if (numMatch[2].includes(".")) {
                const decimals = numMatch[2].split(".")[1].length;
                displayValue = `${prefix}${current.toFixed(decimals)}${suffix}`;
              } else {
                displayValue = `${prefix}${Math.round(current).toLocaleString()}${suffix}`;
              }
              if (countSpring > 0.98) displayValue = stat.value;
            }

            return (
              <div
                key={i}
                style={{
                  transform: `scale(${cardScale})`,
                  opacity: cardOp,
                  background: "rgba(255,255,255,0.04)",
                  border: `1px solid ${accentColor}30`,
                  borderRadius: 16,
                  padding: "28px 40px",
                  minWidth: 240,
                  textAlign: "center",
                }}
              >
                <div
                  style={{
                    fontFamily: "'Inter', sans-serif",
                    fontSize: 52,
                    fontWeight: 900,
                    color: "#FFFFFF",
                    marginBottom: 8,
                  }}
                >
                  {displayValue}
                </div>
                <div
                  style={{
                    fontFamily: "'Inter', sans-serif",
                    fontSize: 18,
                    fontWeight: 500,
                    color: accentColor,
                    textTransform: "uppercase",
                    letterSpacing: 1,
                  }}
                >
                  {stat.label}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
