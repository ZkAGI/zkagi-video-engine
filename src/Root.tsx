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

// ── ZkTerminal Prediction Market Story — Mar 8, 2026 ──
// Story Mode: prediction market degen spots BTC trend 6 hours early
// Audio durations: 8.96 + 9.92 + 8.48 + 12.32 + 9.76 = 49.44s
const ZKTERMINAL_SCENES = [
  {
    characterId: "pad",
    dialogue: "Three AM. Kyle's glued to his charts. Crypto Twitter is screaming about resistance levels. Nobody agrees. Nobody ever does.",
    emotion: "serious" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 8.96,
  },
  {
    characterId: "pad",
    dialogue: "But Kyle's not reading tweets. He's watching ZkTerminal. The AI just flagged a Bitcoin trend reversal. Six hours before anyone else.",
    emotion: "explaining" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 9.92,
  },
  {
    characterId: "pad",
    dialogue: "While everyone debates, Kyle's already locked in. Prediction markets set. Entry confirmed. Zero hesitation.",
    emotion: "excited" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 8.48,
  },
  {
    characterId: "pad",
    dialogue: "Six hours later, the move hits. CT finally catches on. Kyle's already taking profit. Better APIs beat louder opinions every time.",
    emotion: "celebrating" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 12.32,
  },
  {
    characterId: "pad",
    dialogue: "zkterminal dot zkagi dot ai. I don't predict the future. I just have better APIs than you.",
    emotion: "celebrating" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 9.76,
  },
];

// Frame counts from TTS durations (30fps):
// S0: 8.96s → 269   S1: 9.92s → 298   S2: 8.48s → 254
// S3: 12.32s → 370   S4: 9.76s → 293
const TOTAL_FRAMES = 269 + 298 + 254 + 370 + 293 + 300; // = 1784 (scenes + ending clip)

const zkterminalProps = {
  title: "Prediction Market Degen Spots BTC Trend Early",
  characters: CHARACTERS,
  scenes: ZKTERMINAL_SCENES,
  style: { theme: "zkagi-brand" as const, format: "16:9" as const, showSubtitles: true, showCharacterName: false, transitionType: "fade" as const },
  music: { volume: 0.12 },
  watermark: { text: "ZkAGI", show: true },
  useGeneratedBackgrounds: true,
};

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="ZkAGIVideo" component={ZkAGIVideo} durationInFrames={TOTAL_FRAMES} fps={30} width={1920} height={1080} schema={VideoConfigSchema} defaultProps={zkterminalProps} />
    <Composition id="ZkAGIVideoVertical" component={ZkAGIVideo} durationInFrames={TOTAL_FRAMES} fps={30} width={1080} height={1920} schema={VideoConfigSchema} defaultProps={{ ...zkterminalProps, style: { ...zkterminalProps.style, format: "9:16" as const } }} />
  </>
);
