/* eslint-disable no-promise-executor-return */
/* eslint-disable no-await-in-loop */

interface PollableResponse {
  status: string;
  error?: string;
  [key: string]: any; // Allow for additional fields like transcription or llm_output
}

interface PollingConfig {
  endpoint: string;
  requestBody?: Record<string, any>;
  successField: string; // Field to check in response (e.g., 'transcription' or 'llm_output')
  interval?: number;
  maxErrors?: number;
  method?: string;
}

export async function pollEndpoint<T>({
  endpoint,
  requestBody,
  successField,
  interval = 2000,
  maxErrors = 30,
  method = "POST",
}: PollingConfig): Promise<T> {
  let errorCount = 0;

  while (true) {
    try {
      const response = await fetch(endpoint, {
        method,
        headers: { "Content-Type": "application/json" },
        ...(requestBody && { body: JSON.stringify(requestBody) }),
      });

      if (!response.ok) {
        console.warn("Fetch failed with status", response.status);
        errorCount += 1;
      } else {
        const data: PollableResponse = await response.json();

        if (data.status === "completed" && data[successField]) {
          return data[successField];
        }

        if (data.status === "failed") {
          throw new Error(data.error || "Operation failed");
        }
      }

      // Wait before the next iteration
      await new Promise((resolve) => setTimeout(resolve, interval));
    } catch (error) {
      errorCount += 1;
      if (errorCount > maxErrors) {
        throw error;
      }
      // Wait before the next iteration
      await new Promise((resolve) => setTimeout(resolve, interval));
    }
  }
}

// Example usage functions:
// export function pollTranscription(fileKey: string): Promise<Transcription> {
//   return pollEndpoint({
//     endpoint: `/api/proxy/query-transcription?file_key=${fileKey}`,
//     method: "GET",
//     successField: "transcription",
//   });
// }

export function pollLLMOutput(taskId: string): Promise<any> {
  return pollEndpoint({
    endpoint: `/api/proxy/query-llm-output/${taskId}`,
    method: "GET",
    successField: "llm_output",
  });
}
