import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

export interface ProductShowcaseProps {
  /** Product name e.g. "PawPad" */
  name: string;
  /** Tagline e.g. "The seedless crypto wallet" */
  tagline: string;
  /** Feature bullet points */
  features: string[];
  /** Product URL for CTA */
  url: string;
  accentColor?: string;
  durationInFrames: number;
}

export const ProductShowcase: React.FC<ProductShowcaseProps> = ({
  name,
  tagline,
  features,
  url,
  accentColor = "#7C3AED",
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Name springs in
  const nameSpring = spring({ frame, fps, config: { damping: 12, mass: 0.5, stiffness: 150 } });
  const nameScale = interpolate(nameSpring, [0, 1], [0.3, 1]);
  const nameOp = interpolate(nameSpring, [0, 1], [0, 1]);

  // Tagline slides up
  const tagSpring = spring({ frame: Math.max(0, frame - 10), fps, config: { damping: 16, mass: 0.5, stiffness: 140 } });
  const tagY = interpolate(tagSpring, [0, 1], [20, 0]);
  const tagOp = interpolate(tagSpring, [0, 1], [0, 1]);

  // URL glow pulse
  const urlSpring = spring({
    frame: Math.max(0, frame - 15 - features.length * 8),
    fps,
    config: { damping: 14, mass: 0.5, stiffness: 120 },
  });
  const urlOp = interpolate(urlSpring, [0, 1], [0, 1]);
  const urlScale = interpolate(urlSpring, [0, 1], [0.8, 1]);
  const glowPulse = Math.sin(frame * 0.1) * 0.3 + 0.7;

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
        {/* Product name */}
        <div
          style={{
            fontFamily: "'Inter', sans-serif",
            fontSize: 80,
            fontWeight: 900,
            color: "#FFFFFF",
            transform: `scale(${nameScale})`,
            opacity: nameOp,
            textShadow: `0 0 40px ${accentColor}50`,
          }}
        >
          {name}
        </div>

        {/* Tagline */}
        <div
          style={{
            fontFamily: "'Inter', sans-serif",
            fontSize: 28,
            fontWeight: 400,
            color: "rgba(255,255,255,0.7)",
            transform: `translateY(${tagY}px)`,
            opacity: tagOp,
            marginBottom: 16,
          }}
        >
          {tagline}
        </div>

        {/* Features — pop in one by one */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12, alignItems: "center" }}>
          {features.map((feature, i) => {
            const fSpring = spring({
              frame: Math.max(0, frame - 18 - i * 8),
              fps,
              config: { damping: 14, mass: 0.4, stiffness: 160 },
            });
            const fScale = interpolate(fSpring, [0, 1], [0.6, 1]);
            const fOp = interpolate(fSpring, [0, 1], [0, 1]);

            return (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  transform: `scale(${fScale})`,
                  opacity: fOp,
                }}
              >
                <div
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    background: accentColor,
                    boxShadow: `0 0 8px ${accentColor}`,
                  }}
                />
                <span
                  style={{
                    fontFamily: "'Inter', sans-serif",
                    fontSize: 26,
                    fontWeight: 500,
                    color: "rgba(255,255,255,0.9)",
                  }}
                >
                  {feature}
                </span>
              </div>
            );
          })}
        </div>

        {/* URL CTA with glow */}
        <div
          style={{
            marginTop: 28,
            transform: `scale(${urlScale})`,
            opacity: urlOp,
          }}
        >
          <div
            style={{
              background: `${accentColor}20`,
              border: `2px solid ${accentColor}90`,
              padding: "14px 44px",
              borderRadius: 14,
              boxShadow: `0 0 ${30 * glowPulse}px ${accentColor}40, 0 0 ${60 * glowPulse}px ${accentColor}20`,
            }}
          >
            <span
              style={{
                fontFamily: "'Inter', sans-serif",
                fontSize: 32,
                fontWeight: 800,
                color: "#FFFFFF",
                letterSpacing: 1,
                textShadow: `0 0 12px ${accentColor}60`,
              }}
            >
              {url}
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
