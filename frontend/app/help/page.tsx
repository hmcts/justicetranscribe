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
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Get started with Justice Transcribe
          </p>
        </div>

        {/* Tutorial Video Card */}
        <section className="mb-12">
          <Card className="group hover:shadow-md transition-shadow max-w-md mx-auto">
            <CardHeader className="text-center pb-4">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-muted flex items-center justify-center group-hover:bg-muted/80 transition-colors">
                <Play className="w-8 h-8 text-muted-foreground" aria-hidden="true" />
              </div>
              <CardTitle className="text-xl">Tutorial Video</CardTitle>
              <CardDescription>
                Short video: how to record, label speakers, generate minutes
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <p className="text-sm text-muted-foreground mb-4">Coming soon</p>
              <Button 
                variant="default" 
                size="lg" 
                disabled
                className="w-full"
                aria-label="Play tutorial video - coming soon"
              >
                <Play className="w-4 h-4 mr-2" />
                Play Tutorial
              </Button>
            </CardContent>
          </Card>
        </section>

        {/* Individual Sections */}
        <div className="space-y-6">
          {/* Device Setup */}
          <section className="border rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-2">Device Setup</h3>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium mb-2">Desktop</h4>
                <p className="text-sm text-muted-foreground mb-2">Save as bookmark</p>
                <ul className="text-sm text-muted-foreground space-y-1 ml-4">
                  <li>• Press Ctrl+D (Windows) or Cmd+D (Mac)</li>
                  <li>• Save to bookmarks bar for quick access</li>
                  <li>• Use external microphone for better quality</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium mb-2">Mobile</h4>
                <p className="text-sm text-muted-foreground mb-2">Enable "Do Not Disturb"</p>
                <ul className="text-sm text-muted-foreground space-y-1 ml-4">
                  <li>• Swipe down from top-right corner</li>
                  <li>• Tap moon icon to enable DND</li>
                  <li>• Prevents call interruptions during recording</li>
                </ul>
              </div>
            </div>
          </section>

          {/* Need additional support */}
          <section className="border rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-2">Need additional support?</h3>
            <p className="text-muted-foreground mb-3">
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
            <p className="text-muted-foreground mb-3">
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
            <p className="text-muted-foreground mb-3">
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
