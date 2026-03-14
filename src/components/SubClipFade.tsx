import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";

export const SubClipFade: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const mid = durationInFrames / 2;
  const opacity = frame < mid
    ? interpolate(frame, [0, mid], [0, 0.5], { extrapolateRight: "clamp" })
    : interpolate(frame, [mid, durationInFrames], [0.5, 0], { extrapolateRight: "clamp" });
  return <AbsoluteFill style={{ backgroundColor: "#0a0a1a", opacity, zIndex: 30 }} />;
};
