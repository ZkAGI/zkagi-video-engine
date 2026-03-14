import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";

export const WordPopSubtitles: React.FC<{
  text: string;
  accentColor: string;
  durationInFrames: number;
  highlightWords?: string[];
}> = ({ text, accentColor, durationInFrames, highlightWords = [] }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = text.split(" ");

  const revealEnd = durationInFrames * 0.85;
  const framesPerWord = revealEnd / words.length;

  const enterSpring = spring({ frame, fps, config: { damping: 15, mass: 0.5, stiffness: 140 } });
  const slideY = interpolate(enterSpring, [0, 1], [40, 0]);
  const enterOp = interpolate(enterSpring, [0, 1], [0, 1]);

  const exitOp = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <div style={{
      position: "absolute",
      bottom: 36,
      left: "50%",
      transform: `translateX(-50%) translateY(${slideY}px)`,
      maxWidth: "65%",
      opacity: enterOp * exitOp,
      zIndex: 50,
    }}>
      <div style={{
        background: "rgba(0,0,0,0.72)",
        backdropFilter: "blur(16px)",
        padding: "8px 18px",
        borderRadius: 10,
        borderLeft: `3px solid ${accentColor}`,
      }}>
        <p style={{
          color: "#FFFFFF",
          fontSize: 22,
          lineHeight: 1.4,
          fontFamily: "'Inter', sans-serif",
          fontWeight: 500,
          margin: 0,
          textAlign: "left",
        }}>
          {words.map((word, i) => {
            const wordFrame = i * framesPerWord;
            const isVisible = frame >= wordFrame;
            if (!isVisible) return null;

            const wordSpring = spring({
              frame: frame - wordFrame,
              fps,
              config: { damping: 12, mass: 0.3, stiffness: 200 },
            });
            const scale = interpolate(wordSpring, [0, 1], [0.6, 1]);
            const wordOp = interpolate(wordSpring, [0, 1], [0, 1]);

            const isHighlight = highlightWords.some(hw =>
              word.toLowerCase().replace(/[.,?!'"]/g, "").includes(hw.toLowerCase())
            );

            return (
              <span key={i} style={{
                display: "inline-block",
                transform: `scale(${scale})`,
                opacity: wordOp,
                color: isHighlight ? accentColor : "#FFFFFF",
                fontWeight: isHighlight ? 800 : 500,
                textShadow: isHighlight ? `0 0 14px ${accentColor}50` : "none",
                marginRight: 5,
              }}>
                {word}
              </span>
            );
          })}
        </p>
      </div>
    </div>
  );
};
