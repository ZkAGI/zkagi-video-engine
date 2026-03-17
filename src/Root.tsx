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

// ── ZkAGI Brand Story — Mar 15, 2026 (Day 10) ──
// Story Mode (funny): GPU Empire Cracks — Groq pantsed NVIDIA, EU dress codes, ZkAGI ships
// Audio durations: 11.52 + 10.56 + 11.52 + 12.16 + 13.92 + 10.40 = 70.08s
const ZKAGI_SCENES = [
  {
    characterId: "pad",
    dialogue: "NVIDIA's been the undisputed king of AI chips. This week, Groq hit one billion requests without a single GPU. The king just got pantsed.",
    emotion: "serious" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 11.52,
  },
  {
    characterId: "pad",
    dialogue: "Tesla built its own AI brain. Boston Dynamics' robot walks better than your intern. The GPU monopoly didn't crack — it shattered on live TV.",
    emotion: "explaining" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 10.56,
  },
  {
    characterId: "pad",
    dialogue: "But MIT found forty-two percent of robot AI falls apart in the real world. Simulations lied. Reality checked the receipts.",
    emotion: "thinking" as const,
    visualType: "talking-head" as const,
    sceneType: "motion-graphic" as const,
    durationOverride: 11.52,
  },
  {
    characterId: "pad",
    dialogue: "And the EU just dropped a bomb. Show your training data, your bias audits, or get banned. Open source just got a dress code.",
    emotion: "serious" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 12.16,
  },
  {
    characterId: "pad",
    dialogue: "ZkAGI ships while the industry argues. Zynapse for private APIs. ZkTerminal for signals. PawPad for wallets. Zero employees, full stack, all gas.",
    emotion: "excited" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 13.92,
  },
  {
    characterId: "pad",
    dialogue: "The AI stack is splitting three ways. Don't get caught in the middle. zkagi dot ai — the zero employee enterprise.",
    emotion: "celebrating" as const,
    visualType: "talking-head" as const,
    sceneType: "motion-graphic" as const,
    durationOverride: 10.40,
  },
];

// Frame counts from TTS durations (30fps):
// S0: 11.52s → 346   S1: 10.56s → 317   S2: 11.52s → 346
// S3: 12.16s → 365   S4: 13.92s → 418   S5: 10.40s → 312
// Ending clip: 300
const TOTAL_FRAMES = 346 + 317 + 346 + 365 + 418 + 312 + 300; // = 2404

const zkAGIProps = {
  title: "The GPU Empire Cracks — ZkAGI",
  characters: CHARACTERS,
  scenes: ZKAGI_SCENES,
  style: { theme: "zkagi-brand" as const, format: "16:9" as const, showSubtitles: true, showCharacterName: false, transitionType: "fade" as const },
  music: { volume: 0.12 },
  watermark: { text: "ZkAGI", show: true },
  useGeneratedBackgrounds: true,
};

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="ZkAGIVideo" component={ZkAGIVideo} durationInFrames={TOTAL_FRAMES} fps={30} width={1920} height={1080} schema={VideoConfigSchema} defaultProps={zkAGIProps} />
    <Composition id="ZkAGIVideoVertical" component={ZkAGIVideo} durationInFrames={TOTAL_FRAMES} fps={30} width={1080} height={1920} schema={VideoConfigSchema} defaultProps={{ ...zkAGIProps, style: { ...zkAGIProps.style, format: "9:16" as const } }} />
  </>
);
