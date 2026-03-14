import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

export interface PriceTickerProps {
  /** e.g. "BTC" */
  symbol: string;
  /** e.g. "$118,520" */
  price: string;
  /** e.g. "+4.2%" or "-1.8%" */
  change: string;
  /** true = green/up, false = red/down */
  isPositive: boolean;
  /** Accent color for the border/glow */
  accentColor?: string;
  durationInFrames: number;
}

export const PriceTicker: React.FC<PriceTickerProps> = ({
  symbol,
  price,
  change,
  isPositive,
  accentColor = "#7C3AED",
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Container fade in
  const containerSpring = spring({ frame, fps, config: { damping: 18, mass: 0.6, stiffness: 120 } });
  const containerScale = interpolate(containerSpring, [0, 1], [0.8, 1]);
  const containerOp = interpolate(containerSpring, [0, 1], [0, 1]);

  // Symbol slides in from left
  const symbolSpring = spring({ frame: Math.max(0, frame - 5), fps, config: { damping: 14, mass: 0.4, stiffness: 160 } });
  const symbolX = interpolate(symbolSpring, [0, 1], [-40, 0]);

  // Price counter roll effect
  const priceSpring = spring({ frame: Math.max(0, frame - 10), fps, config: { damping: 20, mass: 0.8, stiffness: 100 } });
  const priceOp = interpolate(priceSpring, [0, 1], [0, 1]);

  // Parse numeric value from price for counter animation
  const numericPrice = parseFloat(price.replace(/[^0-9.]/g, ""));
  const displayValue = Math.round(numericPrice * priceSpring);
  const formattedPrice = price.startsWith("$")
    ? `$${displayValue.toLocaleString()}`
    : displayValue.toLocaleString();
  const finalPrice = priceSpring > 0.98 ? price : formattedPrice;

  // Arrow bounce
  const arrowSpring = spring({ frame: Math.max(0, frame - 20), fps, config: { damping: 8, mass: 0.3, stiffness: 200 } });
  const arrowY = interpolate(arrowSpring, [0, 1], [isPositive ? 20 : -20, 0]);

  // Change % fades in
  const changeSpring = spring({ frame: Math.max(0, frame - 25), fps, config: { damping: 16, mass: 0.5, stiffness: 140 } });
  const changeOp = interpolate(changeSpring, [0, 1], [0, 1]);

  // Exit
  const exitOp = interpolate(frame, [durationInFrames - 15, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const changeColor = isPositive ? "#10B981" : "#EF4444";
  const arrow = isPositive ? "\u25B2" : "\u25BC";

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
          transform: `scale(${containerScale})`,
          opacity: containerOp * exitOp,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 24,
        }}
      >
        {/* Symbol */}
        <div
          style={{
            transform: `translateX(${symbolX}px)`,
            fontFamily: "'Inter', sans-serif",
            fontSize: 48,
            fontWeight: 800,
            color: accentColor,
            letterSpacing: 4,
            textShadow: `0 0 20px ${accentColor}40`,
          }}
        >
          {symbol}
        </div>

        {/* Price card */}
        <div
          style={{
            background: "rgba(255,255,255,0.05)",
            border: `2px solid ${accentColor}60`,
            borderRadius: 20,
            padding: "32px 64px",
            backdropFilter: "blur(16px)",
            boxShadow: `0 0 40px ${accentColor}20`,
          }}
        >
          <div
            style={{
              fontFamily: "'Inter', sans-serif",
              fontSize: 96,
              fontWeight: 900,
              color: "#FFFFFF",
              opacity: priceOp,
              letterSpacing: -2,
            }}
          >
            {finalPrice}
          </div>
        </div>

        {/* Change row */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            opacity: changeOp,
          }}
        >
          <span
            style={{
              transform: `translateY(${arrowY}px)`,
              fontSize: 32,
              color: changeColor,
              display: "inline-block",
            }}
          >
            {arrow}
          </span>
          <span
            style={{
              fontFamily: "'Inter', sans-serif",
              fontSize: 40,
              fontWeight: 700,
              color: changeColor,
            }}
          >
            {change}
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
