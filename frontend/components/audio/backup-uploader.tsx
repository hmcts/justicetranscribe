"use client";

import React, { useState, useCallback } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RefreshCw } from "lucide-react";
import ProcessingLoader, {
  AudioProcessingStatus,
} from "@/components/audio/processing-loader";
import AudioPlayerComponent from "@/components/audio/audio-player";
import { AudioBackup, audioBackupDB } from "@/lib/indexeddb-backup";
import { useTranscripts } from "@/providers/transcripts";
import { apiClient } from "@/lib/api-client";
import posthog from "posthog-js";

interface BackupUploaderProps {
  backup: AudioBackup;
  onClose: () => void;
  onUploadSuccess: () => void;
}

function BackupUploader({
  backup,
  onClose,
  onUploadSuccess,
}: BackupUploaderProps) {
  const [processingStatus, setProcessingStatus] =
    useState<AudioProcessingStatus>("idle");
  const [uploadError, setUploadError] = useState<string | null>(null);
  const { setIsProcessingTranscription } = useTranscripts();

  // CHUNKED UPLOAD FALLBACK: Split blob into chunks and upload individually
  const uploadBlobAsChunks = useCallback(
    async (blob: Blob, baseUploadUrl: string): Promise<void> => {
      const chunkSize = 1024 * 1024; // 1MB chunks
      const totalChunks = Math.ceil(blob.size / chunkSize);
      
      
      for (let i = 0; i < totalChunks; i++) {
        const start = i * chunkSize;
        const end = Math.min(start + chunkSize, blob.size);
        const chunk = blob.slice(start, end);
        
        const chunkUploadUrl = `${baseUploadUrl}&chunk=${i}&total=${totalChunks}`;
        
        setProcessingStatus({ 
          state: "uploading", 
          progress: Math.round((i / totalChunks) * 100) 
        });
        
        // Upload individual chunk
        const xhr = new XMLHttpRequest();
        await new Promise((resolve, reject) => {
          xhr.addEventListener("load", () => {
            if (xhr.status >= 200 && xhr.status < 300) {
              resolve(xhr.response);
            } else {
              reject(new Error(`Chunk ${i} upload failed with status ${xhr.status}`));
            }
          });
          
          xhr.addEventListener("error", () => {
            reject(new Error(`Network error uploading chunk ${i}`));
          });
          
          xhr.open("PUT", chunkUploadUrl);
          xhr.setRequestHeader("x-ms-blob-type", "BlockBlob");
          xhr.send(chunk);
        });
      }
      
      setProcessingStatus({ state: "uploading", progress: 100 });
    },
    []
  );

  const startTranscription = useCallback(
    async (blob: Blob) => {
      try {
        const fileExtension = blob.type.includes("mp4") ? "mp4" : "webm";
        setProcessingStatus({ state: "uploading", progress: 0 });
        setUploadError(null);

        const urlResult = await apiClient.getUploadUrl(fileExtension);

        if (urlResult.error) {
          throw new Error("Failed to get upload URL");
        }

        // eslint-disable-next-line @typescript-eslint/naming-convention
        const { upload_url, user_upload_s3_file_key } = urlResult.data!;

        // Try single file upload first
        try {
          // Create XMLHttpRequest to track upload progress
          const xhr = new XMLHttpRequest();
          await new Promise((resolve, reject) => {
            xhr.upload.addEventListener("progress", (event) => {
              if (event.lengthComputable) {
                const progress = Math.round((event.loaded / event.total) * 100);
                setProcessingStatus({ state: "uploading", progress });
              }
            });

            xhr.addEventListener("load", () => {
              if (xhr.status >= 200 && xhr.status < 300) {
                resolve(xhr.response);
              } else {
                reject(new Error("Failed to upload file to Azure Storage"));
              }
            });

            xhr.addEventListener("error", () => {
              reject(new Error("Network error during upload"));
            });

            xhr.addEventListener("timeout", () => {
              reject(new Error("Upload timed out"));
            });

            xhr.open("PUT", upload_url);
            // Add required headers for Azure Blob Storage
            xhr.setRequestHeader("x-ms-blob-type", "BlockBlob");
            xhr.send(blob);
          });
        } catch (uploadError) {
          
          // CHUNKED UPLOAD FALLBACK: For backup uploader, we need to split the blob into chunks
          try {
            await uploadBlobAsChunks(blob, upload_url);
          } catch (chunkedError) {
            console.error("❌ Both single and chunked upload failed:", chunkedError);
            const uploadErrorMessage = uploadError instanceof Error ? uploadError.message : String(uploadError);
            const chunkedErrorMessage = chunkedError instanceof Error ? chunkedError.message : String(chunkedError);
            throw new Error(`Upload failed: Single upload (${uploadErrorMessage}) and chunked fallback (${chunkedErrorMessage})`);
          }
        }

        const transcriptionJobResult = await apiClient.startTranscriptionJob(
          user_upload_s3_file_key
        );

        if (transcriptionJobResult.error) {
          throw new Error("Failed to start transcription job");
        }

        setProcessingStatus("transcribing");

        posthog.capture("transcription_started", {
          file_type: blob.type,
          source: "backup_retry",
        });

        // Clean up backup after successful upload
        try {
          await audioBackupDB.deleteAudioBackup(backup.id);
          if (onUploadSuccess) {
            onUploadSuccess();
          }
        } catch (error) {
          // Sentry.captureException(error);
          alert(`error deleting backup: ${error}`);
        }
      } catch (error) {
        setUploadError(
          error instanceof Error
            ? error.message
            : "Error occurred while transcribing"
        );
        setIsProcessingTranscription(false);
        setProcessingStatus("idle");
      }
    },
    [setIsProcessingTranscription, backup.id, onUploadSuccess]
  );

  const handleRetryUpload = () => {
    startTranscription(backup.blob);
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return "Unknown duration";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="mx-auto mt-8 w-full max-w-3xl">
      <Card>
        <CardContent className="space-y-6">
          <div className="-mr-4 flex justify-end">
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="mt-1 bg-red-50 hover:bg-red-100 dark:bg-red-900/10 dark:hover:bg-red-900/30"
              style={{ color: "#B21010" }}
            >
              Close
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="size-4"
              >
                <path d="M18 6 6 18" />
                <path d="m6 6 12 12" />
              </svg>
            </Button>
          </div>

          {processingStatus !== "idle" ? (
            <ProcessingLoader
              status={processingStatus}
              onStopPolling={() => setProcessingStatus("idle")}
            />
          ) : (
            <div className="space-y-4">
              <div className="text-center">
                <h1 className="mb-2 text-2xl font-semibold">
                  Retry Upload - Backed Up Recording
                </h1>
                <div className="space-y-1 text-sm text-gray-600">
                  <p>File: {backup.fileName}</p>
                  <p>Recorded: {formatTimestamp(backup.timestamp)}</p>
                  <p>Duration: {formatDuration(backup.recordingDuration)}</p>
                </div>
              </div>

              <AudioPlayerComponent audioBlob={backup.blob} />

              <div className="flex justify-center gap-4">
                <Button
                  onClick={handleRetryUpload}
                  className="flex items-center gap-2"
                >
                  <RefreshCw className="size-4" />
                  Retry Upload
                </Button>
              </div>
            </div>
          )}

          {uploadError && (
            <Alert
              variant="destructive"
              className="border border-red-200 bg-red-50 text-red-900 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300"
            >
              <AlertDescription className="flex items-center gap-2">
                <svg
                  className="size-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                {uploadError}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default BackupUploader;
