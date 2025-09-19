"use client";

import posthog from "posthog-js";
import { PostHogProvider } from "posthog-js/react";
import React from "react";
import { useUserSettings } from "@/providers/user-settings";
import PostHogPageView from "./posthog-page-view";

// Only initialize on client-side when API key is provided
if (typeof window !== "undefined" && process.env.NEXT_PUBLIC_POSTHOG_API_KEY) {
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_API_KEY, {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://eu.i.posthog.com",
    capture_pageview: true,
    session_recording: {
      maskAllInputs: true,
      maskInputOptions: {
        password: true,
      },
    },
  });
}

function PosthogProvider({ children }: React.PropsWithChildren) {
  const { user, loading } = useUserSettings();

  React.useEffect(() => {
    if (user && user.email) {
      console.log("user email in provider", user.email);
      posthog.identify(user.email, { email: user.email });
    }
  }, [user]);

  // If PostHog API key is not provided, just render children without PostHog wrapper
  if (!process.env.NEXT_PUBLIC_POSTHOG_API_KEY) {
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
