import { apiClient } from "@/lib/api-client";

export interface UploadUrlData {
  upload_url: string;
  user_upload_s3_file_key: string;
}

export interface FetchUploadUrlResult {
  success: boolean;
  data?: UploadUrlData;
}

/**
 * Detect the supported MIME type for recording
 */
export function detectSupportedMimeType(): string {
  const mimeTypes = [
    "video/mp4", // iOS primary format
    "audio/mp4", // Desktop MP4 format
    "audio/webm", // WebM fallback
  ];

  const supportedMimeType = mimeTypes.find((mimeType) =>
    MediaRecorder.isTypeSupported(mimeType)
  );

  // Default fallback
  return supportedMimeType || "audio/webm";
}

/**
 * Fetch an upload URL from the API with retry logic
 */
export async function fetchUploadUrl(): Promise<FetchUploadUrlResult> {
  const maxRetries = 3;
  const retryDelay = 1000;

  /* eslint-disable no-await-in-loop */
  for (let attempt = 1; attempt <= maxRetries; attempt += 1) {
    try {
      const mimeType = detectSupportedMimeType();
      const fileExtension = mimeType.includes("mp4") ? "mp4" : "webm";

      const urlResult = await apiClient.getUploadUrl(fileExtension);

      if (urlResult.error) {
        // eslint-disable-next-line no-console
        console.error(
          `Failed to fetch upload URL (attempt ${attempt}/${maxRetries}):`,
          urlResult.error
        );
        if (attempt < maxRetries) {
          await new Promise<void>((resolve) => {
            setTimeout(resolve, retryDelay);
          });
          // eslint-disable-next-line no-continue
          continue;
        }
        return { success: false };
      }

      if (urlResult.data) {
        return { success: true, data: urlResult.data };
      }
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error(
        `Error fetching upload URL (attempt ${attempt}/${maxRetries}):`,
        error
      );
      if (attempt < maxRetries) {
        await new Promise<void>((resolve) => {
          setTimeout(resolve, retryDelay);
        });
      }
    }
  }
  /* eslint-enable no-await-in-loop */

  return { success: false };
}
