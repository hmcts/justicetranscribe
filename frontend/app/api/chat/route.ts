import { createAzure } from "@ai-sdk/azure";
import { createEdgeRuntimeAPI } from "@assistant-ui/react/edge";

export const runtime = "edge";

const azure = createAzure({
  resourceName: "oai-i-dot-ai-playground-sweden", // Azure resource name
  apiKey: process.env.AZURE_OPENAI_API_KEY,
});

export const { POST } = createEdgeRuntimeAPI({
  model: azure("gpt-4o"),
});
