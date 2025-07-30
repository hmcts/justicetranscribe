/* eslint-disable jsx-a11y/media-has-caption */

"use client";

import React, { useEffect, useState } from "react";

interface AudioPlayerProps {
  audioBlob: Blob;
}

const getFileExtension = (blob: Blob): string => {
  try {
    if (!blob.type) {
      return "media";
    }

    const mimeType = blob.type.split(";")[0]; // Remove codec information
    const [category, type] = mimeType.split("/");

    if (category !== "audio" && category !== "video") {
      return "media";
    }

    // Map common media MIME types to their appropriate extensions
    const mimeToExtension: Record<string, string> = {
      // Audio types
      "audio/webm": "webm",
      "audio/ogg": "ogg",
      "audio/mpeg": "mp3",
      "audio/wav": "wav",
      "audio/x-wav": "wav",
      "audio/mp4": "m4a",
      // Video types
      "video/webm": "webm",
      "video/mp4": "mp4",
      "video/quicktime": "mov",
      "video/x-msvideo": "avi",
      "video/ogg": "ogv",
    };

    return mimeToExtension[mimeType] || type || category;
  } catch (error) {
    console.warn("Error determining media file type:", error);
    return "media";
  }
};

function AudioPlayerComponent({ audioBlob }: AudioPlayerProps) {
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string>("");

  useEffect(() => {
    if (audioBlob) {
      const url = URL.createObjectURL(audioBlob);
      setAudioUrl(url);

      const fileExtension = getFileExtension(audioBlob);
      setFileName(`audio-file.${fileExtension}`);

      return () => {
        if (url) URL.revokeObjectURL(url);
      };
    }
    return undefined;
  }, [audioBlob]);

  if (!audioUrl) return null;

  return (
    <div className="mb-4">
      <audio controls className="w-full rounded-md" preload="none">
        <source src={audioUrl} type={audioBlob.type} />
        Your browser does not support the audio element.
      </audio>
      <div className="flex justify-end">
        <a
          href={audioUrl}
          download={fileName}
          className="mt-2 text-sm text-blue-600 hover:underline"
        >
          Download Audio File
        </a>
      </div>
    </div>
  );
}

export default AudioPlayerComponent;
