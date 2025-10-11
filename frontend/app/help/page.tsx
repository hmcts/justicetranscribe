"use client";

import React, { useEffect, useState } from "react";
import { Play, ExternalLink } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
// (no Card import; custom tiles instead)

type SanityVideoData = {
  title?: string;
  videoUrl?: string;
  thumbnailUrl?: string;
  thumbnailAlt?: string;
};

const SANITY_PROJECT_ID = process.env.NEXT_PUBLIC_SANITY_PROJECT_ID;
const SANITY_DATASET = process.env.NEXT_PUBLIC_SANITY_DATASET;
const SANITY_API_VERSION = process.env.NEXT_PUBLIC_SANITY_API_VERSION;

// Same tutorial document type (IDs split for basic/advanced for easy future change)
const SANITY_VIDEO_DOCUMENT_TYPE = "videoTutorial";
const SANITY_BASIC_TUTORIAL_UUID = "7d6e810c-087e-422a-af0a-62632e305bab";
const SANITY_ADVANCED_TUTORIAL_UUID = "146f7345-0da6-48b5-9a24-851bc7548298";
const SANITY_BASIC_TUTORIAL_ID = `${SANITY_VIDEO_DOCUMENT_TYPE};${SANITY_BASIC_TUTORIAL_UUID}`;
const SANITY_ADVANCED_TUTORIAL_ID = `${SANITY_VIDEO_DOCUMENT_TYPE};${SANITY_ADVANCED_TUTORIAL_UUID}`;

