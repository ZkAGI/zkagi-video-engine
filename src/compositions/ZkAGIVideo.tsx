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
import {
  KenBurnsImage,
  GlitchFlash,
  ScreenShake,
  WordPopSubtitles,
  BottomGradient,
  SubClipFade,
  TopicBadge,
  CtaUrl,
  Watermark,
} from "../components";
import { StatGrid, ProductShowcase } from "../components/motion-graphics";
import { getTheme } from "../lib/themes";

// ═══════════════════════════════════════════════════════════════
// MAIN COMPOSITION — ZkAGI Brand Story: The GPU Empire Cracks (Day 10)
// ═══════════════════════════════════════════════════════════════
interface ZkAGIVideoProps extends VideoConfig {
  useGeneratedBackgrounds?: boolean;
}

export const ZkAGIVideo: React.FC<ZkAGIVideoProps> = (props) => {
  const { scenes, characters, style, music, watermark } = props;
  const theme = getTheme(style.theme);

  // Scene durations (30fps) from TTS audio
  // S0: 11.52s → 346   S1: 10.56s → 317   S2: 11.52s → 346
  // S3: 12.16s → 365   S4: 13.92s → 418   S5: 10.40s → 312
  const S0 = 346;
  const S1 = 317;
  const S2 = 346;
  const S3 = 365;
  const S4 = 418;
  const S5 = 312;

  const START = [
    0,
    S0,
    S0 + S1,
    S0 + S1 + S2,
    S0 + S1 + S2 + S3,
    S0 + S1 + S2 + S3 + S4,
  ];

  const ENDING_START = S0 + S1 + S2 + S3 + S4 + S5; // 2104
  const ENDING_CLIP_FRAMES = 300;

  const XF = 8; // crossfade frames

  // Video clip duration at 30fps comp: 97 frames @25fps = 3.88s → 116 comp frames
  const V1 = 116;

  const TOPICS = ["THE DETHRONE", "THE PILE-ON", "REALITY CHECK", "THE HAMMER", "THE ANSWER", "YOUR MOVE"];
  const SCENE_COLORS = ["#EF4444", "#F59E0B", "#8B5CF6", "#F97316", "#06B6D4", "#10B981"];

  // Ken Burns overflow splits for video scenes
  // S0: 346 - 116 = 230 remaining → 2 images: 115, 115
  const S0_R = S0 - V1;
  const S0_KB = [Math.ceil(S0_R / 2), S0_R - Math.ceil(S0_R / 2)];
  // S1: 317 - 116 = 201 remaining → 2 images: 101, 100
  const S1_R = S1 - V1;
  const S1_KB = [Math.ceil(S1_R / 2), S1_R - Math.ceil(S1_R / 2)];
  // S3: 365 - 116 = 249 remaining → 3 images: 83, 83, 83
  const S3_R = S3 - V1;
  const S3_KB = [Math.ceil(S3_R / 3), Math.ceil(S3_R / 3), S3_R - 2 * Math.ceil(S3_R / 3)];
  // S4: 418 - 116 = 302 remaining → 3 images: 101, 101, 100
  const S4_R = S4 - V1;
  const S4_KB = [Math.ceil(S4_R / 3), Math.ceil(S4_R / 3), S4_R - 2 * Math.ceil(S4_R / 3)];

  return (
    <AbsoluteFill style={{ background: "#0a0a1a" }}>

      {/* ═══ SCENE 0: THE DETHRONE — "NVIDIA got pantsed" (11.52s = 346 frames) ═══ */}
      <Sequence from={START[0]} durationInFrames={S0}>
        <ScreenShake triggerFrame={300} intensity={5}>
          {/* Video clip */}
          <Sequence from={0} durationInFrames={V1 + XF}>
            <AbsoluteFill>
              <Video
                src={staticFile("scenes/scene-0-a.mp4")}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
                volume={0}
              />
            </AbsoluteFill>
          </Sequence>
          <Sequence from={V1 - XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
          {/* KB image b */}
          <Sequence from={V1} durationInFrames={S0_KB[0] + XF}>
            <KenBurnsImage imagePath="scenes/scene-0-b.png" durationInFrames={S0_KB[0] + XF} fadeIn={8} direction="pan-left" />
          </Sequence>
          <Sequence from={V1 + S0_KB[0] - XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
          {/* KB image c */}
          <Sequence from={V1 + S0_KB[0]} durationInFrames={S0_KB[1]}>
            <KenBurnsImage imagePath="scenes/scene-0-c.png" durationInFrames={S0_KB[1]} fadeIn={8} direction="zoom-in" />
          </Sequence>
        </ScreenShake>
        <BottomGradient intensity={0.75} />
        <TopicBadge label={TOPICS[0]} color={SCENE_COLORS[0]} durationInFrames={S0} />
        <WordPopSubtitles text={scenes[0].dialogue} accentColor={SCENE_COLORS[0]} durationInFrames={S0}
          highlightWords={["NVIDIA", "undisputed", "king", "billion", "GPU", "pantsed"]} />
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

      {/* ═══ SCENE 1: THE PILE-ON — "Tesla, Boston Dynamics, shattered" (10.56s = 317 frames) ═══ */}
      <Sequence from={START[1]} durationInFrames={S1}>
        <ScreenShake triggerFrame={280} intensity={4}>
          {/* Video clip */}
          <Sequence from={0} durationInFrames={V1 + XF}>
            <AbsoluteFill>
              <Video
                src={staticFile("scenes/scene-1-a.mp4")}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
                volume={0}
              />
            </AbsoluteFill>
          </Sequence>
          <Sequence from={V1 - XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
          {/* KB image b */}
          <Sequence from={V1} durationInFrames={S1_KB[0] + XF}>
            <KenBurnsImage imagePath="scenes/scene-1-b.png" durationInFrames={S1_KB[0] + XF} fadeIn={8} direction="pan-right" />
          </Sequence>
          <Sequence from={V1 + S1_KB[0] - XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
          {/* KB image c */}
          <Sequence from={V1 + S1_KB[0]} durationInFrames={S1_KB[1]}>
            <KenBurnsImage imagePath="scenes/scene-1-c.png" durationInFrames={S1_KB[1]} fadeIn={8} direction="zoom-in" />
          </Sequence>
        </ScreenShake>
        <BottomGradient intensity={0.7} />
        <TopicBadge label={TOPICS[1]} color={SCENE_COLORS[1]} durationInFrames={S1} />
        <WordPopSubtitles text={scenes[1].dialogue} accentColor={SCENE_COLORS[1]} durationInFrames={S1}
          highlightWords={["Tesla", "Boston Dynamics", "intern", "monopoly", "shattered", "live TV"]} />
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

      {/* ═══ SCENE 2: REALITY CHECK — Motion Graphic StatGrid (11.52s = 346 frames) ═══ */}
      <Sequence from={START[2]} durationInFrames={S2}>
        <StatGrid
          title="The AI Reality Check"
          stats={[
            { value: "42%", label: "Sim-to-real performance drop" },
            { value: "1B", label: "Groq requests (0 GPUs)" },
            { value: "Dojo 2", label: "Tesla's custom AI chip" },
            { value: "EU Act", label: "Mandatory compliance" },
          ]}
          accentColor="#8B5CF6"
          durationInFrames={S2}
        />
        <BottomGradient intensity={0.7} />
        <TopicBadge label={TOPICS[2]} color={SCENE_COLORS[2]} durationInFrames={S2} />
        <WordPopSubtitles text={scenes[2].dialogue} accentColor={SCENE_COLORS[2]} durationInFrames={S2}
          highlightWords={["forty-two", "percent", "falls apart", "Simulations", "lied", "receipts"]} />
        <Audio src={staticFile("audio/scene-2.wav")} />
      </Sequence>

      {/* TRANSITION 2→3 */}
      <Sequence from={START[3] - 4} durationInFrames={12}>
        <Audio src={staticFile("sfx/whoosh.wav")} volume={0.4} />
      </Sequence>
      <Sequence from={START[3]} durationInFrames={10}>
        <GlitchFlash color={SCENE_COLORS[3]} />
        <Audio src={staticFile("sfx/pop.wav")} volume={0.4} />
      </Sequence>

      {/* ═══ SCENE 3: THE HAMMER — "EU dropped a bomb" (12.16s = 365 frames) ═══ */}
      <Sequence from={START[3]} durationInFrames={S3}>
        <ScreenShake triggerFrame={320} intensity={5}>
          {/* Video clip */}
          <Sequence from={0} durationInFrames={V1 + XF}>
            <AbsoluteFill>
              <Video
                src={staticFile("scenes/scene-3-a.mp4")}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
                volume={0}
              />
            </AbsoluteFill>
          </Sequence>
          <Sequence from={V1 - XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
          {/* KB image b */}
          <Sequence from={V1} durationInFrames={S3_KB[0] + XF}>
            <KenBurnsImage imagePath="scenes/scene-3-b.png" durationInFrames={S3_KB[0] + XF} fadeIn={8} direction="pan-right" />
          </Sequence>
          <Sequence from={V1 + S3_KB[0] - XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
          {/* KB image c */}
          <Sequence from={V1 + S3_KB[0]} durationInFrames={S3_KB[1] + XF}>
            <KenBurnsImage imagePath="scenes/scene-3-c.png" durationInFrames={S3_KB[1] + XF} fadeIn={8} direction="zoom-in" />
          </Sequence>
          <Sequence from={V1 + S3_KB[0] + S3_KB[1] - XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
          {/* KB image d */}
          <Sequence from={V1 + S3_KB[0] + S3_KB[1]} durationInFrames={S3_KB[2]}>
            <KenBurnsImage imagePath="scenes/scene-3-d.png" durationInFrames={S3_KB[2]} fadeIn={8} direction="zoom-out" />
          </Sequence>
        </ScreenShake>
        <BottomGradient intensity={0.7} />
        <TopicBadge label={TOPICS[3]} color={SCENE_COLORS[3]} durationInFrames={S3} />
        <WordPopSubtitles text={scenes[3].dialogue} accentColor={SCENE_COLORS[3]} durationInFrames={S3}
          highlightWords={["EU", "bomb", "training data", "bias", "banned", "dress code"]} />
        <Audio src={staticFile("audio/scene-3.wav")} />
      </Sequence>

      {/* TRANSITION 3→4 */}
      <Sequence from={START[4] - 4} durationInFrames={12}>
        <Audio src={staticFile("sfx/whoosh.wav")} volume={0.4} />
      </Sequence>
      <Sequence from={START[4]} durationInFrames={10}>
        <GlitchFlash color={SCENE_COLORS[4]} />
        <Audio src={staticFile("sfx/ping.wav")} volume={0.4} />
      </Sequence>

      {/* ═══ SCENE 4: THE ANSWER — "ZkAGI ships" (13.92s = 418 frames) ═══ */}
      <Sequence from={START[4]} durationInFrames={S4}>
        <ScreenShake triggerFrame={380} intensity={4}>
          {/* Video clip */}
          <Sequence from={0} durationInFrames={V1 + XF}>
            <AbsoluteFill>
              <Video
                src={staticFile("scenes/scene-4-a.mp4")}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
                volume={0}
              />
            </AbsoluteFill>
          </Sequence>
          <Sequence from={V1 - XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
          {/* KB image b */}
          <Sequence from={V1} durationInFrames={S4_KB[0] + XF}>
            <KenBurnsImage imagePath="scenes/scene-4-b.png" durationInFrames={S4_KB[0] + XF} fadeIn={8} direction="pan-left" />
          </Sequence>
          <Sequence from={V1 + S4_KB[0] - XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
          {/* KB image c */}
          <Sequence from={V1 + S4_KB[0]} durationInFrames={S4_KB[1] + XF}>
            <KenBurnsImage imagePath="scenes/scene-4-c.png" durationInFrames={S4_KB[1] + XF} fadeIn={8} direction="zoom-in" />
          </Sequence>
          <Sequence from={V1 + S4_KB[0] + S4_KB[1] - XF} durationInFrames={XF * 2}>
            <SubClipFade durationInFrames={XF * 2} />
          </Sequence>
          {/* KB image d */}
          <Sequence from={V1 + S4_KB[0] + S4_KB[1]} durationInFrames={S4_KB[2]}>
            <KenBurnsImage imagePath="scenes/scene-4-d.png" durationInFrames={S4_KB[2]} fadeIn={8} direction="zoom-out" />
          </Sequence>
        </ScreenShake>
        <BottomGradient intensity={0.65} />
        <TopicBadge label={TOPICS[4]} color={SCENE_COLORS[4]} durationInFrames={S4} />
        <WordPopSubtitles text={scenes[4].dialogue} accentColor={SCENE_COLORS[4]} durationInFrames={S4}
          highlightWords={["ZkAGI", "ships", "Zynapse", "ZkTerminal", "PawPad", "Zero", "employees", "all gas"]} />
        <Audio src={staticFile("audio/scene-4.wav")} />
      </Sequence>

      {/* TRANSITION 4→5 */}
      <Sequence from={START[5] - 4} durationInFrames={12}>
        <Audio src={staticFile("sfx/bass-drop.wav")} volume={0.45} />
      </Sequence>
      <Sequence from={START[5]} durationInFrames={10}>
        <GlitchFlash color={SCENE_COLORS[5]} />
      </Sequence>

      {/* ═══ SCENE 5: YOUR MOVE — Motion Graphic ProductShowcase (10.40s = 312 frames) ═══ */}
      <Sequence from={START[5]} durationInFrames={S5}>
        <ProductShowcase
          name="ZkAGI"
          tagline="Zero employees. Full AI product suite."
          features={["Zynapse — Privacy APIs", "ZkTerminal — Trading Signals", "PawPad — Self-Custody Wallet", "Built for the chaos"]}
          url="zkagi.ai"
          accentColor="#10B981"
          durationInFrames={S5}
        />
        <BottomGradient intensity={0.7} />
        <TopicBadge label={TOPICS[5]} color={SCENE_COLORS[5]} durationInFrames={S5} />
        <WordPopSubtitles text={scenes[5].dialogue} accentColor={SCENE_COLORS[5]} durationInFrames={S5}
          highlightWords={["splitting", "three", "middle", "zkagi", "zero employee", "enterprise"]} />
        <CtaUrl url="zkagi.ai" color={SCENE_COLORS[5]} triggerFrame={45} durationInFrames={S5} />
        <Audio src={staticFile("audio/scene-5.wav")} />
      </Sequence>
      <Sequence from={START[5] + 45} durationInFrames={10}>
        <Audio src={staticFile("sfx/ping.wav")} volume={0.4} />
      </Sequence>

      {/* ═══ ENDING CLIP — ending.mp4 (300 frames) ═══ */}
      <Sequence from={ENDING_START} durationInFrames={ENDING_CLIP_FRAMES}>
        <AbsoluteFill>
          <Video
            src={staticFile("video/ending.mp4")}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
            volume={1}
            startFrom={0}
          />
        </AbsoluteFill>
      </Sequence>

      {/* GLOBAL LAYERS */}
      {music.url && <Audio src={staticFile(music.url)} volume={music.volume} loop />}
      {watermark.show && <Watermark text={watermark.text} color={theme.watermarkColor} />}
    </AbsoluteFill>
  );
};
