"use client";

import React from "react";

import WelcomePage from "@/components/welcome-page";
import DialogueManager from "@/components/dialogue-manager";
import { useBrowserNavigation } from "@/hooks/use-browser-navigation";

function MainParentComponent() {
  const { currentParams } = useBrowserNavigation();

  // Check if we're directly accessing a transcript via URL
  const transcriptId = currentParams?.get("id");

  return (
    <div className="flex">
      <div className="mx-auto flex w-full items-center justify-center">
        {!transcriptId && (
          <div className="w-full">
            <WelcomePage />
          </div>
        )}
        {transcriptId && (
          <div className="w-full">
            <DialogueManager />
          </div>
        )}
      </div>
    </div>
  );
}

export default MainParentComponent;
