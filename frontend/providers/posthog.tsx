"use client";

import posthog from "posthog-js";
import { PostHogProvider } from "posthog-js/react";
import React from "react";
import { useUserSettings } from "@/providers/user-settings";
import PostHogPageView from "./posthog-page-view";

// PostHog configuration from environment variables
const POSTHOG_API_KEY = process.env.NEXT_PUBLIC_POSTHOG_API_KEY;
const POSTHOG_HOST = process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://eu.i.posthog.com";
const POSTHOG_ENABLED = process.env.NEXT_PUBLIC_POSTHOG_ENABLED === "true";

// Only initialize on client-side when enabled and API key is provided
if (typeof window !== "undefined" && POSTHOG_ENABLED && POSTHOG_API_KEY) {
  posthog.init(POSTHOG_API_KEY, {
    api_host: POSTHOG_HOST,
    capture_pageview: true,
    session_recording: {
      maskAllInputs: true,
      maskInputOptions: {
        password: true,
      },
      recordCrossOriginIframes: true,
    },
    // Enable debug mode for localhost to see more logs
    debug: process.env.NODE_ENV === 'development',
    // Ensure localhost is captured
    opt_out_capturing_by_default: false,
  });
}

function PosthogProvider({ children }: React.PropsWithChildren) {
  const { user } = useUserSettings();

  React.useEffect(() => {
    // Only identify user if PostHog is enabled and properly initialized
    if (POSTHOG_ENABLED && POSTHOG_API_KEY && user && user.email) {
      posthog.identify(user.email, { email: user.email });
    }
  }, [user]);

  // If PostHog is disabled, just render children without PostHog wrapper
  if (!POSTHOG_ENABLED || !POSTHOG_API_KEY) {
    return <>{children}</>;
  }

  return (
    <PostHogProvider client={posthog}>
      <PostHogPageView />
      {children}
    </PostHogProvider>
  );
}

export default PosthogProvider;
