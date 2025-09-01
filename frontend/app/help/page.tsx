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
        <section className="mb-12">
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

        {/* Individual Sections */}
        <div className="space-y-6">
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

          {/* Need additional support */}
          <section className="rounded-lg border p-6">
            <h3 className="mb-2 text-lg font-semibold">
              Need additional support?
            </h3>
            <p className="mb-3">
              Join our Microsoft Teams channel for real-time assistance from our
              support team.
            </p>
            <Button variant="outline" asChild>
              <a
                href="https://teams.microsoft.com"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Join Teams channel for support - opens in new tab"
              >
                Join Teams Channel <ExternalLink className="ml-1 size-4" />
              </a>
            </Button>
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
            <Button variant="outline" asChild>
              <a
                href="https://example.com/ai-policy"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="View AI Policy & Guidance - opens in new tab"
              >
                View AI Policy & Guidance{" "}
                <ExternalLink className="ml-1 size-4" />
              </a>
            </Button>
          </section>

          {/* Probation Information Flyer */}
          <section className="rounded-lg border p-6">
            <h3 className="mb-2 text-lg font-semibold">
              Probation Information Flyer
            </h3>
            <p className="mb-3">
              Share this flyer with people on probation. It explains how our AI
              system works and our data compliance approach.
            </p>
            <Button variant="outline" asChild>
              <a
                href="/downloads/probation-flyer.pdf"
                download
                aria-label="Download Probation Flyer"
              >
                Download Probation Flyer{" "}
                <ExternalLink className="ml-1 size-4" />
              </a>
            </Button>
          </section>
        </div>
      </div>
    </div>
  );
}
