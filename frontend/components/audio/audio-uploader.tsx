/* eslint-disable no-nested-ternary */

"use client";

import posthog from "posthog-js";
import React, { useState, useCallback } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent } from "@/components/ui/card";
import { useTranscripts } from "@/providers/transcripts";
import ProcessingLoader, {
  AudioProcessingStatus,
} from "@/components/audio/processing-loader";
import { Button } from "@/components/ui/button";
import { RefreshCw } from "lucide-react";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogCancel,
  AlertDialogAction,
} from "@/components/ui/alert-dialog";
import { audioBackupDB } from "@/lib/indexeddb-backup";
import { apiClient } from "@/lib/api-client";
import * as Sentry from "@sentry/nextjs";
import ErrorReportCard from "@/components/ui/error-report-card";
import { getDuration } from "@/components/audio/processing-status";
import AudioRecorderComponent from "./audio-recorder";
import ScreenRecorder from "./screen-recorder";

interface ContentDisplayProps {
  processingStatus: AudioProcessingStatus;
  setProcessingStatus: (status: AudioProcessingStatus) => void;
  uploadError: string | null;
  audioBlob: Blob | null;
  startTranscription: (blob: Blob, backupIdToDelete?: string | null) => void;
  initialRecordingMode: "mic" | "screen";
  onRecordingStop: (blob: Blob | null, backupId?: string | null) => void;
  onRecordingStart: () => void;
  onClose: () => void;
  // isRecording: boolean;
}

