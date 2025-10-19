/* eslint-disable @typescript-eslint/no-shadow */
/* eslint-disable jsx-a11y/label-has-associated-control */

"use client";

import { Info, Mic, AlertTriangle, RefreshCw, Clock, Moon } from "lucide-react";
import React, { useCallback, useEffect, useRef, useState } from "react";
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

import { useTranscripts } from "@/providers/transcripts";
import RecordingControl from "@/components/audio/recording/recording-control";
import {
  hasReachedMaxDuration,
  shouldShowWarning,
  getRemainingTime,
  formatRemainingTime,
} from "@/lib/recording-config";
import useIsMobile from "@/hooks/use-mobile";

// Local storage key for the dialog preference
const DIALOG_PREFERENCE_KEY = "tab-recorder-show-instructions-dialog";
const LONG_RECORDING_WARNING_KEY =
  "screen-recorder-long-recording-warning-seen";

interface ScreenRecorderProps {
  onRecordingStop: (blob: Blob | null) => void;
  onRecordingStart: () => void;
  disabled: boolean;
}

interface ScreenShareGuidanceProps {
  isVisible: boolean;
}

function ScreenShareGuidance({ isVisible }: ScreenShareGuidanceProps) {
  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Semi-transparent background */}
      <div className="absolute inset-0 bg-black/50" />

      {/* Left instruction */}
      <div className="absolute left-8 top-1/2 -translate-y-1/2">
        <div className="flex items-center gap-4">
          <div className="w-[280px] rounded-xl bg-white p-6 shadow-lg">
            <div className="flex items-start gap-4">
              <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary text-xl font-bold text-primary-foreground">
                2
              </div>
              <div className="space-y-2">
                <p className="text-xl font-bold leading-tight">
                  Choose a screen
                </p>
                <p className="text-base text-muted-foreground">
                  If there are multiple screens, choose the screen where Teams
                  is
                </p>
              </div>
            </div>
          </div>
          <div
            className="size-0 shrink-0 border-y-[12px]
            border-l-[24px] border-y-transparent 
            border-l-white"
          />
        </div>
      </div>

      {/* Right top instruction */}
      <div className="absolute right-8 top-24">
        <div className="flex items-center gap-4">
          <div
            className="size-0 shrink-0 border-y-[12px]
            border-r-[24px] border-y-transparent 
            border-r-white"
          />
          <div className="w-[280px] rounded-xl bg-white p-6 shadow-lg">
            <div className="flex items-start gap-4">
              <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary text-xl font-bold text-primary-foreground">
                1
              </div>
              <div className="space-y-2">
                <p className="text-xl font-bold leading-tight">
                  Click &quot;Entire Screen&quot; tab
                </p>
                <p className="text-base text-muted-foreground">
                  Found at the top of dialog
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right bottom instruction */}
      <div className="absolute bottom-24 right-8">
        <div className="flex items-center gap-4">
          <div
            className="size-0 shrink-0 border-y-[12px]
            border-r-[24px] border-y-transparent 
            border-r-white"
          />
          <div className="w-[280px] rounded-xl bg-white p-6 shadow-lg">
            <div className="flex items-start gap-4">
              <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary text-xl font-bold text-primary-foreground">
                3
              </div>
              <div className="space-y-2">
                <p className="text-xl font-bold leading-tight">
                  Make sure &quot;Share audio&quot; is checked
                </p>
                <p className="text-base text-muted-foreground">
                  There is a switch in the bottom right of the pop up
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ScreenRecorder({
  onRecordingStop,
  onRecordingStart,
  disabled = false,
}: ScreenRecorderProps) {
  const [err, setError] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [wakeLock, setWakeLock] = useState<any>(null);
  const { setIsRecording: setAppIsRecording } = useTranscripts();
  const [audioContext, setAudioContext] = useState<AudioContext | null>(null);
  const [recordingGain, setRecordingGain] = useState<GainNode | null>(null);
  const [showInstructionsDialog, setShowInstructionsDialog] = useState(false);
  const [showInstructionsInDialog, setShowInstructionsInDialog] =
    useState(false);
  const [isMacOS, setIsMacOS] = useState(false);
  const [showShareGuidance, setShowShareGuidance] = useState(false);
  const [showTimeWarning, setShowTimeWarning] = useState(false);
  const [remainingMinutes, setRemainingMinutes] = useState<string>("");
  const [showLongRecordingWarning, setShowLongRecordingWarning] =
    useState(false);
  const isMobile = useIsMobile();

  // Load dialog preference from local storage on component mount
  useEffect(() => {
    // Only run in browser environment
    if (typeof window !== "undefined") {
      try {
        const savedPreference = localStorage.getItem(DIALOG_PREFERENCE_KEY);
        // If a preference exists and is set to "false", don't show the dialog
        if (savedPreference === "false") {
          setShowInstructionsInDialog(false);
        }
      } catch (error) {
        // If there's an error accessing localStorage, default to showing the dialog
        console.error("Error accessing localStorage:", error);
      }
    }
  }, []);

  // Check if long recording warning has been shown before
  useEffect(() => {
    if (typeof window !== "undefined") {
      try {
        const warningSeen = localStorage.getItem(LONG_RECORDING_WARNING_KEY);
        if (!warningSeen) {
          setShowLongRecordingWarning(true);
        }
      } catch (error) {
        console.error("Error accessing localStorage:", error);
      }
    }
  }, []);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const visibilityListenerRef = useRef<(() => void) | null>(null);

  // Handle wake lock to prevent screen sleeping during recording
  const requestWakeLock = async () => {
    try {
      if ("wakeLock" in navigator) {
        // Only request wake lock if the page is visible
        if (document.visibilityState === "visible") {
          const lock = await navigator.wakeLock.request("screen");
          setWakeLock(lock);

          // Create and store the listener so we can remove it later
          const visibilityHandler = async () => {
            if (document.visibilityState === "visible" && !wakeLock) {
              try {
                const newLock = await navigator.wakeLock.request("screen");
                setWakeLock(newLock);
              } catch (visibilityErr) {
                // Continue recording even if wake lock fails
              }
            }
          };

          visibilityListenerRef.current = visibilityHandler;
          document.addEventListener("visibilitychange", visibilityHandler);
        }
      }
    } catch (err) {
      // Continue recording even if wake lock fails
    }
  };

  const releaseWakeLock = useCallback(async () => {
    if (wakeLock) {
      try {
        await wakeLock.release();
        setWakeLock(null);
      } catch (err) {
        // Continue recording even if wake lock fails
      }
    }

    // Remove the visibility change event listener to prevent memory leak
    if (visibilityListenerRef.current) {
      document.removeEventListener(
        "visibilitychange",
        visibilityListenerRef.current
      );
      visibilityListenerRef.current = null;
    }
  }, [wakeLock]);

  const stopRecording = useCallback(() => {
    // Prevent multiple calls to stopRecording
    if (!mediaRecorderRef.current || !isRecording) {
      return;
    }

    try {
      // Clear timer
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }

      // Only call stop() if the state is not 'inactive'
      if (mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      } else {
        // If already inactive, manually clean up
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }

        setIsRecording(false);
        setRecordingTime(0);
        releaseWakeLock();
      }
    } catch (err) {
      // Clean up streams even if stop fails
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }

      setIsRecording(false);
      setRecordingTime(0);
      releaseWakeLock();
    }
  }, [isRecording, releaseWakeLock]);

  // Monitor recording time and trigger auto-stop when limit is reached
  useEffect(() => {
    if (!isRecording) {
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
      console.log(
        "Maximum recording duration reached. Auto-stopping recording."
      );
      stopRecording();
    }
  }, [recordingTime, isRecording, stopRecording]);

  useEffect(() => {
    if (isRecording) {
      setAppIsRecording(true);
    }
    return () => {
      if (isRecording) {
        setAppIsRecording(false);
      }
    };
  }, [isRecording, setAppIsRecording]);

  // Handle pause state changes
  const handlePauseStateChange = useCallback(
    (paused: boolean) => {
      // If we have a gain node, we can use it to "pause" recording by setting gain to 0
      if (recordingGain) {
        recordingGain.gain.value = paused ? 0 : 1;
      }
    },
    [recordingGain]
  );

  const startRecording = async () => {
    setError(null);
    mediaChunksRef.current = [];

    try {
      if (!navigator.mediaDevices?.getDisplayMedia) {
        throw new Error(
          "Screen capture is not supported in this browser. Please use Chrome or Edge."
        );
      }

      // Show the guidance
      setShowShareGuidance(true);

      // Request screen sharing
      const screenStream = await navigator.mediaDevices
        .getDisplayMedia({
          video: {
            displaySurface: "browser",
          },
          audio: {
            autoGainControl: false,
            echoCancellation: false,
            noiseSuppression: false,
          },
        })
        .finally(() => {
          // Hide the guidance when the dialog closes (whether successful or cancelled)
          setShowShareGuidance(false);
        });

      // After getting the stream, we can stop the video track immediately since we don't need it
      screenStream.getVideoTracks().forEach((track) => track.stop());

      // Check if we have an audio track from the tab
      if (!screenStream.getAudioTracks().length) {
        screenStream.getTracks().forEach((track) => track.stop());
        throw new Error(
          "We couldn't pick up any audio. Please make sure when you click share 'Entire Screen' you then check 'Share audio' at the bottom right of the pop up."
        );
      }

      let composedStream: MediaStream;

      // Create a new audio context for processing audio and for pausing
      const newAudioContext = new AudioContext();
      const destination = newAudioContext.createMediaStreamDestination();
      setAudioContext(newAudioContext);

      // Create a gain node for pause/resume functionality
      const gainNode = newAudioContext.createGain();
      gainNode.gain.value = 1.0; // Start with full volume
      setRecordingGain(gainNode);

      // Merge both audio streams with gain control
      try {
        const micStream = await navigator.mediaDevices.getUserMedia({
          audio: true,
        });

        // Add screen audio to the composed stream
        const screenSource =
          newAudioContext.createMediaStreamSource(screenStream);
        const screenGain = newAudioContext.createGain();
        screenGain.gain.value = 1.0;
        screenSource.connect(screenGain).connect(gainNode).connect(destination);

        // Add mic audio to the composed stream
        const micSource = newAudioContext.createMediaStreamSource(micStream);
        const micGain = newAudioContext.createGain();
        micGain.gain.value = 1.0;
        micSource.connect(micGain).connect(gainNode).connect(destination);

        // Create a new stream with the merged audio
        composedStream = new MediaStream();

        // Add the merged audio track
        destination.stream.getAudioTracks().forEach((track) => {
          composedStream.addTrack(track);
        });
      } catch (micError) {
        console.warn(
          "Could not access microphone. Recording only tab audio.",
          micError
        );
        // Create a new stream with just the tab audio, still with gain control
        const screenSource =
          newAudioContext.createMediaStreamSource(screenStream);
        screenSource.connect(gainNode).connect(destination);

        composedStream = new MediaStream();
        destination.stream.getAudioTracks().forEach((track) => {
          composedStream.addTrack(track);
        });
      }

      streamRef.current = composedStream;

      // Create a media recorder from the composed stream
      let options;
      // Try MP4 first (preferred format)
      if (MediaRecorder.isTypeSupported("audio/mp4")) {
        options = { mimeType: "audio/mp4" };
      } else {
        // Fall back to WebM if MP4 is not supported
        options = { mimeType: "audio/webm" };
      }
      const mediaRecorder = new MediaRecorder(composedStream, options);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          mediaChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onerror = () => {
        setError("Recording error occurred. Please try again.");
        // Don't call stopRecording here as it might cause a loop
        // Just clean up manually if needed
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }
        setIsRecording(false);
        setRecordingTime(0);
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
        releaseWakeLock();
      };

      mediaRecorder.onstop = () => {
        if (mediaChunksRef.current.length > 0) {
          const audioBlob = new Blob(mediaChunksRef.current, {
            type: options.mimeType,
          });
          onRecordingStop(audioBlob);

          // Track successful recording completion
          posthog.capture("virtual_meeting_recording_completed", {
            duration_seconds: recordingTime,
            file_size_bytes: audioBlob.size,
            mime_type: options.mimeType,
          });
        } else {
          setError(
            "No audio data was recorded. Please try again and ensure audio is shared."
          );

          // Track failed recording
          posthog.capture("virtual_meeting_recording_failed", {
            duration_seconds: recordingTime,
          });
        }

        // Clean up all streams
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
        }
        if (screenStream) {
          screenStream.getTracks().forEach((track) => track.stop());
        }
        streamRef.current = null;
        mediaRecorderRef.current = null;

        setIsRecording(false);
        setRecordingTime(0);
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
        releaseWakeLock();
      };

      // Start recording
      try {
        await requestWakeLock(); // Don't throw if wake lock fails
      } catch (wakeLockError) {
        console.warn(
          "Wake lock request failed, continuing without it:",
          wakeLockError
        );
      }

      mediaRecorder.start(1000); // Collect data every second
      setIsRecording(true);
      onRecordingStart();

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);

      // Track virtual meeting recording start
      posthog.capture("virtual_meeting_recording_started", {
        mime_type: options.mimeType,
      });
    } catch (error) {
      setShowShareGuidance(false);
      setError(
        error instanceof Error ? error.message : "An unknown error occurred"
      );
      setIsRecording(false);
      setRecordingTime(0);
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  // Clean up audio context and connections on unmount
  useEffect(() => {
    return () => {
      if (audioContext) {
        audioContext.close().catch(console.error);
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [audioContext]);

  useEffect(() => {
    setIsMacOS(navigator.platform.toLowerCase().includes("mac"));
  }, []);

  return (
    <div className="space-y-4">
      <div className="my-6 text-center">
        <h1 className="text-2xl font-semibold">Virtual Meeting Recorder</h1>
        <p className="text-sm text-muted-foreground">
          Record audio by sharing your screen with Justice Transcribe
        </p>
      </div>

      {!isRecording && !showInstructionsInDialog && (
        <>
          <Alert variant="default" className="mb-2">
            <Info className="size-4" />
            <AlertDescription className="ml-2 text-sm">
              You will be asked to share your screen to record a virtual meeting
              on Teams.
            </AlertDescription>
          </Alert>

          {/* Do Not Disturb Reminder - Only show on mobile */}
          {isMobile && (
            <div 
              role="status"
              aria-label="Reminder to enable Do Not Disturb mode"
              className="rounded-lg border border-purple-200 bg-purple-50 px-4 py-3" 
              style={{ borderColor: '#D8C8FF', backgroundColor: '#F4F1FF' }}
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5 rounded-full p-2" style={{ backgroundColor: '#CABDFF' }}>
                  <Moon className="size-5" style={{ color: '#1F1247' }} aria-hidden="true" />
                </div>
                <div className="flex-1">
                  <h3 className="text-sm font-semibold" style={{ color: '#1F1247' }}>
                    Silence notifications
                  </h3>
                  <p className="mt-0.5 text-sm" style={{ color: '#362952' }}>
                    Turn on Do Not Disturb while recording.
                  </p>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Long Recording Warning Dialog */}
      <Dialog
        open={showLongRecordingWarning}
        onOpenChange={(open) => {
          setShowLongRecordingWarning(open);
          if (!open) {
            try {
              localStorage.setItem(LONG_RECORDING_WARNING_KEY, "true");
            } catch (error) {
              console.error("Error saving warning preference:", error);
            }
          }
        }}
      >
        <DialogContent className="max-w-[calc(100vw-2rem)] sm:max-w-2xl">
          <div className="flex flex-col items-start gap-4 sm:flex-row">
            {/* Warning Icon */}
            <div className="flex size-12 shrink-0 items-center justify-center rounded-2xl bg-amber-100 dark:bg-amber-900/30">
              <AlertTriangle className="size-6 text-amber-600 dark:text-amber-400" />
            </div>

            {/* Content */}
            <div className="flex-1 pt-0 sm:pt-1">
              <DialogHeader className="space-y-3 pb-0">
                <DialogTitle className="text-left text-lg font-semibold sm:text-xl">
                  Please refresh before recording
                </DialogTitle>
                <DialogDescription className="text-left text-sm text-gray-600 dark:text-gray-400 sm:text-base">
                  There&apos;s a temporary issue affecting long sessions. To
                  avoid disruption, please refresh before you begin. If a
                  session exceeds 60 minutes, it will stop and upload
                  automatically.
                </DialogDescription>
              </DialogHeader>

              {/* Bullet Points */}
              <div className="mt-4 space-y-3 border-t pt-4 sm:mt-6 sm:space-y-4 sm:pt-6">
                <div className="flex items-start gap-3">
                  <RefreshCw className="mt-0.5 size-4 shrink-0 text-gray-600 dark:text-gray-400 sm:size-5" />
                  <div className="text-sm sm:text-base">
                    <span className="font-semibold text-gray-900 dark:text-gray-100">
                      Refresh before recording
                    </span>
                    <span className="text-gray-600 dark:text-gray-400">
                      {" "}
                      to ensure a clean start.
                    </span>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Clock className="mt-0.5 size-4 shrink-0 text-gray-600 dark:text-gray-400 sm:size-5" />
                  <div className="text-sm sm:text-base">
                    <span className="text-gray-600 dark:text-gray-400">
                      If your meeting goes past{" "}
                    </span>
                    <span className="font-semibold text-gray-900 dark:text-gray-100">
                      60:00
                    </span>
                    <span className="text-gray-600 dark:text-gray-400">
                      , recording will auto-stop and upload.
                    </span>
                  </div>
                </div>
              </div>

              {/* Continue Button */}
              <DialogFooter className="mt-6 border-t pt-4">
                <Button
                  onClick={() => {
                    setShowLongRecordingWarning(false);
                    try {
                      localStorage.setItem(LONG_RECORDING_WARNING_KEY, "true");
                    } catch (error) {
                      console.error("Error saving warning preference:", error);
                    }
                  }}
                  className="w-full sm:w-auto"
                >
                  Continue
                </Button>
              </DialogFooter>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Instructions Dialog */}
      {showInstructionsInDialog && (
        <Dialog
          open={showInstructionsDialog}
          onOpenChange={setShowInstructionsDialog}
        >
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>How to Record Meeting Audio</DialogTitle>
              <DialogDescription>
                Follow these 3 steps to successfully record your virtual meeting
                audio:
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-2">
              {isMacOS ? (
                <>
                  <div className="flex items-start gap-3">
                    <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                      1
                    </div>
                    <p>
                      <strong>Use a browser tab</strong> - Join your meeting
                      (Teams, Meet, Zoom, etc.) in a browser tab, not a desktop
                      app. Desktop apps cannot be recorded.
                    </p>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                      2
                    </div>
                    <p>
                      <strong>Share the correct tab</strong> - When prompted,
                      select the specific browser tab with your meeting and make
                      sure to check &quot;<strong>Share audio</strong>&quot;. Do
                      not share your entire screen or a window.
                    </p>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                      3
                    </div>
                    <p>
                      <strong>Keep both tabs open</strong> - Don&apos;t close
                      either tab during recording. Switching between tabs is
                      fine, but both must remain open.
                    </p>
                  </div>
                </>
              ) : (
                <>
                  <div className="flex items-start gap-3">
                    <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                      1
                    </div>
                    <p>
                      <strong>Share your screen</strong> - When prompted, select
                      &quot;Entire Screen&quot; to capture audio from any
                      application.
                    </p>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                      2
                    </div>
                    <p>
                      <strong>Enable audio sharing</strong> - Make sure to
                      toggle on &quot;<strong>Share system audio</strong>&quot;
                      in the sharing dialog.
                    </p>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                      3
                    </div>
                    <p>
                      <strong>Keep this tab open</strong> - Don&apos;t close
                      this tab during recording. You can minimize the browser or
                      switch to other applications.
                    </p>
                  </div>
                </>
              )}
            </div>
            <DialogFooter className="sm:justify-start">
              <Button
                type="button"
                onClick={() => {
                  setShowInstructionsDialog(false);
                  startRecording();
                }}
              >
                Start Recording
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      <div className="flex flex-col space-y-4">
        {!isRecording ? (
          <Button
            onClick={
              showInstructionsInDialog
                ? () => setShowInstructionsDialog(true)
                : startRecording
            }
            disabled={disabled}
          >
            <Mic className="mr-2 size-4" />
            {disabled ? "Initializing..." : "Start Recording Virtual Meeting"}
          </Button>
        ) : (
          <div className="space-y-4">
            <RecordingControl
              stream={streamRef.current}
              isRecording={isRecording}
              onStopRecording={stopRecording}
              onPauseStateChange={handlePauseStateChange}
              elapsedTime={recordingTime}
              showTimeWarning={showTimeWarning}
              remainingTime={remainingMinutes}
            />
          </div>
        )}
      </div>

      {err && (
        <Alert variant="destructive">
          <AlertDescription>{err}</AlertDescription>
        </Alert>
      )}

      <ScreenShareGuidance isVisible={showShareGuidance} />
    </div>
  );
}

export default ScreenRecorder;
