/**
 * Streaming Llama Inference Client (TypeScript)
 *
 * Connects to the HarchOS streaming Llama inference server and prints
 * tokens as they arrive via Server-Sent Events (SSE).
 *
 * Usage:
 *   npx ts-node inference.ts
 *   ENDPOINT=http://localhost:8080 npx ts-node inference.ts
 */

const ENDPOINT = process.env.ENDPOINT || "http://localhost:8080";
const DEFAULT_PROMPT = "Explain quantum computing in simple terms.";

interface GenerateRequest {
  prompt: string;
  max_tokens?: number;
  temperature?: number;
  top_p?: number;
}

interface StreamChunk {
  token: string;
  finished: boolean;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
  };
}

async function streamGenerate(request: GenerateRequest): Promise<void> {
  const url = `${ENDPOINT}/generate`;
  console.log(`Connecting to ${url}...\n`);

  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }

  if (!response.body) {
    throw new Error("Response body is null — streaming not supported");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let fullText = "";
  const startTime = Date.now();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Parse SSE events from buffer
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";  // Keep incomplete line in buffer

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const jsonStr = line.slice(6).trim();
        if (!jsonStr) continue;

        try {
          const chunk: StreamChunk = JSON.parse(jsonStr);

          if (chunk.finished) {
            const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
            console.log("\n");
            console.log("─".repeat(50));
            console.log(`Generation complete in ${elapsed}s`);
            if (chunk.usage) {
              console.log(`Prompt tokens:     ${chunk.usage.prompt_tokens}`);
              console.log(`Completion tokens: ${chunk.usage.completion_tokens}`);
              const tokensPerSec = chunk.usage.completion_tokens / (parseFloat(elapsed) || 1);
              console.log(`Tokens/sec:        ${tokensPerSec.toFixed(1)}`);
            }
          } else {
            process.stdout.write(chunk.token);
            fullText += chunk.token;
          }
        } catch (parseErr) {
          console.error(`Failed to parse SSE chunk: ${jsonStr}`);
        }
      }
    }
  }

  console.log(`\n\nFull response:\n${fullText}`);
}

async function checkHealth(): Promise<void> {
  try {
    const response = await fetch(`${ENDPOINT}/health`);
    const data = await response.json();
    console.log("Health check:", data);
  } catch (err) {
    console.error("Health check failed:", err);
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  const prompt = process.env.PROMPT || DEFAULT_PROMPT;
  const maxTokens = parseInt(process.env.MAX_TOKENS || "256", 10);
  const temperature = parseFloat(process.env.TEMPERATURE || "0.7");

  console.log("Streaming Llama Inference Client");
  console.log(`Endpoint:    ${ENDPOINT}`);
  console.log(`Prompt:      "${prompt}"`);
  console.log(`Max tokens:  ${maxTokens}`);
  console.log(`Temperature: ${temperature}\n`);

  // Health check first
  await checkHealth();
  console.log("");

  // Run streaming generation
  await streamGenerate({
    prompt,
    max_tokens: maxTokens,
    temperature,
  });
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
