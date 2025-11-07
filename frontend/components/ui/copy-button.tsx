import React, { useState } from "react";
import { Copy } from "lucide-react";
import posthog from "posthog-js";

export interface DownloadStyleCopyButtonProps {
  textToCopy: string;
  posthogEventName: string;
  onCopy: () => void;
}

export default function DownloadStyleCopyButton({
  textToCopy,
  posthogEventName,
  onCopy,
}: DownloadStyleCopyButtonProps) {
  const [showCopied, setShowCopied] = useState(false);

  const handleCopy = async () => {
    // Use DOM to extract plain text, which strips all formatting
    const tempDiv = document.createElement("div");
    tempDiv.innerHTML = textToCopy;
    const plainText = tempDiv.textContent || tempDiv.innerText || "";

    await navigator.clipboard.writeText(plainText);

    posthog.capture(posthogEventName, {
      contentLength: textToCopy.length,
    });

    setShowCopied(true);
    setTimeout(() => setShowCopied(false), 2000);

    if (onCopy) onCopy();
  };

  return (
    <button
      className={`flex items-center justify-center gap-2 
                rounded-md px-4 py-2 text-white
                shadow-sm transition-all duration-200 
                ${showCopied ? "bg-green-600" : "bg-green-700 hover:bg-green-800"}`}
      onClick={handleCopy}
      title="Copy content"
      type="button"
    >
      <Copy className="size-5 md:mr-2" />
      <span className="hidden md:inline">
        {showCopied ? "Copied!" : "Copy"}
      </span>
    </button>
  );
}
