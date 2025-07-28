import {
  TranscriptionMetadata,
  Transcription,
  TranscriptionJob,
  User,
  MinuteVersion_Input,
} from "@/src/api/generated";

export type MinuteVersion = MinuteVersion_Input;

/**
 * Saves a transcription to the backend
 */
export const saveTranscription = async (
  transcription: Transcription,
): Promise<void> => {
  try {
    const response = await fetch(`/api/proxy/transcriptions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(transcription),
    });

    if (!response.ok) {
      throw new Error(`Error saving transcription: ${response.statusText}`);
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
  id: string,
): Promise<Transcription | null> => {
  try {
    const response = await fetch(`/api/proxy/transcriptions/${id}`);

    if (!response.ok) {
      throw new Error(`Error fetching transcription: ${response.statusText}`);
    }

    return await response.json();
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
    const response = await fetch(`/api/proxy/transcriptions-metadata`);

    if (!response.ok) {
      throw new Error(
        `Error fetching transcriptions metadata: ${response.statusText}`,
      );
    }

    const metadata: TranscriptionMetadata[] = await response.json();
    return metadata.map((m) => ({
      ...m,
      created_datetime: new Date(m.created_datetime).toISOString(),
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
    const response = await fetch(`/api/proxy/transcriptions/${id}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      throw new Error(`Error deleting transcription: ${response.statusText}`);
    }

    console.log("Transcription deleted successfully");
  } catch (error) {
    console.error("Error deleting transcription:", error);
  }
};

export const getMinuteVersions = async (
  transcriptionId: string,
): Promise<MinuteVersion[]> => {
  try {
    const response = await fetch(
      `/api/proxy/transcriptions/${transcriptionId}/minute-versions`,
    );

    if (!response.ok) {
      throw new Error(`Error fetching minute versions: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error fetching minute versions:", error);
    return [];
  }
};

export const saveMinuteVersion = async (
  transcriptionId: string,
  data: MinuteVersion,
) => {
  const response = await fetch(
    `/api/proxy/transcriptions/${transcriptionId}/minute-versions`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    },
  );

  if (!response.ok) {
    throw new Error(`Error creating minute version: ${response.statusText}`);
  }

  return response.json();
};

export const getTranscriptionJobs = async (
  transcriptionId: string,
): Promise<TranscriptionJob[]> => {
  try {
    const response = await fetch(
      `/api/proxy/transcriptions/${transcriptionId}/jobs`,
    );

    if (!response.ok) {
      throw new Error(
        `Error fetching transcription jobs: ${response.statusText}`,
      );
    }

    return await response.json();
  } catch (error) {
    console.error("Error fetching transcription jobs:", error);
    return [];
  }
};

export const saveTranscriptionJob = async (
  transcriptionId: string,
  jobData: TranscriptionJob,
) => {
  try {
    const response = await fetch(
      `/api/proxy/transcriptions/${transcriptionId}/jobs`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(jobData),
      },
    );

    if (!response.ok) {
      throw new Error(
        `Error creating transcription job: ${response.statusText}`,
      );
    }

    return await response.json();
  } catch (error) {
    console.error("Error creating transcription job:", error);
    throw error;
  }
};

export const getMinuteVersionById = async (
  transcriptionId: string,
  minuteVersionId: string,
): Promise<MinuteVersion | null> => {
  try {
    const response = await fetch(
      `/api/proxy/transcriptions/${transcriptionId}/minute-versions/${minuteVersionId}`,
    );

    if (!response.ok) {
      throw new Error(`Error fetching minute version: ${response.statusText}`);
    }

    return await response.json();
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
    const response = await fetch(`/api/proxy/user`);
    if (!response.ok) {
      throw new Error(`Error fetching user: ${response.statusText}`);
    }
    return await response.json();
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
  updates: Partial<Pick<User, "hide_citations">>,
): Promise<User | null> => {
  try {
    const response = await fetch(`/api/proxy/user`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(updates),
    });
    if (!response.ok) {
      throw new Error(`Error updating user: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error updating user:", error);
    return null;
  }
};
