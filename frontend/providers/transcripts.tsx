"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useMemo,
  Suspense,
  useCallback,
} from "react";
import { useRouter, usePathname, useSearchParams } from "next/navigation";

import { Transcription, TranscriptionJob } from "@/src/api/generated";
import { TranscriptionMetadata } from "@/src/api/generated/models/TranscriptionMetadata";
import {
  saveTranscription,
  getAllTranscriptionMetadata,
  getTranscriptionById,
  deleteTranscription,
  getTranscriptionJobs,
  saveTranscriptionJob,
} from "../lib/database";

interface TranscriptsContextType {
  transcriptsMetadata: TranscriptionMetadata[];
  currentTranscription: Transcription | null;
  saveTranscription: (transcription: Transcription) => void;
  loadTranscription: (id: string) => void;
  deleteTranscription: (id: string) => void;
  newTranscription: () => void;
  isLoading: boolean;
  audioBlob: Blob | null;
  setAudioBlob: (blob: Blob | null) => void;
  isProcessingTranscription: boolean;
  setIsProcessingTranscription: (isProcessing: boolean) => void;
  isRecording: boolean;
  setIsRecording: (isRecording: boolean) => void;
  renameTranscription: (id: string, newTitle: string) => Promise<void>;
  transcriptionJobs: TranscriptionJob[];
  saveTranscriptionJob: (job: TranscriptionJob) => Promise<TranscriptionJob>;
  selectedRecordingMode: "mic" | "screen" | null;
  setSelectedRecordingMode: (mode: "mic" | "screen" | null) => void;
}

const TranscriptsContext = createContext<TranscriptsContextType | undefined>(
  undefined,
);

export function TranscriptsProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  // Wrap the actual implementation with Suspense
  return (
    <Suspense fallback={<div>Loading transcripts...</div>}>
      <TranscriptsProviderContent children={children} />
    </Suspense>
  );
}

