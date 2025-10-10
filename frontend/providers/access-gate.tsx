"use client";
import React, { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";

export default function AccessGate({
  children,
}: {
  children: React.ReactNode;
}) {
  const [accessStatus, setAccessStatus] = useState<'checking' | 'allowed' | 'denied' | null>(null);

  useEffect(() => {
    let isMounted = true;
    
    const checkAccess = async () => {
      console.log("🔍 Starting access check");
      
      try {
        const res = await apiClient.request<{
          is_allowlisted: boolean;
          should_show_coming_soon: boolean;
          should_show_onboarding: boolean;
          has_completed_onboarding: boolean;
        }>("/user/onboarding-status");
        
        console.log("📡 API response:", res.data);
        
        if (isMounted && res.data) {
          const { should_show_coming_soon, should_show_onboarding } = res.data;
          const newStatus = should_show_coming_soon ? 'denied' : 'allowed';
          console.log("✅ Setting status:", newStatus);
          setAccessStatus(newStatus);
          
          // Handle redirects - check if we're in browser environment
          if (typeof window !== 'undefined') {
            const currentPathname = window.location.pathname;
            const currentSearch = window.location.search;
            const onComingSoon = currentPathname?.startsWith("/coming-soon");
            const onOnboarding = currentPathname?.startsWith("/onboarding");
            // More specific check for transcript pages - look for ?id= or &id= pattern
            const isTranscriptPage = currentSearch?.match(/[?&]id=/);
            
            if (should_show_coming_soon && !onComingSoon) {
              console.log("🔄 Redirecting to coming-soon");
              window.location.href = "/coming-soon";
            } else if (!should_show_coming_soon && should_show_onboarding && !onOnboarding && !isTranscriptPage) {
              console.log("🔄 Redirecting to onboarding");
              window.location.href = "/onboarding";
            } else if (!should_show_coming_soon && !should_show_onboarding && onComingSoon) {
              console.log("🔄 Redirecting to home");
              window.location.href = "/";
            } else {
              console.log("✅ No redirect needed");
            }
          }
        }
      } catch (e) {
        console.warn("❌ Access gate check failed:", e);
        if (isMounted) {
          setAccessStatus('denied');
          // Check if we're in browser environment before accessing window
          if (typeof window !== 'undefined') {
            const currentPathname = window.location.pathname;
            const onComingSoon = currentPathname?.startsWith("/coming-soon");
            if (!onComingSoon) {
              window.location.href = "/coming-soon";
            }
          }
        }
      }
    };

    // Only check if we haven't checked yet
    if (accessStatus === null) {
      setAccessStatus('checking');
      checkAccess();
    }

    return () => {
      isMounted = false;
    };
  }, []); // Empty dependency array - only run once

  // Show loading screen while checking
  if (accessStatus === 'checking') {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-50">
        <div 
          className="text-center"
          role="status"
          aria-live="polite"
          aria-busy="true"
        >
          <h1 className="text-2xl font-semibold text-gray-800 mb-6">
            Access Verification
          </h1>
          <div 
            className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"
            aria-hidden="true"
          ></div>
          <p className="text-gray-600 font-medium" aria-label="Verifying your access permissions">
            Verifying access...
          </p>
        </div>
      </main>
    );
  }

  // Render the page content
  return <>{children}</>;
}
