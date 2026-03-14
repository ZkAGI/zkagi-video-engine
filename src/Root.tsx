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

// ── ZkAGI Brand Story — Mar 14, 2026 ──
// Story Mode (funny): AI chaos digest — robots fail, NVIDIA dumped, EU assigns homework
// Audio durations: 8.48 + 12.80 + 12.16 + 9.12 + 13.28 + 7.52 = 63.36s
const ZKAGI_SCENES = [
  {
    characterId: "pad",
    dialogue: "Robots just scored forty-two percent worse in real life than in simulations. The future showed up and face-planted on the doorstep.",
    emotion: "serious" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 8.48,
  },
  {
    characterId: "pad",
    dialogue: "While robots trip, NVIDIA's crying. Groq served a billion requests with zero GPUs. Tesla built its own chip. Everyone's dumping NVIDIA.",
    emotion: "explaining" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 12.80,
  },
  {
    characterId: "pad",
    dialogue: "And now the EU wants a permission slip for every AI model. Explainability reports. Bias audits. Your AI has homework.",
    emotion: "thinking" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 12.16,
  },
  {
    characterId: "pad",
    dialogue: "Three industries cracking at once. New chips, new rules, new excuses. Engineers are rebuilding the plane mid-flight in a thunderstorm.",
    emotion: "serious" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 9.12,
  },
  {
    characterId: "pad",
    dialogue: "ZkAGI ships while the industry argues. Zynapse for APIs. ZkTerminal for signals. PawPad for wallets. Zero employees, all products.",
    emotion: "excited" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 13.28,
  },
  {
    characterId: "pad",
    dialogue: "The chaos won't stop. Build anyway. zkagi dot ai.",
    emotion: "celebrating" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 7.52,
  },
];

// Frame counts from TTS durations (30fps):
// S0: 8.48s → 255   S1: 12.80s → 384   S2: 12.16s → 365
// S3: 9.12s → 274   S4: 13.28s → 399   S5: 7.52s → 226
// Ending clip: 300
const TOTAL_FRAMES = 255 + 384 + 365 + 274 + 399 + 226 + 300; // = 2203

const zkAGIProps = {
  title: "The AI Industry is Having the Worst Week — ZkAGI",
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
