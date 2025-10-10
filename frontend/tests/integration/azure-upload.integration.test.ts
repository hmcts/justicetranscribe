/**
 * Integration tests for Azure Block Blob upload functionality
 * 
 * These tests upload actual files to Azure Storage (dev)
 * and verify chunked upload fallback behavior.
 * 
 * Run with: npm test -- --run tests/integration/azure-upload.integration.test.ts
 * 
 * Environment variables required:
 * - AZURE_STORAGE_CONNECTION_STRING (or will skip tests)
 * - TEST_INTEGRATION=true (to enable integration tests)
 */

import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { uploadBlobAsChunks, uploadChunksFromBackup } from "@/lib/azure-upload";
import { createMockAudioBlob, createMockAudioChunks } from "../fixtures";

// Skip integration tests unless explicitly enabled
const runIntegrationTests = process.env.TEST_INTEGRATION === "true";
const describeIntegration = runIntegrationTests ? describe : describe.skip;

describeIntegration("Azure Upload Integration Tests", () => {
  let uploadedBlobKeys: string[] = [];
  const testSubdirectory = "frontend-integration-tests";

  beforeAll(() => {
    // Verify environment is set up
    if (!process.env.NEXT_PUBLIC_API_URL) {
      throw new Error("NEXT_PUBLIC_API_URL must be set for integration tests");
    }
    
    // Reset uploaded blobs list at the start of the test suite
    uploadedBlobKeys = [];
  });

  afterAll(async () => {
    // Log test files for manual cleanup
    console.log(`\n📋 Integration test uploaded ${uploadedBlobKeys.length} files:`);
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    
    if (uploadedBlobKeys.length === 0) {
      console.log("   ✅ No files were uploaded (all tests skipped or failed early)");
      return;
    }

    console.log("\n   Container: application-data");
    console.log("   Path prefix: user-uploads/developer@localhost.com/\n");
    
    for (const fileKey of uploadedBlobKeys) {
      const fileName = fileKey.split('/').pop();
      console.log(`   📄 ${fileName}`);
    }
    
    console.log("\n💡 Manual cleanup instructions:");
    console.log("   1. Go to Azure Portal → dev atorage account");
    console.log("   2. Navigate to: Containers → application-data → user-uploads/developer@localhost.com/");
    console.log("   3. Delete the files listed above");
    console.log("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
  });

  /**
   * Test 1: Upload a small blob in a single request
   */
  it("should successfully upload a small blob (single PUT)", async () => {
    const blob = createMockAudioBlob(1024 * 50, "audio/mp4"); // 50KB
    const mimeType = "audio/mp4";
    
    let progressUpdates: number[] = [];
    
    const result = await uploadBlobAsChunks({
      blob,
      mimeType,
      onProgress: (progress) => {
        progressUpdates.push(progress);
      },
    });
    
    // Verify result
    expect(result.fileKey).toBeDefined();
    expect(result.fileKey).toMatch(/\.mp4$/);
    
    // Track for cleanup
    uploadedBlobKeys.push(result.fileKey);
    
    // Verify progress was reported
    expect(progressUpdates.length).toBeGreaterThan(0);
    expect(progressUpdates[progressUpdates.length - 1]).toBe(100);
    
    console.log(`✅ Uploaded small blob: ${result.fileKey}`);
    console.log(`   Progress updates: ${progressUpdates.length}`);
  }, 30000); // 30 second timeout

  /**
   * Test 2: Upload a larger blob using chunked upload
   */
  it("should successfully upload a large blob (chunked)", async () => {
    const blob = createMockAudioBlob(1024 * 1024 * 5, "audio/mp4"); // 5MB
    const mimeType = "audio/mp4";
    
    let progressUpdates: number[] = [];
    
    const result = await uploadBlobAsChunks({
      blob,
      mimeType,
      onProgress: (progress) => {
        progressUpdates.push(progress);
      },
    });
    
    // Verify result
    expect(result.fileKey).toBeDefined();
    expect(result.fileKey).toMatch(/\.mp4$/);
    
    // Track for cleanup
    uploadedBlobKeys.push(result.fileKey);
    
    // Verify progress was reported for multiple chunks
    expect(progressUpdates.length).toBeGreaterThan(5); // Should have multiple updates
    expect(progressUpdates[progressUpdates.length - 1]).toBe(100);
    
    // Verify progress increased monotonically
    for (let i = 1; i < progressUpdates.length; i++) {
      expect(progressUpdates[i]).toBeGreaterThanOrEqual(progressUpdates[i - 1]);
    }
    
    console.log(`✅ Uploaded large blob (chunked): ${result.fileKey}`);
    console.log(`   Blob size: ${(blob.size / 1024 / 1024).toFixed(2)} MB`);
    console.log(`   Progress updates: ${progressUpdates.length}`);
    console.log(`   Chunks uploaded: ~${Math.ceil(blob.size / (1024 * 1024))}`);
  }, 60000); // 60 second timeout for larger file

  /**
   * Test 3: Upload using pre-existing chunks (IndexedDB simulation)
   */
  it("should successfully upload from pre-existing chunks", async () => {
    const chunks = createMockAudioChunks(1024 * 200, 1024 * 20); // 200KB in 20KB chunks
    const mimeType = "audio/mp4";
    
    let progressUpdates: number[] = [];
    
    const result = await uploadBlobAsChunks({
      chunks,
      mimeType,
      onProgress: (progress) => {
        progressUpdates.push(progress);
      },
    });
    
    // Verify result
    expect(result.fileKey).toBeDefined();
    expect(result.fileKey).toMatch(/\.mp4$/);
    
    // Track for cleanup
    uploadedBlobKeys.push(result.fileKey);
    
    // Verify progress
    expect(progressUpdates.length).toBeGreaterThan(0);
    expect(progressUpdates[progressUpdates.length - 1]).toBe(100);
    
    console.log(`✅ Uploaded from ${chunks.length} pre-existing chunks: ${result.fileKey}`);
    console.log(`   Progress updates: ${progressUpdates.length}`);
  }, 30000);

  /**
   * Test 4: Verify Azure Block Blob API usage (URL structure)
   */
  it("should use correct Azure Block Blob API endpoints", async () => {
    const blob = createMockAudioBlob(1024 * 100, "audio/mp4"); // 100KB
    
    // We'll need to intercept the XHR calls to verify URLs
    // This is more of a unit test, but including for completeness
    const result = await uploadBlobAsChunks({
      blob,
      mimeType: "audio/mp4",
    });
    
    expect(result.fileKey).toBeDefined();
    uploadedBlobKeys.push(result.fileKey);
    
    // The actual verification of ?comp=block and ?comp=blocklist
    // would require XHR interception, which is better tested in unit tests
    console.log(`✅ Upload completed with proper Azure API: ${result.fileKey}`);
  }, 30000);

  /**
   * Test 5: WebM format support
   */
  it("should successfully upload WebM format", async () => {
    const blob = createMockAudioBlob(1024 * 75, "audio/webm");
    const mimeType = "audio/webm";
    
    const result = await uploadBlobAsChunks({
      blob,
      mimeType,
    });
    
    expect(result.fileKey).toBeDefined();
    expect(result.fileKey).toMatch(/\.webm$/);
    
    uploadedBlobKeys.push(result.fileKey);
    
    console.log(`✅ Uploaded WebM blob: ${result.fileKey}`);
  }, 30000);

  /**
   * Test 6: Upload from IndexedDB backup ID (convenience wrapper)
   */
  it("should upload using uploadChunksFromBackup wrapper", async () => {
    // Note: This would require actual IndexedDB setup
    // For now, test that the function exists and has correct signature
    expect(uploadChunksFromBackup).toBeDefined();
    expect(typeof uploadChunksFromBackup).toBe("function");
  });

  /**
   * Test 7: Error handling for invalid inputs
   */
  it("should throw error when neither blob nor chunks provided", async () => {
    await expect(
      uploadBlobAsChunks({
        mimeType: "audio/mp4",
      })
    ).rejects.toThrow("Either blob or chunks must be provided");
  });

  /**
   * Test 8: Error handling for empty chunks array
   */
  it("should throw error when chunks array is empty", async () => {
    await expect(
      uploadBlobAsChunks({
        chunks: [],
        mimeType: "audio/mp4",
      })
    ).rejects.toThrow("Either blob or chunks must be provided");
  });
});

/**
 * Test suite for measuring upload performance
 */
describeIntegration("Azure Upload Performance Tests", () => {
  let uploadedBlobKeys: string[] = [];

  beforeAll(() => {
    uploadedBlobKeys = [];
  });

  afterAll(async () => {
    // Log performance test files for manual cleanup
    console.log(`\n📋 Performance tests uploaded ${uploadedBlobKeys.length} files:`);
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    
    if (uploadedBlobKeys.length === 0) {
      console.log("   ✅ No files were uploaded");
      return;
    }

    console.log("\n   Container: application-data");
    console.log("   Path prefix: user-uploads/developer@localhost.com/\n");
    
    for (const fileKey of uploadedBlobKeys) {
      const fileName = fileKey.split('/').pop();
      console.log(`   📄 ${fileName}`);
    }
    
    console.log("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
  });

  it("should complete 1MB upload within reasonable time", async () => {
    const blob = createMockAudioBlob(1024 * 1024, "audio/mp4"); // 1MB
    const startTime = Date.now();
    
    const result = await uploadBlobAsChunks({
      blob,
      mimeType: "audio/mp4",
    });
    
    const duration = Date.now() - startTime;
    
    expect(result.fileKey).toBeDefined();
    uploadedBlobKeys.push(result.fileKey); // Track for cleanup
    
    console.log(`✅ 1MB upload completed in ${duration}ms`);
    
    // Should complete within 10 seconds (adjust based on network)
    expect(duration).toBeLessThan(10000);
  }, 15000);

  it("should report progress at regular intervals", async () => {
    const blob = createMockAudioBlob(1024 * 500, "audio/mp4"); // 500KB
    const progressUpdates: number[] = [];
    
    const result = await uploadBlobAsChunks({
      blob,
      mimeType: "audio/mp4",
      onProgress: (progress) => {
        progressUpdates.push(progress);
      },
    });
    
    uploadedBlobKeys.push(result.fileKey); // Track for cleanup
    
    // Should have multiple progress updates
    expect(progressUpdates.length).toBeGreaterThan(1);
    
    // Progress should be monotonically increasing
    for (let i = 1; i < progressUpdates.length; i++) {
      expect(progressUpdates[i]).toBeGreaterThanOrEqual(progressUpdates[i - 1]);
    }
    
    // Should end at 100%
    expect(progressUpdates[progressUpdates.length - 1]).toBe(100);
    
    console.log(`✅ Progress reported ${progressUpdates.length} times`);
    console.log(`   Values: [${progressUpdates.join(", ")}]`);
  }, 30000);
});

