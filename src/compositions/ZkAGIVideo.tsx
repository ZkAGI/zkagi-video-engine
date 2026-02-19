import React from "react";
import {
  AbsoluteFill,
  Audio,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  staticFile,
  Easing,
  Img,
} from "remotion";
import { VideoConfig, Scene, Emotion } from "../types";
import { Watermark } from "../components/Watermark";
import { getTheme, Theme } from "../lib/themes";

// ═══════════════════════════════════════════════════════════════
// Scene Background with Ken Burns effect
// ═══════════════════════════════════════════════════════════════
const SceneBackground: React.FC<{
  sceneIndex: number;
  durationInFrames: number;
  backgroundUrl?: string;
}> = ({ sceneIndex, durationInFrames, backgroundUrl }) => {
  const frame = useCurrentFrame();

  // Ken Burns zoom effect - slow zoom in
  const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.15], {
    extrapolateRight: "clamp",
  });

  // Subtle pan
  const panX = interpolate(frame, [0, durationInFrames], [0, -3], {
    extrapolateRight: "clamp",
  });
  const panY = interpolate(frame, [0, durationInFrames], [0, -2], {
    extrapolateRight: "clamp",
  });

  // Fade in
  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  const imagePath = backgroundUrl || `scenes/scene-${sceneIndex}.png`;

  return (
    <AbsoluteFill>
      {/* AI-generated scene background */}
      <Img
        src={staticFile(imagePath)}
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale}) translate(${panX}%, ${panY}%)`,
          opacity,
        }}
      />

      {/* Gradient overlay for text readability */}
      <div
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          background: `linear-gradient(180deg, rgba(0,0,0,0.2) 0%, rgba(0,0,0,0.1) 40%, rgba(0,0,0,0.6) 100%)`,
        }}
      />

      {/* Subtle vignette */}
      <div
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          background: `radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.4) 100%)`,
        }}
      />
    </AbsoluteFill>
  );
};

// ═══════════════════════════════════════════════════════════════
// Animated Gradient Background (fallback)
// ═══════════════════════════════════════════════════════════════
const AnimatedBackground: React.FC<{
  theme: Theme;
  sceneIndex: number;
}> = ({ theme, sceneIndex }) => {
  const frame = useCurrentFrame();

  // Subtle gradient rotation and shift
  const gradientAngle = interpolate(frame, [0, 300], [135 + sceneIndex * 15, 180 + sceneIndex * 15], {
    extrapolateRight: "clamp",
  });

  // Pulsing glow effect
  const glowIntensity = 0.3 + Math.sin(frame / 40) * 0.1;
  const glowSize = 40 + Math.sin(frame / 25) * 10;

  return (
    <AbsoluteFill>
      {/* Base gradient */}
      <div
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          background: `linear-gradient(${gradientAngle}deg, #0f172a 0%, #1e1b4b 40%, #0c4a6e 100%)`,
        }}
      />

      {/* Animated orbs */}
      <div
        style={{
          position: "absolute",
          top: "20%",
          left: "10%",
          width: 400,
          height: 400,
          borderRadius: "50%",
          background: `radial-gradient(circle, rgba(124,58,237,${glowIntensity}) 0%, transparent 70%)`,
          filter: `blur(${glowSize}px)`,
          transform: `translate(${Math.sin(frame / 50) * 30}px, ${Math.cos(frame / 40) * 20}px)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: "15%",
          right: "15%",
          width: 350,
          height: 350,
          borderRadius: "50%",
          background: `radial-gradient(circle, rgba(6,182,212,${glowIntensity * 0.8}) 0%, transparent 70%)`,
          filter: `blur(${glowSize * 1.2}px)`,
          transform: `translate(${Math.cos(frame / 45) * 25}px, ${Math.sin(frame / 35) * 25}px)`,
        }}
      />

      {/* Grid overlay for tech feel */}
      <div
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          backgroundImage: `
            linear-gradient(rgba(124,58,237,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(124,58,237,0.03) 1px, transparent 1px)
          `,
          backgroundSize: "60px 60px",
          opacity: 0.5,
        }}
      />
    </AbsoluteFill>
  );
};

// ═══════════════════════════════════════════════════════════════
// Kinetic Typography - Animated words with spring physics
// ═══════════════════════════════════════════════════════════════
const KineticTypography: React.FC<{
  text: string;
  highlightText?: string;
  durationInFrames: number;
  accentColor: string;
}> = ({ text, highlightText, durationInFrames, accentColor }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = text.split(" ");

  // Calculate how many words to show
  const wordsPerFrame = words.length / (durationInFrames * 0.7);
  const currentWordCount = Math.min(words.length, Math.floor(frame * wordsPerFrame) + 1);

  // Container spring animation
  const containerSpring = spring({
    frame,
    fps,
    config: { damping: 20, mass: 0.8, stiffness: 100 },
  });

  const containerY = interpolate(containerSpring, [0, 1], [30, 0]);
  const containerOpacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 20, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        position: "absolute",
        bottom: 80,
        left: "50%",
        transform: `translateX(-50%) translateY(${containerY}px)`,
        maxWidth: "80%",
        opacity: containerOpacity * fadeOut,
      }}
    >
      <div
        style={{
          background: "rgba(15,23,42,0.9)",
          backdropFilter: "blur(20px)",
          padding: "24px 48px",
          borderRadius: 20,
          borderLeft: `5px solid ${accentColor}`,
          boxShadow: `0 20px 60px rgba(0,0,0,0.4), 0 0 40px ${accentColor}20`,
        }}
      >
        <p
          style={{
            color: "#FFFFFF",
            fontSize: 38,
            lineHeight: 1.6,
            fontFamily: "'Inter', sans-serif",
            fontWeight: 500,
            margin: 0,
            display: "flex",
            flexWrap: "wrap",
            gap: "0.3em",
          }}
        >
          {words.slice(0, currentWordCount).map((word, i) => {
            const wordFrame = Math.max(0, frame - i / wordsPerFrame);
            const wordSpring = spring({
              frame: wordFrame,
              fps,
              config: { damping: 12, mass: 0.5, stiffness: 200 },
            });

            const isHighlight = highlightText?.toLowerCase().includes(word.toLowerCase().replace(/[!?,.]/, ""));
            const scale = interpolate(wordSpring, [0, 1], [0.5, 1]);
            const opacity = interpolate(wordSpring, [0, 1], [0, 1]);
            const y = interpolate(wordSpring, [0, 1], [20, 0]);

            return (
              <span
                key={i}
                style={{
                  display: "inline-block",
                  color: isHighlight ? accentColor : "#FFFFFF",
                  fontWeight: isHighlight ? 800 : 500,
                  transform: `scale(${scale}) translateY(${y}px)`,
                  opacity,
                  textShadow: isHighlight ? `0 0 20px ${accentColor}60` : "none",
                }}
              >
                {word}
              </span>
            );
          })}
        </p>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
// Animated Character with bounce/zoom effects
// ═══════════════════════════════════════════════════════════════
const AnimatedCharacter: React.FC<{
  characterId: string;
  poseUrl: string;
  emotion: Emotion;
  characterName: string;
  characterColor: string;
  size: number;
  position: "left" | "center" | "right";
  durationInFrames: number;
}> = ({ poseUrl, emotion, characterName, characterColor, size, position, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Entrance spring animation
  const entranceSpring = spring({
    frame,
    fps,
    config: { damping: 12, mass: 1, stiffness: 80 },
  });

  // Bounce effect on entrance
  const bounceY = interpolate(entranceSpring, [0, 1], [100, 0]);
  const bounceScale = interpolate(
    entranceSpring,
    [0, 0.5, 0.8, 1],
    [0.3, 1.1, 0.95, 1]
  );

  // Subtle breathing/idle animation
  const breathe = Math.sin(frame / 25) * 4;
  const sway = Math.sin(frame / 40) * 2;

  // Exit animation
  const exitStart = durationInFrames - 15;
  const exitProgress = interpolate(
    frame,
    [exitStart, durationInFrames],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const exitScale = interpolate(exitProgress, [0, 1], [1, 0.8]);
  const exitOpacity = interpolate(exitProgress, [0, 1], [1, 0]);

  // Emotion-based animations
  const emotionBounce = emotion === "excited" || emotion === "celebrating"
    ? Math.abs(Math.sin(frame / 8)) * 8
    : 0;

  // Position calculations
  const posX = position === "left" ? "8%" : position === "right" ? "72%" : "50%";
  const translateX = position === "center" ? "-50%" : "0";

  // Glow effect matching character color
  const glowPulse = 0.4 + Math.sin(frame / 20) * 0.2;

  return (
    <div
      style={{
        position: "absolute",
        bottom: 80,
        left: posX,
        transform: `
          translateX(${translateX})
          translateY(${bounceY + breathe + emotionBounce}px)
          scale(${bounceScale * exitScale})
          rotate(${sway}deg)
        `,
        opacity: exitOpacity,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      {/* Character glow */}
      <div
        style={{
          position: "absolute",
          width: size * 0.8,
          height: size * 0.3,
          bottom: -20,
          borderRadius: "50%",
          background: `radial-gradient(ellipse, ${characterColor}${Math.round(glowPulse * 50).toString(16).padStart(2, "0")} 0%, transparent 70%)`,
          filter: "blur(25px)",
        }}
      />

      {/* Character image */}
      <Img
        src={staticFile(poseUrl)}
        style={{
          width: size,
          height: size,
          objectFit: "contain",
          filter: `drop-shadow(0 15px 40px rgba(0,0,0,0.5)) drop-shadow(0 0 30px ${characterColor}30)`,
        }}
      />

      {/* Name badge */}
      <div
        style={{
          marginTop: 12,
          padding: "8px 24px",
          borderRadius: 24,
          background: `linear-gradient(135deg, ${characterColor}30, ${characterColor}10)`,
          border: `2px solid ${characterColor}`,
          backdropFilter: "blur(10px)",
          boxShadow: `0 4px 20px ${characterColor}30`,
        }}
      >
        <span
          style={{
            color: characterColor,
            fontSize: 20,
            fontWeight: 700,
            fontFamily: "'Inter', sans-serif",
            textShadow: `0 0 10px ${characterColor}50`,
          }}
        >
          {characterName}
        </span>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
// Highlight Text - Large animated title
// ═══════════════════════════════════════════════════════════════
const HighlightTitle: React.FC<{
  text: string;
  position: "center" | "right";
  accentColor: string;
  durationInFrames: number;
}> = ({ text, position, accentColor, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enterSpring = spring({
    frame,
    fps,
    config: { damping: 15, mass: 1.2, stiffness: 100 },
  });

  const scale = interpolate(enterSpring, [0, 1], [0.5, 1]);
  const y = interpolate(enterSpring, [0, 1], [-50, 0]);
  const opacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 15, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Shimmer effect
  const shimmerX = interpolate(frame, [0, 60], [-200, 200], {
    extrapolateRight: "extend",
  }) % 400;

  const leftPos = position === "right" ? "55%" : "50%";

  return (
    <div
      style={{
        position: "absolute",
        top: "18%",
        left: leftPos,
        transform: `translateX(-50%) translateY(${y}px) scale(${scale})`,
        opacity: opacity * fadeOut,
      }}
    >
      <h1
        style={{
          color: "#FFFFFF",
          fontSize: 72,
          fontWeight: 900,
          fontFamily: "'Inter', sans-serif",
          textAlign: "center",
          lineHeight: 1.2,
          margin: 0,
          textShadow: `
            0 4px 30px rgba(0,0,0,0.5),
            0 0 60px ${accentColor}40
          `,
          background: `linear-gradient(90deg, #FFFFFF 0%, ${accentColor} 50%, #FFFFFF 100%)`,
          backgroundSize: "200% 100%",
          backgroundPosition: `${shimmerX}px 0`,
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          backgroundClip: "text",
        }}
      >
        {text}
      </h1>

      {/* Underline accent */}
      <div
        style={{
          marginTop: 12,
          height: 4,
          borderRadius: 2,
          background: `linear-gradient(90deg, transparent, ${accentColor}, transparent)`,
          transform: `scaleX(${enterSpring})`,
        }}
      />
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
// Scene Transition Overlay
// ═══════════════════════════════════════════════════════════════
const SceneTransition: React.FC<{
  durationInFrames: number;
  accentColor: string;
}> = ({ durationInFrames, accentColor }) => {
  const frame = useCurrentFrame();

  // Wipe in from left
  const wipeIn = interpolate(frame, [0, 8], [100, 0], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  // Wipe out to right
  const wipeOut = interpolate(frame, [8, 16], [0, -100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.in(Easing.cubic),
  });

  const shouldShow = frame < 16;

  if (!shouldShow) return null;

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        background: `linear-gradient(90deg, ${accentColor}, #7C3AED)`,
        transform: `translateX(${frame < 8 ? wipeIn : wipeOut}%)`,
        zIndex: 100,
      }}
    />
  );
};

