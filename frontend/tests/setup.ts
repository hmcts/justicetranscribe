/**
 * Vitest setup file for test configuration
 */

import { beforeAll, afterEach, vi } from "vitest";

// Setup environment variables for tests
beforeAll(() => {
  // Set test environment variables
  process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000";
  process.env.NODE_ENV = "test";
});

// Clean up after each test
afterEach(() => {
  vi.clearAllMocks();
});

// Mock window.URL.createObjectURL and revokeObjectURL
global.URL.createObjectURL = vi.fn(() => "blob:mock-url");
global.URL.revokeObjectURL = vi.fn();

// Mock MediaRecorder if not available in test environment
if (!global.MediaRecorder) {
  global.MediaRecorder = vi.fn().mockImplementation(() => ({
    start: vi.fn(),
    stop: vi.fn(),
    pause: vi.fn(),
    resume: vi.fn(),
    ondataavailable: null,
    onstop: null,
    state: "inactive",
  })) as any;
}

// Mock navigator.mediaDevices if not available
if (!global.navigator.mediaDevices) {
  (global.navigator as any).mediaDevices = {
    getUserMedia: vi.fn().mockResolvedValue({
      getTracks: () => [
        {
          stop: vi.fn(),
          kind: "audio",
          label: "Mock Audio Track",
        },
      ],
    }),
  };
}

