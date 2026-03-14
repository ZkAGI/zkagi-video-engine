import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";

export const ScreenShake: React.FC<{
  children: React.ReactNode;
  triggerFrame: number;
  intensity?: number;
}> = ({ children, triggerFrame, intensity = 6 }) => {
  const frame = useCurrentFrame();
  const shakeProgress = frame - triggerFrame;

  let x = 0, y = 0;
  if (shakeProgress >= 0 && shakeProgress < 12) {
    const decay = Math.max(0, 1 - shakeProgress / 12);
    x = Math.sin(shakeProgress * 4.5) * intensity * decay;
    y = Math.cos(shakeProgress * 3.7) * intensity * 0.6 * decay;
  }

  return (
    <AbsoluteFill style={{ transform: `translate(${x}px, ${y}px)` }}>
      {children}
    </AbsoluteFill>
  );
};
