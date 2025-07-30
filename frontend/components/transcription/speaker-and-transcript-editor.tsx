import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { useTranscripts } from "@/providers/transcripts";
import TranscriptEditor from "@/components/transcription/transcript-editor";
import AudioPlayerComponent from "@/components/audio/audio-player";

interface SpeakerAndTranscriptEditorProps {
  currentCitationIndex: number | null;
}

function SpeakerAndTranscriptEditor({
  currentCitationIndex,
}: SpeakerAndTranscriptEditorProps) {
  const { currentTranscription, audioBlob } = useTranscripts();

  if (!currentTranscription) return null;

  return (
    <div className="space-y-4">
      {audioBlob && <AudioPlayerComponent audioBlob={audioBlob} />}

      <Card>
        <div className="relative">
          <CardContent className="p-4">
            <TranscriptEditor currentCitationIndex={currentCitationIndex} />
          </CardContent>
        </div>
      </Card>
    </div>
  );
}

export default SpeakerAndTranscriptEditor;
