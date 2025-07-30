"use client";

import posthog from "posthog-js";
import { PostHogProvider } from "posthog-js/react";
import React from "react";
import { useUserSettings } from "@/providers/user-settings";
import PostHogPageView from "./posthog-page-view";

// Only initialize on client-side
if (typeof window !== "undefined") {
  // pragma: allowlist secret
  const API_KEY = "phc_gMiQR2FpJt3FObuZ2HXF2yVtbGfKhdHfbpbjTcpyQQz"; // pragma: allowlist secret
  posthog.init(API_KEY, {
    api_host: "https://eu.i.posthog.com",
    capture_pageview: false, // Disable automatic pageview capture, as we capture manually
    session_recording: {
      maskAllInputs: false,
      maskInputOptions: {
        password: true,
      },
    },
  });
}

function PosthogProvider({ children }: React.PropsWithChildren) {
  const { user } = useUserSettings();

  React.useEffect(() => {
    if (user && user.email) {
      console.log("user email in provider", user.email);
      posthog.identify(user.email, { email: user.email });
    }
  }, [user]);

  return (
    <PostHogProvider client={posthog}>
      <PostHogPageView />
      {children}
    </PostHogProvider>
  );
}

export default PosthogProvider;
