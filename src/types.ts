import { z } from "zod";

// ── Emotions map to character pose images ──
export const EmotionEnum = z.enum([
  "neutral", "excited", "thinking", "serious",
  "explaining", "celebrating", "waving",
]);
export type Emotion = z.infer<typeof EmotionEnum>;

// ── Character: poses + voice config ──
export const CharacterSchema = z.object({
  id: z.string(),
  name: z.string(),
  color: z.string(),
  role: z.string(),
  poses: z.record(EmotionEnum, z.string()),
  voice: z.object({
    refAudioPath: z.string(),
    refText: z.string(),
    cfgValue: z.string().default("2.0"),
    steps: z.string().default("15"),
  }),
});
export type Character = z.infer<typeof CharacterSchema>;

// ── Scene: one dialogue block ──
export const VisualTypeEnum = z.enum([
  "talking-head", "split-screen", "text-overlay", "character-only",
]);

export const SceneSchema = z.object({
  characterId: z.string(),
  dialogue: z.string(),
  emotion: EmotionEnum.default("neutral"),
  visualType: VisualTypeEnum.default("talking-head"),
  backgroundUrl: z.string().optional(),
  backgroundColor: z.string().optional(),
  highlightText: z.string().optional(),
  durationOverride: z.number().optional(),
});
export type Scene = z.infer<typeof SceneSchema>;

// ── Full video config ──
export const VideoStyleSchema = z.object({
  theme: z.enum(["dark", "light", "zkagi-brand", "pawpad"]).default("zkagi-brand"),
  format: z.enum(["16:9", "9:16", "1:1"]).default("16:9"),
  showSubtitles: z.boolean().default(true),
  showCharacterName: z.boolean().default(true),
  transitionType: z.enum(["fade", "slide", "none"]).default("fade"),
});

export const VideoConfigSchema = z.object({
  title: z.string(),
  characters: z.record(z.string(), CharacterSchema),
  scenes: z.array(SceneSchema).min(1),
  style: VideoStyleSchema.default({}),
  music: z.object({
    url: z.string().optional(),
    volume: z.number().default(0.12),
  }).default({}),
  watermark: z.object({
    text: z.string().default("ZkAGI"),
    show: z.boolean().default(true),
  }).default({}),
});
export type VideoConfig = z.infer<typeof VideoConfigSchema>;
