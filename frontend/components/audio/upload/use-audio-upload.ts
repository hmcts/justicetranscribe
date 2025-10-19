"use client";

import { useState, useCallback, useEffect } from "react";
import posthog from "posthog-js";
import * as Sentry from "@sentry/nextjs";
import { AudioProcessingStatus } from "@/components/audio/processing/processing-loader";
import { getDuration } from "@/components/audio/processing/processing-status";
// CHUNKED UPLOAD: Commented out imports
// import { uploadChunksFromBackup, uploadBlobAsChunks } from "@/lib/azure-upload";
import { audioBackupDB } from "@/lib/indexeddb-backup";
import { apiClient } from "@/lib/api-client";
import { UploadErrorDetails } from "./types";

interface UseAudioUploadOptions {
  initialRecordingMode: "mic" | "screen";
  setIsProcessingTranscription: (isProcessing: boolean) => void;
}

interface UploadUrlData {
  upload_url: string;
  user_upload_s3_file_key: string;
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
  const [uploadUrlData, setUploadUrlData] = useState<UploadUrlData | null>(
    null
  );
  const [isUploadUrlReady, setIsUploadUrlReady] = useState<boolean>(false);
  const [errorDetails, setErrorDetails] = useState<UploadErrorDetails>({
    requestId: null,
    statusCode: null,
    sentryEventId: null,
    userUploadKey: null,
    duration: null,
  });

  // Detect the supported MIME type for recording
  const detectSupportedMimeType = useCallback((): string => {
    const mimeTypes = [
      "video/mp4", // iOS primary format
      "audio/mp4", // Desktop MP4 format
      "audio/webm", // WebM fallback
    ];

    const supportedMimeType = mimeTypes.find((mimeType) =>
      MediaRecorder.isTypeSupported(mimeType)
    );

    // Default fallback
    return supportedMimeType || "audio/webm";
  }, []);

  // Fetch upload URL with retry logic
  const fetchUploadUrl = useCallback(async (): Promise<boolean> => {
    const maxRetries = 3;
    const retryDelay = 1000;

    /* eslint-disable no-await-in-loop */
    for (let attempt = 1; attempt <= maxRetries; attempt += 1) {
      try {
        const mimeType = detectSupportedMimeType();
        const fileExtension = mimeType.includes("mp4") ? "mp4" : "webm";

        const urlResult = await apiClient.getUploadUrl(fileExtension);

        if (urlResult.error) {
          // eslint-disable-next-line no-console
          console.error(
            `Failed to fetch upload URL (attempt ${attempt}/${maxRetries}):`,
            urlResult.error
          );
          if (attempt < maxRetries) {
            await new Promise<void>((resolve) => {
              setTimeout(resolve, retryDelay);
            });
            // eslint-disable-next-line no-continue
            continue;
          }
          return false;
        }

        if (urlResult.data) {
          setUploadUrlData(urlResult.data);
          setErrorDetails((prev) => ({
            ...prev,
            userUploadKey: urlResult.data!.user_upload_s3_file_key,
          }));
          return true;
        }
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error(
          `Error fetching upload URL (attempt ${attempt}/${maxRetries}):`,
          error
        );
        if (attempt < maxRetries) {
          await new Promise<void>((resolve) => {
            setTimeout(resolve, retryDelay);
          });
        }
      }
    }
    /* eslint-enable no-await-in-loop */

    return false;
  }, [detectSupportedMimeType]);

