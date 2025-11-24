# Requirements Document

## Introduction

The Adaptive Research Agent is a demonstration of proper Model Context Protocol (MCP) implementation. The system shows how to build custom MCP servers that expose tools for Claude to use autonomously. When a user submits a research query, Claude decides which tools to call (API search, API execution, memory lookup, report generation) and orchestrates the research process. This demonstrates the power of MCP: giving AI assistants access to external capabilities through a standardized protocol.

**Core Innovation:**
- **Proper MCP Architecture**: Build custom MCP servers that Claude can use as tools
- **Autonomous Tool Selection**: Claude decides when and how to use available tools
- **Real API Integration**: Demonstrate MCP with real Postman Public API Network
- **Simple but Complete**: Focus on MCP demonstration without unnecessary complexity

## Glossary

- **Adaptive_Research_Agent**: The system demonstrating MCP implementation with Claude and custom MCP servers
- **MCP_Server**: Custom Model Context Protocol server that exposes tools for Claude to use (we build this)
- **MCP_Tool**: A function exposed by an MCP server that Claude can call (e.g., search_apis, call_api)
- **Postman_MCP_Server**: Custom MCP server providing tools to search and call Postman Public API Network
- **Research_Query**: User request for information gathering from API sources
- **Claude_API**: Anthropic's Claude LLM accessed directly via @anthropic-ai/sdk
- **Tool_Call**: When Claude decides to use an MCP tool to accomplish a task
- **Research_Report**: Markdown document summarizing gathered information with citations
- **Redis_Store**: Simple Redis storage for query history and results

## Requirements

### Requirement 1

**User Story:** As a researcher, I want to submit natural language queries and have Claude autonomously use MCP tools to gather information from APIs, so that I can see MCP in action.

#### Acceptance Criteria

1. WHEN a user submits a Research_Query, THE Adaptive_Research_Agent SHALL call Claude_API with the query and available MCP_Tool definitions
2. THE Adaptive_Research_Agent SHALL provide Claude with search_apis tool to discover relevant APIs from Postman Public API Network
3. THE Adaptive_Research_Agent SHALL provide Claude with call_api tool to execute API requests
4. WHEN Claude makes a Tool_Call, THE Adaptive_Research_Agent SHALL execute the tool via Postman_MCP_Server and return results to Claude
5. THE Adaptive_Research_Agent SHALL allow Claude to make multiple tool calls until it has sufficient information
6. THE Adaptive_Research_Agent SHALL use Claude to synthesize gathered information into a coherent response
7. THE Adaptive_Research_Agent SHALL return the synthesized answer with source citations

### Requirement 2

**User Story:** As a developer, I want to build a custom Postman MCP server, so that I can demonstrate how to create MCP servers that expose tools to Claude.

#### Acceptance Criteria

1. THE Adaptive_Research_Agent SHALL implement a Postman_MCP_Server using @modelcontextprotocol/sdk in TypeScript
2. THE Postman_MCP_Server SHALL expose a search_apis tool that searches Postman Public API Network
3. THE Postman_MCP_Server SHALL expose a call_api tool that executes API requests with authentication
4. THE Postman_MCP_Server SHALL expose a get_api_details tool that retrieves API documentation
5. THE Postman_MCP_Server SHALL run as a standalone Node.js process on a configured port
6. THE Postman_MCP_Server SHALL handle errors gracefully and return structured error responses
7. THE Postman_MCP_Server SHALL log all tool invocations for debugging

### Requirement 3

**User Story:** As a developer, I want the Python application to communicate with MCP servers, so that Claude can use the exposed tools.

#### Acceptance Criteria

1. THE Adaptive_Research_Agent SHALL implement an MCP_Tool_Router that connects to running MCP servers
2. THE MCP_Tool_Router SHALL discover available tools from connected MCP servers at startup
3. THE MCP_Tool_Router SHALL convert tool definitions to Claude-compatible format
4. WHEN Claude requests a tool call, THE MCP_Tool_Router SHALL route the request to the appropriate MCP server
5. THE MCP_Tool_Router SHALL handle MCP server failures gracefully and report errors to Claude
6. THE MCP_Tool_Router SHALL support multiple MCP servers running on different ports
7. THE MCP_Tool_Router SHALL log all tool executions with timing information

