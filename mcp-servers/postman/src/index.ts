#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";

// Postman API configuration
const POSTMAN_API_BASE = "https://api.getpostman.com";
const POSTMAN_API_KEY = process.env.POSTMAN_API_KEY;

if (!POSTMAN_API_KEY) {
  console.error("Error: POSTMAN_API_KEY environment variable is required");
  process.exit(1);
}

// Create MCP server
const server = new Server(
  {
    name: "postman-mcp-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Tool 1: search_apis - Search Postman Public API Network
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "search_apis",
        description: "Search Postman Public API Network for relevant APIs",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "Search query for finding APIs",
            },
            verified_only: {
              type: "boolean",
              description: "Only return verified APIs",
              default: true,
            },
          },
          required: ["query"],
        },
      },
      {
        name: "call_api",
        description: "Execute an API request from Postman Public API Network",
        inputSchema: {
          type: "object",
          properties: {
            api_id: {
              type: "string",
              description: "The Postman API ID",
            },
            endpoint: {
              type: "string",
              description: "The API endpoint to call",
            },
            method: {
              type: "string",
              description: "HTTP method (GET, POST, etc.)",
              default: "GET",
            },
            params: {
              type: "object",
              description: "Query parameters or request body",
            },
          },
          required: ["api_id", "endpoint"],
        },
      },
      {
        name: "get_api_details",
        description: "Get detailed information about a specific API",
        inputSchema: {
          type: "object",
          properties: {
            api_id: {
              type: "string",
              description: "The Postman API ID",
            },
          },
          required: ["api_id"],
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
      case "search_apis":
        return await handleSearchApis(args);
      case "call_api":
        return await handleCallApi(args);
      case "get_api_details":
        return await handleGetApiDetails(args);
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error: any) {
    console.error(`Error executing tool ${name}:`, error.message);
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

// Implementation: search_apis
async function handleSearchApis(args: any) {
  const { query, verified_only = true } = args;

  console.log(`[Postman MCP] Searching APIs: ${query}`);

  try {
    const response = await axios.get(`${POSTMAN_API_BASE}/apis`, {
      headers: {
        "X-Api-Key": POSTMAN_API_KEY,
      },
      params: {
        q: query,
        limit: 10,
      },
    });

    let apis = response.data.apis || [];

    // Filter for verified APIs if requested
    if (verified_only) {
      apis = apis.filter((api: any) => api.isVerified);
    }

    const results = apis.map((api: any) => ({
      api_id: api.id,
      api_name: api.name,
      description: api.summary || api.description || "No description available",
      verified: api.isVerified || false,
      created_by: api.createdBy,
    }));

    console.log(`[Postman MCP] Found ${results.length} APIs`);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(results, null, 2),
        },
      ],
    };
  } catch (error: any) {
    throw new Error(`Failed to search APIs: ${error.message}`);
  }
}

// Implementation: call_api
async function handleCallApi(args: any) {
  const { api_id, endpoint, method = "GET", params = {} } = args;

  console.log(`[Postman MCP] Calling API ${api_id} at ${endpoint}`);

  try {
    // First, get API details to find the base URL
    const apiDetailsResponse = await axios.get(
      `${POSTMAN_API_BASE}/apis/${api_id}`,
      {
        headers: {
          "X-Api-Key": POSTMAN_API_KEY,
        },
      }
    );

    const apiData = apiDetailsResponse.data.api;
    
    // Construct the full URL
    // Note: This is a simplified implementation
    // In a real scenario, you'd need to parse the API schema to get the correct base URL
    const fullUrl = endpoint.startsWith("http") ? endpoint : `https://api.example.com${endpoint}`;

    // Make the API call
    const config: any = {
      method: method.toUpperCase(),
      url: fullUrl,
      headers: {
        "Content-Type": "application/json",
      },
    };

    if (method.toUpperCase() === "GET") {
      config.params = params;
    } else {
      config.data = params;
    }

    const response = await axios(config);

    console.log(`[Postman MCP] API call successful`);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              status: response.status,
              data: response.data,
            },
            null,
            2
          ),
        },
      ],
    };
  } catch (error: any) {
    throw new Error(
      `Failed to call API: ${error.response?.data?.message || error.message}`
    );
  }
}

// Implementation: get_api_details
async function handleGetApiDetails(args: any) {
  const { api_id } = args;

  console.log(`[Postman MCP] Getting details for API ${api_id}`);

  try {
    const response = await axios.get(`${POSTMAN_API_BASE}/apis/${api_id}`, {
      headers: {
        "X-Api-Key": POSTMAN_API_KEY,
      },
    });

    const api = response.data.api;

    const details = {
      api_id: api.id,
      name: api.name,
      summary: api.summary,
      description: api.description,
      created_at: api.createdAt,
      updated_at: api.updatedAt,
      created_by: api.createdBy,
      collections: api.collections || [],
    };

    console.log(`[Postman MCP] Retrieved API details`);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(details, null, 2),
        },
      ],
    };
  } catch (error: any) {
    throw new Error(`Failed to get API details: ${error.message}`);
  }
}

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("[Postman MCP] Server started successfully");
}

main().catch((error) => {
  console.error("[Postman MCP] Fatal error:", error);
  process.exit(1);
});