  // Fetch upload URL when component mounts
  useEffect(() => {
    const initializeUploadUrl = async () => {
      setIsUploadUrlReady(false);
      const success = await fetchUploadUrl();
      setIsUploadUrlReady(success);

      if (!success) {
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
  }, [fetchUploadUrl]);

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

  // CHUNKED UPLOAD: Commented out for readability
  // const uploadChunksAsFallback = useCallback(
  //   async (backupId: string, mimeType: string): Promise<string> => {
  //     try {
  //       const result = await uploadChunksFromBackup(
  //         backupId,
  //         mimeType,
  //         (progress) => {
  //           setProcessingStatus({ state: "uploading", progress });
  //         }
  //       );
  //       return result.fileKey;
  //     } catch (error) {
  //       console.error("❌ Chunked upload fallback failed:", error);
  //       throw error;
  //     }
  //   },
  //   []
  // );

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
        setProcessingStatus({ state: "uploading", progress: 0 });
        setUploadError(null);

        // Show retry attempt to user
        if (attempt > 1) {
          setUploadError(
            `Retrying upload (attempt ${attempt} of ${maxRetries})...`
          );
        }

        // Upload URL should always be available due to pre-fetch with retry logic
        if (!uploadUrlData) {
          const errorMsg = "Upload URL not available. This should not happen.";
          // eslint-disable-next-line no-console
          console.error(errorMsg);
          Sentry.captureMessage(errorMsg, {
            level: "error",
            tags: { area: "audio-upload" },
          });
          throw new Error(errorMsg);
        }

        // eslint-disable-next-line @typescript-eslint/naming-convention
        const { upload_url, user_upload_s3_file_key } = uploadUrlData;
        currentUserUploadKey = user_upload_s3_file_key;
        setErrorDetails((prev) => ({
          ...prev,
          userUploadKey: user_upload_s3_file_key,
        }));

        // Clear retry message on successful URL fetch
        if (attempt > 1) {
          setUploadError(null);
        }

        // CHUNKED UPLOAD: Force chunked mode commented out
        // const isLocalDev = process.env.NODE_ENV === "development";
        // const forceChunked =
        //   isLocalDev && process.env.NEXT_PUBLIC_FORCE_CHUNKED_UPLOAD === "true";

        await uploadFile(blob, upload_url);

        // CHUNKED UPLOAD FALLBACK: Commented out for readability
        // try {
        //   if (forceChunked) {
        //     throw new Error("Forced chunked upload (test mode)");
        //   }
        //   await uploadFile(blob, upload_url);
        // } catch (uploadErrorResult) {
        //   console.warn(
        //     "Single file upload failed, attempting chunked upload fallback:",
        //     uploadErrorResult
        //   );
        //   try {
        //     if (currentBackupId) {
        //       finalFileKey = await uploadChunksAsFallback(
        //         currentBackupId,
        //         blob.type
        //       );
        //     } else {
        //       console.log(
        //         "No backup ID available, splitting blob for chunked upload"
        //       );
        //       const result = await uploadBlobAsChunks({
        //         blob,
        //         mimeType: blob.type,
        //         onProgress: (progress: number) => {
        //           setProcessingStatus({ state: "uploading", progress });
        //         },
        //       });
        //       finalFileKey = result.fileKey;
        //     }
        //     currentUserUploadKey = finalFileKey;
        //     setErrorDetails((prev) => ({
        //       ...prev,
        //       userUploadKey: finalFileKey,
        //     }));
        //   } catch (chunkedError) {
        //     console.error(
        //       "❌ Both single and chunked upload failed:",
        //       chunkedError
        //     );
        //     const uploadErrorMessage =
        //       uploadErrorResult instanceof Error
        //         ? uploadErrorResult.message
        //         : String(uploadErrorResult);
        //     const chunkedErrorMessage =
        //       chunkedError instanceof Error
        //         ? chunkedError.message
        //         : String(chunkedError);
        //     throw new Error(
        //       `Upload failed: Single upload (${uploadErrorMessage}) and chunked fallback (${chunkedErrorMessage})`
        //     );
        //   }
        // }

        // const transcriptionJobResult =
        //   await apiClient.startTranscriptionJob(finalFileKey);

        // if (transcriptionJobResult.error) {
        //   const errorMsg = `Transcription job start failed: ${JSON.stringify(transcriptionJobResult.error)}`;
        //   console.error(errorMsg);
        //   throw new Error(errorMsg);
        // }

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
        setUploadUrlData(null);
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
      uploadUrlData,
      fetchUploadUrl,
      // uploadChunksAsFallback, // CHUNKED UPLOAD: Commented out
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
