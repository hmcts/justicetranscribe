/**
 * Shared test fixtures and utilities for frontend tests
 */

/**
 * Create a mock audio blob for testing
 */
export function createMockAudioBlob(
  sizeBytes: number = 1024 * 100, // 100KB default
  mimeType: string = "audio/mp4"
): Blob {
  // Create a buffer of the specified size
  const buffer = new ArrayBuffer(sizeBytes);
  const view = new Uint8Array(buffer);
  
  // Fill with some pseudo-random data
  for (let i = 0; i < view.length; i++) {
    view[i] = Math.floor(Math.random() * 256);
  }
  
  return new Blob([buffer], { type: mimeType });
}

/**
 * Create mock audio chunks (simulating IndexedDB chunks)
 */
export function createMockAudioChunks(
  totalSize: number = 1024 * 100,
  chunkSize: number = 1024 * 10 // 10KB chunks
): Array<{ id: string; chunkIndex: number; timestamp: number; data: Blob }> {
  const chunks: Array<{ id: string; chunkIndex: number; timestamp: number; data: Blob }> = [];
  const numChunks = Math.ceil(totalSize / chunkSize);
  const baseTimestamp = Date.now();
  const backupId = `test-backup-${Date.now()}`;
  
  for (let i = 0; i < numChunks; i++) {
    const currentChunkSize = Math.min(chunkSize, totalSize - i * chunkSize);
    const buffer = new ArrayBuffer(currentChunkSize);
    const view = new Uint8Array(buffer);
    
    // Fill with data
    for (let j = 0; j < view.length; j++) {
      view[j] = (i * chunkSize + j) % 256;
    }
    
    chunks.push({
      id: backupId,
      chunkIndex: i,
      timestamp: baseTimestamp + i,
      data: new Blob([buffer], { type: "audio/mp4" }),
    });
  }
  
  return chunks;
}

/**
 * Create a mock File object for testing
 */
export function createMockAudioFile(
  filename: string = "test-audio.mp4",
  sizeBytes: number = 1024 * 100,
  mimeType: string = "audio/mp4"
): File {
  const blob = createMockAudioBlob(sizeBytes, mimeType);
  return new File([blob], filename, { type: mimeType });
}

/**
 * Mock XMLHttpRequest for testing uploads
 */
export class MockXHRBuilder {
  private onload: ((event: ProgressEvent) => void) | null = null;
  private onerror: ((event: ProgressEvent) => void) | null = null;
  private onabort: ((event: ProgressEvent) => void) | null = null;
  private uploadOnProgress: ((event: ProgressEvent) => void) | null = null;
  
  public method: string = "";
  public url: string = "";
  public requestHeaders: Record<string, string> = {};
  public body: any = null;
  public status: number = 200;
  public statusText: string = "OK";
  public response: any = "";
  
  private uploadObj = {
    addEventListener: (event: string, handler: any) => {
      if (event === "progress") {
        this.uploadOnProgress = handler;
      }
    },
  };

  addEventListener(event: string, handler: any) {
    if (event === "load") this.onload = handler;
    if (event === "error") this.onerror = handler;
    if (event === "abort") this.onabort = handler;
  }

  open(method: string, url: string) {
    this.method = method;
    this.url = url;
  }

  setRequestHeader(name: string, value: string) {
    this.requestHeaders[name] = value;
  }

  send(body?: any) {
    this.body = body;
    
    // Simulate upload progress
    if (this.uploadOnProgress) {
      this.uploadOnProgress({
        lengthComputable: true,
        loaded: body?.size || 1024,
        total: body?.size || 1024,
      } as ProgressEvent);
    }
    
    // Simulate completion
    setTimeout(() => {
      if (this.status >= 200 && this.status < 300 && this.onload) {
        this.onload({} as ProgressEvent);
      } else if (this.onerror) {
        this.onerror({} as ProgressEvent);
      }
    }, 10);
  }

  get upload() {
    return this.uploadObj;
  }
}

/**
 * Wait for a condition to be true
 */
export async function waitFor(
  condition: () => boolean,
  timeout: number = 5000,
  interval: number = 100
): Promise<void> {
  const startTime = Date.now();
  
  while (!condition()) {
    if (Date.now() - startTime > timeout) {
      throw new Error("Timeout waiting for condition");
    }
    await new Promise((resolve) => setTimeout(resolve, interval));
  }
}

/**
 * Sleep for a specified duration
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

