import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring, Img, staticFile } from "remotion";
import { Character, Emotion } from "../types";

export const CharacterDisplay: React.FC<{
  character: Character;
  emotion: Emotion;
  size?: number;
  position?: "left" | "center" | "right";
  showName?: boolean;
  nameColor?: string;
  nameBadgeBg?: string;
}> = ({ character, emotion, size = 350, position = "left", showName = true, nameColor, nameBadgeBg }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const poseUrl = character.poses[emotion] || character.poses["neutral"];
  const entrance = spring({ frame, fps, config: { damping: 14, mass: 0.8 } });
  const slideY = interpolate(entrance, [0, 1], [60, 0]);
  const opacity = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const breathe = Math.sin(frame / 20) * 3;

  const posX = position === "left" ? "8%" : position === "right" ? "72%" : "50%";
  const translateX = position === "center" ? "-50%" : "0";

  return (
    <div style={{
      position: "absolute", bottom: 60, left: posX,
      transform: `translateX(${translateX}) translateY(${slideY + breathe}px)`,
      opacity, display: "flex", flexDirection: "column", alignItems: "center",
    }}>
      <Img src={staticFile(poseUrl)} style={{
        width: size, height: size, objectFit: "contain",
        filter: "drop-shadow(0 8px 24px rgba(0,0,0,0.4))",
      }} />
      {showName && (
        <div style={{
          marginTop: 8, padding: "6px 20px", borderRadius: 20,
          background: nameBadgeBg || "rgba(124,58,237,0.2)",
          border: `1.5px solid ${character.color}`,
        }}>
          <span style={{
            color: nameColor || character.color, fontSize: 18,
            fontWeight: 700, fontFamily: "'Inter', sans-serif",
          }}>{character.name}</span>
        </div>
      )}
    </div>
  );
};
