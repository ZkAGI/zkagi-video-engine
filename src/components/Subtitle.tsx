import React from "react";
import { useCurrentFrame, interpolate } from "remotion";

export const Subtitle: React.FC<{
  text: string;
  durationInFrames: number;
  bgColor?: string;
  textColor?: string;
  accentColor?: string;
  highlightText?: string;
}> = ({ text, durationInFrames, bgColor = "rgba(10,10,26,0.85)", textColor = "#FFF", accentColor = "#7C3AED", highlightText }) => {
  const frame = useCurrentFrame();
  const words = text.split(" ");
  const wordsToShow = Math.min(words.length, Math.floor((frame / durationInFrames) * words.length * 1.3) + 1);
  const fadeIn = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = interpolate(frame, [durationInFrames - 15, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <div style={{ position: "absolute", bottom: 50, left: "50%", transform: "translateX(-50%)", maxWidth: "75%", opacity: fadeIn * fadeOut }}>
      <div style={{
        background: bgColor, padding: "18px 36px", borderRadius: 16,
        borderLeft: `4px solid ${accentColor}`, backdropFilter: "blur(12px)",
        boxShadow: "0 8px 32px rgba(0,0,0,0.3)",
      }}>
        <p style={{ color: textColor, fontSize: 34, lineHeight: 1.5, fontFamily: "'Inter', sans-serif", fontWeight: 500, margin: 0 }}>
          {words.slice(0, wordsToShow).map((word, i) => {
            const isHL = highlightText?.toLowerCase().includes(word.toLowerCase());
            return <span key={i} style={{ color: isHL ? accentColor : textColor, fontWeight: isHL ? 800 : 500 }}>{word} </span>;
          })}
        </p>
      </div>
    </div>
  );
};
