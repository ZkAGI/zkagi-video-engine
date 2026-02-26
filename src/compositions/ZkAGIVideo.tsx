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
// GLITCH FLASH — cyber transition between scenes
// ═══════════════════════════════════════════════════════════════
const GlitchFlash: React.FC<{ color?: string }> = ({ color = "#7C3AED" }) => {
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
// WORD-POP SUBTITLES — words spring in one by one, key words glow
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

  // Words reveal over first 85% of scene
  const revealEnd = durationInFrames * 0.85;
  const framesPerWord = revealEnd / words.length;

  // Container entrance
  const enterSpring = spring({ frame, fps, config: { damping: 15, mass: 0.5, stiffness: 140 } });
  const slideY = interpolate(enterSpring, [0, 1], [40, 0]);
  const enterOp = interpolate(enterSpring, [0, 1], [0, 1]);

  // Container exit
  const exitOp = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <div style={{
      position: "absolute",
      bottom: 36,
      left: "50%",
      transform: `translateX(-50%) translateY(${slideY}px)`,
      maxWidth: "82%",
      opacity: enterOp * exitOp,
      zIndex: 50,
    }}>
      <div style={{
        background: "rgba(0,0,0,0.72)",
        backdropFilter: "blur(16px)",
        padding: "10px 22px",
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
// SPEAKER BADGE — small tag top-left
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
// CTA URL REVEAL — URL pops in at end with glow
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

  const popSpring = spring({
    frame: localFrame,
    fps,
    config: { damping: 10, mass: 0.5, stiffness: 120 },
  });
  const scale = interpolate(popSpring, [0, 1], [0.3, 1]);
  const opacity = interpolate(popSpring, [0, 1], [0, 1]);

  // Pulsing glow
  const glowPulse = Math.sin(localFrame * 0.15) * 0.3 + 0.7;

  const exitOp = interpolate(frame, [durationInFrames - 15, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <div style={{
      position: "absolute",
      bottom: 100,
      left: "50%",
      transform: `translateX(-50%) scale(${scale})`,
      opacity: opacity * exitOp,
      zIndex: 60,
    }}>
      <div style={{
        background: `${color}20`,
        border: `2px solid ${color}90`,
        padding: "12px 36px",
        borderRadius: 14,
        backdropFilter: "blur(12px)",
        boxShadow: `0 0 ${30 * glowPulse}px ${color}40, 0 0 ${60 * glowPulse}px ${color}20`,
      }}>
        <span style={{
          color: "#FFFFFF",
          fontSize: 28,
          fontWeight: 800,
          fontFamily: "'Inter', sans-serif",
          letterSpacing: 1,
          textShadow: `0 0 12px ${color}60`,
        }}>
          {url}
        </span>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
// MAIN COMPOSITION — PawPad Seed Phrase Roast (55s, 5 scenes)
// ═══════════════════════════════════════════════════════════════
interface ZkAGIVideoProps extends VideoConfig {
  useGeneratedBackgrounds?: boolean;
}

export const ZkAGIVideo: React.FC<ZkAGIVideoProps> = (props) => {
  const { scenes, characters, style, music, watermark } = props;
  const theme = getTheme(style.theme);

  const PAW_COLOR = "#7C3AED"; // purple — all scenes use paw voice

  // ── Scene durations from TTS audio (30fps) + breathing room ──
  // Scene 0: 5.92s  → 178 + 30 = 208 frames
  // Scene 1: 10.08s → 303 + 25 = 328 frames
  // Scene 2: 8.64s  → 260 + 25 = 285 frames
  // Scene 3: 14.24s → 428 + 25 = 453 frames
  // Scene 4: 8.32s  → 250 + 80 = 330 frames (CTA needs breathing room)
  const S0 = 208;
  const S1 = 328;
  const S2 = 285;
  const S3 = 453;
  const S4 = 330;
  const TOTAL = S0 + S1 + S2 + S3 + S4; // 1604

  // Scene start frames
  const START = [0, S0, S0 + S1, S0 + S1 + S2, S0 + S1 + S2 + S3];

  // LTX-2 clip at 25fps, 97 frames = 3.88s → at 30fps ≈ 117 frames
  const CLIP = 117;
  const XF = 12; // crossfade overlap

  return (
    <AbsoluteFill style={{ background: "#0a0a1a" }}>

      {/* ═══════════════════════════════════════════ */}
      {/* SCENE 0: HOOK — Seed phrase roast (comic)  */}
      {/* ═══════════════════════════════════════════ */}
      <Sequence from={START[0]} durationInFrames={S0}>
        <ScreenShake triggerFrame={60} intensity={8}>
          {/* Clip A: panicked character + napkin (0→117) */}
          <Sequence from={0} durationInFrames={CLIP}>
            <VideoClipBg videoPath="scenes/scene-0-a.mp4" durationInFrames={CLIP} fadeIn={0} />
          </Sequence>
          {/* Clip B: napkin ripping into abyss (105→208) */}
          <Sequence from={CLIP - XF} durationInFrames={S0 - (CLIP - XF)}>
            <VideoClipBg videoPath="scenes/scene-0-b.mp4" durationInFrames={S0 - (CLIP - XF)} />
          </Sequence>
          {/* Crossfade between clips */}
          <Sequence from={CLIP - XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
        </ScreenShake>

        <BottomGradient intensity={0.75} />

        <SpeakerBadge name="Paw" color={PAW_COLOR} durationInFrames={S0} />

        <WordPopSubtitles
          text={scenes[0].dialogue}
          accentColor={PAW_COLOR}
          durationInFrames={S0}
          highlightWords={["napkin", "security", "treasure", "hackers"]}
        />

        <Audio src={staticFile("audio/scene-0.wav")} />
      </Sequence>

      {/* Record scratch on the hook opening */}
      <Sequence from={0} durationInFrames={20}>
        <Audio src={staticFile("sfx/scratch.wav")} volume={0.45} />
      </Sequence>

      {/* Bass drop on "treasure map for hackers" punchline */}
      <Sequence from={START[0] + 130} durationInFrames={15}>
        <Audio src={staticFile("sfx/bass-drop.wav")} volume={0.4} />
      </Sequence>

      {/* ═══════════════════════════════════════════ */}
      {/* TRANSITION: Scene 0 → 1 (whoosh + glitch) */}
      {/* ═══════════════════════════════════════════ */}
      <Sequence from={START[1] - 4} durationInFrames={12}>
        <Audio src={staticFile("sfx/whoosh.wav")} volume={0.45} />
      </Sequence>
      <Sequence from={START[1]} durationInFrames={10}>
        <GlitchFlash color={PAW_COLOR} />
      </Sequence>

      {/* ═══════════════════════════════════════════ */}
      {/* SCENE 1: TWIST — Billions lost, noir style */}
      {/* ═══════════════════════════════════════════ */}
      <Sequence from={START[1]} durationInFrames={S1}>
        {/* Clip A: sticky notes on fridge (0→117) */}
        <Sequence from={0} durationInFrames={CLIP}>
          <VideoClipBg videoPath="scenes/scene-1-a.mp4" durationInFrames={CLIP} fadeIn={0} />
        </Sequence>
        {/* Clip B: money dissolving to ash (105→222) */}
        <Sequence from={CLIP - XF} durationInFrames={CLIP}>
          <VideoClipBg videoPath="scenes/scene-1-b.mp4" durationInFrames={CLIP} />
        </Sequence>
        {/* Clip C: wallet corrupting, glitch (210→328) */}
        <Sequence from={2 * CLIP - 2 * XF} durationInFrames={S1 - (2 * CLIP - 2 * XF)}>
          <VideoClipBg videoPath="scenes/scene-1-c.mp4" durationInFrames={S1 - (2 * CLIP - 2 * XF)} />
        </Sequence>
        {/* Crossfades */}
        <Sequence from={CLIP - XF} durationInFrames={XF * 2}>
          <SubClipFade durationInFrames={XF * 2} />
        </Sequence>
        <Sequence from={2 * CLIP - 2 * XF} durationInFrames={XF * 2}>
          <SubClipFade durationInFrames={XF * 2} />
        </Sequence>

        <BottomGradient intensity={0.7} />

        <SpeakerBadge name="Paw" color={PAW_COLOR} durationInFrames={S1} />

        <WordPopSubtitles
          text={scenes[1].dialogue}
          accentColor={PAW_COLOR}
          durationInFrames={S1}
          highlightWords={["billions", "sticky", "poof", "gone"]}
        />

        <Audio src={staticFile("audio/scene-1.wav")} />
      </Sequence>

      {/* Pop on "poof" */}
      <Sequence from={START[1] + 260} durationInFrames={10}>
        <Audio src={staticFile("sfx/pop.wav")} volume={0.4} />
      </Sequence>

      {/* ═══════════════════════════════════════════ */}
      {/* TRANSITION: Scene 1 → 2 (whoosh + glitch) */}
      {/* ═══════════════════════════════════════════ */}
      <Sequence from={START[2] - 4} durationInFrames={12}>
        <Audio src={staticFile("sfx/whoosh.wav")} volume={0.45} />
      </Sequence>
      <Sequence from={START[2]} durationInFrames={10}>
        <GlitchFlash color="#FFD700" />
      </Sequence>

      {/* ═══════════════════════════════════════════ */}
      {/* SCENE 2: SOLUTION — Vault protection, Pixar */}
      {/* ═══════════════════════════════════════════ */}
      <Sequence from={START[2]} durationInFrames={S2}>
        {/* Clip A: vault opens with golden light (0→117) */}
        <Sequence from={0} durationInFrames={CLIP}>
          <VideoClipBg videoPath="scenes/scene-2-a.mp4" durationInFrames={CLIP} fadeIn={0} />
        </Sequence>
        {/* Clip B: keys in force field (105→222) */}
        <Sequence from={CLIP - XF} durationInFrames={CLIP}>
          <VideoClipBg videoPath="scenes/scene-2-b.mp4" durationInFrames={CLIP} />
        </Sequence>
        {/* Clip C: vault layers pull-back (210→285) */}
        <Sequence from={2 * CLIP - 2 * XF} durationInFrames={S2 - (2 * CLIP - 2 * XF)}>
          <VideoClipBg videoPath="scenes/scene-2-c.mp4" durationInFrames={S2 - (2 * CLIP - 2 * XF)} />
        </Sequence>
        {/* Crossfades */}
        <Sequence from={CLIP - XF} durationInFrames={XF * 2}>
          <SubClipFade durationInFrames={XF * 2} />
        </Sequence>
        <Sequence from={2 * CLIP - 2 * XF} durationInFrames={XF * 2}>
          <SubClipFade durationInFrames={XF * 2} />
        </Sequence>

        <BottomGradient intensity={0.6} />

        <SpeakerBadge name="Paw" color={PAW_COLOR} durationInFrames={S2} />

        <WordPopSubtitles
          text={scenes[2].dialogue}
          accentColor={PAW_COLOR}
          durationInFrames={S2}
          highlightWords={["PawPad", "vault", "never", "peek"]}
        />

        <Audio src={staticFile("audio/scene-2.wav")} />
      </Sequence>

      {/* Bass drop on "never leave" emphasis */}
      <Sequence from={START[2] + 100} durationInFrames={15}>
        <Audio src={staticFile("sfx/bass-drop.wav")} volume={0.35} />
      </Sequence>

      {/* ═══════════════════════════════════════════ */}
      {/* TRANSITION: Scene 2 → 3 (whoosh)          */}
      {/* ═══════════════════════════════════════════ */}
      <Sequence from={START[3] - 4} durationInFrames={12}>
        <Audio src={staticFile("sfx/whoosh.wav")} volume={0.4} />
      </Sequence>
      <Sequence from={START[3]} durationInFrames={10}>
        <GlitchFlash color="#06B6D4" />
      </Sequence>

      {/* ═══════════════════════════════════════════ */}
      {/* SCENE 3: WALKTHROUGH — Step by step, iso   */}
      {/* ═══════════════════════════════════════════ */}
      <Sequence from={START[3]} durationInFrames={S3}>
        {/* Clip A: phone tap create wallet (0→117) */}
        <Sequence from={0} durationInFrames={CLIP}>
          <VideoClipBg videoPath="scenes/scene-3-a.mp4" durationInFrames={CLIP} fadeIn={0} />
        </Sequence>
        {/* Clip B: QR code scan (105→222) */}
        <Sequence from={CLIP - XF} durationInFrames={CLIP}>
          <VideoClipBg videoPath="scenes/scene-3-b.mp4" durationInFrames={CLIP} />
        </Sequence>
        {/* Clip C: backup download + checkmark (210→327) */}
        <Sequence from={2 * CLIP - 2 * XF} durationInFrames={CLIP}>
          <VideoClipBg videoPath="scenes/scene-3-c.mp4" durationInFrames={CLIP} />
        </Sequence>
        {/* Clip D: complete setup reveal (315→453) */}
        <Sequence from={3 * CLIP - 3 * XF} durationInFrames={S3 - (3 * CLIP - 3 * XF)}>
          <VideoClipBg videoPath="scenes/scene-3-d.mp4" durationInFrames={S3 - (3 * CLIP - 3 * XF)} />
        </Sequence>
        {/* Crossfades */}
        <Sequence from={CLIP - XF} durationInFrames={XF * 2}>
          <SubClipFade durationInFrames={XF * 2} />
        </Sequence>
        <Sequence from={2 * CLIP - 2 * XF} durationInFrames={XF * 2}>
          <SubClipFade durationInFrames={XF * 2} />
        </Sequence>
        <Sequence from={3 * CLIP - 3 * XF} durationInFrames={XF * 2}>
          <SubClipFade durationInFrames={XF * 2} />
        </Sequence>

        <BottomGradient intensity={0.6} />

        <SpeakerBadge name="Paw" color={PAW_COLOR} durationInFrames={S3} />

        <WordPopSubtitles
          text={scenes[3].dialogue}
          accentColor={PAW_COLOR}
          durationInFrames={S3}
          highlightWords={["wallet", "QR", "backup", "Done", "seed", "vibes"]}
        />

        <Audio src={staticFile("audio/scene-3.wav")} />
      </Sequence>

      {/* Ping on each step completion */}
      <Sequence from={START[3] + 80} durationInFrames={10}>
        <Audio src={staticFile("sfx/pop.wav")} volume={0.3} />
      </Sequence>
      <Sequence from={START[3] + 180} durationInFrames={10}>
        <Audio src={staticFile("sfx/pop.wav")} volume={0.3} />
      </Sequence>
      <Sequence from={START[3] + 280} durationInFrames={10}>
        <Audio src={staticFile("sfx/pop.wav")} volume={0.3} />
      </Sequence>
      {/* Satisfying ping on "Done" */}
      <Sequence from={START[3] + 340} durationInFrames={10}>
        <Audio src={staticFile("sfx/ping.wav")} volume={0.4} />
      </Sequence>

      {/* ═══════════════════════════════════════════ */}
      {/* TRANSITION: Scene 3 → 4 (bass + glitch)   */}
      {/* ═══════════════════════════════════════════ */}
      <Sequence from={START[4] - 4} durationInFrames={12}>
        <Audio src={staticFile("sfx/bass-drop.wav")} volume={0.45} />
      </Sequence>
      <Sequence from={START[4]} durationInFrames={10}>
        <GlitchFlash color={PAW_COLOR} />
      </Sequence>

      {/* ═══════════════════════════════════════════ */}
      {/* SCENE 4: CTA — Stop trusting napkins       */}
      {/* ═══════════════════════════════════════════ */}
      <Sequence from={START[4]} durationInFrames={S4}>
        <ScreenShake triggerFrame={100} intensity={5}>
          {/* Clip A: split — dumpster fire vs vault (0→117) */}
          <Sequence from={0} durationInFrames={CLIP}>
            <VideoClipBg videoPath="scenes/scene-4-a.mp4" durationInFrames={CLIP} fadeIn={0} />
          </Sequence>
          {/* Clip B: golden shockwave (105→222) */}
          <Sequence from={CLIP - XF} durationInFrames={CLIP}>
            <VideoClipBg videoPath="scenes/scene-4-b.mp4" durationInFrames={CLIP} />
          </Sequence>
          {/* Clip C: lanterns rising, portal (210→330) */}
          <Sequence from={2 * CLIP - 2 * XF} durationInFrames={S4 - (2 * CLIP - 2 * XF)}>
            <VideoClipBg videoPath="scenes/scene-4-c.mp4" durationInFrames={S4 - (2 * CLIP - 2 * XF)} />
          </Sequence>
          {/* Crossfades */}
          <Sequence from={CLIP - XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
          <Sequence from={2 * CLIP - 2 * XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
        </ScreenShake>

        <BottomGradient intensity={0.7} />

        <SpeakerBadge name="Paw" color={PAW_COLOR} durationInFrames={S4} />

        <WordPopSubtitles
          text={scenes[4].dialogue}
          accentColor={PAW_COLOR}
          durationInFrames={S4}
          highlightWords={["napkins", "paw", "home", "crypto"]}
        />

        {/* CTA URL reveal — appears when paw says the URL */}
        <CtaUrl
          url="paw.zkagi.ai"
          color={PAW_COLOR}
          triggerFrame={140}
          durationInFrames={S4}
        />

        <Audio src={staticFile("audio/scene-4.wav")} />
      </Sequence>

      {/* Ping on CTA URL reveal */}
      <Sequence from={START[4] + 140} durationInFrames={10}>
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
