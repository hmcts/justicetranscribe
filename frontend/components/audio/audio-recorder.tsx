/* eslint-disable no-restricted-syntax */
/* eslint-disable no-nested-ternary */

"use client";

import { Mic, Loader2, BellOff } from "lucide-react";
import * as React from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import posthog from "posthog-js";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

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
  AudioChunk,
} from "@/lib/indexeddb-backup";
import { AudioDevice, MicrophonePermission } from "./microphone-permission";

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

  // DEBUG: Make audioBackupDB available in console immediately
  useEffect(() => {
    (window as any).audioBackupDB = audioBackupDB;
  }, []);

  const [wakeLock, setWakeLock] = useState<any>(null);
  const [showProcessingRecording, setShowProcessingRecording] = useState(false);
  const [mediaStream, setMediaStream] = useState<MediaStream | null>(null);

  const audioRef = useRef<HTMLAudioElement>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunkIndexRef = useRef<number>(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const currentBackupIdRef = useRef<string | null>(null);
  const audioUrlRef = useRef<string | null>(null);
  const visibilityListenerRef = useRef<(() => void) | null>(null);

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
      // Wake Lock error handled silently
    }
  };

  const releaseWakeLock = useCallback(async () => {
    if (wakeLock) {
      try {
        await wakeLock.release();
        setWakeLock(null);
      } catch (err) {
        // Wake Lock release error handled silently
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


  // STREAMING: Stream chunks directly to IndexedDB instead of periodic backups
  const streamChunkToIndexedDB = useCallback(async (chunkData: Blob) => {
    if (!currentBackupIdRef.current) {
      currentBackupIdRef.current = IndexedDBBackup.generateBackupId();
    }

    try {
      await audioBackupDB.appendChunk(
        currentBackupIdRef.current,
        chunkIndexRef.current++,
        chunkData
      );
    } catch (err) {
      console.error("❌ Failed to stream chunk to IndexedDB:", err);
      // Try to initialize IndexedDB if it failed
      try {
        await audioBackupDB.init();
        await audioBackupDB.appendChunk(
          currentBackupIdRef.current,
          chunkIndexRef.current - 1, // Use the same index since we incremented it
          chunkData
        );
      } catch (retryErr) {
        console.error("❌ Failed to store chunk even after retry:", retryErr);
      }
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
      chunkIndexRef.current = 0; // Reset chunk index for new recording

      // STREAMING: Stream each chunk directly to IndexedDB as it arrives
      mediaRecorder.ondataavailable = async (event) => {
        if (event.data.size > 0) {
          await streamChunkToIndexedDB(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        // STREAMING: Reconstruct final blob from streamed chunks
        if (currentBackupIdRef.current && chunkIndexRef.current > 0) {
          try {
            let audioBlob = await audioBackupDB.reconstructBlob(
              currentBackupIdRef.current,
              selectedMimeType
            );
            onRecordingStop(audioBlob, currentBackupIdRef.current);

            posthog.capture("in_person_recording_completed", {
              duration_seconds: recordingTime,
              file_size_bytes: audioBlob.size,
            });
            
            // EXPLICIT NULLIFICATION: Help Next.js garbage collection
            // @ts-ignore - Explicitly nullify to help GC
            audioBlob = null;
          } catch (err) {
            console.error("Failed to reconstruct final blob:", err);
            onRecordingStop(null, currentBackupIdRef.current);
          }
        } else {
          onRecordingStop(null, currentBackupIdRef.current);
        }

        // EXPLICIT NULLIFICATION: Help Next.js garbage collection
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
        chunkIndexRef.current = 0; // Reset chunk index
        releaseWakeLock();
      };

      await requestWakeLock();
      
      // DEBUG: Check IndexedDB status before starting recording
      // await audioBackupDB.debugIndexedDB();
      
      mediaRecorder.start(1000); // Collect data every second
      setIsRecording(true);
      onRecordingStart();

      // STREAMING: No need for delayed backup start - chunks stream immediately

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
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    } else if (mediaRecorderRef.current.state === "paused") {
      mediaRecorderRef.current.resume();
      setIsPaused(false);
      // STREAMING: Resume timer but streaming continues automatically
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);

    }
  };

  useEffect(() => {
    if (recordedAudio || isRecording) {
      setIsRecording(true);
    }
  }, [isRecording, setIsRecording, recordedAudio]);

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

              {/* Do Not Disturb Notification - One line below header */}
              <div className="rounded-lg border border-amber-200/60 bg-gradient-to-r from-amber-50/70 to-orange-50/70 px-3 py-2 dark:border-amber-800/20 dark:from-amber-950/20 dark:to-orange-950/20">
                <div className="flex items-center justify-center gap-2">
                  <BellOff className="size-3.5 text-amber-600 dark:text-amber-400" />
                  <p className="text-sm text-amber-800 dark:text-amber-300">
                    💡 Turn on Do Not Disturb mode to prevent interruptions
                    during recording
                  </p>
                </div>
              </div>
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
