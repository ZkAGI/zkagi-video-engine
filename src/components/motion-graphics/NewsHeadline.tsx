import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

export interface NewsHeadlineProps {
  /** e.g. "BREAKING" or "TRENDING" */
  tag: string;
  /** Main headline text */
  headline: string;
  /** Optional source attribution */
  source?: string;
  accentColor?: string;
  durationInFrames: number;
}

export const NewsHeadline: React.FC<NewsHeadlineProps> = ({
  tag,
  headline,
  source,
  accentColor = "#EF4444",
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Tag badge pops in
  const tagSpring = spring({ frame, fps, config: { damping: 12, mass: 0.4, stiffness: 180 } });
  const tagScale = interpolate(tagSpring, [0, 1], [0, 1]);

  // Decorative line expands from left
  const lineSpring = spring({ frame: Math.max(0, frame - 5), fps, config: { damping: 20, mass: 0.5, stiffness: 100 } });
  const lineWidth = interpolate(lineSpring, [0, 1], [0, 100]); // percentage

  // Typewriter headline
  const typeDelay = 10;
  const charsPerFrame = headline.length / (durationInFrames * 0.5);
  const visibleChars = Math.min(
    headline.length,
    Math.max(0, Math.floor((frame - typeDelay) * charsPerFrame * 1.5))
  );
  const displayText = frame < typeDelay ? "" : headline.slice(0, visibleChars);
  const showCursor = frame >= typeDelay && visibleChars < headline.length && Math.floor(frame / 4) % 2 === 0;

  // Source slides in
  const sourceSpring = spring({
    frame: Math.max(0, frame - typeDelay - Math.ceil(headline.length / (charsPerFrame * 1.5))),
    fps,
    config: { damping: 16, mass: 0.5, stiffness: 140 },
  });
  const sourceOp = interpolate(sourceSpring, [0, 1], [0, 1]);
  const sourceY = interpolate(sourceSpring, [0, 1], [15, 0]);

  // Exit
  const exitOp = interpolate(frame, [durationInFrames - 15, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "flex-start",
        padding: "0 120px",
        background: "linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 50%, #0a1a2e 100%)",
      }}
    >
      <div style={{ opacity: exitOp, maxWidth: 1400 }}>
        {/* Tag badge */}
        <div
          style={{
            display: "inline-block",
            transform: `scale(${tagScale})`,
            marginBottom: 24,
          }}
        >
          <div
            style={{
              background: accentColor,
              padding: "6px 20px",
              borderRadius: 6,
            }}
          >
            <span
              style={{
                fontFamily: "'Inter', sans-serif",
                fontSize: 18,
                fontWeight: 800,
                color: "#FFFFFF",
                letterSpacing: 3,
                textTransform: "uppercase",
              }}
            >
              {tag}
            </span>
          </div>
        </div>

        {/* Decorative line */}
        <div
          style={{
            width: `${lineWidth}%`,
            height: 2,
            background: `linear-gradient(90deg, ${accentColor}, transparent)`,
            marginBottom: 28,
          }}
        />

        {/* Headline */}
        <div
          style={{
            fontFamily: "'Inter', sans-serif",
            fontSize: 64,
            fontWeight: 800,
            color: "#FFFFFF",
            lineHeight: 1.2,
            minHeight: 160,
          }}
        >
          {displayText}
          {showCursor && (
            <span style={{ color: accentColor }}>|</span>
          )}
        </div>

        {/* Source */}
        {source && (
          <div
            style={{
              fontFamily: "'Inter', sans-serif",
              fontSize: 20,
              fontWeight: 400,
              color: "rgba(255,255,255,0.5)",
              marginTop: 20,
              opacity: sourceOp,
              transform: `translateY(${sourceY}px)`,
            }}
          >
            {source}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
