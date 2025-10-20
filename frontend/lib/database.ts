import {
  TranscriptionMetadata,
  Transcription,
  TranscriptionJob,
  User,
  MinuteVersion_Input,
} from "@/src/api/generated";
import { apiClient } from "@/lib/api-client";

export type MinuteVersion = MinuteVersion_Input;

/**
 * Saves a transcription to the backend
 */
export const saveTranscription = async (
  transcription: Transcription
): Promise<void> => {
  try {
    const result = await apiClient.request("/transcriptions", {
      method: "POST",
      body: JSON.stringify(transcription),
    });

    if (result.error) {
      throw new Error(`Error saving transcription: ${result.error}`);
    }
  } catch (error) {
    console.error("Error saving transcription:", error);
  }
};

/**
 * Loads a specific transcription by ID
 * Returns null if not found
 */
export const getTranscriptionById = async (
  id: string
): Promise<Transcription | null> => {
  try {
    const result = await apiClient.request<Transcription>(
      `/transcriptions/${id}`
    );

    if (result.error) {
      throw new Error(`Error fetching transcription: ${result.error}`);
    }

    return result.data || null;
  } catch (error) {
    console.error("Error fetching transcription:", error);
    return null;
  }
};

/**
 * Gets metadata for all stored transcriptions
 */
export const getAllTranscriptionMetadata = async (): Promise<
  TranscriptionMetadata[]
> => {
  try {
    const result = await apiClient.request<TranscriptionMetadata[]>(
      "/transcriptions-metadata"
    );

    if (result.error) {
      throw new Error(
        `Error fetching transcriptions metadata: ${result.error}`
      );
    }

    const metadata = result.data || [];
    return metadata.map((m) => ({
      ...m,
      created_datetime: new Date(m.created_datetime || "").toISOString(),
    }));
  } catch (error) {
    console.error("Error fetching transcriptions metadata:", error);
    return [];
  }
};

/**
 * Deletes a transcription by ID
 */
export const deleteTranscription = async (id: string): Promise<void> => {
  try {
    const result = await apiClient.request(`/transcriptions/${id}`, {
      method: "DELETE",
    });

    if (result.error) {
      throw new Error(`Error deleting transcription: ${result.error}`);
    }

    // eslint-disable-next-line no-console
    console.log("Transcription deleted successfully");
  } catch (error) {
    console.error("Error deleting transcription:", error);
  }
};

export const getMinuteVersions = async (
  transcriptionId: string
): Promise<MinuteVersion[]> => {
  try {
    const result = await apiClient.request<MinuteVersion[]>(
      `/transcriptions/${transcriptionId}/minute-versions`
    );

    if (result.error) {
      throw new Error(`Error fetching minute versions: ${result.error}`);
    }

    return result.data || [];
  } catch (error) {
    console.error("Error fetching minute versions:", error);
    return [];
  }
};

export const saveMinuteVersion = async (
  transcriptionId: string,
  data: MinuteVersion
) => {
  const result = await apiClient.request<MinuteVersion>(
    `/transcriptions/${transcriptionId}/minute-versions`,
    {
      method: "POST",
      body: JSON.stringify(data),
    }
  );

  if (result.error) {
    throw new Error(`Error creating minute version: ${result.error}`);
  }

  return result.data!;
};

export const getTranscriptionJobs = async (
  transcriptionId: string
): Promise<TranscriptionJob[]> => {
  try {
    const result = await apiClient.request<TranscriptionJob[]>(
      `/transcriptions/${transcriptionId}/jobs`
    );

    if (result.error) {
      throw new Error(`Error fetching transcription jobs: ${result.error}`);
    }

    return result.data || [];
  } catch (error) {
    console.error("Error fetching transcription jobs:", error);
    return [];
  }
};

export const saveTranscriptionJob = async (
  transcriptionId: string,
  jobData: TranscriptionJob
) => {
  try {
    const result = await apiClient.request<TranscriptionJob>(
      `/transcriptions/${transcriptionId}/jobs`,
      {
        method: "POST",
        body: JSON.stringify(jobData),
      }
    );

    if (result.error) {
      throw new Error(`Error creating transcription job: ${result.error}`);
    }

    return result.data!;
  } catch (error) {
    console.error("Error creating transcription job:", error);
    throw error;
  }
};

export const getMinuteVersionById = async (
  transcriptionId: string,
  minuteVersionId: string
): Promise<MinuteVersion | null> => {
  try {
    const result = await apiClient.request<MinuteVersion>(
      `/transcriptions/${transcriptionId}/minute-versions/${minuteVersionId}`
    );

    if (result.error) {
      throw new Error(`Error fetching minute version: ${result.error}`);
    }

    return result.data || null;
  } catch (error) {
    console.error("Error fetching minute version:", error);
    return null;
  }
};

/**
 * Gets the current user from the backend
 */
export const getCurrentUser = async (): Promise<User | null> => {
  try {
    const result = await apiClient.getCurrentUser();
    if (result.error) {
      throw new Error(`Error fetching user: ${result.error}`);
    }
    return result.data || null;
  } catch (error) {
    console.error("Error fetching user:", error);
    return null;
  }
};

/**
 * Updates the current user in the backend
 * Pass only the fields you want to update (e.g., { hide_citations: true })
 */
export const updateCurrentUser = async (
  updates: Partial<User>
): Promise<User | null> => {
  try {
    const result = await apiClient.request<User>("/user", {
      method: "POST",
      body: JSON.stringify(updates),
    });
    if (result.error) {
      throw new Error(`Error updating user: ${result.error}`);
    }
    return result.data || null;
  } catch (error) {
    console.error("Error updating user:", error);
    return null;
  }
};
