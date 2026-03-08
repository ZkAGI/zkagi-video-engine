import React from "react";
import {
  AbsoluteFill,
  Audio,
  Video,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  staticFile,
  Img,
} from "remotion";
import { VideoConfig, Scene } from "../types";
import { Watermark } from "../components/Watermark";
import { getTheme } from "../lib/themes";

// ═══════════════════════════════════════════════════════════════
// VIDEO CLIP BACKGROUND — plays LTX-2 generated clips
// ═══════════════════════════════════════════════════════════════
const VideoClipBg: React.FC<{
  videoPath: string;
  durationInFrames: number;
  fadeIn?: number;
}> = ({ videoPath, durationInFrames, fadeIn = 8 }) => {
  const frame = useCurrentFrame();
  const opacity = fadeIn > 0
    ? interpolate(frame, [0, fadeIn], [0, 1], { extrapolateRight: "clamp" })
    : 1;

  return (
    <AbsoluteFill>
      <Video
        src={staticFile(videoPath)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          opacity,
        }}
        volume={0}
        startFrom={0}
      />
    </AbsoluteFill>
  );
};

// ═══════════════════════════════════════════════════════════════
// KEN BURNS IMAGE — zoom/pan on reference image
// ═══════════════════════════════════════════════════════════════
const KenBurnsImage: React.FC<{
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

// ═══════════════════════════════════════════════════════════════
// GLITCH FLASH — cyber transition between scenes
// ═══════════════════════════════════════════════════════════════
const GlitchFlash: React.FC<{ color?: string }> = ({ color = "#06B6D4" }) => {
  const frame = useCurrentFrame();
  if (frame > 8) return null;

  const flash1 = frame < 2 ? 0.7 : 0;
  const flash2 = frame >= 3 && frame < 5 ? 0.4 : 0;
  const scanline = frame >= 2 && frame < 6 ? 0.3 : 0;

  return (
    <AbsoluteFill style={{ zIndex: 200 }}>
      <div style={{
        position: "absolute", width: "100%", height: "100%",
        backgroundColor: color, opacity: flash1 + flash2,
      }} />
      {scanline > 0 && (
        <div style={{
          position: "absolute", width: "100%", height: "100%",
          background: `repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,${scanline}) 2px, rgba(0,0,0,${scanline}) 4px)`,
        }} />
      )}
    </AbsoluteFill>
  );
};

// ═══════════════════════════════════════════════════════════════
// SCREEN SHAKE — impact on punchlines
// ═══════════════════════════════════════════════════════════════
const ScreenShake: React.FC<{
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

// ═══════════════════════════════════════════════════════════════
// WORD-POP SUBTITLES — words spring in one by one
// ═══════════════════════════════════════════════════════════════
const WordPopSubtitles: React.FC<{
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

// ═══════════════════════════════════════════════════════════════
// BOTTOM GRADIENT — darken bottom for subtitle readability
// ═══════════════════════════════════════════════════════════════
const BottomGradient: React.FC<{ intensity?: number }> = ({ intensity = 0.65 }) => (
  <AbsoluteFill style={{ zIndex: 40 }}>
    <div style={{
      position: "absolute", width: "100%", height: "100%",
      background: `linear-gradient(180deg, transparent 0%, transparent 55%, rgba(0,0,0,${intensity * 0.3}) 75%, rgba(0,0,0,${intensity}) 100%)`,
    }} />
  </AbsoluteFill>
);

// ═══════════════════════════════════════════════════════════════
// SUB-CLIP CROSSFADE
// ═══════════════════════════════════════════════════════════════
const SubClipFade: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const mid = durationInFrames / 2;
  const opacity = frame < mid
    ? interpolate(frame, [0, mid], [0, 0.5], { extrapolateRight: "clamp" })
    : interpolate(frame, [mid, durationInFrames], [0.5, 0], { extrapolateRight: "clamp" });
  return <AbsoluteFill style={{ backgroundColor: "#0a0a1a", opacity, zIndex: 30 }} />;
};

// ═══════════════════════════════════════════════════════════════
// TOPIC BADGE — scene topic indicator top-left
// ═══════════════════════════════════════════════════════════════
const TopicBadge: React.FC<{
  label: string;
  color: string;
  durationInFrames: number;
}> = ({ label, color, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enterSpring = spring({ frame, fps, config: { damping: 20, mass: 0.4, stiffness: 160 } });
  const slideX = interpolate(enterSpring, [0, 1], [-60, 0]);
  const opacity = interpolate(enterSpring, [0, 1], [0, 1]);
  const exitOp = interpolate(frame, [durationInFrames - 8, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <div style={{
      position: "absolute", top: 28, left: 28,
      transform: `translateX(${slideX}px)`, opacity: opacity * exitOp, zIndex: 55,
    }}>
      <div style={{
        background: `${color}30`, border: `1px solid ${color}60`,
        padding: "4px 14px", borderRadius: 6, backdropFilter: "blur(8px)",
      }}>
        <span style={{
          color, fontSize: 14, fontWeight: 700,
          fontFamily: "'Inter', sans-serif", textTransform: "uppercase", letterSpacing: 1.5,
        }}>{label}</span>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
// CTA URL REVEAL
// ═══════════════════════════════════════════════════════════════
const CtaUrl: React.FC<{
  url: string;
  color: string;
  triggerFrame: number;
  durationInFrames: number;
}> = ({ url, color, triggerFrame, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const localFrame = frame - triggerFrame;
  if (localFrame < 0) return null;

  const popSpring = spring({ frame: localFrame, fps, config: { damping: 10, mass: 0.5, stiffness: 120 } });
  const scale = interpolate(popSpring, [0, 1], [0.3, 1]);
  const opacity = interpolate(popSpring, [0, 1], [0, 1]);
  const glowPulse = Math.sin(localFrame * 0.15) * 0.3 + 0.7;
  const exitOp = interpolate(frame, [durationInFrames - 15, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <div style={{
      position: "absolute", top: "35%", left: "50%",
      transform: `translateX(-50%) scale(${scale})`, opacity: opacity * exitOp, zIndex: 60,
    }}>
      <div style={{
        background: `${color}20`, border: `2px solid ${color}90`,
        padding: "12px 36px", borderRadius: 14, backdropFilter: "blur(12px)",
        boxShadow: `0 0 ${30 * glowPulse}px ${color}40, 0 0 ${60 * glowPulse}px ${color}20`,
      }}>
        <span style={{
          color: "#FFFFFF", fontSize: 28, fontWeight: 800,
          fontFamily: "'Inter', sans-serif", letterSpacing: 1,
          textShadow: `0 0 12px ${color}60`,
        }}>{url}</span>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
// MAIN COMPOSITION — ZkTerminal Prediction Market Story
// ═══════════════════════════════════════════════════════════════
interface ZkAGIVideoProps extends VideoConfig {
  useGeneratedBackgrounds?: boolean;
}

export const ZkAGIVideo: React.FC<ZkAGIVideoProps> = (props) => {
  const { scenes, characters, style, music, watermark } = props;
  const theme = getTheme(style.theme);

  const PAD_COLOR = "#06B6D4";

  // Scene durations (30fps) from TTS audio
  // S0: 10.24s → 307   S1: 8.64s → 259   S2: 11.84s → 355
  // S3: 9.92s → 298    S4: 9.28s → 278
  const S0 = 307;
  const S1 = 259;
  const S2 = 355;
  const S3 = 298;
  const S4 = 278;

  const START = [0, S0, S0 + S1, S0 + S1 + S2, S0 + S1 + S2 + S3];

  // Video clip is 97 frames at 25fps = 3.88s → at 30fps = ~116 frames
  const VIDEO_FRAMES = 116;
  const XF = 8; // crossfade frames

  const TOPICS = ["3:00 AM", "ZKTERMINAL", "IN POSITION", "PAYOFF", "YOUR MOVE"];
  const SCENE_COLORS = ["#3B82F6", "#10B981", "#F59E0B", "#22C55E", "#7C3AED"];

  return (
    <AbsoluteFill style={{ background: "#0a0a1a" }}>

      {/* ═══ SCENE 0: THE SITUATION — 3AM Charts (10.24s = 307 frames) ═══ */}
      <Sequence from={START[0]} durationInFrames={S0}>
        <ScreenShake triggerFrame={250} intensity={4}>
          {/* Video clip first: 116 frames */}
          <Sequence from={0} durationInFrames={VIDEO_FRAMES}>
            <VideoClipBg videoPath="scenes/scene-0-a.mp4" durationInFrames={VIDEO_FRAMES} fadeIn={0} />
          </Sequence>
          {/* Crossfade video→image */}
          <Sequence from={VIDEO_FRAMES - XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
          {/* Overflow: 307 - 116 = 191 frames for 2 images (96 + 95) */}
          <Sequence from={VIDEO_FRAMES} durationInFrames={96 + XF}>
            <KenBurnsImage imagePath="scenes/scene-0-b.png" durationInFrames={96 + XF} fadeIn={8} direction="pan-right" />
          </Sequence>
          <Sequence from={VIDEO_FRAMES + 96 - XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
          <Sequence from={VIDEO_FRAMES + 96} durationInFrames={S0 - VIDEO_FRAMES - 96}>
            <KenBurnsImage imagePath="scenes/scene-0-c.png" durationInFrames={S0 - VIDEO_FRAMES - 96} fadeIn={8} direction="zoom-in" />
          </Sequence>
        </ScreenShake>
        <BottomGradient intensity={0.75} />
        <TopicBadge label={TOPICS[0]} color={SCENE_COLORS[0]} durationInFrames={S0} />
        <WordPopSubtitles text={scenes[0].dialogue} accentColor={SCENE_COLORS[0]} durationInFrames={S0}
          highlightWords={["Three", "AM", "Kyle", "screaming", "resistance", "Nobody"]} />
        <Audio src={staticFile("audio/scene-0.wav")} />
      </Sequence>
      <Sequence from={0} durationInFrames={15}>
        <Audio src={staticFile("sfx/bass-drop.wav")} volume={0.5} />
      </Sequence>

      {/* TRANSITION 0→1 */}
      <Sequence from={START[1] - 4} durationInFrames={12}>
        <Audio src={staticFile("sfx/whoosh.wav")} volume={0.45} />
      </Sequence>
      <Sequence from={START[1]} durationInFrames={10}>
        <GlitchFlash color={SCENE_COLORS[1]} />
        <Audio src={staticFile("sfx/pop.wav")} volume={0.4} />
      </Sequence>

      {/* ═══ SCENE 1: THE EDGE — ZkTerminal AI Signal (8.64s = 259 frames) ═══ */}
      <Sequence from={START[1]} durationInFrames={S1}>
        {/* Video clip first: 116 frames */}
        <Sequence from={0} durationInFrames={VIDEO_FRAMES}>
          <VideoClipBg videoPath="scenes/scene-1-a.mp4" durationInFrames={VIDEO_FRAMES} fadeIn={0} />
        </Sequence>
        {/* Crossfade */}
        <Sequence from={VIDEO_FRAMES - XF} durationInFrames={XF * 2}>
          <SubClipFade durationInFrames={XF * 2} />
        </Sequence>
        {/* Overflow: 259 - 116 = 143 frames for 2 images (72 + 71) */}
        <Sequence from={VIDEO_FRAMES} durationInFrames={72 + XF}>
          <KenBurnsImage imagePath="scenes/scene-1-b.png" durationInFrames={72 + XF} fadeIn={8} direction="zoom-out" />
        </Sequence>
        <Sequence from={VIDEO_FRAMES + 72 - XF} durationInFrames={XF * 2}>
          <SubClipFade durationInFrames={XF * 2} />
        </Sequence>
        <Sequence from={VIDEO_FRAMES + 72} durationInFrames={S1 - VIDEO_FRAMES - 72}>
          <KenBurnsImage imagePath="scenes/scene-1-c.png" durationInFrames={S1 - VIDEO_FRAMES - 72} fadeIn={8} direction="pan-left" />
        </Sequence>
        <BottomGradient intensity={0.7} />
        <TopicBadge label={TOPICS[1]} color={SCENE_COLORS[1]} durationInFrames={S1} />
        <WordPopSubtitles text={scenes[1].dialogue} accentColor={SCENE_COLORS[1]} durationInFrames={S1}
          highlightWords={["ZkTerminal", "AI", "flagged", "trend", "Six", "hours", "early"]} />
        <Audio src={staticFile("audio/scene-1.wav")} />
      </Sequence>

      {/* TRANSITION 1→2 */}
      <Sequence from={START[2] - 4} durationInFrames={12}>
        <Audio src={staticFile("sfx/whoosh.wav")} volume={0.45} />
      </Sequence>
      <Sequence from={START[2]} durationInFrames={10}>
        <GlitchFlash color={SCENE_COLORS[2]} />
        <Audio src={staticFile("sfx/ping.wav")} volume={0.35} />
      </Sequence>

      {/* ═══ SCENE 2: IN POSITION — Locked & Loaded (11.84s = 355 frames) ═══ */}
      <Sequence from={START[2]} durationInFrames={S2}>
        <ScreenShake triggerFrame={280} intensity={4}>
          {/* Video clip first: 116 frames */}
          <Sequence from={0} durationInFrames={VIDEO_FRAMES}>
            <VideoClipBg videoPath="scenes/scene-2-a.mp4" durationInFrames={VIDEO_FRAMES} fadeIn={0} />
          </Sequence>
          {/* Crossfade */}
          <Sequence from={VIDEO_FRAMES - XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
          {/* Overflow: 355 - 116 = 239 frames for 2 images (120 + 119) */}
          <Sequence from={VIDEO_FRAMES} durationInFrames={120 + XF}>
            <KenBurnsImage imagePath="scenes/scene-2-b.png" durationInFrames={120 + XF} fadeIn={8} direction="pan-right" />
          </Sequence>
          <Sequence from={VIDEO_FRAMES + 120 - XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
          <Sequence from={VIDEO_FRAMES + 120} durationInFrames={S2 - VIDEO_FRAMES - 120}>
            <KenBurnsImage imagePath="scenes/scene-2-c.png" durationInFrames={S2 - VIDEO_FRAMES - 120} fadeIn={8} direction="zoom-in" />
          </Sequence>
        </ScreenShake>
        <BottomGradient intensity={0.7} />
        <TopicBadge label={TOPICS[2]} color={SCENE_COLORS[2]} durationInFrames={S2} />
        <WordPopSubtitles text={scenes[2].dialogue} accentColor={SCENE_COLORS[2]} durationInFrames={S2}
          highlightWords={["position", "Prediction", "markets", "locked", "Entry", "set", "No", "hesitation"]} />
        <Audio src={staticFile("audio/scene-2.wav")} />
      </Sequence>

      {/* TRANSITION 2→3 */}
      <Sequence from={START[3] - 4} durationInFrames={12}>
        <Audio src={staticFile("sfx/whoosh.wav")} volume={0.4} />
      </Sequence>
      <Sequence from={START[3]} durationInFrames={10}>
        <GlitchFlash color={SCENE_COLORS[3]} />
        <Audio src={staticFile("sfx/ping.wav")} volume={0.4} />
      </Sequence>

      {/* ═══ SCENE 3: THE PAYOFF — Gains (9.92s = 298 frames) ═══ */}
      <Sequence from={START[3]} durationInFrames={S3}>
        <ScreenShake triggerFrame={230} intensity={6}>
          {/* Video clip first: 116 frames */}
          <Sequence from={0} durationInFrames={VIDEO_FRAMES}>
            <VideoClipBg videoPath="scenes/scene-3-a.mp4" durationInFrames={VIDEO_FRAMES} fadeIn={0} />
          </Sequence>
          {/* Crossfade */}
          <Sequence from={VIDEO_FRAMES - XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
          {/* Overflow: 298 - 116 = 182 frames for 2 images (91 + 91) */}
          <Sequence from={VIDEO_FRAMES} durationInFrames={91 + XF}>
            <KenBurnsImage imagePath="scenes/scene-3-b.png" durationInFrames={91 + XF} fadeIn={8} direction="zoom-out" />
          </Sequence>
          <Sequence from={VIDEO_FRAMES + 91 - XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
          <Sequence from={VIDEO_FRAMES + 91} durationInFrames={S3 - VIDEO_FRAMES - 91}>
            <KenBurnsImage imagePath="scenes/scene-3-c.png" durationInFrames={S3 - VIDEO_FRAMES - 91} fadeIn={8} direction="pan-right" />
          </Sequence>
        </ScreenShake>
        <BottomGradient intensity={0.65} />
        <TopicBadge label={TOPICS[3]} color={SCENE_COLORS[3]} durationInFrames={S3} />
        <WordPopSubtitles text={scenes[3].dialogue} accentColor={SCENE_COLORS[3]} durationInFrames={S3}
          highlightWords={["move", "hits", "catches", "gains", "Better", "APIs", "beat"]} />
        <Audio src={staticFile("audio/scene-3.wav")} />
      </Sequence>
      <Sequence from={START[3] + 230} durationInFrames={15}>
        <Audio src={staticFile("sfx/scratch.wav")} volume={0.35} />
      </Sequence>

      {/* TRANSITION 3→4 */}
      <Sequence from={START[4] - 4} durationInFrames={12}>
        <Audio src={staticFile("sfx/bass-drop.wav")} volume={0.45} />
      </Sequence>
      <Sequence from={START[4]} durationInFrames={10}>
        <GlitchFlash color={SCENE_COLORS[4]} />
      </Sequence>

      {/* ═══ SCENE 4: MIC DROP — CTA (9.28s = 278 frames) ═══ */}
      <Sequence from={START[4]} durationInFrames={S4}>
        <ScreenShake triggerFrame={200} intensity={7}>
          {/* Video clip first: 116 frames */}
          <Sequence from={0} durationInFrames={VIDEO_FRAMES}>
            <VideoClipBg videoPath="scenes/scene-4-a.mp4" durationInFrames={VIDEO_FRAMES} fadeIn={0} />
          </Sequence>
          {/* Crossfade */}
          <Sequence from={VIDEO_FRAMES - XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
          {/* Overflow: 278 - 116 = 162 frames for 2 images (81 + 81) */}
          <Sequence from={VIDEO_FRAMES} durationInFrames={81 + XF}>
            <KenBurnsImage imagePath="scenes/scene-4-b.png" durationInFrames={81 + XF} fadeIn={8} direction="pan-left" />
          </Sequence>
          <Sequence from={VIDEO_FRAMES + 81 - XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
          <Sequence from={VIDEO_FRAMES + 81} durationInFrames={S4 - VIDEO_FRAMES - 81}>
            <KenBurnsImage imagePath="scenes/scene-4-c.png" durationInFrames={S4 - VIDEO_FRAMES - 81} fadeIn={8} direction="zoom-in" />
          </Sequence>
        </ScreenShake>
        <BottomGradient intensity={0.7} />
        <TopicBadge label={TOPICS[4]} color={SCENE_COLORS[4]} durationInFrames={S4} />
        <WordPopSubtitles text={scenes[4].dialogue} accentColor={SCENE_COLORS[4]} durationInFrames={S4}
          highlightWords={["terminal", "zkagi", "predict", "future", "better", "APIs"]} />
        <CtaUrl url="terminal.zkagi.ai" color={SCENE_COLORS[4]} triggerFrame={45} durationInFrames={S4} />
        <Audio src={staticFile("audio/scene-4.wav")} />
      </Sequence>
      <Sequence from={START[4] + 45} durationInFrames={10}>
        <Audio src={staticFile("sfx/ping.wav")} volume={0.4} />
      </Sequence>

      {/* GLOBAL LAYERS */}
      {music.url && <Audio src={staticFile(music.url)} volume={music.volume} loop />}
      {watermark.show && <Watermark text={watermark.text} color={theme.watermarkColor} />}
    </AbsoluteFill>
  );
};