// Move the actual implementation to a separate component
function TranscriptsProviderContent({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [transcriptsMetadata, setTranscriptsMetadata] = useState<
    TranscriptionMetadata[]
  >([]);
  const [currentTranscription, setCurrentTranscription] =
    useState<Transcription | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [isProcessingTranscription, setIsProcessingTranscription] =
    useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [transcriptionJobs, setTranscriptionJobs] = useState<
    TranscriptionJob[]
  >([]);
  const [selectedRecordingMode, setSelectedRecordingMode] = useState<
    "mic" | "screen" | null
  >(null);

  // Get current values from URL
  const transcriptId = searchParams?.get("id");

  // Load transcription when ID in URL changes
  useEffect(() => {
    if (transcriptId) {
      const loadTranscription = async () => {
        try {
          const transcription = await getTranscriptionById(transcriptId);
          setCurrentTranscription(transcription);
          setAudioBlob(null);
          setIsProcessingTranscription(false);
          setIsRecording(false);
        } catch (error) {
          console.error("Error loading transcription:", error);
          // Redirect to home if transcription not found
          router.push("/");
        }
      };

      loadTranscription();
    } else if (!transcriptId) {
      setCurrentTranscription(null);
    }
  }, [transcriptId, router]);

  useEffect(() => {
    const loadMetadata = async () => {
      const returnedMetadata = await getAllTranscriptionMetadata();
      setTranscriptsMetadata(returnedMetadata);
      setIsLoading(false);
    };
    loadMetadata();
  }, []);

  // Add this effect to fetch transcription jobs when ID changes
  useEffect(() => {
    const loadTranscriptionJobs = async () => {
      if (!transcriptId) {
        setTranscriptionJobs([]);
        return;
      }

      try {
        const jobs = await getTranscriptionJobs(transcriptId);
        setTranscriptionJobs(jobs);
      } catch (error) {
        console.error("Failed to fetch transcription jobs:", error);
        setTranscriptionJobs([]);
      }
    };

    loadTranscriptionJobs();
  }, [transcriptId]);

  const handleSaveTranscription = useCallback(
    async (transcription: Transcription) => {
      await saveTranscription(transcription);
      const returnedMetadata = await getAllTranscriptionMetadata();
      setTranscriptsMetadata(returnedMetadata);
    },
    [],
  );

  const handleLoadTranscription = useCallback(
    async (id: string) => {
      // Update URL with transcription ID and reset stage
      const params = new URLSearchParams(searchParams?.toString() || "");
      params.set("id", id);
      params.delete("stage"); // Reset to default stage
      router.push(`${pathname}?${params.toString()}`);
    },
    [pathname, router, searchParams],
  );

  const handleDeleteTranscription = useCallback(
    async (id: string) => {
      await deleteTranscription(id);
      const returnedMetadata = await getAllTranscriptionMetadata();
      setTranscriptsMetadata(returnedMetadata);

      // If current transcription was deleted, redirect to home
      if (currentTranscription?.id === id) {
        router.push("/");
      }
    },
    [currentTranscription, router],
  );

  const handleNewTranscription = useCallback(() => {
    // Clear URL params to create new transcription
    router.push(pathname || "");
    setAudioBlob(null);
    setIsRecording(false);
  }, [pathname, router]);

  const handleRenameTranscription = useCallback(
    async (id: string, newTitle: string) => {
      // Load the full transcription
      const fullTranscription = await getTranscriptionById(id);
      if (!fullTranscription) {
        throw new Error("Transcription not found");
      }

      // Update and save
      fullTranscription.title = newTitle;
      await saveTranscription(fullTranscription);

      // Refresh metadata
      const returnedMetadata = await getAllTranscriptionMetadata();
      setTranscriptsMetadata(returnedMetadata);

      // Update current transcription if it's the one being renamed
      if (currentTranscription?.id === id) {
        setCurrentTranscription(fullTranscription);
      }
    },
    [currentTranscription],
  );

  const handleSaveTranscriptionJob = useCallback(
    async (job: TranscriptionJob) => {
      if (!currentTranscription?.id) {
        throw new Error("No active transcription");
      }

      const savedJob = await saveTranscriptionJob(currentTranscription.id, job);

      setTranscriptionJobs((prev) =>
        job.id
          ? prev.map((j) => (j.id === job.id ? savedJob : j))
          : [...prev, savedJob],
      );
      return savedJob;
    },
    [currentTranscription?.id],
  );

  // Add this useEffect for navigation prevention
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isProcessingTranscription || isRecording) {
        e.preventDefault();
        e.returnValue = "";
      }
    };

    const handlePopState = (e: PopStateEvent) => {
      if (isProcessingTranscription || isRecording) {
        window.history.pushState(null, "", window.location.href);

        const confirmNavigation = window.confirm(
          "You have an active recording or processing in progress. Are you sure you want to leave? Your progress will be lost.",
        );

        if (!confirmNavigation) {
          e.preventDefault();
          window.history.pushState(null, "", window.location.href);
        }
      }
    };

    window.history.pushState(null, "", window.location.href);

    window.addEventListener("beforeunload", handleBeforeUnload);
    window.addEventListener("popstate", handlePopState);

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
      window.removeEventListener("popstate", handlePopState);
    };
  }, [isProcessingTranscription, isRecording]);

  const contextValue = useMemo(
    () => ({
      transcriptsMetadata,
      currentTranscription,
      saveTranscription: handleSaveTranscription,
      loadTranscription: handleLoadTranscription,
      deleteTranscription: handleDeleteTranscription,
      newTranscription: handleNewTranscription,
      isLoading,
      audioBlob,
      setAudioBlob,
      isProcessingTranscription,
      setIsProcessingTranscription,
      isRecording,
      setIsRecording,
      renameTranscription: handleRenameTranscription,
      transcriptionJobs,
      saveTranscriptionJob: handleSaveTranscriptionJob,
      selectedRecordingMode,
      setSelectedRecordingMode,
    }),
    [
      transcriptsMetadata,
      currentTranscription,
      handleSaveTranscription,
      handleLoadTranscription,
      handleDeleteTranscription,
      handleNewTranscription,
      isLoading,
      audioBlob,
      isProcessingTranscription,
      isRecording,
      handleRenameTranscription,
      transcriptionJobs,
      handleSaveTranscriptionJob,
      selectedRecordingMode,
    ],
  );

  return (
    <TranscriptsContext.Provider value={contextValue}>
      {children}
    </TranscriptsContext.Provider>
  );
}

// Custom hook for using the transcription context
export function useTranscripts() {
  const context = useContext(TranscriptsContext);
  if (context === undefined) {
    throw new Error("useTranscripts must be used within a TranscriptsProvider");
  }
  return context;
}
