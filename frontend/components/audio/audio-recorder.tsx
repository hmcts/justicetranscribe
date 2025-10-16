/* eslint-disable no-restricted-syntax */
/* eslint-disable no-nested-ternary */

"use client";

import { Mic, Loader2, BellOff, AlertTriangle, RefreshCw, Clock, Moon } from "lucide-react";
import * as React from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import posthog from "posthog-js";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import RecordingControl from "@/components/audio/recording-control";
import {
  audioBackupDB,
  AudioBackup,
  IndexedDBBackup,
} from "@/lib/indexeddb-backup";
import { AudioDevice, MicrophonePermission } from "./microphone-permission";
import { 
  hasReachedMaxDuration, 
  shouldShowWarning, 
  getRemainingTime,
  formatRemainingTime
} from "@/lib/recording-config";
import useIsMobile from "@/hooks/use-mobile";

interface MicRecorderProps {
  onRecordingStop: (blob: Blob | null, backupId?: string | null) => void;
  onRecordingStart: () => void;
}

function AudioRecorderComponent({
  onRecordingStop,
  onRecordingStart,
}: MicRecorderProps) {
  const [recordedAudio, setRecordedAudio] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [audioDevices, setAudioDevices] = useState<AudioDevice[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>("");
  const [permissionGranted, setPermissionGranted] = useState<boolean>(false);

  const [wakeLock, setWakeLock] = useState<any>(null);
  const [showProcessingRecording, setShowProcessingRecording] = useState(false);
  const [mediaStream, setMediaStream] = useState<MediaStream | null>(null);
  const [showTimeWarning, setShowTimeWarning] = useState(false);
  const [remainingMinutes, setRemainingMinutes] = useState<string>("");

  const audioRef = useRef<HTMLAudioElement>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const backupIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const currentBackupIdRef = useRef<string | null>(null);
  const audioUrlRef = useRef<string | null>(null);
  const visibilityListenerRef = useRef<(() => void) | null>(null);
  const isMobile = useIsMobile();

  const handlePermissionGranted = (devices: AudioDevice[]) => {
    setAudioDevices(devices);
    setSelectedDeviceId(devices[0].deviceId);
    setPermissionGranted(true);
    setError(null);
  };

  const requestWakeLock = async () => {
    try {
      if ("wakeLock" in navigator) {
        const lock = await navigator.wakeLock.request("screen");
        setWakeLock(lock);

        // Create and store the listener so we can remove it later
        const visibilityHandler = async () => {
          if (document.visibilityState === "visible" && !wakeLock) {
            const newLock = await navigator.wakeLock.request("screen");
            setWakeLock(newLock);
          }
        };
        
        visibilityListenerRef.current = visibilityHandler;
        document.addEventListener("visibilitychange", visibilityHandler);
      }
    } catch (err) {
      console.log("Wake Lock error:", err);
    }
  };

  const releaseWakeLock = useCallback(async () => {
    if (wakeLock) {
      try {
        await wakeLock.release();
        setWakeLock(null);
      } catch (err) {
        console.log("Wake Lock release error:", err);
      }
    }
    
    // Remove the visibility change event listener to prevent memory leak
    if (visibilityListenerRef.current) {
      document.removeEventListener("visibilitychange", visibilityListenerRef.current);
      visibilityListenerRef.current = null;
    }
  }, [wakeLock]);

  useEffect(() => {
    return () => {
      releaseWakeLock();
    };
  }, [releaseWakeLock]);

  const clearAudio = () => {
    // Properly revoke object URL to free memory
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
    }
    
    setRecordedAudio(null);
    if (audioRef.current) {
      audioRef.current.src = "";
    }
    onRecordingStop(null, null);
  };

  const createPeriodicBackup = useCallback(async () => {
    if (!mediaRecorderRef.current || mediaChunksRef.current.length === 0) {
      return;
    }

    try {
      const selectedMimeType = mediaRecorderRef.current.mimeType;
      const currentChunks = [...mediaChunksRef.current];
      const audioBlob = new Blob(currentChunks, { type: selectedMimeType });

      if (!currentBackupIdRef.current) {
        currentBackupIdRef.current = IndexedDBBackup.generateBackupId();
      }

      const backup: AudioBackup = {
        id: currentBackupIdRef.current,
        blob: audioBlob,
        fileName: `recording_${new Date().toISOString()}.${selectedMimeType.includes("mp4") ? "mp4" : "webm"}`,
        timestamp: Date.now(),
        mimeType: selectedMimeType,
        recordingDuration: recordingTime,
      };

      await audioBackupDB.saveAudioBackup(backup);
    } catch (err) {
      console.error("Failed to create periodic backup:", err);
    }
  }, [recordingTime]);

  const startPeriodicBackup = useCallback(() => {
    if (backupIntervalRef.current) {
      clearInterval(backupIntervalRef.current);
    }

    backupIntervalRef.current = setInterval(() => {
      createPeriodicBackup();
    }, 15000); // Backup every 15 seconds
  }, [createPeriodicBackup]);

  const stopPeriodicBackup = useCallback(() => {
    if (backupIntervalRef.current) {
      clearInterval(backupIntervalRef.current);
      backupIntervalRef.current = null;
    }
  }, []);

  const startRecording = async () => {
    if (recordedAudio) {
      clearAudio();
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          deviceId: selectedDeviceId,
          noiseSuppression: true,
          echoCancellation: true,
          autoGainControl: true,
        },
      });

      streamRef.current = stream;
      setMediaStream(stream);

      const mimeTypes = [
        "video/mp4", // iOS primary format
        "audio/mp4", // Desktop MP4 format
        "audio/webm", // WebM fallback
      ];

      // Find the first supported MIME type
      let selectedMimeType = "";
      for (const mimeType of mimeTypes) {
        if (MediaRecorder.isTypeSupported(mimeType)) {
          selectedMimeType = mimeType;
          break;
        }
      }

      if (!selectedMimeType) {
        throw new Error("No supported MIME type found for audio recording");
      }

      const options = { mimeType: selectedMimeType };
      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;
      mediaChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          mediaChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        if (mediaChunksRef.current.length > 0) {
          const audioBlob = new Blob(mediaChunksRef.current, {
            type: selectedMimeType, // Use the selected MIME type
          });
          onRecordingStop(audioBlob, currentBackupIdRef.current);

          posthog.capture("in_person_recording_completed", {
            duration_seconds: recordingTime,
            file_size_bytes: audioBlob.size,
          });
        }

        // Clean up
        stopPeriodicBackup();
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }
        
        mediaRecorderRef.current = null;
        setMediaStream(null);
        setIsRecording(false);
        setRecordingTime(0);
        
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
        
        currentBackupIdRef.current = null;
        releaseWakeLock();
      };

      await requestWakeLock();
      mediaRecorder.start(1000); // Collect data every second
      setIsRecording(true);
      onRecordingStart();

      // Start backup after initial recording data is available
      setTimeout(() => {
        startPeriodicBackup();
      }, 5000); // Wait 5 seconds before starting backups

      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "An unknown error occurred while accessing audio."
      );
    }
  };

  const stopRecording = () => {
    setShowProcessingRecording(true);
    stopPeriodicBackup();
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !== "inactive"
    ) {
      mediaRecorderRef.current.stop();
    }
  };

  const togglePauseResume = () => {
    if (!mediaRecorderRef.current) return;

    if (mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.pause();
      setIsPaused(true);
      stopPeriodicBackup();
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    } else if (mediaRecorderRef.current.state === "paused") {
      mediaRecorderRef.current.resume();
      setIsPaused(false);
      startPeriodicBackup();
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    }
  };

  // Monitor recording time and trigger auto-stop when limit is reached
  useEffect(() => {
    if (!isRecording || isPaused) {
      return;
    }

    // Check if we should show the warning
    if (shouldShowWarning(recordingTime)) {
      const remaining = getRemainingTime(recordingTime);
      setRemainingMinutes(formatRemainingTime(remaining));
      setShowTimeWarning(true);
    } else {
      setShowTimeWarning(false);
      setRemainingMinutes("");
    }

    // Check if we've reached the maximum duration
    if (hasReachedMaxDuration(recordingTime)) {
      console.log("Maximum recording duration reached. Auto-stopping recording.");
      stopRecording();
    }
  }, [recordingTime, isRecording, isPaused]);

  useEffect(() => {
    if (isRecording && !isPaused) {
      return;
    }
  }, [isRecording, isPaused]);

  useEffect(() => {
    // Clean up previous URL before creating a new one
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
    }
    
    // Create new URL only when we have audio to play
    if (recordedAudio && audioRef.current) {
      const audioSource = URL.createObjectURL(recordedAudio);
      audioUrlRef.current = audioSource;
      audioRef.current.src = audioSource;
    }
    
    // Cleanup function to revoke URL when component unmounts or recordedAudio changes
    return () => {
      if (audioUrlRef.current) {
        URL.revokeObjectURL(audioUrlRef.current);
        audioUrlRef.current = null;
      }
    };
  }, [recordedAudio]);

  return (
    <div className="space-y-4">
      {!permissionGranted || !audioDevices.length ? (
        <MicrophonePermission
          onPermissionGranted={handlePermissionGranted}
          onError={setError}
        />
      ) : (
        <>
          {!showProcessingRecording && (
            <>
              <div className="my-6 text-center">
                <h1 className="text-2xl font-semibold">
                  In-Person Meeting Recorder
                </h1>
              </div>

              {/* Do Not Disturb Reminder - Only show on mobile */}
              {isMobile && (
                <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-800/50">
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 rounded-full bg-slate-200 p-2 dark:bg-slate-700">
                      <Moon className="size-5 text-slate-600 dark:text-slate-300" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                        Silence notifications?
                      </h3>
                      <p className="mt-0.5 text-sm text-slate-600 dark:text-slate-400">
                        Turn on Do Not Disturb while recording.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          {showProcessingRecording ? (
            <div className="mx-auto flex max-w-md flex-col items-center justify-center space-y-6 py-12">
              <div className="relative">
                <div className="absolute inset-0 animate-ping rounded-full bg-gradient-to-r from-blue-400 to-blue-500 opacity-20" />
                <div className="absolute inset-1 rounded-full bg-blue-100 dark:bg-blue-900/30" />
                <Loader2 className="relative z-10 size-14 animate-spin text-blue-500" />
              </div>
              <div className="text-center">
                <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                  Uploading your meeting...
                </h3>
              </div>
            </div>
          ) : isRecording ? (
            <div className="flex flex-col space-y-2">
              <RecordingControl
                stream={mediaStream}
                isRecording={isRecording}
                onStopRecording={stopRecording}
                recorderControls={{
                  togglePauseResume,
                  isPaused,
                  recordingTime,
                }}
                elapsedTime={recordingTime}
                showTimeWarning={showTimeWarning}
                remainingTime={remainingMinutes}
              />
            </div>
          ) : (
            <div className="flex flex-col space-y-4">
              <div className="flex flex-col items-start">
                <span className="mb-2 text-sm font-medium">
                  1. Choose microphone
                </span>
                <Select
                  onValueChange={(value) => {
                    setSelectedDeviceId(value);
                  }}
                  value={selectedDeviceId}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select microphone" />
                  </SelectTrigger>
                  <SelectContent>
                    {audioDevices.map((device) => (
                      <SelectItem key={device.deviceId} value={device.deviceId}>
                        {device.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col items-start">
                <span className="mb-2 text-sm font-medium">
                  2. Start recording
                </span>
                <div className="w-full">
                  <Button
                    onClick={startRecording}
                    className="mt-2 h-12 w-full"
                    size="lg"
                  >
                    <Mic className="mr-2 size-4" />
                    Start recording
                  </Button>
                </div>
              </div>
            </div>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </>
      )}
    </div>
  );
}

export default AudioRecorderComponent;
