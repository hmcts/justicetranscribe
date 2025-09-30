"use client";
import React, { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { apiClient } from "@/lib/api-client";

export default function AccessGate({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [accessStatus, setAccessStatus] = useState<'checking' | 'allowed' | 'denied' | null>(null);

  useEffect(() => {
    const onComingSoon = pathname?.startsWith("/coming-soon");
    
    // If we already checked and know the status
    if (accessStatus === 'denied' && !onComingSoon) {
      // Denied access, redirect to coming-soon
      router.push("/coming-soon");
      return;
    }
    
    if (accessStatus === 'allowed' && onComingSoon) {
      // Allowed but on coming-soon page, redirect home
      router.push("/");
      return;
    }
    
    // If we already know the status and user is on correct page, we're done
    if (accessStatus !== null && accessStatus !== 'checking') {
      return;
    }
    
    // Need to check access - do it once
    if (accessStatus === null) {
      setAccessStatus('checking');
      
      const check = async () => {
        try {
          const res = await apiClient.request<{
            is_allowlisted: boolean;
            should_show_coming_soon: boolean;
          }>("/user/onboarding-status");
          
          if (res.data) {
            const { should_show_coming_soon } = res.data;
            const newStatus = should_show_coming_soon ? 'denied' : 'allowed';
            setAccessStatus(newStatus);
            
            // Redirect if needed
            if (should_show_coming_soon && !onComingSoon) {
              router.push("/coming-soon");
            } else if (!should_show_coming_soon && onComingSoon) {
              router.push("/");
            }
          }
        } catch (e) {
          // On error, deny access (fail-safe)
          console.warn("Access gate check failed:", e);
          setAccessStatus('denied');
          if (!onComingSoon) {
            router.push("/coming-soon");
          }
        }
      };
      
      check();
    }
  }, [router, pathname, accessStatus]);

  // Show loading screen only while actively checking
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
