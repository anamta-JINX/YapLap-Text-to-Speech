import { Angry, Frown, Meh, Smile, type LucideIcon } from "lucide-react";

export type VoiceId = "zubeda" | "khalda" | "samundar" | "jameed";
export type ToneId = "neutral" | "happy" | "sad" | "angry";
export type AccentId = "general" | "american" | "british" | "australian" | "indian";

export type VoiceOption = {
  id: VoiceId;
  name: string;
  note: string;
  initials: string;
};

export type ToneOption = {
  id: ToneId;
  label: string;
  note: string;
  icon: LucideIcon;
};

export type AccentOption = {
  id: AccentId;
  label: string;
  locale: string;
};

export const MAX_CHARS = 5000;

export const voices: VoiceOption[] = [
  { id: "zubeda", name: "Zubeda", note: "woman · warm + grounded", initials: "ZU" },
  { id: "khalda", name: "Khalda", note: "woman · bright + crisp", initials: "KH" },
  { id: "samundar", name: "Samundar Khan", note: "man · deep + steady", initials: "SK" },
  { id: "jameed", name: "Jameed", note: "man · clear + upbeat", initials: "JA" },
];

export const tones: ToneOption[] = [
  { id: "neutral", label: "Neutral", note: "steady + clear", icon: Meh },
  { id: "happy", label: "Happy", note: "bright + upbeat", icon: Smile },
  { id: "sad", label: "Sad", note: "soft + slower", icon: Frown },
  { id: "angry", label: "Angry", note: "firm + intense", icon: Angry },
];

export const accents: AccentOption[] = [
  { id: "general", label: "General English", locale: "en" },
  { id: "american", label: "American", locale: "en-US" },
  { id: "british", label: "British", locale: "en-GB" },
  { id: "australian", label: "Australian", locale: "en-AU" },
  { id: "indian", label: "Indian", locale: "en-IN" },
];

export const examples = [
  {
    label: "Motivation",
    text: "You do not need permission to take up space. Say it like you mean it.",
  },
  {
    label: "Product Demo",
    text: "Meet the idea that turns a complicated workflow into one simple click.",
  },
  {
    label: "Bedtime Story",
    text: "The moon tucked itself behind a cloud while the little fox finally found its way home.",
  },
  {
    label: "Announcement",
    text: "Quick update: the launch is live, the doors are open, and we cannot wait to show you around.",
  },
];

export const wave = [
  18, 32, 52, 26, 68, 42, 78, 36, 58, 24, 72, 48, 30, 62, 84, 44,
  66, 28, 54, 38, 76, 48, 64, 34, 56, 22, 70, 42, 58, 30, 48, 20,
];
