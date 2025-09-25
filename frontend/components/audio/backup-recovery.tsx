"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  RefreshCw,
  Trash2,
  Upload,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { audioBackupDB, AudioBackup } from "@/lib/indexeddb-backup";
import AudioPlayerComponent from "./audio-player";

interface BackupRecoveryProps {
  onRetryUpload: (backup: AudioBackup) => void;
}

function BackupRecovery({ onRetryUpload }: BackupRecoveryProps) {
  const [backups, setBackups] = useState<AudioBackup[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  const loadBackups = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const allBackups = await audioBackupDB.getAllAudioBackups();
      // Sort by timestamp (newest first)
      allBackups.sort((a, b) => b.timestamp - a.timestamp);
      setBackups(allBackups);

      // Auto-collapse if more than 1 recording, otherwise expand
      setIsOpen(allBackups.length <= 1);
    } catch (err) {
      setError("Failed to load backed up recordings");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadBackups();
  }, [loadBackups]);

  const handleDeleteBackup = async (backupId: string) => {
    try {
      await audioBackupDB.deleteAudioBackup(backupId);
      setBackups((prev) => prev.filter((backup) => backup.id !== backupId));
    } catch (err) {
      setError("Failed to delete backup");
    }
  };

  const handleRetryUpload = (backup: AudioBackup) => {
    onRetryUpload(backup);
  };

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  };

  const formatFileSize = (blob: Blob) => {
    const bytes = blob.size;
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / k ** i).toFixed(2))} ${sizes[i]}`;
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="size-5" />
            Backed Up Recordings
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="size-6 animate-spin text-gray-400" />
            <span className="ml-2 text-gray-600">
              Loading backed up recordings...
            </span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription className="flex items-center justify-between">
          <span>{error}</span>
          <Button variant="outline" size="sm" onClick={loadBackups}>
            <RefreshCw className="mr-1 size-4" />
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  if (backups.length === 0) {
    return null; // Don't show anything if no backups exist
  }

  return (
    <Card>
      <CardContent className="pt-6">
        <Collapsible open={isOpen} onOpenChange={setIsOpen}>
          <CollapsibleTrigger className="flex w-full items-center justify-between rounded-lg border p-4 text-left hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
            <div className="flex items-center gap-3">
              <Upload className="size-5 text-gray-600" />
              <div>
                <h2 className="font-medium text-gray-900">
                  Reupload Recordings
                </h2>
                <p className="text-sm text-gray-500">
                  {backups.length} recording{backups.length !== 1 ? "s" : ""}{" "}
                  waiting for upload
                </p>
              </div>
              {/* Count badge */}
              <div className="ml-2 flex size-6 items-center justify-center rounded-full bg-blue-100 text-xs font-medium text-blue-800">
                {backups.length}
              </div>
            </div>
            <div className="flex items-center gap-2">
              {isOpen ? (
                <ChevronDown className="size-4 text-gray-400" />
              ) : (
                <ChevronRight className="size-4 text-gray-400" />
              )}
            </div>
          </CollapsibleTrigger>

          <CollapsibleContent className="mt-4">
            <div className="space-y-4">
              <Alert>
                <AlertDescription>
                  These recordings were automatically backed up but haven&apos;t
                  been uploaded yet.
                </AlertDescription>
              </Alert>

              {backups.map((backup, index) => (
                <div
                  key={backup.id}
                  className="space-y-3 rounded-lg border bg-gray-50 p-4"
                >
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div className="space-y-1">
                      <h4 className="text-sm font-medium">
                        Recording #{backups.length - index} -{" "}
                        {formatTimestamp(backup.timestamp)}
                      </h4>
                      <div className="flex flex-wrap items-center gap-2 text-xs text-gray-600 sm:gap-4">
                        <span>Size: {formatFileSize(backup.blob)}</span>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2 sm:shrink-0 sm:flex-nowrap">
                      <Button
                        variant="default"
                        size="sm"
                        onClick={() => handleRetryUpload(backup)}
                        className="flex-1 sm:flex-initial"
                      >
                        <RefreshCw className="mr-1 size-3" />
                        Retry Upload
                      </Button>

                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button
                            variant="outline"
                            size="sm"
                            className="flex-1 text-red-600 hover:text-red-700 sm:flex-initial"
                          >
                            <Trash2 className="mr-1 size-3" />
                            Delete
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>
                              Delete Recording
                            </AlertDialogTitle>
                            <AlertDialogDescription>
                              Are you sure you want to delete &quot;
                              {backup.fileName}&quot;? This action cannot be
                              undone and you will lose this recording
                              permanently.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => handleDeleteBackup(backup.id)}
                              className="bg-red-600 text-white hover:bg-red-700"
                            >
                              Delete
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  </div>

                  <AudioPlayerComponent audioBlob={backup.blob} />
                </div>
              ))}
            </div>
          </CollapsibleContent>
        </Collapsible>
      </CardContent>
    </Card>
  );
}

export default BackupRecovery;
