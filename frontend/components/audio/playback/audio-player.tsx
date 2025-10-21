/* eslint-disable jsx-a11y/media-has-caption */

"use client";

import React, { useEffect, useState } from "react";

interface AudioPlayerProps {
  audioBlob: Blob;
  restrictDownload: boolean;
}

function AudioPlayerComponent({
  audioBlob,
  restrictDownload = false,
}: AudioPlayerProps) {
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  useEffect(() => {
    if (audioBlob) {
      const url = URL.createObjectURL(audioBlob);
      setAudioUrl(url);

      return () => {
        if (url) URL.revokeObjectURL(url);
      };
    }
    return undefined;
  }, [audioBlob]);

  if (!audioUrl) return null;

  return (
    <div className="mb-4">
      <audio
        controls
        className="w-full rounded-md"
        preload="none"
        controlsList={restrictDownload ? "nodownload" : undefined}
      >
        <source src={audioUrl} type={audioBlob.type} />
        Your browser does not support the audio element.
      </audio>
    </div>
  );
}

export default AudioPlayerComponent;
