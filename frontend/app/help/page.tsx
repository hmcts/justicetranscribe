import React from "react";
import Link from "next/link";
import { Play, ExternalLink } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export default function HelpPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Main Content */}
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Page Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold tracking-tight mb-4">Help</h1>
          <p className="text-xl max-w-2xl mx-auto">
            Get started with Justice Transcribe
          </p>
        </div>

        {/* Tutorial Cards */}
        <section className="mb-12">
          <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            {/* Basic Tutorial Card */}
            <Card className="group hover:shadow-md transition-shadow">
              <CardHeader className="text-center pb-4">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-muted flex items-center justify-center group-hover:bg-muted/80 transition-colors">
                  <Play className="w-8 h-8 text-muted-foreground" aria-hidden="true" />
                </div>
                <CardTitle className="text-xl">Basic Tutorial</CardTitle>
                <CardDescription>
                  Must-know actions to succeed straight away
                </CardDescription>
              </CardHeader>
              <CardContent className="text-center">
                <p className="text-sm text-muted-foreground mb-4">Coming soon</p>
                <Button 
                  variant="default" 
                  size="lg" 
                  disabled
                  className="w-full"
                  aria-label="Play basic tutorial - coming soon"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Play Basic Tutorial
                </Button>
              </CardContent>
            </Card>

            {/* Advanced Tutorial Card */}
            <Card className="group hover:shadow-md transition-shadow">
              <CardHeader className="text-center pb-4">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-muted flex items-center justify-center group-hover:bg-muted/80 transition-colors">
                  <Play className="w-8 h-8 text-muted-foreground" aria-hidden="true" />
                </div>
                <CardTitle className="text-xl">Advanced Tutorial</CardTitle>
                <CardDescription>
                  Time-saving tricks with AI edit for summaries
                </CardDescription>
              </CardHeader>
              <CardContent className="text-center">
                <p className="text-sm text-muted-foreground mb-4">Coming soon</p>
                <Button 
                  variant="default" 
                  size="lg" 
                  disabled
                  className="w-full"
                  aria-label="Play advanced tutorial - coming soon"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Play Advanced Tutorial
                </Button>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Individual Sections */}
        <div className="space-y-6">
          {/* Mobile Recording Tips */}
          <section className="border rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Before you start recording on mobile</h3>
            <p className="mb-3">Do these two things to avoid losing your recording:</p>
            <ol className="space-y-2 ml-6 list-decimal">
              <li>Turn on Do Not Disturb to stop calls or notifications from interrupting.</li>
              <li>Don't refresh the page as this will delete your recording.</li>
            </ol>
          </section>

          {/* Need additional support */}
          <section className="border rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-2">Need additional support?</h3>
            <p className="mb-3">
              Join our Microsoft Teams channel for real-time assistance from our support team.
            </p>
            <Button 
              variant="outline" 
              asChild
            >
              <a 
                href="#" 
                target="_blank" 
                rel="noopener noreferrer"
                aria-label="Join Teams channel for support - opens in new tab"
              >
                Join Teams Channel <ExternalLink className="w-4 h-4 ml-1" />
              </a>
            </Button>
          </section>

          {/* Policies & Guidelines */}
          <section className="border rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-2">Policies & Guidelines</h3>
            <p className="mb-3">
              Review our organization's AI usage policies and best practices.
            </p>
            <Button 
              variant="outline" 
              asChild
            >
              <a 
                href="#" 
                target="_blank" 
                rel="noopener noreferrer"
                aria-label="View AI Policy & Guidance - opens in new tab"
              >
                View AI Policy & Guidance <ExternalLink className="w-4 h-4 ml-1" />
              </a>
            </Button>
          </section>

          {/* Probation Information Flyer */}
          <section className="border rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-2">Probation Information Flyer</h3>
            <p className="mb-3">
              Share this flyer with people on probation. It explains how our AI system works and our data compliance approach.
            </p>
            <Button 
              variant="outline" 
              asChild
            >
              <a 
                href="#" 
                download
                aria-label="Download Probation Flyer"
              >
                Download Probation Flyer <ExternalLink className="w-4 h-4 ml-1" />
              </a>
            </Button>
          </section>
        </div>
      </div>
    </div>
  );
}
