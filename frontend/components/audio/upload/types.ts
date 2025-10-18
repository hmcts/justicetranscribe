import { AudioProcessingStatus } from "@/components/audio/processing/processing-loader";

export interface ContentDisplayProps {
  processingStatus: AudioProcessingStatus;
  setProcessingStatus: (status: AudioProcessingStatus) => void;
  uploadError: string | null;
  audioBlob: Blob | null;
  startTranscription: (blob: Blob, backupIdToDelete?: string | null) => void;
  initialRecordingMode: "mic" | "screen";
  onRecordingStop: (blob: Blob | null, backupId?: string | null) => void;
  onRecordingStart: () => void;
  onClose: () => void;
}

export interface AudioUploaderProps {
  initialRecordingMode: "mic" | "screen";
  onClose: () => void;
}

export interface UploadErrorDetails {
  requestId: string | null;
  statusCode: number | null;
  sentryEventId: string | null;
  userUploadKey: string | null;
  duration: number | null;
}
