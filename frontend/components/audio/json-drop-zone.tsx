/* eslint-disable react/require-default-props */

"use client";

import React, { useState, useRef } from "react";
import { v4 as uuidv4 } from "uuid";
import posthog from "posthog-js";

type DialogueEntry = {
  speaker: string;
  text: string;
  start_time: number;
  end_time: number;
};

type TranscriptionData = {
  id: string;
  dialogue_entries: DialogueEntry[];
  date: string;
};

interface JsonDropZoneProps {
  onJsonProcessed: (transcription: TranscriptionData) => void;
  onError?: (errorMessage: string) => void;
  children: React.ReactNode;
}

export default function JsonDropZone({
  onJsonProcessed,
  onError,
  children,
}: JsonDropZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [dragCounter, setDragCounter] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleDragEnter = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setDragCounter((prevCount) => prevCount + 1);
    setIsDragging(true);
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setDragCounter((prevCount) => prevCount - 1);

    // Only set isDragging to false when we've left all elements
    if (dragCounter - 1 === 0) {
      setIsDragging(false);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    // Keep the dragging state true while dragging over
    if (!isDragging) setIsDragging(true);
  };

  const handleJsonFile = async (file: File) => {
    try {
      const fileContent = await file.text();
      const jsonData = JSON.parse(fileContent);

      // Validate that the JSON has the expected format
      if (
        !Array.isArray(jsonData) ||
        !jsonData.every(
          (entry) =>
            typeof entry.speaker === "string" &&
            typeof entry.text === "string" &&
            typeof entry.start_time === "number" &&
            typeof entry.end_time === "number"
        )
      ) {
        throw new Error("Invalid JSON format");
      }

      // Process as if it was a transcription
      const transcription: TranscriptionData = {
        id: uuidv4(),
        dialogue_entries: jsonData,
        date: new Date().toISOString().split("T")[0],
      };

      onJsonProcessed(transcription);

      posthog.capture("test_json_transcription_uploaded", {
        entry_count: jsonData.length,
      });
    } catch (error) {
      console.error("Error processing JSON file:", error);
      if (onError) {
        onError(
          error instanceof Error ? error.message : "Error processing JSON file"
        );
      }
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
    setDragCounter(0);

    const file = event.dataTransfer.files[0];
    if (!file || !file.name.endsWith(".json")) {
      return;
    }

    handleJsonFile(file);
  };

  return (
    <div
      className="relative"
      ref={containerRef}
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {children}

      {isDragging && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/10 backdrop-blur-sm">
          <div className="rounded-lg bg-white p-6 shadow-lg dark:bg-gray-800">
            <p className="text-lg font-medium">
              Release to upload JSON transcription
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
