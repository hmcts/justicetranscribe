/* eslint-disable no-plusplus */
/* eslint-disable no-promise-executor-return */
/* eslint-disable no-await-in-loop */
/* eslint-disable no-restricted-syntax */
import { DialogueEntry, TranscriptionJob } from "@/src/api/generated";
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

import { LangfuseWeb } from "langfuse";
import { getMinuteVersionById, MinuteVersion } from "@/lib/database";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default cn;

export function concatenateDialogueEntriesInTranscriptionJobs(
  jobs: TranscriptionJob[],
): DialogueEntry[] {
  return jobs.flatMap((job) => job.dialogue_entries);
}

export function replaceSpeakerInDialogueEntries(
  entries: DialogueEntry[],
  oldSpeaker: string,
  newSpeaker: string,
): DialogueEntry[] {
  return entries.map((entry) =>
    entry.speaker === oldSpeaker ? { ...entry, speaker: newSpeaker } : entry,
  );
}

export const langfuseWeb = new LangfuseWeb({
  publicKey: "pk-lf-16763a4a-2b6e-4705-89c5-ef25239a4ccf",
  baseUrl: "https://cloud.langfuse.com", // 🇪🇺 EU region
});

export const findExistingMinuteVersionForTemplate = (
  minuteVersions: MinuteVersion[],
  templateName: string,
): MinuteVersion | undefined => {
  return minuteVersions
    .filter((version) => version.template.name === templateName)
    .sort((a, b) => {
      const dateA = new Date(a.created_datetime || "").getTime();
      const dateB = new Date(b.created_datetime || "").getTime();
      return dateB - dateA; // Sort in descending order (newest first)
    })[0];
};

export async function pollMinuteVersion(
  transcriptionId: string,
  versionId: string,
  options: {
    maxAttempts?: number;
    interval?: number;
  } = {},
): Promise<MinuteVersion> {
  const maxAttempts = options.maxAttempts ?? 210; // 7 minutes total
  const interval = options.interval ?? 2000; // 2 seconds
  let attempts = 0;

  while (attempts < maxAttempts) {
    const version = await getMinuteVersionById(transcriptionId, versionId);
    if (version && !version.is_generating) {
      return version as MinuteVersion;
    }
    await new Promise((resolve) => setTimeout(resolve, interval));
    attempts++;
  }

  throw new Error("Timeout: Failed to get minute version after 7 minutes");
}

export const getFirstName = (email: string) => {
  try {
    if (!email || typeof email !== "string") {
      return "";
    }

    const beforeAt = email.split("@")[0];
    if (!beforeAt) {
      return "";
    }

    const firstName = beforeAt.split(".")[0];
    return firstName || "";
  } catch (error) {
    console.warn("Error extracting first name from email:", error);
    return "";
  }
};
