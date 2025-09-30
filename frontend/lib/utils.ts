/* eslint-disable no-plusplus */
/* eslint-disable no-promise-executor-return */
/* eslint-disable no-await-in-loop */
/* eslint-disable no-restricted-syntax */
import { DialogueEntry, TranscriptionJob } from "@/src/api/generated";
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

import { getMinuteVersionById, MinuteVersion } from "@/lib/database";

// Constant for fallback when no meeting title is available
export const DEFAULT_MEETING_TITLE = "Untitled Meeting";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default cn;

export function concatenateDialogueEntriesInTranscriptionJobs(
  jobs: TranscriptionJob[]
): DialogueEntry[] {
  return jobs.flatMap((job) => job.dialogue_entries);
}

export function replaceSpeakerInDialogueEntries(
  entries: DialogueEntry[],
  oldSpeaker: string,
  newSpeaker: string
): DialogueEntry[] {
  return entries.map((entry) =>
    entry.speaker === oldSpeaker ? { ...entry, speaker: newSpeaker } : entry
  );
}

// Langfuse trace submission via backend proxy
export const submitLangfuseTrace = async (params: {
  traceId: string;
  name: string;
  metadata?: Record<string, any>;
  inputData?: Record<string, any> | string;
  outputData?: Record<string, any> | string;
}) => {
  const { apiClient } = await import("@/lib/api-client");

  const result = await apiClient.request("/langfuse/trace", {
    method: "POST",
    body: JSON.stringify({
      trace_id: params.traceId,
      name: params.name,
      metadata: params.metadata,
      input_data: params.inputData,
      output_data: params.outputData,
    }),
  });

  if (result.error) {
    throw new Error(`Failed to submit trace: ${result.error}`);
  }

  return result.data;
};

// Langfuse score submission via backend proxy
export const submitLangfuseScore = async (params: {
  traceId: string;
  name: string;
  value: number;
  comment?: string;
}) => {
  const { apiClient } = await import("@/lib/api-client");

  const result = await apiClient.request("/langfuse/score", {
    method: "POST",
    body: JSON.stringify({
      trace_id: params.traceId,
      name: params.name,
      value: params.value,
      comment: params.comment,
    }),
  });

  if (result.error) {
    throw new Error(`Failed to submit score: ${result.error}`);
  }

  return result.data;
};

export const findExistingMinuteVersionForTemplate = (
  minuteVersions: MinuteVersion[],
  templateName: string
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
  } = {}
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
