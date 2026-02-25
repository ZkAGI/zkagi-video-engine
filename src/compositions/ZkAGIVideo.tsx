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
// GLITCH FLASH — tech/crypto scene transition
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
// SCREEN SHAKE — impact effect for comedy moments
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
// SUBTITLES — clean lower-third with word reveal
// ═══════════════════════════════════════════════════════════════
const Subtitles: React.FC<{
  text: string;
  accentColor: string;
  durationInFrames: number;
  highlightWords?: string[];
}> = ({ text, accentColor, durationInFrames, highlightWords = [] }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = text.split(" ");

  const revealEnd = durationInFrames * 0.85;
  const wordsPerFrame = words.length / revealEnd;
  const visibleCount = Math.min(words.length, Math.floor(frame * wordsPerFrame) + 1);

  const enterSpring = spring({ frame, fps, config: { damping: 15, mass: 0.5, stiffness: 140 } });
  const slideY = interpolate(enterSpring, [0, 1], [30, 0]);
  const enterOp = interpolate(enterSpring, [0, 1], [0, 1]);

  const exitOp = interpolate(frame, [durationInFrames - 10, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <div style={{
      position: "absolute",
      bottom: 32,
      left: "50%",
      transform: `translateX(-50%) translateY(${slideY}px)`,
      maxWidth: "82%",
      opacity: enterOp * exitOp,
      zIndex: 50,
    }}>
      <div style={{
        background: "rgba(0,0,0,0.72)",
        backdropFilter: "blur(16px)",
        padding: "10px 24px",
        borderRadius: 10,
        borderLeft: `3px solid ${accentColor}`,
      }}>
        <p style={{
          color: "#FFFFFF",
          fontSize: 22,
          lineHeight: 1.5,
          fontFamily: "'Inter', sans-serif",
          fontWeight: 500,
          margin: 0,
          textAlign: "left",
          display: "-webkit-box",
          WebkitLineClamp: 2,
          WebkitBoxOrient: "vertical",
          overflow: "hidden",
        }}>
          {words.slice(0, visibleCount).map((word, i) => {
            const isHighlight = highlightWords.some(hw =>
              word.toLowerCase().replace(/[.,?!]/g, "").includes(hw.toLowerCase())
            );
            return (
              <span key={i} style={{
                color: isHighlight ? accentColor : "#FFFFFF",
                fontWeight: isHighlight ? 800 : 500,
                textShadow: isHighlight ? `0 0 12px ${accentColor}40` : "none",
              }}>
                {word}{" "}
              </span>
            );
          })}
        </p>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
// DARK GRADIENT — bottom overlay for subtitle readability
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
// CROSSFADE between sub-clips
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
// SPEAKER BADGE — small name tag top-left
// ═══════════════════════════════════════════════════════════════
const SpeakerBadge: React.FC<{
  name: string;
  color: string;
  durationInFrames: number;
}> = ({ name, color, durationInFrames }) => {
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
      position: "absolute",
      top: 28,
      left: 28,
      transform: `translateX(${slideX}px)`,
      opacity: opacity * exitOp,
      zIndex: 55,
    }}>
      <div style={{
        background: `${color}30`,
        border: `1px solid ${color}60`,
        padding: "4px 14px",
        borderRadius: 6,
        backdropFilter: "blur(8px)",
      }}>
        <span style={{
          color,
          fontSize: 14,
          fontWeight: 700,
          fontFamily: "'Inter', sans-serif",
          textTransform: "uppercase",
          letterSpacing: 1.5,
        }}>
          {name}
        </span>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
// MAIN COMPOSITION — PawPad Wallet Creation Demo (60s)
// ═══════════════════════════════════════════════════════════════
interface ZkAGIVideoProps extends VideoConfig {
  useGeneratedBackgrounds?: boolean;
}

export const ZkAGIVideo: React.FC<ZkAGIVideoProps> = (props) => {
  const { scenes, characters, style, music, watermark } = props;
  const theme = getTheme(style.theme);

  const PAD_COLOR = "#06B6D4"; // teal — all scenes use pad voice

  // ── Scene durations from TTS audio (30fps) ──
  // Scene 0: 13.92s = 418 frames
  // Scene 1: 15.36s = 461 frames
  // Scene 2: 17.92s = 538 frames
  // Scene 3: 14.56s = 437 frames
  const S0 = 418;
  const S1 = 461;
  const S2 = 538;
  const S3 = 437;
  const TOTAL = S0 + S1 + S2 + S3; // 1854

  // Scene start frames
  const START = [0, S0, S0 + S1, S0 + S1 + S2];

  // LTX-2 clip at 25fps, 97 frames = 3.88s → at 30fps ≈ 117 frames
  const CLIP = 117;
  const XF = 12; // crossfade overlap

  return (
    <AbsoluteFill style={{ background: "#0a0a1a" }}>

      {/* ═══════════════════════════════════════════ */}
      {/* SCENE 0: HOOK — "24 words on paper? Really?" */}
      {/* ═══════════════════════════════════════════ */}
      <Sequence from={START[0]} durationInFrames={S0}>
        <ScreenShake triggerFrame={15} intensity={8}>
          {/* Clip A: drawer chaos (0→117) */}
          <Sequence from={0} durationInFrames={CLIP}>
            <VideoClipBg videoPath="scenes/scene-0-a.mp4" durationInFrames={CLIP} fadeIn={0} />
          </Sequence>
          {/* Clip B: stained napkin (105→222) */}
          <Sequence from={CLIP - XF} durationInFrames={CLIP}>
            <VideoClipBg videoPath="scenes/scene-0-b.mp4" durationInFrames={CLIP} />
          </Sequence>
          {/* Clip C: napkin falling into darkness (210→418) */}
          <Sequence from={2 * CLIP - 2 * XF} durationInFrames={S0 - (2 * CLIP - 2 * XF)}>
            <VideoClipBg videoPath="scenes/scene-0-c.mp4" durationInFrames={S0 - (2 * CLIP - 2 * XF)} />
          </Sequence>
          {/* Sub-clip crossfades */}
          <Sequence from={CLIP - XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
          <Sequence from={2 * CLIP - 2 * XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
        </ScreenShake>

        <BottomGradient intensity={0.7} />

        <SpeakerBadge name="Pad" color={PAD_COLOR} durationInFrames={S0} />

        <Subtitles
          text={scenes[0].dialogue}
          accentColor={PAD_COLOR}
          durationInFrames={S0}
          highlightWords={["napkin", "security", "paper"]}
        />

        <Audio src={staticFile("audio/scene-0.wav")} />
      </Sequence>

      {/* Record scratch at start for comedy hook */}
      <Sequence from={0} durationInFrames={20}>
        <Audio src={staticFile("sfx/scratch.wav")} volume={0.45} />
      </Sequence>

      {/* Bass drop on "not security" punchline */}
      <Sequence from={START[0] + 280} durationInFrames={15}>
        <Audio src={staticFile("sfx/bass-drop.wav")} volume={0.4} />
      </Sequence>

      {/* ═══════════════════════════════════════════ */}
      {/* TRANSITION: Scene 0 → 1 (whoosh + glitch) */}
      {/* ═══════════════════════════════════════════ */}
      <Sequence from={START[1] - 4} durationInFrames={12}>
        <Audio src={staticFile("sfx/whoosh.wav")} volume={0.45} />
      </Sequence>
      <Sequence from={START[1]} durationInFrames={10}>
        <GlitchFlash color={PAD_COLOR} />
      </Sequence>

      {/* ═══════════════════════════════════════════ */}
      {/* SCENE 1: TEE — hardware vault explanation   */}
      {/* ═══════════════════════════════════════════ */}
      <Sequence from={START[1]} durationInFrames={S1}>
        {/* Clip A: vault interior (0→117) */}
        <Sequence from={0} durationInFrames={CLIP}>
          <VideoClipBg videoPath="scenes/scene-1-a.mp4" durationInFrames={CLIP} fadeIn={0} />
        </Sequence>
        {/* Clip B: keys in sealed cube (105→222) */}
        <Sequence from={CLIP - XF} durationInFrames={CLIP}>
          <VideoClipBg videoPath="scenes/scene-1-b.mp4" durationInFrames={CLIP} />
        </Sequence>
        {/* Clip C: shield blocking intruders (210→461) */}
        <Sequence from={2 * CLIP - 2 * XF} durationInFrames={S1 - (2 * CLIP - 2 * XF)}>
          <VideoClipBg videoPath="scenes/scene-1-c.mp4" durationInFrames={S1 - (2 * CLIP - 2 * XF)} />
        </Sequence>
        {/* Sub-clip crossfades */}
        <Sequence from={CLIP - XF} durationInFrames={XF * 2}>
          <SubClipFade durationInFrames={XF * 2} />
        </Sequence>
        <Sequence from={2 * CLIP - 2 * XF} durationInFrames={XF * 2}>
          <SubClipFade durationInFrames={XF * 2} />
        </Sequence>

        <BottomGradient intensity={0.6} />

        <SpeakerBadge name="Pad" color={PAD_COLOR} durationInFrames={S1} />

        <Subtitles
          text={scenes[1].dialogue}
          accentColor={PAD_COLOR}
          durationInFrames={S1}
          highlightWords={["TEE", "vault", "never", "nobody"]}
        />

        <Audio src={staticFile("audio/scene-1.wav")} />
      </Sequence>

      {/* Pop sounds on "Not hackers, not operators" */}
      <Sequence from={START[1] + 280} durationInFrames={10}>
        <Audio src={staticFile("sfx/pop.wav")} volume={0.35} />
      </Sequence>
      <Sequence from={START[1] + 340} durationInFrames={10}>
        <Audio src={staticFile("sfx/pop.wav")} volume={0.35} />
      </Sequence>
      <Sequence from={START[1] + 400} durationInFrames={10}>
        <Audio src={staticFile("sfx/pop.wav")} volume={0.35} />
      </Sequence>

      {/* ═══════════════════════════════════════════ */}
      {/* TRANSITION: Scene 1 → 2 (whoosh + glitch) */}
      {/* ═══════════════════════════════════════════ */}
      <Sequence from={START[2] - 4} durationInFrames={12}>
        <Audio src={staticFile("sfx/whoosh.wav")} volume={0.45} />
      </Sequence>
      <Sequence from={START[2]} durationInFrames={10}>
        <GlitchFlash color={PAD_COLOR} />
      </Sequence>

      {/* ═══════════════════════════════════════════ */}
      {/* SCENE 2: WALLET CREATION — step-by-step   */}
      {/* ═══════════════════════════════════════════ */}
      <Sequence from={START[2]} durationInFrames={S2}>
        {/* Clip A: smartphone UI (0→117) */}
        <Sequence from={0} durationInFrames={CLIP}>
          <VideoClipBg videoPath="scenes/scene-2-a.mp4" durationInFrames={CLIP} fadeIn={0} />
        </Sequence>
        {/* Clip B: QR scan authentication (105→222) */}
        <Sequence from={CLIP - XF} durationInFrames={CLIP}>
          <VideoClipBg videoPath="scenes/scene-2-b.mp4" durationInFrames={CLIP} />
        </Sequence>
        {/* Clip C: backup download + vault lock (210→538) */}
        <Sequence from={2 * CLIP - 2 * XF} durationInFrames={S2 - (2 * CLIP - 2 * XF)}>
          <VideoClipBg videoPath="scenes/scene-2-c.mp4" durationInFrames={S2 - (2 * CLIP - 2 * XF)} />
        </Sequence>
        {/* Sub-clip crossfades */}
        <Sequence from={CLIP - XF} durationInFrames={XF * 2}>
          <SubClipFade durationInFrames={XF * 2} />
        </Sequence>
        <Sequence from={2 * CLIP - 2 * XF} durationInFrames={XF * 2}>
          <SubClipFade durationInFrames={XF * 2} />
        </Sequence>

        <BottomGradient intensity={0.6} />

        <SpeakerBadge name="Pad" color={PAD_COLOR} durationInFrames={S2} />

        <Subtitles
          text={scenes[2].dialogue}
          accentColor={PAD_COLOR}
          durationInFrames={S2}
          highlightWords={["PawPad", "seedless", "wallet", "QR", "backup"]}
        />

        <Audio src={staticFile("audio/scene-2.wav")} />
      </Sequence>

      {/* Ping on "seedless wallet is live" */}
      <Sequence from={START[2] + 470} durationInFrames={10}>
        <Audio src={staticFile("sfx/ping.wav")} volume={0.35} />
      </Sequence>

      {/* ═══════════════════════════════════════════ */}
      {/* TRANSITION: Scene 2 → 3 (bass + glitch)   */}
      {/* ═══════════════════════════════════════════ */}
      <Sequence from={START[3] - 4} durationInFrames={12}>
        <Audio src={staticFile("sfx/bass-drop.wav")} volume={0.45} />
      </Sequence>
      <Sequence from={START[3]} durationInFrames={10}>
        <GlitchFlash color={PAD_COLOR} />
      </Sequence>

      {/* ═══════════════════════════════════════════ */}
      {/* SCENE 3: CTA — "Try it at paw.zkagi.ai"   */}
      {/* ═══════════════════════════════════════════ */}
      <Sequence from={START[3]} durationInFrames={S3}>
        {/* Clip A: napkin vs vault split (0→117) */}
        <Sequence from={0} durationInFrames={CLIP}>
          <VideoClipBg videoPath="scenes/scene-3-a.mp4" durationInFrames={CLIP} fadeIn={0} />
        </Sequence>
        {/* Clip B: logo materializing (105→222) */}
        <Sequence from={CLIP - XF} durationInFrames={CLIP}>
          <VideoClipBg videoPath="scenes/scene-3-b.mp4" durationInFrames={CLIP} />
        </Sequence>
        {/* Clip C: portal / CTA energy (210→437) */}
        <Sequence from={2 * CLIP - 2 * XF} durationInFrames={S3 - (2 * CLIP - 2 * XF)}>
          <VideoClipBg videoPath="scenes/scene-3-c.mp4" durationInFrames={S3 - (2 * CLIP - 2 * XF)} />
        </Sequence>
        {/* Sub-clip crossfades */}
        <Sequence from={CLIP - XF} durationInFrames={XF * 2}>
          <SubClipFade durationInFrames={XF * 2} />
        </Sequence>
        <Sequence from={2 * CLIP - 2 * XF} durationInFrames={XF * 2}>
          <SubClipFade durationInFrames={XF * 2} />
        </Sequence>

        <BottomGradient intensity={0.65} />

        <SpeakerBadge name="Pad" color={PAD_COLOR} durationInFrames={S3} />

        <Subtitles
          text={scenes[3].dialogue}
          accentColor={PAD_COLOR}
          durationInFrames={S3}
          highlightWords={["PawPad", "napkins", "hardware", "paw"]}
        />

        <Audio src={staticFile("audio/scene-3.wav")} />
      </Sequence>

      {/* Ping on CTA "paw dot zkagi dot ai" */}
      <Sequence from={START[3] + 340} durationInFrames={10}>
        <Audio src={staticFile("sfx/ping.wav")} volume={0.4} />
      </Sequence>

      {/* ═══════════════════════════════════════════ */}
      {/* GLOBAL LAYERS                              */}
      {/* ═══════════════════════════════════════════ */}

      {/* Background music */}
      {music.url && <Audio src={staticFile(music.url)} volume={music.volume} loop />}

      {/* Watermark */}
      {watermark.show && <Watermark text={watermark.text} color={theme.watermarkColor} />}
    </AbsoluteFill>
  );
};
