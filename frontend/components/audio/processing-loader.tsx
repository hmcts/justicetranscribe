import React from "react";
import { Loader2 } from "lucide-react";
import { useTranscripts } from "@/providers/transcripts";
import StartNewMeetingButton from "@/components/ui/start-new-meeting-button";

export type AudioProcessingStatus =
  | "idle"
  | "recording"
  | { state: "uploading"; progress: number }
  | "transcribing";

interface ProcessingLoaderProps {
  status: AudioProcessingStatus;
  onStopPolling: () => void;
}

export default function ProcessingLoader({
  status,
  onStopPolling,
}: ProcessingLoaderProps) {
  const { newTranscription } = useTranscripts();

  const handleNewTranscription = () => {
    onStopPolling();
    newTranscription();
  };

  if (typeof status === "object" && status.state === "uploading") {
    return (
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
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
            Progress: {status.progress}%
          </p>
          <div className="mt-3 h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
            <div
              className="h-2 rounded-full bg-blue-500 transition-all duration-300"
              style={{ width: `${status.progress}%` }}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md py-12 text-center">
      <h1 className="mb-6 text-3xl font-bold text-gray-900 dark:text-gray-100">
        Upload Complete
      </h1>
      <div className="rounded-lg border border-blue-100 bg-blue-50 p-6 dark:border-blue-900/30 dark:bg-blue-900/10">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          Your meeting is safely saved
        </h2>
        <p className="mt-3 text-sm text-gray-600 dark:text-gray-300">
          We&apos;ll send you an email once your meeting is ready.
        </p>
        <div className="mt-6 flex justify-center">
          <StartNewMeetingButton
            onClick={handleNewTranscription}
            className="px-4 shadow-md transition-all duration-200 hover:scale-105 hover:shadow-lg active:scale-95"
            fullWidth={false}
            showIcon={false}
          />
        </div>
      </div>
    </div>
  );
}
