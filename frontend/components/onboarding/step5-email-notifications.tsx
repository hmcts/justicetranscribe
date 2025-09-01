import React from "react";
import { Mail } from "lucide-react";

interface Step5EmailNotificationsProps {
  email: string;
}

export default function Step5EmailNotifications({ email }: Step5EmailNotificationsProps) {
  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h3 className="text-2xl font-semibold">Email notifications</h3>
        <p>
          We&apos;ll email you when your summary is ready for review.
        </p>
      </div>

      {/* Email Display */}
      <div className="border rounded-lg p-6 bg-gray-50">
        <div className="flex items-center space-x-3">
          <Mail className="w-6 h-6 text-gray-600" />
          <div>
            <p className="font-semibold">Notifications to:</p>
            <p className="text-lg">{email || "your-email@example.com"}</p>
          </div>
        </div>
      </div>

      {/* Information */}
      <div className="space-y-3">
        <div className="flex items-start space-x-3">
          <span className="text-lg">•</span>
          <span>Processing usually takes 2-5 minutes</span>
        </div>
        <div className="flex items-start space-x-3">
          <span className="text-lg">•</span>
          <span>You&apos;ll get a secure link to review your summary</span>
        </div>
        <div className="flex items-start space-x-3">
          <span className="text-lg">•</span>
          <span>No sensitive content is sent in emails</span>
        </div>
      </div>
    </div>
  );
}