// ═══════════════════════════════════════════════════════════════
// Scene Renderer - Simplified: Background + Subtitles + Audio only
// ═══════════════════════════════════════════════════════════════
const SceneRenderer: React.FC<{
  scene: Scene;
  sceneIndex: number;
  characters: VideoConfig["characters"];
  theme: Theme;
  durationInFrames: number;
  showSubtitles: boolean;
  showCharacterName: boolean;
  useGeneratedBackgrounds?: boolean;
}> = ({ scene, sceneIndex, characters, theme, durationInFrames, showSubtitles, useGeneratedBackgrounds = true }) => {
  const character = characters[scene.characterId];
  if (!character) return null;

  return (
    <AbsoluteFill>
      {/* Full-screen AI-generated background */}
      {useGeneratedBackgrounds ? (
        <SceneBackground
          sceneIndex={sceneIndex}
          durationInFrames={durationInFrames}
          backgroundUrl={scene.backgroundUrl}
        />
      ) : (
        <AnimatedBackground theme={theme} sceneIndex={sceneIndex} />
      )}

      {/* Scene transition effect */}
      <SceneTransition durationInFrames={durationInFrames} accentColor={character.color} />

      {/* Subtitles only - no character overlay */}
      {showSubtitles && (
        <KineticTypography
          text={scene.dialogue}
          highlightText={scene.highlightText}
          durationInFrames={durationInFrames}
          accentColor={character.color}
        />
      )}

      {/* Scene audio */}
      <Audio src={staticFile(`audio/scene-${sceneIndex}.wav`)} />
    </AbsoluteFill>
  );
};

