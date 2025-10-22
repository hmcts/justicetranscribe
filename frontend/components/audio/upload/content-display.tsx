/* eslint-disable no-nested-ternary */

"use client";

import React, { useState } from "react";
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
import ProcessingLoader from "@/components/audio/processing/processing-loader";
import AudioRecorderComponent from "../recording/audio-recorder";
import ScreenRecorder from "../recording/screen-recorder";
import { ContentDisplayProps } from "./types";

export default function ContentDisplay({
  processingStatus,
  setProcessingStatus,
  uploadError,
  audioBlob,
  startTranscription,
  initialRecordingMode,
  isUploadUrlReady,
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
    <div
      className={
        initialRecordingMode === "mic" ? "md:origin-top md:scale-125" : ""
      }
    >
      <div className="-mr-4 flex justify-end">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleClose}
          className="mt-1 bg-red-50 hover:bg-red-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-600 dark:bg-red-900/10 dark:hover:bg-red-900/30"
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
            aria-hidden="true"
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
              className="focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
            >
              <RefreshCw className="mr-2 size-4" aria-hidden="true" />
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
              disabled={!isUploadUrlReady}
            />
          ) : (
            <ScreenRecorder
              onRecordingStop={onRecordingStop}
              onRecordingStart={onRecordingStart}
              disabled={!isUploadUrlReady}
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
