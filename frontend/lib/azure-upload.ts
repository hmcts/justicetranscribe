/**
 * Azure Block Blob API compliant chunked upload utilities
 */

import { apiClient } from "@/lib/api-client";
import { audioBackupDB, AudioChunk } from "@/lib/indexeddb-backup";

export interface ChunkedUploadResult {
  fileKey: string;
}

export interface UploadProgressCallback {
  (progress: number): void;
}

/**
 * Uploads a blob or chunks using Azure's Block Blob API
 * 
 * This function handles chunked uploads in a way that's compatible with Azure's
 * SAS URL signatures by using the PutBlock and PutBlockList APIs.
 * 
 * @param options.blob - The blob to upload (will be split into chunks)
 * @param options.chunks - Pre-existing chunks to upload (from IndexedDB)
 * @param options.mimeType - MIME type of the file (e.g., "audio/mp4")
 * @param options.onProgress - Optional callback for upload progress (0-100)
 * @returns The file key to use for transcription
 */
export async function uploadBlobAsChunks(options: {
  blob?: Blob;
  chunks?: AudioChunk[];
  mimeType: string;
  onProgress?: UploadProgressCallback;
}): Promise<ChunkedUploadResult> {
  const { blob, chunks, mimeType, onProgress } = options;

  // Validate inputs
  if (!blob && (!chunks || chunks.length === 0)) {
    throw new Error("Either blob or chunks must be provided");
  }

  // Get a new upload URL for chunked upload
  const fileExtension = mimeType.includes("mp4") ? "mp4" : "webm";
  const urlResult = await apiClient.getUploadUrl(fileExtension);

  if (urlResult.error) {
    throw new Error("Failed to get upload URL for chunked upload");
  }

  const { upload_url, user_upload_s3_file_key } = urlResult.data!;

  // Parse the base URL (without query params)
  const url = new URL(upload_url);
  const baseUrl = `${url.origin}${url.pathname}`;
  const sasParams = url.search; // Keep the SAS token params

  // Prepare chunks for upload
  let chunksToUpload: Blob[];
  if (chunks) {
    // Use pre-existing chunks
    chunksToUpload = chunks.map((c) => c.data);
  } else if (blob) {
    // Split blob into chunks on-the-fly
    const chunkSize = 1024 * 1024; // 1MB chunks
    const totalChunks = Math.ceil(blob.size / chunkSize);
    chunksToUpload = [];
    for (let i = 0; i < totalChunks; i++) {
      const start = i * chunkSize;
      const end = Math.min(start + chunkSize, blob.size);
      chunksToUpload.push(blob.slice(start, end));
    }
  } else {
    throw new Error("No data to upload");
  }

  const blockIds: string[] = [];
  const totalChunks = chunksToUpload.length;

  // Phase 1: Upload each chunk as a block
  for (let i = 0; i < totalChunks; i++) {
    const chunk = chunksToUpload[i];

    // Generate a block ID (must be base64 encoded, same length for all blocks)
    const blockId = btoa(String(i).padStart(6, "0"));
    blockIds.push(blockId);

    // Use Azure's PutBlock API: ?comp=block&blockid=<id>
    const blockUploadUrl = `${baseUrl}?comp=block&blockid=${encodeURIComponent(
      blockId
    )}${sasParams.substring(1) ? "&" + sasParams.substring(1) : ""}`;

    // Report progress (account for the final commit step)
    if (onProgress) {
      onProgress(Math.round((i / (totalChunks + 1)) * 100));
    }

    // Upload individual block
    await new Promise<void>((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.addEventListener("load", () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve();
        } else {
          reject(
            new Error(
              `Block ${i} upload failed with status ${xhr.status}: ${xhr.statusText}`
            )
          );
        }
      });

      xhr.addEventListener("error", () => {
        reject(new Error(`Network error uploading block ${i}`));
      });

      xhr.open("PUT", blockUploadUrl);
      xhr.setRequestHeader("x-ms-blob-type", "BlockBlob");
      xhr.send(chunk);
    });
  }

  // Phase 2: Commit all blocks using PutBlockList
  const commitUrl = `${baseUrl}?comp=blocklist${
    sasParams.substring(1) ? "&" + sasParams.substring(1) : ""
  }`;

  // Create the block list XML
  const blockListXml = `<?xml version="1.0" encoding="utf-8"?>
<BlockList>
${blockIds.map((id) => `  <Latest>${id}</Latest>`).join("\n")}
</BlockList>`;

  await new Promise<void>((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
      } else {
        reject(
          new Error(
            `Block list commit failed with status ${xhr.status}: ${xhr.statusText}`
          )
        );
      }
    });

    xhr.addEventListener("error", () => {
      reject(new Error("Network error committing block list"));
    });

    xhr.open("PUT", commitUrl);
    xhr.setRequestHeader("Content-Type", "application/xml");
    xhr.send(blockListXml);
  });

  // Report final progress
  if (onProgress) {
    onProgress(100);
  }

  // Return the file key to use for transcription
  return { fileKey: user_upload_s3_file_key };
}

/**
 * Upload chunks from IndexedDB backup using Azure Block Blob API
 * 
 * @param backupId - The backup ID containing chunks in IndexedDB
 * @param mimeType - MIME type of the file
 * @param onProgress - Optional progress callback
 * @returns The file key to use for transcription
 */
export async function uploadChunksFromBackup(
  backupId: string,
  mimeType: string,
  onProgress?: UploadProgressCallback
): Promise<ChunkedUploadResult> {
  const chunks = await audioBackupDB.getChunks(backupId);
  if (chunks.length === 0) {
    throw new Error("No chunks found for fallback upload");
  }

  return uploadBlobAsChunks({ chunks, mimeType, onProgress });
}