// ═══════════════════════════════════════════════════════════════
// Main Composition
// ═══════════════════════════════════════════════════════════════
interface ZkAGIVideoProps extends VideoConfig {
  useGeneratedBackgrounds?: boolean;
}

export const ZkAGIVideo: React.FC<ZkAGIVideoProps> = (props) => {
  const { scenes, characters, style, music, watermark, useGeneratedBackgrounds = true } = props;
  const theme = getTheme(style.theme);
  const DEFAULT_SCENE_FRAMES = 120;

  const sceneDurations = scenes.map((s) =>
    s.durationOverride ? Math.ceil(s.durationOverride * 30) : DEFAULT_SCENE_FRAMES
  );

  let frameOffset = 0;

  return (
    <AbsoluteFill style={{ background: theme.background }}>
      {scenes.map((scene, i) => {
        const start = frameOffset;
        frameOffset += sceneDurations[i];
        return (
          <Sequence key={i} from={start} durationInFrames={sceneDurations[i]}>
            <SceneRenderer
              scene={scene}
              sceneIndex={i}
              characters={characters}
              theme={theme}
              durationInFrames={sceneDurations[i]}
              showSubtitles={style.showSubtitles}
              showCharacterName={style.showCharacterName}
              useGeneratedBackgrounds={useGeneratedBackgrounds}
            />
          </Sequence>
        );
      })}

      {/* Background music */}
      {music.url && <Audio src={staticFile(music.url)} volume={music.volume} loop />}

      {/* Watermark */}
      {watermark.show && <Watermark text={watermark.text} color={theme.watermarkColor} />}
    </AbsoluteFill>
  );
};