### Requirement 4

**User Story:** As a researcher, I want the agent to store query results in Redis, so that I can review past research and see patterns over time.

#### Acceptance Criteria

1. THE Adaptive_Research_Agent SHALL connect to Redis_Store for data persistence
2. WHEN a query is processed, THE Adaptive_Research_Agent SHALL store the query text, results, and timestamp in Redis
3. THE Adaptive_Research_Agent SHALL store API sources used and their response data
4. THE Adaptive_Research_Agent SHALL provide a history endpoint that retrieves past queries
5. THE Adaptive_Research_Agent SHALL implement automatic expiration of entries older than 30 days
6. THE Adaptive_Research_Agent SHALL handle Redis connection failures gracefully

### Requirement 5

**User Story:** As a researcher, I want the agent to generate markdown reports, so that I can save and share research findings.

#### Acceptance Criteria

1. THE Adaptive_Research_Agent SHALL generate Research_Report documents in markdown format
2. THE Research_Report SHALL include query, synthesized answer, sources used, and timestamp
3. THE Research_Report SHALL organize information with clear headings and bullet points
4. THE Research_Report SHALL include all API sources with their endpoints and response summaries
5. THE Research_Report SHALL save to a configured output directory with timestamped filenames
6. THE Adaptive_Research_Agent SHALL provide an endpoint to list and retrieve generated reports

### Requirement 6

**User Story:** As a developer, I want the agent exposed as a FastAPI REST service, so that I can interact with it programmatically.

#### Acceptance Criteria

1. THE Adaptive_Research_Agent SHALL expose a POST endpoint at /api/research/query accepting natural language queries
2. THE Adaptive_Research_Agent SHALL expose a GET endpoint at /api/research/history returning past queries with pagination
3. THE Adaptive_Research_Agent SHALL expose a GET endpoint at /api/reports listing generated reports
4. THE Adaptive_Research_Agent SHALL expose a GET endpoint at /api/reports/{report_id} returning specific report content
5. THE Adaptive_Research_Agent SHALL expose a GET endpoint at /health for service health checks
6. THE Adaptive_Research_Agent SHALL return appropriate HTTP status codes and structured JSON responses
7. THE Adaptive_Research_Agent SHALL include request IDs in responses for tracing

### Requirement 7

**User Story:** As a system administrator, I want to configure the agent via environment variables, so that I can deploy it in different environments.

#### Acceptance Criteria

1. THE Adaptive_Research_Agent SHALL read ANTHROPIC_API_KEY from environment variables for Claude access
2. THE Adaptive_Research_Agent SHALL read POSTMAN_API_KEY from environment variables for Postman API access
3. THE Adaptive_Research_Agent SHALL read REDIS_URL from environment variables for data storage
4. THE Adaptive_Research_Agent SHALL read REPORT_OUTPUT_DIR from environment variables for report storage
5. THE Adaptive_Research_Agent SHALL read MCP_SERVER_PORTS from environment variables for MCP server configuration
6. IF ANTHROPIC_API_KEY is missing, THEN THE Adaptive_Research_Agent SHALL fail to start with a clear error message
7. IF Redis or MCP servers are unavailable, THE Adaptive_Research_Agent SHALL start in degraded mode with warnings

### Requirement 8

**User Story:** As a system operator, I want basic logging and error handling, so that I can debug issues when they occur.

#### Acceptance Criteria

1. THE Adaptive_Research_Agent SHALL log all queries, tool calls, and responses with timestamps
2. THE Adaptive_Research_Agent SHALL use structured JSON logging for machine readability
3. THE Adaptive_Research_Agent SHALL log errors with stack traces and context information
4. THE Adaptive_Research_Agent SHALL handle Claude API failures with retry logic (3 attempts with exponential backoff)
5. THE Adaptive_Research_Agent SHALL handle MCP server failures gracefully and continue with available tools
6. THE Adaptive_Research_Agent SHALL return user-friendly error messages in API responses

