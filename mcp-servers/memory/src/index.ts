#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import Redis from "ioredis";

// Redis configuration
const REDIS_URL = process.env.REDIS_URL || "redis://localhost:6379";

// Create Redis client
const redis = new Redis(REDIS_URL);

redis.on("error", (err) => {
  console.error("[Memory MCP] Redis connection error:", err);
});

redis.on("connect", () => {
  console.error("[Memory MCP] Connected to Redis");
});

// Create MCP server
const server = new Server(
  {
    name: "memory-mcp-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Define tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "store_result",
        description: "Store query results in Redis memory",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "The research query",
            },
            results: {
              type: "object",
              description: "The query results to store",
            },
            timestamp: {
              type: "number",
              description: "Unix timestamp",
            },
          },
          required: ["query", "results", "timestamp"],
        },
      },
      {
        name: "get_history",
        description: "Retrieve past query history from Redis",
        inputSchema: {
          type: "object",
          properties: {
            limit: {
              type: "number",
              description: "Maximum number of queries to return",
              default: 50,
            },
            offset: {
              type: "number",
              description: "Offset for pagination",
              default: 0,
            },
          },
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "store_result":
        return await handleStoreResult(args);
      case "get_history":
        return await handleGetHistory(args);
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error: any) {
    console.error(`[Memory MCP] Error executing tool ${name}:`, error.message);
    return {
      content: [
        {
          type: "text",
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// Implementation: store_result
async function handleStoreResult(args: any) {
  const { query, results, timestamp } = args;

  console.log(`[Memory MCP] Storing result for query: ${query}`);

  try {
    // Generate unique query ID
    const queryId = `query:${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    // Store query data in Redis hash
    await redis.hset(queryId, {
      query_text: query,
      results_summary: JSON.stringify(results),
      timestamp: timestamp.toString(),
      api_sources: JSON.stringify(results.sources || []),
    });

    // Set expiration (30 days)
    await redis.expire(queryId, 30 * 24 * 60 * 60);

    // Add to sorted set for chronological retrieval
    await redis.zadd("queries:timeline", timestamp, queryId);

    console.log(`[Memory MCP] Stored query with ID: ${queryId}`);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            success: true,
            query_id: queryId,
            message: "Query stored successfully",
          }),
        },
      ],
    };
  } catch (error: any) {
    throw new Error(`Failed to store result: ${error.message}`);
  }
}

// Implementation: get_history
async function handleGetHistory(args: any) {
  const { limit = 50, offset = 0 } = args;

  console.log(`[Memory MCP] Retrieving history (limit: ${limit}, offset: ${offset})`);

  try {
    // Get query IDs from sorted set (most recent first)
    const queryIds = await redis.zrevrange(
      "queries:timeline",
      offset,
      offset + limit - 1
    );

    if (queryIds.length === 0) {
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              queries: [],
              total: 0,
            }),
          },
        ],
      };
    }

    // Fetch query data for each ID
    const queries = [];
    for (const queryId of queryIds) {
      const data = await redis.hgetall(queryId);
      if (data && data.query_text) {
        queries.push({
          query_id: queryId,
          query: data.query_text,
          results: JSON.parse(data.results_summary || "{}"),
          sources: JSON.parse(data.api_sources || "[]"),
          timestamp: parseFloat(data.timestamp || "0"),
        });
      }
    }

    console.log(`[Memory MCP] Retrieved ${queries.length} queries`);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            queries,
            total: queries.length,
            limit,
            offset,
          }, null, 2),
        },
      ],
    };
  } catch (error: any) {
    throw new Error(`Failed to get history: ${error.message}`);
  }
}

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("[Memory MCP] Server started successfully");
}

main().catch((error) => {
  console.error("[Memory MCP] Fatal error:", error);
  process.exit(1);
});
