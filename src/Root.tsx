import { Composition } from "remotion";
import { ZkAGIVideo } from "./compositions/ZkAGIVideo";
import { VideoConfigSchema } from "./types";

// ── Tiger characters (ZkAGI mascots) ──
const CHARACTERS = {
  paw: {
    id: "paw", name: "Paw", color: "#7C3AED", role: "host",
    poses: {
      neutral: "/characters/paw/neutral.png",
      excited: "/characters/paw/excited.png",
      waving: "/characters/paw/neutral.png",
      explaining: "/characters/paw/neutral.png",
      thinking: "/characters/paw/neutral.png",
      serious: "/characters/paw/neutral.png",
      celebrating: "/characters/paw/excited.png",
    },
    voice: { refAudioPath: "./voices/paw.wav", refText: "ZM folks, here is your July 24th 2025 crypto update. Bitcoin is trading around 118520 US dollars.", cfgValue: "2.0", steps: "15" },
  },
  pad: {
    id: "pad", name: "Pad", color: "#06B6D4", role: "explainer",
    poses: {
      neutral: "/characters/pad/neutral.png",
      thinking: "/characters/pad/thinking.png",
      serious: "/characters/pad/thinking.png",
      explaining: "/characters/pad/neutral.png",
      excited: "/characters/pad/neutral.png",
      waving: "/characters/pad/neutral.png",
      celebrating: "/characters/pad/neutral.png",
    },
    voice: { refAudioPath: "./voices/pad.wav", refText: "Today, software handles our money, our health, our work.", cfgValue: "2.0", steps: "15" },
  },
};

// ── "This Video Was Made By AI" — Mar 9, 2026 ──
// Story Mode: Meta self-referential AI demo → ZkAGI Video Engine
// Audio durations: 10.08 + 10.24 + 6.88 + 9.60 + 7.84 = 44.64s
const META_AI_SCENES = [
  {
    characterId: "pad",
    dialogue: "This video was made by AI. Script, voice, images, editing. All AI. Zero humans touched this.",
    emotion: "serious" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 10.08,
  },
  {
    characterId: "pad",
    dialogue: "A language model wrote these exact words. Then it cloned a tiger's voice, generated every frame, and edited everything together.",
    emotion: "explaining" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 10.24,
  },
  {
    characterId: "pad",
    dialogue: "You're not watching a demo of the product. You're watching the product demo itself. Inception level meta.",
    emotion: "thinking" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 6.88,
  },
  {
    characterId: "pad",
    dialogue: "Most companies show you a slideshow about their AI. We let our AI make the slideshow. And this sentence.",
    emotion: "excited" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 9.60,
  },
  {
    characterId: "pad",
    dialogue: "ZkAGI Video Engine. One prompt. Full production. zkagi dot ai.",
    emotion: "celebrating" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 7.84,
  },
];

// Frame counts from TTS durations (30fps):
// S0: 10.08s → 302   S1: 10.24s → 307   S2: 6.88s → 206
// S3: 9.60s → 288   S4: 7.84s → 235
// BrandOutro: 275   Ending clip: 300
const TOTAL_FRAMES = 302 + 307 + 206 + 288 + 235 + 275 + 300; // = 1913

const metaAiProps = {
  title: "This Video Was Made By AI — ZkAGI",
  characters: CHARACTERS,
  scenes: META_AI_SCENES,
  style: { theme: "zkagi-brand" as const, format: "16:9" as const, showSubtitles: true, showCharacterName: false, transitionType: "fade" as const },
  music: { volume: 0.12 },
  watermark: { text: "ZkAGI", show: true },
  useGeneratedBackgrounds: true,
};

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="ZkAGIVideo" component={ZkAGIVideo} durationInFrames={TOTAL_FRAMES} fps={30} width={1920} height={1080} schema={VideoConfigSchema} defaultProps={metaAiProps} />
    <Composition id="ZkAGIVideoVertical" component={ZkAGIVideo} durationInFrames={TOTAL_FRAMES} fps={30} width={1080} height={1920} schema={VideoConfigSchema} defaultProps={{ ...metaAiProps, style: { ...metaAiProps.style, format: "9:16" as const } }} />
  </>
);
