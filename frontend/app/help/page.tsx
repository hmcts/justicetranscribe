import React from "react";
import Link from "next/link";
import { Play, RotateCcw, Users, Shield, FileText, ExternalLink } from "lucide-react";

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

        {/* Get Started Section */}
        <section className="mb-12">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Tutorial Video Card */}
            <Card className="group hover:shadow-md transition-shadow">
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

            {/* Interactive Tutorial Card */}
            <Card className="group hover:shadow-md transition-shadow">
              <CardHeader className="text-center pb-4">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-muted flex items-center justify-center group-hover:bg-muted/80 transition-colors">
                  <RotateCcw className="w-8 h-8 text-muted-foreground" aria-hidden="true" />
                </div>
                <CardTitle className="text-xl">Interactive Tutorial</CardTitle>
                <CardDescription>
                  Restart the setup process
                </CardDescription>
              </CardHeader>
              <CardContent className="text-center">
                <p className="text-sm text-muted-foreground mb-4">
                  Go through the onboarding flow again step by step
                </p>
                <Button 
                  variant="default" 
                  size="lg" 
                  className="w-full"
                  asChild
                >
                  <Link href="/onboarding" aria-label="Restart interactive tutorial">
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Restart Tutorial
                  </Link>
                </Button>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Support Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-6 text-center">Need additional support?</h2>
          <div className="text-center mb-6">
            <p className="text-muted-foreground">
              Join our Microsoft Teams channel for real-time assistance from our support team.
            </p>
          </div>
          <div className="flex justify-center">
            <Card className="w-full max-w-md group hover:shadow-md transition-shadow">
              <CardContent className="p-6 text-center">
                <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-blue-100 flex items-center justify-center group-hover:bg-blue-200 transition-colors">
                  <Users className="w-6 h-6 text-blue-600" aria-hidden="true" />
                </div>
                <h3 className="font-semibold mb-2">Microsoft Teams Support</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Connect with our support team for immediate help
                </p>
                <Button 
                  variant="outline" 
                  className="w-full"
                  asChild
                >
                  <a 
                    href="#" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    aria-label="Join Teams channel for support - opens in new tab"
                  >
                    Join Teams Channel
                    <ExternalLink className="w-4 h-4 ml-2" />
                  </a>
                </Button>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Policies & Guidelines Section */}
        <section>
          <h2 className="text-2xl font-semibold mb-6 text-center">Policies & Guidelines</h2>
          <div className="text-center mb-6">
            <p className="text-muted-foreground">
              Review our organization's AI usage policies and best practices.
            </p>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            {/* AI Policy Card */}
            <Card className="group hover:shadow-md transition-shadow">
              <CardContent className="p-6 text-center">
                <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-green-100 flex items-center justify-center group-hover:bg-green-200 transition-colors">
                  <Shield className="w-6 h-6 text-green-600" aria-hidden="true" />
                </div>
                <h3 className="font-semibold mb-2">AI Policy & Guidance</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Guidelines for responsible AI usage in your organization
                </p>
                <Button 
                  variant="outline" 
                  className="w-full"
                  asChild
                >
                  <a 
                    href="#" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    aria-label="View AI Policy & Guidance - opens in new tab"
                  >
                    View AI Policy & Guidance
                    <ExternalLink className="w-4 h-4 ml-2" />
                  </a>
                </Button>
              </CardContent>
            </Card>

            {/* Probation Flyer Card */}
            <Card className="group hover:shadow-md transition-shadow">
              <CardContent className="p-6 text-center">
                <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-purple-100 flex items-center justify-center group-hover:bg-purple-200 transition-colors">
                  <FileText className="w-6 h-6 text-purple-600" aria-hidden="true" />
                </div>
                <h3 className="font-semibold mb-2">Probation Information Flyer</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Share this flyer with people on probation. It explains how our AI system works and our data compliance approach.
                </p>
                <Button 
                  variant="outline" 
                  className="w-full"
                  asChild
                >
                  <a 
                    href="#" 
                    download
                    aria-label="Download Probation Flyer"
                  >
                    Download Probation Flyer
                    <FileText className="w-4 h-4 ml-2" />
                  </a>
                </Button>
              </CardContent>
            </Card>
          </div>
        </section>
      </div>
    </div>
  );
}
