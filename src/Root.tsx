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

// ── PawPad Wallet Creation Demo (60s, 4 scenes, all pad voice) ──
// Audio durations: 13.92s + 15.36s + 17.92s + 14.56s = 61.76s
const PAWPAD_SCENES = [
  {
    characterId: "pad",
    dialogue: "Twenty four random words written down on a piece of paper. That is your master plan for protecting your entire life savings? Come on now. That is not security. That is like writing your bank password on a napkin and praying nobody finds it.",
    emotion: "serious" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 13.92,
  },
  {
    characterId: "pad",
    dialogue: "PawPad generates your wallet keys inside a hardware vault called a Trusted Execution Environment. Your keys never leave the vault. Not hackers, not node operators, nobody can see what is inside. It is like a safe that only opens for you.",
    emotion: "explaining" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 15.36,
  },
  {
    characterId: "pad",
    dialogue: "Here is how easy it is. Open PawPad, tap create wallet, choose seedless wallet. A QR code pops up on screen. Scan it with Google Authenticator, save your encrypted backup file, and boom. Your wallet is live. Thirty seconds flat.",
    emotion: "excited" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 17.92,
  },
  {
    characterId: "pad",
    dialogue: "No seed phrases to lose. No passwords to forget. Just your keys locked in hardware that nobody can crack. Stop trusting napkins with your life savings. Try PawPad right now at paw dot zkagi dot ai.",
    emotion: "celebrating" as const,
    visualType: "talking-head" as const,
    sceneType: "video" as const,
    durationOverride: 14.56,
  },
];

// Total: 418 + 461 + 538 + 437 = 1854 frames at 30fps = 61.8s
const TOTAL_FRAMES = 1854;

const pawpadProps = {
  title: "PawPad: Your Keys, Locked in Hardware",
  characters: CHARACTERS,
  scenes: PAWPAD_SCENES,
  style: { theme: "pawpad" as const, format: "16:9" as const, showSubtitles: true, showCharacterName: false, transitionType: "fade" as const },
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
