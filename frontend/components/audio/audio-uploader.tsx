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
import AudioPlayerComponent from "@/components/audio/audio-player";
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
import AudioRecorderComponent from "./audio-recorder";
import ScreenRecorder from "./screen-recorder";

interface ContentDisplayProps {
  processingStatus: AudioProcessingStatus;
  setProcessingStatus: (status: AudioProcessingStatus) => void;
  uploadError: string | null;
  audioBlob: Blob | null;
  startTranscription: (blob: Blob) => void;
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
          <AudioPlayerComponent audioBlob={audioBlob} />
          <div className="flex justify-center gap-4">
            <Button
              variant="default"
              onClick={() => {
                startTranscription(audioBlob);
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
  const { setIsProcessingTranscription } = useTranscripts();
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

        const transcriptionJobResult = await apiClient.startTranscriptionJob(
          user_upload_s3_file_key
        );

        if (transcriptionJobResult.error) {
          throw new Error("Failed to start transcription job");
        }
        setProcessingStatus("transcribing");

        // await pollTranscription(user_upload_s3_file_key);
        // setProcessingStatus("transcribing_complete");
        posthog.capture("transcription_started", {
          file_type: blob.type,
          source: blob instanceof File ? "upload" : "recording",
        });

        // Clean up backup after successful upload
        if (currentBackupId) {
          try {
            await audioBackupDB.deleteAudioBackup(currentBackupId);
            setCurrentBackupId(null);
          } catch (error) {
            // Sentry.captureException(error);
            alert(`error deleting backup: ${error}`);
          }
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
    [setIsProcessingTranscription, currentBackupId]
  );

  const handleRecordingStart = useCallback(() => {
    setProcessingStatus("recording");
  }, []);

  const handleRecordingStop = useCallback(
    (blob: Blob | null, backupId?: string | null) => {
      if (blob) {
        startTranscription(blob);
        setAudioBlob(blob);
        if (backupId) {
          setCurrentBackupId(backupId);
        }
      }
      setProcessingStatus({ state: "uploading", progress: 0 });
    },
    [startTranscription]
  );

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
            {uploadError}
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}

export default AudioUploader;
