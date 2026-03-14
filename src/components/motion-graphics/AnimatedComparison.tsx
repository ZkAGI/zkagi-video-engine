import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

export interface ComparisonSide {
  title: string;
  items: string[];
  color?: string;
}

export interface AnimatedComparisonProps {
  /** Left side (e.g. "Before" or "Traditional") */
  left: ComparisonSide;
  /** Right side (e.g. "After" or "ZkAGI") */
  right: ComparisonSide;
  accentColor?: string;
  durationInFrames: number;
}

export const AnimatedComparison: React.FC<AnimatedComparisonProps> = ({
  left,
  right,
  accentColor = "#7C3AED",
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const leftColor = left.color || "#EF4444";
  const rightColor = right.color || "#10B981";

  // Center divider draws down
  const dividerSpring = spring({ frame, fps, config: { damping: 20, mass: 0.6, stiffness: 100 } });
  const dividerHeight = interpolate(dividerSpring, [0, 1], [0, 100]); // percentage

  // Left side slides in
  const leftSpring = spring({ frame: Math.max(0, frame - 8), fps, config: { damping: 14, mass: 0.5, stiffness: 140 } });
  const leftX = interpolate(leftSpring, [0, 1], [-80, 0]);
  const leftOp = interpolate(leftSpring, [0, 1], [0, 1]);

  // Right side slides in
  const rightSpring = spring({ frame: Math.max(0, frame - 8), fps, config: { damping: 14, mass: 0.5, stiffness: 140 } });
  const rightX = interpolate(rightSpring, [0, 1], [80, 0]);
  const rightOp = interpolate(rightSpring, [0, 1], [0, 1]);

  // Exit
  const exitOp = interpolate(frame, [durationInFrames - 15, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const renderSide = (side: ComparisonSide, sideColor: string, slideX: number, sideOp: number, startDelay: number) => (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 20,
        transform: `translateX(${slideX}px)`,
        opacity: sideOp,
        padding: "0 40px",
      }}
    >
      {/* Title */}
      <div
        style={{
          fontFamily: "'Inter', sans-serif",
          fontSize: 36,
          fontWeight: 800,
          color: sideColor,
          textTransform: "uppercase",
          letterSpacing: 2,
          marginBottom: 8,
        }}
      >
        {side.title}
      </div>

      {/* Items */}
      {side.items.map((item, i) => {
        const itemSpring = spring({
          frame: Math.max(0, frame - startDelay - i * 6),
          fps,
          config: { damping: 14, mass: 0.4, stiffness: 160 },
        });
        const itemOp = interpolate(itemSpring, [0, 1], [0, 1]);
        const itemScale = interpolate(itemSpring, [0, 1], [0.7, 1]);

        return (
          <div
            key={i}
            style={{
              opacity: itemOp,
              transform: `scale(${itemScale})`,
              background: `${sideColor}10`,
              border: `1px solid ${sideColor}30`,
              borderRadius: 10,
              padding: "10px 24px",
              width: "100%",
              maxWidth: 360,
              textAlign: "center",
            }}
          >
            <span
              style={{
                fontFamily: "'Inter', sans-serif",
                fontSize: 22,
                fontWeight: 500,
                color: "rgba(255,255,255,0.9)",
              }}
            >
              {item}
            </span>
          </div>
        );
      })}
    </div>
  );

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
          alignItems: "flex-start",
          width: "100%",
          maxWidth: 1600,
          padding: "0 60px",
          opacity: exitOp,
        }}
      >
        {/* Left side */}
        {renderSide(left, leftColor, leftX, leftOp, 15)}

        {/* Center divider */}
        <div
          style={{
            width: 3,
            height: `${dividerHeight}%`,
            minHeight: 0,
            maxHeight: 500,
            background: `linear-gradient(180deg, ${accentColor}, transparent)`,
            margin: "0 20px",
            flexShrink: 0,
          }}
        />

        {/* Right side */}
        {renderSide(right, rightColor, rightX, rightOp, 15)}
      </div>
    </AbsoluteFill>
  );
};
