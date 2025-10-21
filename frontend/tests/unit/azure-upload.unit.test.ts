/**
 * Unit tests for Azure upload utility
 * 
 * These tests mock network calls and verify the logic without hitting real Azure endpoints.
 * 
 * Run with: npm test -- --run tests/unit/azure-upload.unit.test.ts
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { uploadBlobAsChunks } from "@/lib/azure-upload";
import { createMockAudioBlob, createMockAudioChunks, MockXHRBuilder } from "../fixtures";
import * as apiClientModule from "@/lib/api-client";

// Mock the API client
vi.mock("@/lib/api-client", () => ({
  apiClient: {
    getUploadUrl: vi.fn(),
  },
}));

describe("Azure Upload Unit Tests", () => {
  let mockXHRInstances: MockXHRBuilder[] = [];
  
  beforeEach(() => {
    mockXHRInstances = [];
    
    // Mock XMLHttpRequest
    global.XMLHttpRequest = vi.fn().mockImplementation(() => {
      const mockXHR = new MockXHRBuilder();
      mockXHRInstances.push(mockXHR);
      return mockXHR;
    }) as any;
    
    // Mock successful API response
    vi.mocked(apiClientModule.apiClient.getUploadUrl).mockResolvedValue({
      data: {
        upload_url: "https://justicetransdevstor.blob.core.windows.net/application-data/test-file.mp4?sv=2023-01-01&sig=testsignature",
        user_upload_s3_file_key: "user-uploads/test@example.com/test-file.mp4",
      },
      error: null,
    } as any);
  });

  describe("uploadBlobAsChunks - Single Blob", () => {
    it("should split blob into 1MB chunks and use Azure Block Blob API", async () => {
      const blob = createMockAudioBlob(1024 * 1024 * 2.5, "audio/mp4"); // 2.5MB
      
      const resultPromise = uploadBlobAsChunks({
        blob,
        mimeType: "audio/mp4",
      });
      
      // Wait for all XHR requests to be created
      await new Promise((resolve) => setTimeout(resolve, 50));
      
      const result = await resultPromise;
      
      // Should make multiple requests: 3 PutBlock + 1 PutBlockList = 4
      expect(mockXHRInstances.length).toBe(4);
      
      // Verify PutBlock requests (first 3)
      for (let i = 0; i < 3; i++) {
        const xhr = mockXHRInstances[i];
        expect(xhr.method).toBe("PUT");
        expect(xhr.url).toContain("comp=block");
        expect(xhr.url).toContain("blockid=");
        expect(xhr.requestHeaders["x-ms-blob-type"]).toBe("BlockBlob");
      }
      
      // Verify PutBlockList request (last one)
      const commitXHR = mockXHRInstances[3];
      expect(commitXHR.method).toBe("PUT");
      expect(commitXHR.url).toContain("comp=blocklist");
      expect(commitXHR.requestHeaders["Content-Type"]).toBe("application/xml");
      expect(commitXHR.body).toContain("<BlockList>");
      expect(commitXHR.body).toContain("<Latest>");
      
      // Verify result
      expect(result.fileKey).toBe("user-uploads/test@example.com/test-file.mp4");
    });

    it("should handle small blobs (single chunk)", async () => {
      const blob = createMockAudioBlob(1024 * 50, "audio/mp4"); // 50KB
      
      await uploadBlobAsChunks({
        blob,
        mimeType: "audio/mp4",
      });
      
      await new Promise((resolve) => setTimeout(resolve, 50));
      
      // Should make 2 requests: 1 PutBlock + 1 PutBlockList
      expect(mockXHRInstances.length).toBe(2);
    });

    it("should report progress correctly", async () => {
      const blob = createMockAudioBlob(1024 * 1024 * 3, "audio/mp4"); // 3MB
      const progressUpdates: number[] = [];
      
      const resultPromise = uploadBlobAsChunks({
        blob,
        mimeType: "audio/mp4",
        onProgress: (progress) => {
          progressUpdates.push(progress);
        },
      });
      
      await new Promise((resolve) => setTimeout(resolve, 100));
      await resultPromise;
      
      // Should have progress updates
      expect(progressUpdates.length).toBeGreaterThan(0);
      
      // Last update should be 100
      expect(progressUpdates[progressUpdates.length - 1]).toBe(100);
      
      // Progress should increase monotonically
      for (let i = 1; i < progressUpdates.length; i++) {
        expect(progressUpdates[i]).toBeGreaterThanOrEqual(progressUpdates[i - 1]);
      }
    });

    it("should generate correct block IDs (base64, consistent length)", async () => {
      const blob = createMockAudioBlob(1024 * 1024 * 2, "audio/mp4"); // 2MB
      
      await uploadBlobAsChunks({
        blob,
        mimeType: "audio/mp4",
      });
      
      await new Promise((resolve) => setTimeout(resolve, 50));
      
      // Extract block IDs from URLs
      const blockIds: string[] = [];
      for (let i = 0; i < mockXHRInstances.length - 1; i++) {
        const url = mockXHRInstances[i].url;
        const match = url.match(/blockid=([^&]+)/);
        if (match) {
          blockIds.push(decodeURIComponent(match[1]));
        }
      }
      
      // All block IDs should be base64
      for (const blockId of blockIds) {
        expect(blockId).toMatch(/^[A-Za-z0-9+/=]+$/);
        
        // Should decode to a padded number
        const decoded = atob(blockId);
        expect(decoded).toMatch(/^\d+$/);
      }
      
      // All block IDs should have the same length
      const lengths = blockIds.map((id) => id.length);
      expect(new Set(lengths).size).toBe(1);
    });
  });

  describe("uploadBlobAsChunks - Pre-existing Chunks", () => {
    it("should upload pre-existing chunks without re-splitting", async () => {
      const chunks = createMockAudioChunks(1024 * 150, 1024 * 50); // 150KB in 50KB chunks = 3 chunks
      
      await uploadBlobAsChunks({
        chunks,
        mimeType: "audio/mp4",
      });
      
      await new Promise((resolve) => setTimeout(resolve, 50));
      
      // Should make 4 requests: 3 PutBlock + 1 PutBlockList
      expect(mockXHRInstances.length).toBe(4);
      
      // Verify all are block operations
      for (let i = 0; i < 3; i++) {
        expect(mockXHRInstances[i].url).toContain("comp=block");
      }
      expect(mockXHRInstances[3].url).toContain("comp=blocklist");
    });
  });

  describe("Error Handling", () => {
    it("should throw error when neither blob nor chunks provided", async () => {
      await expect(
        uploadBlobAsChunks({
          mimeType: "audio/mp4",
        })
      ).rejects.toThrow("Either blob or chunks must be provided");
    });

    it("should throw error when chunks array is empty", async () => {
      await expect(
        uploadBlobAsChunks({
          chunks: [],
          mimeType: "audio/mp4",
        })
      ).rejects.toThrow("Either blob or chunks must be provided");
    });

    it("should handle API error when getting upload URL", async () => {
      vi.mocked(apiClientModule.apiClient.getUploadUrl).mockResolvedValue({
        data: null,
        error: { message: "API Error" },
      } as any);
      
      const blob = createMockAudioBlob(1024, "audio/mp4");
      
      await expect(
        uploadBlobAsChunks({
          blob,
          mimeType: "audio/mp4",
        })
      ).rejects.toThrow("Failed to get upload URL");
    });

    it("should handle XHR upload failure", async () => {
      const blob = createMockAudioBlob(1024, "audio/mp4");
      
      // Mock XHR to fail
      global.XMLHttpRequest = vi.fn().mockImplementation(() => {
        const mockXHR = new MockXHRBuilder();
        mockXHR.status = 500;
        mockXHR.statusText = "Internal Server Error";
        return mockXHR;
      }) as any;
      
      await expect(
        uploadBlobAsChunks({
          blob,
          mimeType: "audio/mp4",
        })
      ).rejects.toThrow();
    });
  });

  describe("File Extension Handling", () => {
    it("should use .mp4 extension for audio/mp4", async () => {
      const blob = createMockAudioBlob(1024, "audio/mp4");
      
      await uploadBlobAsChunks({
        blob,
        mimeType: "audio/mp4",
      });
      
      expect(apiClientModule.apiClient.getUploadUrl).toHaveBeenCalledWith("mp4");
    });

    it("should use .mp4 extension for video/mp4", async () => {
      const blob = createMockAudioBlob(1024, "video/mp4");
      
      await uploadBlobAsChunks({
        blob,
        mimeType: "video/mp4",
      });
      
      expect(apiClientModule.apiClient.getUploadUrl).toHaveBeenCalledWith("mp4");
    });

    it("should use .webm extension for audio/webm", async () => {
      const blob = createMockAudioBlob(1024, "audio/webm");
      
      await uploadBlobAsChunks({
        blob,
        mimeType: "audio/webm",
      });
      
      expect(apiClientModule.apiClient.getUploadUrl).toHaveBeenCalledWith("webm");
    });
  });

  describe("URL Parsing and SAS Token Handling", () => {
    it("should correctly parse and reconstruct URLs with SAS tokens", async () => {
      const blob = createMockAudioBlob(1024 * 1024, "audio/mp4");
      
      await uploadBlobAsChunks({
        blob,
        mimeType: "audio/mp4",
      });
      
      await new Promise((resolve) => setTimeout(resolve, 50));
      
      // Check that all URLs contain the SAS signature
      for (const xhr of mockXHRInstances) {
        expect(xhr.url).toContain("sig=testsignature");
        expect(xhr.url).toContain("sv=2023-01-01");
      }
      
      // Block upload URLs should have comp=block
      expect(mockXHRInstances[0].url).toContain("comp=block");
      
      // Commit URL should have comp=blocklist
      const commitURL = mockXHRInstances[mockXHRInstances.length - 1].url;
      expect(commitURL).toContain("comp=blocklist");
    });
  });
});

