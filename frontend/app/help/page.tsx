import React from "react";
import { Play, ExternalLink } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";

export default function HelpPage() {
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
          <div className="mx-auto grid max-w-4xl gap-6 md:grid-cols-2">
            {/* Basic Tutorial Card */}
            <Card className="group transition-shadow hover:shadow-md">
              <CardHeader className="pb-4 text-center">
                <div className="mx-auto mb-4 flex size-16 items-center justify-center rounded-full bg-muted transition-colors group-hover:bg-muted/80">
                  <Play
                    className="size-8 text-muted-foreground"
                    aria-hidden="true"
                  />
                </div>
                <CardTitle className="text-xl">Basic Tutorial</CardTitle>
                <CardDescription>
                  Must-know actions to succeed straight away
                </CardDescription>
              </CardHeader>
              <CardContent className="text-center">
                <p className="mb-4 text-sm text-muted-foreground">
                  Coming soon
                </p>
                <Button
                  variant="default"
                  size="lg"
                  disabled
                  className="w-full"
                  aria-label="Play basic tutorial - coming soon"
                >
                  <Play className="mr-2 size-4" />
                  Play Basic Tutorial
                </Button>
              </CardContent>
            </Card>

            {/* Advanced Tutorial Card */}
            <Card className="group transition-shadow hover:shadow-md">
              <CardHeader className="pb-4 text-center">
                <div className="mx-auto mb-4 flex size-16 items-center justify-center rounded-full bg-muted transition-colors group-hover:bg-muted/80">
                  <Play
                    className="size-8 text-muted-foreground"
                    aria-hidden="true"
                  />
                </div>
                <CardTitle className="text-xl">Advanced Tutorial</CardTitle>
                <CardDescription>
                  Time-saving tricks with AI edit for summaries
                </CardDescription>
              </CardHeader>
              <CardContent className="text-center">
                <p className="mb-4 text-sm text-muted-foreground">
                  Coming soon
                </p>
                <Button
                  variant="default"
                  size="lg"
                  disabled
                  className="w-full"
                  aria-label="Play advanced tutorial - coming soon"
                >
                  <Play className="mr-2 size-4" />
                  Play Advanced Tutorial
                </Button>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Need additional support: moved directly under tutorials and emphasized */}
        <section
          className="mb-12 rounded-lg border border-blue-200 bg-blue-50 p-6"
          aria-labelledby="need-support-heading"
        >
          <h2 id="need-support-heading" className="mb-2 text-xl font-semibold text-blue-900">
            Need additional support?
          </h2>
          <p className="mb-4 text-blue-900">
            Join our Microsoft Teams channel for real-time assistance from our support team.
          </p>
          <Button variant="default" asChild className="bg-blue-600 text-white hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2">
            <a
              href="https://teams.microsoft.com/l/team/19%3AEo8kdcW8DWqHbl1e-hbFsTHXqJt9uBVr077C7X2Z0NU1%40thread.tacv2/conversations?groupId=4e32ea9c-dfcc-4150-9ebf-f1f73ea873ce&tenantId=c6874728-71e6-41fe-a9e1-2e8c36776ad8"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Join Teams channel for support (opens in new tab)"
            >
              Join Teams Channel <ExternalLink className="ml-1 size-4" aria-hidden="true" />
            </a>
          </Button>
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

          {/* Need additional support: moved above, so removed duplicate here */}

          {/* Policies & Guidelines */}
          <section className="rounded-lg border p-6">
            <h3 className="mb-2 text-lg font-semibold">
              Policies & Guidelines
            </h3>
            <p className="mb-3">
              Review our organization&apos;s AI usage policies and best
              practices.
            </p>
            <Button variant="outline" asChild>
              <a
                href="https://intranet.justice.gov.uk/guidance/it-services/ai-in-moj/"
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
