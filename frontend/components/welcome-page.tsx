/* eslint-disable react/button-has-type */
/* eslint-disable jsx-a11y/no-static-element-interactions */
/* eslint-disable jsx-a11y/click-events-have-key-events */

"use client";

import React from "react";
import { Plus, ChevronLeft, Mic, MonitorPlay } from "lucide-react";
import { useTranscripts } from "@/providers/transcripts";
import { useUserSettings } from "@/providers/user-settings";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useMediaQuery } from "@/hooks/use-media-query";
import { getFirstName } from "@/lib/utils";
import { AudioBackup } from "@/lib/indexeddb-backup";
import StartNewMeetingButton from "@/components/ui/start-new-meeting-button";
import AudioUploader from "./audio/audio-uploader";
import MeetingsList from "./meetings-list";
import BackupRecovery from "./audio/backup-recovery";
import BackupUploader from "./audio/backup-uploader";

function WelcomePage() {
  const {
    newTranscription,
    isLoading,
    selectedRecordingMode,
    setSelectedRecordingMode,
    transcriptsMetadata,
  } = useTranscripts();

  const { user } = useUserSettings();

  const [showAllMeetings, setShowAllMeetings] = React.useState(false);
  const [retryingBackup, setRetryingBackup] =
    React.useState<AudioBackup | null>(null);
  const [speakerFilter, setSpeakerFilter] = React.useState<string>("all");
  const isMobile = useMediaQuery("(max-width: 768px)");

  const firstName = user?.email
    ? getFirstName(user.email).charAt(0).toUpperCase() +
      getFirstName(user.email).slice(1).toLowerCase()
    : "";
  const heading = firstName
    ? `Welcome back ${firstName} 👋`
    : "Welcome back 👋";

  const allSpeakers = React.useMemo(() => {
    const speakers = new Set<string>();
    transcriptsMetadata.forEach((transcript) => {
      transcript.speakers?.forEach((speaker) => speakers.add(speaker));
    });
    return Array.from(speakers).sort();
  }, [transcriptsMetadata]);

  const filteredMeetings = React.useMemo(() => {
    if (speakerFilter === "all") {
      return transcriptsMetadata;
    }
    return transcriptsMetadata.filter((meeting) =>
      meeting.speakers.includes(speakerFilter)
    );
  }, [transcriptsMetadata, speakerFilter]);

  const handleNewMeeting = () => {
    if (isMobile || showAllMeetings) {
      // On mobile or when viewing all meetings, default to mic recording
      setSelectedRecordingMode("mic");
      newTranscription();
    }
  };

  const handleCloseRecorder = () => {
    setSelectedRecordingMode(null);
  };

  const handleRetryUpload = async (backup: AudioBackup) => {
    setRetryingBackup(backup);
  };

  const handleCloseBackupUploader = () => {
    setRetryingBackup(null);
  };

  const handleBackupUploadSuccess = () => {
    setRetryingBackup(null);
    // Optionally refresh the backup list or show a success message
  };

  if (retryingBackup) {
    return (
      <BackupUploader
        backup={retryingBackup}
        onClose={handleCloseBackupUploader}
        onUploadSuccess={handleBackupUploadSuccess}
      />
    );
  }

  if (selectedRecordingMode) {
    return (
      <AudioUploader
        initialRecordingMode={selectedRecordingMode}
        onClose={handleCloseRecorder}
      />
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="mb-8 text-center">
        {showAllMeetings ? (
          <>
            <h1 className="mb-4 text-3xl font-bold">All Meetings</h1>
            <div className="mb-4 flex items-center justify-center">
              <Button
                variant="ghost"
                className="flex items-center gap-1"
                onClick={() => setShowAllMeetings(false)}
              >
                <ChevronLeft className="size-4" />
                Back to Welcome
              </Button>
            </div>
          </>
        ) : (
          <>
            <h1 className="mb-2 text-3xl font-bold">{heading}</h1>
            <p className="text-gray-600">
              Create a new meeting or continue with a recent one
            </p>
          </>
        )}
      </div>

      {!showAllMeetings && (
        <div className="mb-8">
          {isMobile ? (
            <StartNewMeetingButton
              onClick={handleNewMeeting}
              size="large"
            />
          ) : (
            <Popover>
              <PopoverTrigger asChild>
                <StartNewMeetingButton
                  size="large"
                />
              </PopoverTrigger>
              <PopoverContent
                className="w-[--radix-popover-trigger-width] p-3"
                sideOffset={4}
              >
                <div className="grid gap-3">
                  <button
                    className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-4 text-left transition-colors hover:bg-gray-50"
                    onClick={() => {
                      setSelectedRecordingMode("mic");
                      newTranscription();
                    }}
                  >
                    <div className="rounded-lg bg-blue-100 p-2">
                      <Mic className="size-5 text-blue-600" />
                    </div>
                    <div>
                      <div className="font-medium">
                        Record in Person Meeting
                      </div>
                      <div className="text-sm text-gray-500">
                        Use your device&apos;s microphone
                      </div>
                    </div>
                  </button>

                  <button
                    className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-4 text-left transition-colors hover:bg-gray-50"
                    onClick={() => {
                      setSelectedRecordingMode("screen");
                      newTranscription();
                    }}
                  >
                    <div className="rounded-lg bg-blue-100 p-2">
                      <MonitorPlay className="size-5 text-blue-600" />
                    </div>
                    <div>
                      <div className="font-medium">Record Virtual Meeting</div>
                      <div className="text-sm text-gray-500">
                        Record your screen and audio
                      </div>
                    </div>
                  </button>
                </div>
              </PopoverContent>
            </Popover>
          )}
        </div>
      )}

      {!showAllMeetings && allSpeakers.length > 0 && (
        <div className="mb-6 rounded-lg border border-gray-200 bg-gray-50 p-4">
          <div className="mb-2">
            <div
              id="speaker-filter-label"
              className="text-sm font-medium text-gray-700"
            >
              Filter by Speaker
            </div>
          </div>
          <Select value={speakerFilter} onValueChange={setSpeakerFilter}>
            <SelectTrigger 
              className="w-full"
              aria-labelledby="speaker-filter-label"
            >
              <SelectValue placeholder="All speakers" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All speakers</SelectItem>
              {allSpeakers.map((speaker) => (
                <SelectItem key={speaker} value={speaker}>
                  {speaker}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      <BackupRecovery onRetryUpload={handleRetryUpload} />

      <div className="mt-8">
        <MeetingsList
          showAllMeetings={showAllMeetings}
          setShowAllMeetings={setShowAllMeetings}
          handleNewMeeting={handleNewMeeting}
          isLoading={isLoading}
          meetings={filteredMeetings}
        />
      </div>
    </div>
  );
}

export default WelcomePage;
