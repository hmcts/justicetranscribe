"use client";

import { useState, useCallback, useEffect } from "react";
import posthog from "posthog-js";
import * as Sentry from "@sentry/nextjs";
import { AudioProcessingStatus } from "@/components/audio/processing/processing-loader";
import { audioBackupDB } from "@/lib/indexeddb-backup";
import { UploadErrorDetails } from "./types";
import { fetchUploadUrl } from "./upload-utils";

interface UseAudioUploadOptions {
  initialRecordingMode: "mic" | "screen";
  setIsProcessingTranscription: (isProcessing: boolean) => void;
}

export default function useAudioUpload({
  initialRecordingMode,
  setIsProcessingTranscription,
}: UseAudioUploadOptions) {
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [processingStatus, setProcessingStatus] =
    useState<AudioProcessingStatus>("idle");
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [currentBackupId, setCurrentBackupId] = useState<string | null>(null);
  const [uploadUrl, setUploadUrl] = useState<string | null>(null);
  const [isUploadUrlReady, setIsUploadUrlReady] = useState<boolean>(false);
  const [errorDetails, setErrorDetails] = useState<UploadErrorDetails>({
    requestId: null,
    statusCode: null,
    sentryEventId: null,
    userUploadKey: null,
    duration: null,
  });

  // Fetch upload URL when component mounts
  useEffect(() => {
    const initializeUploadUrl = async () => {
      setIsUploadUrlReady(false);
      const result = await fetchUploadUrl();

      if (result.success && result.data) {
        setUploadUrl(result.data.upload_url);
        setErrorDetails((prev) => ({
          ...prev,
          userUploadKey: result.data!.user_upload_s3_file_key,
        }));
        setIsUploadUrlReady(true);
      } else {
        setIsUploadUrlReady(false);
        setUploadError(
          "Failed to initialize upload. Please refresh the page or check your connection."
        );
        Sentry.captureMessage("Failed to pre-fetch upload URL after retries", {
          level: "error",
          tags: { area: "audio-upload-init" },
        });
      }
    };

    initializeUploadUrl();
  }, []);

  const uploadFile = useCallback(
    async (blob: Blob, url: string): Promise<void> => {
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener("progress", (event) => {
          if (event.lengthComputable) {
            const progress = Math.round((event.loaded / event.total) * 100);
            setProcessingStatus({ state: "uploading", progress });
          }
        });

        xhr.addEventListener("load", () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve();
          } else {
            reject(
              new Error(
                `Upload failed with status ${xhr.status}: ${xhr.statusText}`
              )
            );
          }
        });

        xhr.addEventListener("error", () => {
          reject(new Error("Network error during upload"));
        });

        xhr.addEventListener("timeout", () => {
          reject(new Error("Upload timed out"));
        });

        xhr.open("PUT", url);
        xhr.setRequestHeader("x-ms-blob-type", "BlockBlob");
        xhr.send(blob);
      });
    },
    []
  );

  // Helper: Clean up backup after successful upload
  const cleanupBackup = useCallback(
    async (backupIdToDelete?: string | null) => {
      const idToDelete = backupIdToDelete || currentBackupId;
      if (!idToDelete) return;

      try {
        await audioBackupDB.deleteAudioBackup(idToDelete);
        setCurrentBackupId(null);
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error("Error deleting backup:", error);
        // Don't alert user about backup deletion failure
      }
    },
    [currentBackupId]
  );

  // Helper: Report error to Sentry with full context
  const reportError = useCallback(
    (error: Error, blob: Blob) => {
      const errorWithMetadata = error as Error & {
        requestId?: string;
        status?: number;
      };

      const eventId = Sentry.captureException(error, {
        tags: {
          area: "audio-upload",
          recording_mode: initialRecordingMode,
        },
        extra: {
          request_id: errorWithMetadata.requestId || null,
          status_code: errorWithMetadata.status || null,
          user_upload_key: errorDetails.userUploadKey,
          backup_id: currentBackupId,
          blob_type: blob.type,
          blob_size: blob.size,
        },
      });

      setErrorDetails({
        requestId: errorWithMetadata.requestId || null,
        statusCode: errorWithMetadata.status || null,
        sentryEventId: eventId || null,
        userUploadKey: errorDetails.userUploadKey,
        duration: errorDetails.duration,
      });
    },
    [initialRecordingMode, currentBackupId, errorDetails]
  );

  // Helper: Single upload attempt
  const attemptUpload = useCallback(
    async (blob: Blob, attemptNumber: number) => {
      // Validate upload URL is available
      if (!uploadUrl) {
        const errorMsg = "Upload URL not available. This should not happen.";
        // eslint-disable-next-line no-console
        console.error(errorMsg);
        Sentry.captureMessage(errorMsg, {
          level: "error",
          tags: { area: "audio-upload" },
        });
        throw new Error(errorMsg);
      }

      // Show retry message if needed
      if (attemptNumber > 1) {
        setUploadError(`Retrying upload (attempt ${attemptNumber} of 2)...`);
      }

      // Upload the file
      setProcessingStatus({ state: "uploading", progress: 0 });
      await uploadFile(blob, uploadUrl);

      // Track success
      setProcessingStatus("transcribing");
      posthog.capture("transcription_started", {
        file_type: blob.type,
        source: blob instanceof File ? "upload" : "recording",
        retry_attempt: attemptNumber,
      });
    },
    [uploadFile, uploadUrl]
  );

  const startTranscription = useCallback(
    async (blob: Blob, backupIdToDelete?: string | null) => {
      const MAX_RETRIES = 2;
      let lastError: Error | null = null;

      // Try upload with retries
      for (let attempt = 1; attempt <= MAX_RETRIES; attempt += 1) {
        try {
          setUploadError(null);
          // eslint-disable-next-line no-await-in-loop
          await attemptUpload(blob, attempt);

          // Success! Clean up and prepare for next upload
          // eslint-disable-next-line no-await-in-loop
          await cleanupBackup(backupIdToDelete);
          setUploadUrl(null);
          setIsUploadUrlReady(false);
          return; // Exit on success
        } catch (error) {
          lastError =
            error instanceof Error ? error : new Error("Unknown error");
          // eslint-disable-next-line no-console
          console.error(`Upload attempt ${attempt} failed:`, lastError.message);

          // Wait before retry (except on last attempt)
          if (attempt < MAX_RETRIES) {
            // eslint-disable-next-line no-await-in-loop
            await new Promise((resolve) => {
              setTimeout(resolve, 1000);
            });
          }
        }
      }

      // All retries failed - report error
      setUploadError(lastError?.message || "Error occurred while transcribing");
      try {
        reportError(lastError!, blob);
      } catch (reportingError) {
        // eslint-disable-next-line no-console
        console.error("Error capturing sentry event:", reportingError);
      }
      setIsProcessingTranscription(false);
      setProcessingStatus("idle");
    },
    [attemptUpload, cleanupBackup, reportError, setIsProcessingTranscription]
  );

  const handleRecordingStart = useCallback(() => {
    setProcessingStatus("recording");
  }, []);

  const handleRecordingStop = useCallback(
    (blob: Blob | null, backupId?: string | null) => {
      if (blob) {
        setAudioBlob(blob);
        if (backupId) {
          setCurrentBackupId(backupId);
        }
        // Pass backupId directly to ensure it gets deleted after successful upload
        startTranscription(blob, backupId);
      }
      setProcessingStatus({ state: "uploading", progress: 0 });
    },
    [startTranscription]
  );

  return {
    audioBlob,
    processingStatus,
    setProcessingStatus,
    uploadError,
    errorDetails,
    currentBackupId,
    isUploadUrlReady,
    startTranscription,
    handleRecordingStart,
    handleRecordingStop,
  };
}
