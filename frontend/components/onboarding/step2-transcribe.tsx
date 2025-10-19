/* eslint-disable jsx-a11y/media-has-caption */

"use client";

import React, { useEffect, useRef, useState } from "react";

type SanityVideoData = {
  title?: string;
  videoUrl?: string;
};

const SANITY_PROJECT_ID = process.env.NEXT_PUBLIC_SANITY_PROJECT_ID;
const SANITY_DATASET = process.env.NEXT_PUBLIC_SANITY_DATASET;
const SANITY_API_VERSION = process.env.NEXT_PUBLIC_SANITY_API_VERSION;

// Use the same tutorial document as the basic tutorial (type-prefixed id)
const SANITY_VIDEO_DOCUMENT_TYPE = "videoTutorial";
const SANITY_VIDEO_DOCUMENT_UUID = "146f7345-0da6-48b5-9a24-851bc7548298";
const SANITY_VIDEO_DOCUMENT_ID = `${SANITY_VIDEO_DOCUMENT_TYPE};${SANITY_VIDEO_DOCUMENT_UUID}`;

export default function Step2BasicTutorial() {
  const [selectedVideo, setSelectedVideo] = useState<SanityVideoData | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    const fetchVideo = async () => {
      if (!SANITY_PROJECT_ID || !SANITY_DATASET || !SANITY_API_VERSION) {
        setError(
          "Missing Sanity env vars. Set NEXT_PUBLIC_SANITY_PROJECT_ID, NEXT_PUBLIC_SANITY_DATASET, NEXT_PUBLIC_SANITY_API_VERSION."
        );
        setIsLoading(false);
        return;
      }

      const query = `*[_type == "videoTutorial" && _id in [$id, $uuid, "drafts." + $uuid]][0]{
        title,
        "videoUrl": coalesce(video.asset->url, file.asset->url, url)
      }`;

      const apiVersion = (SANITY_API_VERSION || "").startsWith("v")
        ? SANITY_API_VERSION
        : `v${SANITY_API_VERSION}`;

      const encodedQuery = encodeURIComponent(query);
      const encodedId = encodeURIComponent(
        JSON.stringify(SANITY_VIDEO_DOCUMENT_ID)
      );
      const encodedUuid = encodeURIComponent(
        JSON.stringify(SANITY_VIDEO_DOCUMENT_UUID)
      );
      const endpoint = `https://${SANITY_PROJECT_ID}.api.sanity.io/${apiVersion}/data/query/${SANITY_DATASET}?query=${encodedQuery}&%24id=${encodedId}&%24uuid=${encodedUuid}&perspective=published`;

      try {
        const res = await fetch(endpoint, { cache: "no-store" });
        if (!res.ok) {
          const body = await res.text();
          throw new Error(`Request failed (${res.status}): ${body}`);
        }
        const json = await res.json();
        const result: SanityVideoData | null = json?.result ?? null;
        if (!result || !result.videoUrl) {
          throw new Error("Video not found or missing playable URL.");
        }
        setSelectedVideo(result);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load video.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchVideo();
  }, []);

  useEffect(() => {
    if (selectedVideo && videoRef.current) {
      // Try to ensure playback with sound on supported browsers
      try {
        videoRef.current.muted = false;
        videoRef.current.volume = 1;
        const playPromise = videoRef.current.play();
        if (playPromise && typeof playPromise.then === "function") {
          playPromise.catch(() => {
            // Autoplay with sound may be blocked; ignore silently
          });
        }
      } catch (_) {
        // ignore
      }
    }
  }, [selectedVideo]);

  return (
    <div className="w-full space-y-6">
      {/* Content area - YouTube-like: main player left, sidebar right */}
      <div className="grid grid-cols-12 items-start gap-6">
        {/* Video Section */}
        <div className="col-span-12 md:col-span-7 lg:col-span-8">
          <div className="w-full">
            {isLoading && (
              <div className="aspect-video w-full animate-pulse rounded-lg bg-gray-200" />
            )}
            {!isLoading && error && (
              <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                {error}
              </div>
            )}
            {!isLoading && !error && selectedVideo && (
              <div className="aspect-video w-full overflow-hidden rounded-lg bg-black">
                <video
                  controls
                  autoPlay
                  playsInline
                  ref={videoRef}
                  src={selectedVideo.videoUrl}
                  className="size-full object-contain"
                />
              </div>
            )}
          </div>
        </div>

        {/* Steps Section */}
        <div className="col-span-12 min-w-0 md:col-span-5 md:min-w-[280px] lg:col-span-4 lg:min-w-[320px]">
          <div className="mb-4 text-left">
            <h1 className="text-3xl font-semibold sm:text-4xl">
              Transcribe a Meeting
            </h1>
            <h2 className="bg-gradient-to-r from-blue-600 to-blue-400 bg-clip-text text-xl font-medium text-transparent">
              Using Justice Transcribe is simple
            </h2>
          </div>
          <div
            className="space-y-4 text-black"
            aria-label="How to record a meeting steps"
          >
            <p className="text-base">
              <span className="mr-2 font-semibold text-blue-600">1.</span>
              Click start new meeting and select in person or virtual meeting
            </p>
            <p className="text-base">
              <span className="mr-2 font-semibold text-blue-600">2.</span>
              Give permission to use your microphone
            </p>
            <p className="text-base">
              <span className="mr-2 font-semibold text-blue-600">3.</span>
              Click start recording
            </p>
            <p className="text-base">
              <span className="mr-2 font-semibold text-blue-600">4.</span>
              Click stop recording
            </p>
            <p className="text-base">
              <span className="mr-2 font-semibold text-blue-600">5.</span>
              We&apos;ll email you when your summary is ready for review
            </p>
            <p className="mt-6 text-base text-black">
              You can record for up to 2 hours per session.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
