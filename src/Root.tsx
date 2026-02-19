import { Composition } from "remotion";
import { ZkAGIVideo } from "./compositions/ZkAGIVideo";
import { VideoConfigSchema } from "./types";

// ── Default tiger characters (PawPad mascots) ──
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

// ── PawPad Wallet Video Scenes ──
// Audio durations: 8.0, 7.2, 7.36, 7.68, 16.48, 2.88 seconds (~49.6s total)
const PAWPAD_SCENES = [
  {
    characterId: "paw",
    dialogue: "Hey crypto fans! Welcome to PawPad, the friendliest and most secure wallet in the entire web3 space!",
    emotion: "excited" as const,
    visualType: "talking-head" as const,
    highlightText: "Welcome to PawPad",
    durationOverride: 8.0,
  },
  {
    characterId: "pad",
    dialogue: "PawPad uses multi-party computation to keep your private keys secure. Your keys are split across multiple servers.",
    emotion: "thinking" as const,
    visualType: "talking-head" as const,
    highlightText: "Multi-Party Computation",
    durationOverride: 7.2,
  },
  {
    characterId: "pad",
    dialogue: "With biometric authentication and hardware wallet support, your assets stay protected at all times.",
    emotion: "explaining" as const,
    visualType: "talking-head" as const,
    highlightText: "Biometric Security",
    durationOverride: 7.36,
  },
  {
    characterId: "pad",
    dialogue: "Send, receive, and swap tokens across multiple blockchains with just one tap. It is cross-chain made simple.",
    emotion: "neutral" as const,
    visualType: "talking-head" as const,
    highlightText: "Cross-Chain Simple",
    durationOverride: 7.68,
  },
  {
    characterId: "paw",
    dialogue: "Plus, PawPad supports NFTs, DeFi protocols, and comes with built-in gas optimization to save you money!",
    emotion: "excited" as const,
    visualType: "talking-head" as const,
    highlightText: "NFTs + DeFi + Gas Savings",
    durationOverride: 16.48,
  },
  {
    characterId: "paw",
    dialogue: "Download PawPad today and experience crypto the way it should be. Secure, simple, and fun!",
    emotion: "celebrating" as const,
    visualType: "talking-head" as const,
    highlightText: "Download PawPad!",
    durationOverride: 2.88,
  },
];

// Total frames: ~49.6 seconds at 30fps
const TOTAL_FRAMES = Math.ceil((8.0 + 7.2 + 7.36 + 7.68 + 16.48 + 2.88) * 30);

const pawpadProps = {
  title: "PawPad Wallet",
  characters: CHARACTERS,
  scenes: PAWPAD_SCENES,
  style: { theme: "pawpad" as const, format: "16:9" as const, showSubtitles: true, showCharacterName: true, transitionType: "fade" as const },
  music: { volume: 0.12 },
  watermark: { text: "PawPad", show: true },
  useGeneratedBackgrounds: true,
};

// Demo scenes for testing
const DEMO_SCENES = [
  { characterId: "paw", dialogue: "Welcome to ZkAGI! Where privacy meets intelligence.", emotion: "excited" as const, visualType: "talking-head" as const },
  { characterId: "pad", dialogue: "Today we are exploring how zero-knowledge proofs keep your data safe.", emotion: "thinking" as const, visualType: "talking-head" as const, highlightText: "Zero-Knowledge Proofs" },
];

const demoProps = {
  title: "ZkAGI Demo",
  characters: CHARACTERS,
  scenes: DEMO_SCENES,
  style: { theme: "zkagi-brand" as const, format: "16:9" as const, showSubtitles: true, showCharacterName: true, transitionType: "fade" as const },
  music: { volume: 0.12 },
  watermark: { text: "ZkAGI", show: true },
  useGeneratedBackgrounds: false,
};

export const RemotionRoot: React.FC = () => (
  <>
    {/* PawPad Wallet Video - Main composition */}
    <Composition id="ZkAGIVideo" component={ZkAGIVideo} durationInFrames={TOTAL_FRAMES} fps={30} width={1920} height={1080} schema={VideoConfigSchema} defaultProps={pawpadProps} />
    <Composition id="ZkAGIVideoVertical" component={ZkAGIVideo} durationInFrames={TOTAL_FRAMES} fps={30} width={1080} height={1920} schema={VideoConfigSchema} defaultProps={{ ...pawpadProps, style: { ...pawpadProps.style, format: "9:16" as const } }} />
    <Composition id="ZkAGIVideoSquare" component={ZkAGIVideo} durationInFrames={TOTAL_FRAMES} fps={30} width={1080} height={1080} schema={VideoConfigSchema} defaultProps={{ ...pawpadProps, style: { ...pawpadProps.style, format: "1:1" as const } }} />

    {/* Demo composition with gradient backgrounds */}
    <Composition id="ZkAGIDemo" component={ZkAGIVideo} durationInFrames={240} fps={30} width={1920} height={1080} schema={VideoConfigSchema} defaultProps={demoProps} />
  </>
);
