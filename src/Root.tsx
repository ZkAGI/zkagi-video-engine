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
// Audio durations: 10.24 + 8.64 + 11.84 + 9.92 + 9.28 = 49.92s
const ZKTERMINAL_SCENES = [
  {
    characterId: "pad",
    dialogue: "Three AM. Kyle's staring at charts. Crypto Twitter is screaming about resistance levels. Nobody agrees. Nobody ever agrees.",
    emotion: "serious" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 10.24,
  },
  {
    characterId: "pad",
    dialogue: "But Kyle isn't reading tweets. He's reading ZkTerminal. The AI just flagged a Bitcoin trend. Six hours early.",
    emotion: "explaining" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 8.64,
  },
  {
    characterId: "pad",
    dialogue: "While everyone debates direction, Kyle's already in position. Prediction markets locked. Entry set. No hesitation.",
    emotion: "excited" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 11.84,
  },
  {
    characterId: "pad",
    dialogue: "Six hours later, the move hits. CT finally catches on. Kyle's already counting gains. Better APIs beat louder opinions.",
    emotion: "celebrating" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 9.92,
  },
  {
    characterId: "pad",
    dialogue: "terminal dot zkagi dot ai. I don't predict the future. I just have better APIs than you.",
    emotion: "celebrating" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 9.28,
  },
];

// Frame counts from TTS durations (30fps):
// S0: 10.24s → 307   S1: 8.64s → 259   S2: 11.84s → 355
// S3: 9.92s → 298    S4: 9.28s → 278
const TOTAL_FRAMES = 307 + 259 + 355 + 298 + 278; // = 1497

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
