import { Composition } from "remotion";
import { ZkAGIVideo } from "./compositions/ZkAGIVideo";
import { VideoConfigSchema } from "./types";

// ── Tiger characters (PawPad mascots) ──
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

// ── PawPad Seed Phrase Roast (55s, 5 scenes, paw voice) ──
// Audio durations: 5.92s + 10.08s + 8.64s + 14.24s + 8.32s = 47.2s
const PAWPAD_SCENES = [
  {
    characterId: "paw",
    dialogue: "You wrote 24 secret words on a napkin and called it security? That's not a backup plan, that's a treasure map for hackers.",
    emotion: "serious" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 5.92,
  },
  {
    characterId: "paw",
    dialogue: "Every year, billions in crypto vanish because someone's master plan was a sticky note on the fridge. One spill, one house fire, one nosy roommate, and poof. All gone.",
    emotion: "serious" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 10.08,
  },
  {
    characterId: "paw",
    dialogue: "PawPad locks your keys inside a hardware vault. They never leave. Not to your phone, not to the cloud, not to anyone. Even we can't peek.",
    emotion: "explaining" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 8.64,
  },
  {
    characterId: "paw",
    dialogue: "Three taps to create a wallet. Scan a QR code with Google Authenticator. Download your backup file. Done. No seed phrase anywhere. Just vibes and security.",
    emotion: "excited" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 14.24,
  },
  {
    characterId: "paw",
    dialogue: "Stop trusting napkins with your life savings. paw dot zkagi dot ai. Your crypto finally has a real home.",
    emotion: "celebrating" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 8.32,
  },
];

// Total: 208 + 328 + 285 + 453 + 330 = 1604 frames at 30fps = 53.5s
const TOTAL_FRAMES = 1604;

const pawpadProps = {
  title: "PawPad: Stop Trusting Napkins",
  characters: CHARACTERS,
  scenes: PAWPAD_SCENES,
  style: { theme: "zkagi-brand" as const, format: "16:9" as const, showSubtitles: true, showCharacterName: false, transitionType: "fade" as const },
  music: { volume: 0.12 },
  watermark: { text: "PawPad", show: true },
  useGeneratedBackgrounds: true,
};

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="ZkAGIVideo" component={ZkAGIVideo} durationInFrames={TOTAL_FRAMES} fps={30} width={1920} height={1080} schema={VideoConfigSchema} defaultProps={pawpadProps} />
    <Composition id="ZkAGIVideoVertical" component={ZkAGIVideo} durationInFrames={TOTAL_FRAMES} fps={30} width={1080} height={1920} schema={VideoConfigSchema} defaultProps={{ ...pawpadProps, style: { ...pawpadProps.style, format: "9:16" as const } }} />
  </>
);
