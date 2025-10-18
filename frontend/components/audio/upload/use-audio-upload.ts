"use client";

import { useState, useCallback } from "react";
import posthog from "posthog-js";
import * as Sentry from "@sentry/nextjs";
import { AudioProcessingStatus } from "@/components/audio/processing/processing-loader";
import { getDuration } from "@/components/audio/processing/processing-status";
import { uploadChunksFromBackup, uploadBlobAsChunks } from "@/lib/azure-upload";
import { audioBackupDB } from "@/lib/indexeddb-backup";
import { apiClient } from "@/lib/api-client";
import { UploadErrorDetails } from "./types";

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
  const [errorDetails, setErrorDetails] = useState<UploadErrorDetails>({
    requestId: null,
    statusCode: null,
    sentryEventId: null,
    userUploadKey: null,
    duration: null,
  });

  const uploadFile = useCallback(
    async (blob: Blob, uploadUrl: string): Promise<void> => {
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

        xhr.open("PUT", uploadUrl);
        xhr.setRequestHeader("x-ms-blob-type", "BlockBlob");
        xhr.send(blob);
      });
    },
    []
  );

  const uploadChunksAsFallback = useCallback(
    async (backupId: string, mimeType: string): Promise<string> => {
      try {
        const result = await uploadChunksFromBackup(
          backupId,
          mimeType,
          (progress) => {
            setProcessingStatus({ state: "uploading", progress });
          }
        );
        return result.fileKey;
      } catch (error) {
        console.error("❌ Chunked upload fallback failed:", error);
        throw error;
      }
    },
    []
  );

  const startTranscription = useCallback(
    async (blob: Blob, backupIdToDelete?: string | null) => {
      const maxRetries = 2;
      let lastError: Error | null = null;
      let currentRequestId: string | null = null;
      let currentStatusCode: number | null = null;
      let currentUserUploadKey: string | null = null;

      // Calculate duration non-blocking for report (telemetry)
      getDuration(blob).then((d) =>
        setErrorDetails((prev) => ({ ...prev, duration: d ?? null }))
      );

      const delay = (ms: number): Promise<void> => {
        return new Promise((resolve) => {
          setTimeout(() => {
            resolve();
          }, ms);
        });
      };

      const performSingleAttempt = async (attempt: number): Promise<void> => {
        const fileExtension = blob.type.includes("mp4") ? "mp4" : "webm";
        setProcessingStatus({ state: "uploading", progress: 0 });
        setUploadError(null);

        // Show retry attempt to user
        if (attempt > 1) {
          setUploadError(
            `Retrying upload (attempt ${attempt} of ${maxRetries})...`
          );
        }

        const urlResult = await apiClient.getUploadUrl(fileExtension);

        if (urlResult.error) {
          const errorMsg = `Upload URL request failed: ${JSON.stringify(urlResult.error)}`;
          console.error(errorMsg);
          throw new Error(errorMsg);
        }

        // eslint-disable-next-line @typescript-eslint/naming-convention
        const { upload_url, user_upload_s3_file_key } = urlResult.data!;
        currentUserUploadKey = user_upload_s3_file_key;
        setErrorDetails((prev) => ({
          ...prev,
          userUploadKey: user_upload_s3_file_key,
        }));

        // Clear retry message on successful URL fetch
        if (attempt > 1) {
          setUploadError(null);
        }

        // Try single file upload first (unless force chunked mode is enabled)
        let finalFileKey = user_upload_s3_file_key;

        // Check if chunked upload is forced (local development only)
        const isLocalDev = process.env.NODE_ENV === "development";
        const forceChunked =
          isLocalDev && process.env.NEXT_PUBLIC_FORCE_CHUNKED_UPLOAD === "true";

        if (forceChunked) {
          console.log(
            "🧪 FORCE_CHUNKED_UPLOAD enabled - skipping single upload, using chunked upload"
          );
        }

        try {
          if (forceChunked) {
            // Force chunked upload for testing
            throw new Error("Forced chunked upload (test mode)");
          }
          await uploadFile(blob, upload_url);
        } catch (uploadErrorResult) {
          console.warn(
            "Single file upload failed, attempting chunked upload fallback:",
            uploadErrorResult
          );

          // CHUNKED UPLOAD FALLBACK: If single upload fails, try chunked upload
          try {
            // If we have chunks in IndexedDB, use those; otherwise split the blob
            if (currentBackupId) {
              // Try to use existing chunks from recording
              finalFileKey = await uploadChunksAsFallback(
                currentBackupId,
                blob.type
              );
            } else {
              // No IndexedDB chunks - split the blob on-the-fly
              console.log(
                "No backup ID available, splitting blob for chunked upload"
              );
              const result = await uploadBlobAsChunks({
                blob,
                mimeType: blob.type,
                onProgress: (progress: number) => {
                  setProcessingStatus({ state: "uploading", progress });
                },
              });
              finalFileKey = result.fileKey;
            }

            currentUserUploadKey = finalFileKey;
            setErrorDetails((prev) => ({
              ...prev,
              userUploadKey: finalFileKey,
            }));
          } catch (chunkedError) {
            console.error(
              "❌ Both single and chunked upload failed:",
              chunkedError
            );
            const uploadErrorMessage =
              uploadErrorResult instanceof Error
                ? uploadErrorResult.message
                : String(uploadErrorResult);
            const chunkedErrorMessage =
              chunkedError instanceof Error
                ? chunkedError.message
                : String(chunkedError);
            throw new Error(
              `Upload failed: Single upload (${uploadErrorMessage}) and chunked fallback (${chunkedErrorMessage})`
            );
          }
        }

        const transcriptionJobResult =
          await apiClient.startTranscriptionJob(finalFileKey);

        if (transcriptionJobResult.error) {
          const errorMsg = `Transcription job start failed: ${JSON.stringify(transcriptionJobResult.error)}`;
          console.error(errorMsg);
          throw new Error(errorMsg);
        }

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
            console.error("Error deleting backup:", error);
            // Don't alert user about backup deletion failure
          }
        }
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
      uploadChunksAsFallback,
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
    startTranscription,
    handleRecordingStart,
    handleRecordingStop,
  };
}