function ContentDisplay({
  processingStatus,
  setProcessingStatus,
  uploadError,
  audioBlob,
  startTranscription,
  initialRecordingMode,
  onRecordingStop,
  onRecordingStart,
  onClose,
}: ContentDisplayProps) {
  const [showCloseDialog, setShowCloseDialog] = useState(false);

  const handleClose = () => {
    if (!audioBlob && processingStatus === "idle") {
      onClose();
    } else if (processingStatus !== "transcribing") {
      setShowCloseDialog(true);
    } else {
      onClose();
    }
  };

  return (
    <div className="">
      <div className="-mr-4 flex justify-end">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleClose}
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

      {processingStatus !== "idle" && processingStatus !== "recording" ? (
        <ProcessingLoader
          status={processingStatus}
          onStopPolling={() => setProcessingStatus("idle")}
        />
      ) : uploadError && audioBlob ? (
        <div className="mt-8">
          <div className="mb-4 text-center">
            <h3 className="text-lg font-semibold text-red-600 dark:text-red-400">
              Error Processing Audio
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Please check your internet connection and try again
            </p>
          </div>
          <div className="flex justify-center gap-4">
            <Button
              variant="default"
              onClick={() => {
                startTranscription(audioBlob, null);
              }}
              disabled={!audioBlob}
            >
              <RefreshCw className="mr-2 size-4" />
              Retry transcription
            </Button>
          </div>
        </div>
      ) : (
        <div className="">
          {initialRecordingMode === "mic" ? (
            <AudioRecorderComponent
              onRecordingStart={onRecordingStart}
              onRecordingStop={onRecordingStop}
            />
          ) : (
            <ScreenRecorder
              onRecordingStop={onRecordingStop}
              onRecordingStart={onRecordingStart}
            />
          )}
        </div>
      )}

      <AlertDialog open={showCloseDialog} onOpenChange={setShowCloseDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Close Recorder?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to close? YOU WILL NOT BE ABLE TO RESUME
              RECORDING.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="flex-col gap-2 sm:flex-row">
            <AlertDialogCancel className="h-12 w-full sm:h-10 sm:w-auto">
              Go back
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={onClose}
              className="h-12 w-full bg-red-600 text-white hover:bg-red-700 dark:bg-red-900 dark:hover:bg-red-800 sm:h-10 sm:w-auto"
            >
              Close and STOP recording
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

interface AudioUploaderProps {
  initialRecordingMode: "mic" | "screen";
  onClose: () => void;
}
function AudioUploader({ initialRecordingMode, onClose }: AudioUploaderProps) {
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [processingStatus, setProcessingStatus] =
    useState<AudioProcessingStatus>("idle");
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [currentBackupId, setCurrentBackupId] = useState<string | null>(null);
  const [lastRequestId, setLastRequestId] = useState<string | null>(null);
  const [lastStatusCode, setLastStatusCode] = useState<number | null>(null);
  const [lastSentryEventId, setLastSentryEventId] = useState<string | null>(null);
  const [userUploadKey, setUserUploadKey] = useState<string | null>(null);
  const [lastDuration, setLastDuration] = useState<number | null>(null);
  const [showContinueDialog, setShowContinueDialog] = useState(false);
  const [uploadSuccessful, setUploadSuccessful] = useState(false);
  const { setIsProcessingTranscription } = useTranscripts();
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
            reject(new Error(`Upload failed with status ${xhr.status}: ${xhr.statusText}`));
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

  const startTranscription = useCallback(
    async (blob: Blob, backupIdToDelete?: string | null) => {
      const maxRetries = 2;
      let lastError: Error | null = null;
      let currentRequestId: string | null = null;
      let currentStatusCode: number | null = null;
      let currentUserUploadKey: string | null = null;

      // Calculate duration non-blocking for report (telemetry)
      getDuration(blob).then((d) => setLastDuration(d ?? null));

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
          console.log(`Upload attempt ${attempt} of ${maxRetries}`);
          setUploadError(`Retrying upload (attempt ${attempt} of ${maxRetries})...`);
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
        setUserUploadKey(user_upload_s3_file_key);

        // Clear retry message on successful URL fetch
        if (attempt > 1) {
          setUploadError(null);
        }

        // Upload the file with the new URL
        await uploadFile(blob, upload_url);

        const transcriptionJobResult = await apiClient.startTranscriptionJob(
          user_upload_s3_file_key
        );

        if (transcriptionJobResult.error) {
          const errorMsg = `Transcription job start failed: ${JSON.stringify(transcriptionJobResult.error)}`;
          console.error(errorMsg);
          throw new Error(errorMsg);
        }

        setProcessingStatus("transcribing");
        setUploadSuccessful(true);
        setShowContinueDialog(true);

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
          await performSingleAttempt(attempt);
          success = true;
        } catch (error) {
          lastError = error instanceof Error ? error : new Error("Unknown error occurred");
          console.error(`Upload attempt ${attempt} failed:`, lastError.message);

          // Extract request ID and status code from error if available
          const err = lastError as Error & { requestId?: string; status?: number };
          currentRequestId = err?.requestId || null;
          currentStatusCode = err?.status ?? null;

          if (attempt < maxRetries) {
            await delay(1000);
          }
          attempt = attempt + 1;
        }
      }

      if (!success) {
        // All retries failed
        setUploadError(
          lastError?.message || "Error occurred while transcribing"
        );
        // Capture rich context for failed upload/transcription
        try {
          const err = lastError as Error & { requestId?: string; status?: number };
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
          setLastSentryEventId(eventId || null);
          setLastRequestId(currentRequestId);
          setLastStatusCode(currentStatusCode);
        } catch {}
        setIsProcessingTranscription(false);
        setProcessingStatus("idle");
      }
    },
    [setIsProcessingTranscription, currentBackupId, initialRecordingMode, uploadFile]
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

  const handleStartNewRecording = useCallback(() => {
    // Reset all states to allow a new recording
    setAudioBlob(null);
    setProcessingStatus("idle");
    setUploadError(null);
    setShowContinueDialog(false);
    setUploadSuccessful(false);
    setLastRequestId(null);
    setLastStatusCode(null);
    setLastSentryEventId(null);
    setUserUploadKey(null);
    setLastDuration(null);
    
    posthog.capture("new_recording_started_after_auto_stop");
  }, []);

  const handleFinishRecording = useCallback(() => {
    setShowContinueDialog(false);
    onClose();
  }, [onClose]);

  return (
    <div className="mx-auto mt-8 w-full max-w-3xl">
      <Card>
        <CardContent className="space-y-6">
          <ContentDisplay
            processingStatus={processingStatus}
            setProcessingStatus={setProcessingStatus}
            uploadError={uploadError}
            audioBlob={audioBlob}
            startTranscription={startTranscription}
            initialRecordingMode={initialRecordingMode}
            onRecordingStart={handleRecordingStart}
            onRecordingStop={handleRecordingStop}
            onClose={onClose}
          />
        </CardContent>
      </Card>
      {uploadError && (
        <>
          <Alert
            variant="destructive"
            className="my-4 w-full border border-red-200 bg-red-50 text-red-900 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300"
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
              {uploadError} {lastRequestId ? `(req ${lastRequestId})` : ""}
            </AlertDescription>
          </Alert>
          <ErrorReportCard
            data={{
              title: "Audio upload/transcription failure",
              requestId: lastRequestId,
              statusCode: lastStatusCode,
              recordingMode: initialRecordingMode,
              fileSizeBytes: audioBlob?.size ?? null,
              durationSeconds: lastDuration,
              errorMessage: uploadError,
              extra: {
                user_upload_key: userUploadKey,
                backup_id: currentBackupId,
              },
              sentryEventId: lastSentryEventId,
            }}
          />
        </>
      )}

      <AlertDialog open={showContinueDialog} onOpenChange={setShowContinueDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Recording Uploaded Successfully! 🎉</AlertDialogTitle>
            <AlertDialogDescription>
              Your recording has been uploaded and transcription has started. 
              Would you like to start another recording session?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="flex-col gap-2 sm:flex-row">
            <AlertDialogCancel 
              onClick={handleFinishRecording}
              className="h-12 w-full sm:h-10 sm:w-auto"
            >
              No, I&apos;m Done
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleStartNewRecording}
              className="h-12 w-full sm:h-10 sm:w-auto"
            >
              Start New Recording
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

export default AudioUploader;
