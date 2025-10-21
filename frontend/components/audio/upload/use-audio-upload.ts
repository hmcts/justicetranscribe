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

  const startTranscription = useCallback(
    async (blob: Blob, backupIdToDelete?: string | null) => {
      const maxRetries = 2;
      let lastError: Error | null = null;
      let currentRequestId: string | null = null;
      let currentStatusCode: number | null = null;
      const currentUserUploadKey: string | null = null;

      const delay = (ms: number): Promise<void> => {
        return new Promise((resolve) => {
          setTimeout(() => {
            resolve();
          }, ms);
        });
      };

      const performSingleAttempt = async (attempt: number): Promise<void> => {
        setProcessingStatus({ state: "uploading", progress: 0 });
        setUploadError(null);

        // Show retry attempt to user
        if (attempt > 1) {
          setUploadError(
            `Retrying upload (attempt ${attempt} of ${maxRetries})...`
          );
        }

        // Upload URL should always be available due to pre-fetch with retry logic
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

        // Clear retry message on successful URL fetch
        if (attempt > 1) {
          setUploadError(null);
        }

        await uploadFile(blob, uploadUrl);

        setProcessingStatus("transcribing");

        posthog.capture("transcription_started", {
          file_type: blob.type,
          source: blob instanceof File ? "upload" : "recording",
          retry_attempt: attempt,
        });

        // Clean up backup after successful upload
        const idToDelete = backupIdToDelete || currentBackupId;
        if (idToDelete) {
          try {
            await audioBackupDB.deleteAudioBackup(idToDelete);
            setCurrentBackupId(null);
          } catch (error) {
            // eslint-disable-next-line no-console
            console.error("Error deleting backup:", error);
            // Don't alert user about backup deletion failure
          }
        }

        // Clear and re-fetch upload URL for the next recording
        // This ensures each upload uses a fresh, single-use URL
        setUploadUrl(null);
        setIsUploadUrlReady(false);
      };

      // Sequential retry logic without loops or recursion
      let attempt = 1;
      let success = false;

      while (attempt <= maxRetries && !success) {
        try {
          // eslint-disable-next-line no-await-in-loop
          await performSingleAttempt(attempt);
          success = true;
        } catch (error) {
          lastError =
            error instanceof Error
              ? error
              : new Error("Unknown error occurred");
          // eslint-disable-next-line no-console
          console.error(`Upload attempt ${attempt} failed:`, lastError.message);

          // Extract request ID and status code from error if available
          const err = lastError as Error & {
            requestId?: string;
            status?: number;
          };
          currentRequestId = err?.requestId || null;
          currentStatusCode = err?.status ?? null;

          if (attempt < maxRetries) {
            // eslint-disable-next-line no-await-in-loop
            await delay(1000);
          }
          attempt += 1;
        }
      }

      if (!success) {
        // All retries failed
        setUploadError(
          lastError?.message || "Error occurred while transcribing"
        );
        // Capture rich context for failed upload/transcription
        try {
          const err = lastError as Error & {
            requestId?: string;
            status?: number;
          };
          const eventId = Sentry.captureException(err, {
            tags: {
              area: "audio-upload",
              recording_mode: initialRecordingMode,
            },
            extra: {
              request_id: currentRequestId,
              status_code: currentStatusCode,
              user_upload_key: currentUserUploadKey,
              backup_id: currentBackupId,
              blob_type: blob.type,
              blob_size: blob.size,
            },
          });
          setErrorDetails({
            requestId: currentRequestId,
            statusCode: currentStatusCode,
            sentryEventId: eventId || null,
            userUploadKey: currentUserUploadKey,
            duration: errorDetails.duration,
          });
        } catch (error) {
          // eslint-disable-next-line no-console
          console.error("Error capturing sentry event:", error);
        }
        setIsProcessingTranscription(false);
        setProcessingStatus("idle");
      }
    },
    [
      setIsProcessingTranscription,
      currentBackupId,
      initialRecordingMode,
      uploadFile,
      uploadUrl,
      errorDetails.duration,
    ]
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