export default function HelpPage() {
  const [videoBasic, setVideoBasic] = useState<SanityVideoData | null>(null);
  const [isLoadingBasic, setIsLoadingBasic] = useState<boolean>(true);
  const [errorBasic, setErrorBasic] = useState<string | null>(null);

  const [videoAdvanced, setVideoAdvanced] = useState<SanityVideoData | null>(null);
  const [isLoadingAdvanced, setIsLoadingAdvanced] = useState<boolean>(true);
  const [errorAdvanced, setErrorAdvanced] = useState<string | null>(null);

  useEffect(() => {
    const fetchVideo = async () => {
      if (!SANITY_PROJECT_ID || !SANITY_DATASET || !SANITY_API_VERSION) {
        setErrorBasic(
          "Missing Sanity env vars. Set NEXT_PUBLIC_SANITY_PROJECT_ID, NEXT_PUBLIC_SANITY_DATASET, NEXT_PUBLIC_SANITY_API_VERSION."
        );
        setIsLoadingBasic(false);
        setIsLoadingAdvanced(false);
        return;
      }

      const query = `*[_type == "videoTutorial" && _id in [$id, $uuid, "drafts." + $uuid]][0]{
        title,
        "videoUrl": coalesce(video.asset->url, file.asset->url, url),
        "thumbnailUrl": coalesce(image.asset->url, thumbnail.asset->url),
        "thumbnailAlt": coalesce(image.alt, "")
      }`;

      const apiVersion = (SANITY_API_VERSION || "").startsWith("v")
        ? SANITY_API_VERSION
        : `v${SANITY_API_VERSION}`;

      const encodedQuery = encodeURIComponent(query);

      const buildEndpoint = (id: string, uuid: string) => {
        const encodedId = encodeURIComponent(JSON.stringify(id));
        const encodedUuid = encodeURIComponent(JSON.stringify(uuid));
        return `https://${SANITY_PROJECT_ID}.api.sanity.io/${apiVersion}/data/query/${SANITY_DATASET}?query=${encodedQuery}&%24id=${encodedId}&%24uuid=${encodedUuid}&perspective=published`;
      };

      // Fetch both videos in parallel
      try {
        const [resBasic, resAdvanced] = await Promise.all([
          fetch(buildEndpoint(SANITY_BASIC_TUTORIAL_ID, SANITY_BASIC_TUTORIAL_UUID), { cache: "no-store" }),
          fetch(buildEndpoint(SANITY_ADVANCED_TUTORIAL_ID, SANITY_ADVANCED_TUTORIAL_UUID), { cache: "no-store" }),
        ]);

        // Basic
        if (!resBasic.ok) {
          const body = await resBasic.text();
          throw new Error(`Basic request failed (${resBasic.status}): ${body}`);
        }
        const jsonBasic = await resBasic.json();
        const resultBasic: SanityVideoData | null = jsonBasic?.result ?? null;
        if (!resultBasic || !resultBasic.videoUrl) {
          throw new Error("Basic video not found or missing playable URL.");
        }
        setVideoBasic(resultBasic);

        // Advanced
        if (!resAdvanced.ok) {
          const body = await resAdvanced.text();
          throw new Error(`Advanced request failed (${resAdvanced.status}): ${body}`);
        }
        const jsonAdvanced = await resAdvanced.json();
        const resultAdvanced: SanityVideoData | null = jsonAdvanced?.result ?? null;
        if (!resultAdvanced || !resultAdvanced.videoUrl) {
          throw new Error("Advanced video not found or missing playable URL.");
        }
        setVideoAdvanced(resultAdvanced);
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "Failed to load videos.";
        // Set both errors for visibility
        setErrorBasic(msg);
        setErrorAdvanced(msg);
      } finally {
        setIsLoadingBasic(false);
        setIsLoadingAdvanced(false);
      }
    };

    fetchVideo();
  }, []);
  return (
    <div className="min-h-screen bg-background">
      {/* Main Content */}
      <div className="container mx-auto max-w-4xl px-4 py-8">
        {/* Page Header */}
        <div className="mb-12 text-center">
          <h1 className="mb-4 text-4xl font-bold tracking-tight">Help</h1>
          <p className="mx-auto max-w-2xl text-xl">
            Get started with Justice Transcribe
          </p>
        </div>

        {/* Tutorial Cards */}
        <section className="mb-6" aria-labelledby="tutorials-heading">
          <h2 id="tutorials-heading" className="sr-only">Tutorials</h2>
          <div className="mx-auto grid max-w-5xl gap-6 md:grid-cols-2">
            {/* Basic Tutorial Tile */}
            {isLoadingBasic ? (
              <div className="aspect-video w-full animate-pulse rounded-2xl bg-gray-200" />
            ) : errorBasic ? (
              <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">{errorBasic}</div>
            ) : videoBasic ? (
              <Dialog>
                  <DialogTrigger asChild>
                    <button
                      type="button"
                      className="group relative block w-full overflow-hidden rounded-2xl bg-muted/20 transition-transform duration-300 ease-out hover:scale-[1.02] focus:outline-none focus:ring-2 focus:ring-blue-600"
                      aria-label="Open basic tutorial video"
                    >
                      {/* Media */}
                      <div className="relative aspect-video w-full">
                        {videoBasic.thumbnailUrl ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img
                            src={videoBasic.thumbnailUrl}
                            alt={videoBasic.thumbnailAlt || videoBasic.title || "Tutorial thumbnail"}
                            className="absolute inset-0 h-full w-full object-cover"
                          />
                        ) : (
                          <div className="absolute inset-0 h-full w-full bg-gradient-to-br from-indigo-500 via-purple-500 to-fuchsia-600" />
                        )}
                        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-black/20 to-black/70" />
                      </div>
                      {/* Label top-left */}
                      <div className="absolute left-5 top-4 z-10 text-left text-white/90">
                        <span className="text-sm font-medium tracking-wide">Video Tutorial</span>
                      </div>
                      {/* Duration pill */}
                      <div className="absolute right-5 top-4 z-10 rounded-full bg-black/60 px-3 py-1 text-xs font-semibold text-white">
                        6:50
                      </div>
                      {/* Title bottom-left - smaller, left aligned */}
                      <div className="absolute bottom-5 left-5 z-10 pr-6">
                        <p className="text-lg font-semibold leading-tight text-white drop-shadow-sm md:text-xl">
                          {videoBasic.title || "Welcome to Justice Transcribe"}
                        </p>
                      </div>
                      {/* Hover Play Button */}
                      <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center">
                        <div className="translate-y-1 opacity-0 transition-all duration-200 group-hover:translate-y-0 group-hover:opacity-100">
                          <div className="rounded-full bg-white/90 p-5 shadow-md">
                            <Play className="size-6 text-blue-600" />
                          </div>
                        </div>
                      </div>
                    </button>
                  </DialogTrigger>
                  <DialogContent className="max-w-3xl p-0">
                    <div className="aspect-video w-full overflow-hidden rounded-md bg-black">
                      <video
                        controls
                        autoPlay
                        playsInline
                        src={videoBasic.videoUrl}
                        className="h-full w-full object-contain"
                      />
                    </div>
                  </DialogContent>
                </Dialog>
            ) : null}

            {/* Advanced Tutorial Tile - Coming Soon */}
            <div className="group relative block w-full overflow-hidden rounded-2xl bg-muted/20 transition-transform duration-300 ease-out hover:scale-[1.02] focus:outline-none focus:ring-2 focus:ring-blue-600">
              {/* Media */}
              <div className="relative aspect-video w-full">
                <div className="absolute inset-0 h-full w-full bg-gradient-to-br from-cyan-500 via-sky-500 to-blue-600" />
                <div className="absolute inset-0 bg-gradient-to-b from-transparent via-black/20 to-black/70" />
                {/* Drum roll emoji overlay */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-6xl">🥁</div>
                </div>
              </div>
              {/* Label top-left */}
              <div className="absolute left-5 top-4 z-10 text-left text-white/90">
                <span className="text-sm font-medium tracking-wide">Advanced Tutorial</span>
              </div>
              {/* Title bottom-left */}
              <div className="absolute bottom-5 left-5 z-10 pr-6">
                <p className="text-lg font-semibold leading-tight text-white drop-shadow-sm md:text-xl">
                  Coming Soon
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Need additional support: moved directly under tutorials and emphasized */}
        <section
          className="mb-6 rounded-lg border border-green-200 bg-green-50 p-6"
          aria-labelledby="need-support-heading"
        >
          <h2 id="need-support-heading" className="mb-2 text-xl font-bold text-green-700">
            Need additional support?
          </h2>
          <p className="mb-4 text-black">
            Join our Microsoft Teams channel for real-time assistance from our support team.
          </p>
          <Button 
            asChild 
            className="text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#10652F] focus-visible:ring-offset-2"
            style={{ 
              backgroundColor: "#10652F",
              borderColor: "#10652F"
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "#0d4f26";
              e.currentTarget.style.borderColor = "#0d4f26";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "#10652F";
              e.currentTarget.style.borderColor = "#10652F";
            }}
          >
            <a
              href="https://teams.microsoft.com/l/team/19%3AEo8kdcW8DWqHbl1e-hbFsTHXqJt9uBVr077C7X2Z0NU1%40thread.tacv2/conversations?groupId=4e32ea9c-dfcc-4150-9ebf-f1f73ea873ce&tenantId=c6874728-71e6-41fe-a9e1-2e8c36776ad8"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Join Teams channel for support (opens in new tab)"
            >
              <ExternalLink className="mr-2 size-4" aria-hidden="true" />
              Join Teams Channel
            </a>
          </Button>
        </section>

        {/* Justice Transcribe — Approved Use Cases */}
        <section className="mb-6 rounded-lg border p-6">
          <h2 className="mb-4 text-xl font-semibold">
            Justice Transcribe — Approved Use Cases
          </h2>
          <p className="mb-3">
            Per the Data Protection assessment, Justice Transcribe can be used for:
          </p>
          <ul className="mb-3 ml-6 list-disc space-y-1">
            <li>Induction</li>
            <li>Direct contact with People on Probation</li>
            <li>Professionals&apos; meetings</li>
            <li>Preparation for risk assessment</li>
            <li>Staff supervision</li>
          </ul>
          <p className="mb-3">
            <strong>Coming soon:</strong> PSR use cases.
          </p>
          <p>
            If you have any other use cases, reach out to{" "}
            <a
              href="mailto:transcribe@justice.gov.uk"
              className="font-medium underline"
              aria-label="Email transcribe@justice.gov.uk"
            >
              transcribe@justice.gov.uk
            </a>{" "}
            and we&apos;ll get on it.
          </p>
        </section>

        {/* Individual Sections */}
        <div className="space-y-6">
          {/* Phone/VPN Issue */}
          <section className="rounded-lg border p-6">
            <h3 className="mb-4 text-lg font-semibold">
              Phone not working? (VPN not connected)
            </h3>
            <p className="mb-2">
              If your phone can&apos;t connect to apps and you can&apos;t see
              &quot;VPN&quot; at the top of your iPhone screen then you need to
              reconnect:
            </p>
            <ol className="ml-6 list-decimal space-y-1.5">
              <li>Open the GlobalProtect app.</li>
              <li>
                Tap Connect. If you see a grey/paused circle, tap the middle
                until it turns blue and shows Connected.
              </li>
              <li>
                Wait a few seconds for the VPN indicator to appear at the top of your screen.
              </li>
              <li>If this doesn&apos;t work, contact the IT Service Desk.</li>
            </ol>
          </section>

          {/* Privacy and Visibility */}
          <section className="rounded-lg border p-6">
            <h3 className="mb-4 text-lg font-semibold">
              Can my manager or colleagues see my summaries or transcripts?
            </h3>
            <p className="mb-2">
              No. Only you can access your JT transcripts and summaries (the
              audio files aren&apos;t stored). Managers and colleagues
              don&apos;t have visibility unless you choose to share them (e.g.
              by copy-and-paste).
            </p>
            <p>
              The evaluation team may access a small sample to check accuracy
              and product performance under strict governance.
            </p>
          </section>
          {/* Mobile Recording Tips */}
          <section className="rounded-lg border p-6">
            <h3 className="mb-4 text-lg font-semibold">
              Before you start recording on mobile
            </h3>
            <p className="mb-3">
              Do these two things to avoid losing your recording:
            </p>
            <ol className="ml-6 list-decimal space-y-2">
              <li>
                Turn on Do Not Disturb to stop calls or notifications from
                interrupting.
              </li>
              <li>
                Don&apos;t refresh the page as this will delete your recording.
              </li>
            </ol>
          </section>

          {/* Policies & Guidelines */}
          <section className="rounded-lg border p-6">
            <h3 className="mb-2 text-lg font-semibold">
              Policies & Guidelines
            </h3>
            <p className="mb-3">
              Review our organization&apos;s AI usage policies and best
              practices.
            </p>
            <Button 
              variant="outline"
              asChild
            >
              <a
                href="https://intranet.justice.gov.uk/guidance/it-services/ai-in-moj/ai-usage-guidelines/"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="View AI Policy & Guidance - opens in new tab"
              >
                View AI Policy & Guidance{" "}
                <ExternalLink className="ml-1 size-4" />
              </a>
            </Button>
          </section>

          {/* Conversation Script for People on Probation */}
          <section className="rounded-lg border p-6">
            <h3 className="mb-2 text-lg font-semibold">
              Conversation Script for People on Probation
            </h3>
            <p className="mb-3">
              See this document for a simple script to explain Justice Transcribe to people on probation. It explains what it does, why we use it, and how we handle data safely and compliantly.
            </p>
            <Button variant="outline" asChild>
              <a
                href="https://justiceuk.sharepoint.com/:w:/s/JusticeAIUnit/EVMV3NmTchVCgtY-UAlpjSwBDZ9PEe10_HFadAquZUksPw?e=0V5WqE"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Open Conversation Script for People on Probation - opens in new tab"
              >
                Open Conversation Script
                <ExternalLink className="ml-1 size-4" />
              </a>
            </Button>
          </section>

          {/* SARs Request Guidance */}
          <section className="rounded-lg border p-6">
            <h3 className="mb-2 text-lg font-semibold">SARs Request Guidance</h3>
            <p className="mb-3">
              For guidance on how to comply with Subject Access Requests (SARs) email us on
              <a
                href="mailto:transcribe@justice.gov.uk"
                className="mx-1 font-medium underline"
                aria-label="Email transcribe@justice.gov.uk"
              >
                transcribe@justice.gov.uk
              </a>
              .
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
