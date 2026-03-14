import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  interpolate,
  staticFile,
  Img,
} from "remotion";

export const KenBurnsImage: React.FC<{
  imagePath: string;
  durationInFrames: number;
  fadeIn?: number;
  direction?: "zoom-in" | "zoom-out" | "pan-left" | "pan-right" | "pan-up";
}> = ({ imagePath, durationInFrames, fadeIn = 8, direction = "zoom-in" }) => {
  const frame = useCurrentFrame();
  const progress = frame / durationInFrames;

  const fadeOpacity = fadeIn > 0
    ? interpolate(frame, [0, fadeIn], [0, 1], { extrapolateRight: "clamp" })
    : 1;

  let scale = 1;
  let translateX = 0;
  let translateY = 0;

  switch (direction) {
    case "zoom-in":
      scale = 1.0 + progress * 0.15;
      break;
    case "zoom-out":
      scale = 1.15 - progress * 0.15;
      break;
    case "pan-left":
      scale = 1.1;
      translateX = -progress * 5;
      break;
    case "pan-right":
      scale = 1.1;
      translateX = progress * 5;
      break;
    case "pan-up":
      scale = 1.1;
      translateY = -progress * 4;
      break;
  }

  return (
    <AbsoluteFill>
      <Img
        src={staticFile(imagePath)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          opacity: fadeOpacity,
          transform: `scale(${scale}) translate(${translateX}%, ${translateY}%)`,
        }}
      />
    </AbsoluteFill>
  );
};
