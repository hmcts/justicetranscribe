// DialogueManager.tsx
import "react-h5-audio-player/lib/styles.css";

import React, { useState } from "react";

import { Card, CardContent } from "@/components/ui/card";

import SpeakerAndTranscriptEditor from "@/components/transcription/speaker-and-transcript-editor";
import posthog from "posthog-js";
import { useTranscripts } from "@/providers/transcripts";
import DialogueHeader from "@/components/minutes/dialogue-manager-header";
import MinutesEditor from "@/components/minutes/minutes-editor";
import {
  WhatsNewModal,
  useWhatsNewModal,
} from "@/components/ui/whats-new-modal";

function DialogueManager() {
  const [currentCitationIndex, setCurrentCitationIndex] = useState<
    number | null
  >(null);
  const [activeTab, setActiveTab] = useState("minutes");

  const { currentTranscription } = useTranscripts();
  const { showModal, handleDismiss } = useWhatsNewModal();

  const handleCitationClick = (index: number) => {
    setCurrentCitationIndex(index);
    posthog.capture("citation_clicked", {
      citationIndex: index,
    });
  };

  return (
    <Card className="mx-auto min-h-screen w-full border-none pt-5">
      <DialogueHeader currentTranscription={currentTranscription} />
      <CardContent className=" p-1">
        <div className="w-full">
          {/* Custom Tab Buttons */}
          <div className="grid w-full grid-cols-2 rounded-lg bg-muted p-2">
            <button
              type="button"
              onClick={() => setActiveTab("minutes")}
              className={`rounded-md px-4 py-2.5 text-base font-semibold transition-all ${
                activeTab === "minutes"
                  ? "bg-background text-foreground shadow-md"
                  : "text-muted-foreground hover:bg-background/50 hover:text-foreground"
              }`}
              aria-pressed={activeTab === "minutes"}
            >
              Meeting Summary
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("transcript")}
              className={`rounded-md px-4 py-2.5 text-base font-semibold transition-all ${
                activeTab === "transcript"
                  ? "bg-background text-foreground shadow-md"
                  : "text-muted-foreground hover:bg-background/50 hover:text-foreground"
              }`}
              aria-pressed={activeTab === "transcript"}
            >
              Transcript
            </button>
          </div>

          <div className="mt-4">
            <div
              style={{ display: activeTab === "minutes" ? "block" : "none" }}
            >
              <MinutesEditor onCitationClick={handleCitationClick} />{" "}
            </div>

            <div
              style={{ display: activeTab === "transcript" ? "block" : "none" }}
            >
              <SpeakerAndTranscriptEditor
                currentCitationIndex={currentCitationIndex}
              />
            </div>
          </div>
        </div>
      </CardContent>

      {/* What's New Modal */}
      <WhatsNewModal isOpen={showModal} onClose={handleDismiss} />
    </Card>
  );
}

export default DialogueManager;
