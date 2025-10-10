"use client";

import React, { useEffect, useRef, useState } from "react";
import { Check } from "lucide-react";

type SanityVideoData = {
  title?: string;
  videoUrl?: string;
};

const SANITY_PROJECT_ID = process.env.NEXT_PUBLIC_SANITY_PROJECT_ID;
const SANITY_DATASET = process.env.NEXT_PUBLIC_SANITY_DATASET;
const SANITY_API_VERSION = process.env.NEXT_PUBLIC_SANITY_API_VERSION;

// Reuse the same tutorial document as Step 2
const SANITY_VIDEO_DOCUMENT_TYPE = "videoTutorial";
const SANITY_VIDEO_DOCUMENT_UUID = "7cc10ecb-e007-4072-a9f3-a7f8712287ad";
const SANITY_VIDEO_DOCUMENT_ID = `${SANITY_VIDEO_DOCUMENT_TYPE};${SANITY_VIDEO_DOCUMENT_UUID}`;

export default function Step3ReviewEdit() {
  const [selectedVideo, setSelectedVideo] = useState<SanityVideoData | null>(null);
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
      const encodedId = encodeURIComponent(JSON.stringify(SANITY_VIDEO_DOCUMENT_ID));
      const encodedUuid = encodeURIComponent(JSON.stringify(SANITY_VIDEO_DOCUMENT_UUID));
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
      <div className="grid grid-cols-12 gap-6 items-start">
        {/* Video Section */}
        <div className="col-span-12 md:col-span-7 lg:col-span-8">
          <div className="w-full">
            {isLoading && (
              <div className="aspect-video w-full animate-pulse rounded-lg bg-gray-200" />)
            }
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
                  className="h-full w-full object-contain"
                />
              </div>
            )}
          </div>
        </div>

        {/* Sidebar: Title + Checklist */}
        <div className="col-span-12 md:col-span-5 lg:col-span-4 min-w-0 md:min-w-[280px] lg:min-w-[320px]">
          <div className="mb-4 text-left">
            <h1 className="text-3xl font-semibold sm:text-4xl">Review and edit</h1>
            <h2 className="bg-gradient-to-r from-purple-600 to-purple-400 bg-clip-text text-xl font-medium text-transparent">
              Your professional judgement is key
            </h2>
          </div>
          <h3 className="text-xl font-semibold text-black">Common corrections</h3>
          <div className="space-y-4 text-black">
            <div className="flex items-start space-x-3">
              <Check className="mt-1 size-5 shrink-0 text-green-600" />
              <p className="text-base">Verify names, pronouns, places, and acronyms.</p>
            </div>
            <div className="flex items-start space-x-3">
              <Check className="mt-1 size-5 shrink-0 text-green-600" />
              <p className="text-base">Add missing specifics (risk-relevant facts, DOBs).</p>
            </div>
            <div className="flex items-start space-x-3">
              <Check className="mt-1 size-5 shrink-0 text-green-600" />
              <p className="text-base">Stay under 4,000 characters for NDelius.</p>
            </div>
            <div className="flex items-start space-x-3">
              <Check className="mt-1 size-5 shrink-0 text-green-600" />
              <p className="text-base">Describe body language, observations and wider context.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
