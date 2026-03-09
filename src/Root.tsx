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

// ── PawPad DeFi Horror Stories — Mar 9, 2026 ──
// Story Mode: DeFi horror stories → PawPad solution
// Audio durations: 7.68 + 11.52 + 8.32 + 10.56 + 8.64 = 46.72s
const PAWPAD_SCENES = [
  {
    characterId: "pad",
    dialogue: "Meet Rick. Rick approved unlimited token access to definitely not a rug dot finance. Rick woke up broke.",
    emotion: "serious" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 7.68,
  },
  {
    characterId: "pad",
    dialogue: "Then there's Karen. Wrote her seed phrase on a napkin. Her husband used it to blow his nose. Forty thousand dollars. In a tissue.",
    emotion: "explaining" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 11.52,
  },
  {
    characterId: "pad",
    dialogue: "Rick and Karen have one thing in common. Their wallets were dumber than they were. What if your wallet could actually think?",
    emotion: "thinking" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 8.32,
  },
  {
    characterId: "pad",
    dialogue: "PawPad. No seed phrase to lose. Smart limits that block suspicious contracts. An AI agent that flags rugs before you click. Three taps.",
    emotion: "excited" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 10.56,
  },
  {
    characterId: "pad",
    dialogue: "paw dot zkagi dot ai. Your wallet should be smarter than you. PawPad finally makes that possible.",
    emotion: "celebrating" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 8.64,
  },
];

// Frame counts from TTS durations (30fps):
// S0: 7.68s → 230   S1: 11.52s → 346   S2: 8.32s → 250
// S3: 10.56s → 317   S4: 8.64s → 259
// BrandOutro: 275   Ending clip: 300
const TOTAL_FRAMES = 230 + 346 + 250 + 317 + 259 + 275 + 300; // = 1977

const pawpadProps = {
  title: "DeFi Horror Stories — PawPad",
  characters: CHARACTERS,
  scenes: PAWPAD_SCENES,
  style: { theme: "zkagi-brand" as const, format: "16:9" as const, showSubtitles: true, showCharacterName: false, transitionType: "fade" as const },
  music: { volume: 0.12 },
  watermark: { text: "ZkAGI", show: true },
  useGeneratedBackgrounds: true,
};

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="ZkAGIVideo" component={ZkAGIVideo} durationInFrames={TOTAL_FRAMES} fps={30} width={1920} height={1080} schema={VideoConfigSchema} defaultProps={pawpadProps} />
    <Composition id="ZkAGIVideoVertical" component={ZkAGIVideo} durationInFrames={TOTAL_FRAMES} fps={30} width={1080} height={1920} schema={VideoConfigSchema} defaultProps={{ ...pawpadProps, style: { ...pawpadProps.style, format: "9:16" as const } }} />
  </>
);
