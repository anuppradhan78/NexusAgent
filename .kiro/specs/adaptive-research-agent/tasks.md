# Implementation Plan

This implementation plan focuses on building a working MCP demonstration with three custom MCP servers that Claude can use as tools.

## Phase 1: Foundation & MCP Servers

### 1. Set up project structure

- [x] 1.1 Create project directories and configuration
  - Create backend/ directory for Python application
  - Create mcp-servers/ directory with subdirectories: postman/, memory/, research-tools/
  - Create reports/ directory for generated reports
  - Create .env.example with required environment variables
  - Create .gitignore for .env, __pycache__, node_modules/, reports/
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 1.2 Set up Python dependencies
  - Create requirements.txt with: fastapi, uvicorn, anthropic, mcp, redis, pydantic, structlog, python-dotenv
  - Install dependencies: `pip install -r requirements.txt`
  - _Requirements: 6.1, 7.1, 8.1_

### 2. Build Postman MCP Server

- [x] 2.1 Initialize Postman MCP server project
  - Create mcp-servers/postman/package.json
  - Install dependencies: @modelcontextprotocol/sdk, axios
  - Create mcp-servers/postman/index.ts entry point
  - _Requirements: 2.1, 2.5_

- [x] 2.2 Implement search_apis tool
  - Create tool definition with input schema (query: string, verified_only: boolean)
  - Implement function to search Postman Public API Network
  - Use POSTMAN_API_KEY for authentication
  - Return list of relevant APIs with id, name, description
  - _Requirements: 2.2_

- [x] 2.3 Implement call_api tool
  - Create tool definition with input schema (api_id: string, endpoint: string, params: object)
  - Implement function to execute API requests
  - Handle authentication and error responses
  - Return API response data
  - _Requirements: 2.3_

- [x] 2.4 Implement get_api_details tool
  - Create tool definition with input schema (api_id: string)
  - Implement function to retrieve API documentation
  - Return API schema, endpoints, and usage information
  - _Requirements: 2.4_

- [x] 2.5 Add error handling and logging
  - Implement graceful error handling for all tools
  - Return structured error responses
  - Log all tool invocations with timestamps
  - _Requirements: 2.6, 2.7, 8.1, 8.3_

- [ ]* 2.6 Test Postman MCP server independently
  - Write unit tests for each tool
  - Test with sample Postman API calls
  - Verify error handling works correctly

### 3. Build Memory MCP Server

- [x] 3.1 Initialize Memory MCP server project
  - Create mcp-servers/memory/package.json
  - Install dependencies: @modelcontextprotocol/sdk, ioredis
  - Create mcp-servers/memory/index.ts entry point
  - _Requirements: 3.1_

- [x] 3.2 Implement store_result tool
  - Create tool definition with input schema (query: string, results: object, timestamp: number)
  - Connect to Redis using REDIS_URL
  - Implement function to store query and results
  - Set 30-day expiration on entries
  - Add to sorted set for chronological retrieval
  - _Requirements: 4.1, 4.2, 4.3, 4.5_

- [x] 3.3 Implement get_history tool
  - Create tool definition with input schema (limit: number, offset: number)
  - Implement function to retrieve past queries from Redis
  - Return queries in chronological order (most recent first)
  - _Requirements: 4.4_

- [x] 3.4 Add error handling and logging
  - Handle Redis connection failures gracefully
  - Log all tool invocations
  - _Requirements: 4.6, 8.1, 8.3_

- [ ]* 3.5 Test Memory MCP server independently
  - Write unit tests for store and retrieve operations
  - Test Redis connection handling
  - Verify expiration works correctly

### 4. Build Research Tools MCP Server

- [x] 4.1 Initialize Research Tools MCP server project
  - Create mcp-servers/research-tools/package.json
  - Install dependencies: @modelcontextprotocol/sdk
  - Create mcp-servers/research-tools/index.ts entry point
  - _Requirements: 5.1_

- [x] 4.2 Implement generate_report tool
  - Create tool definition with input schema (query: string, answer: string, sources: array, metadata: object)
  - Implement markdown report generation
  - Include query, answer, sources, and timestamp
  - Save to REPORT_OUTPUT_DIR with timestamped filename
  - Return report file path
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 4.3 Add error handling and logging
  - Handle file system errors gracefully
  - Log report generation events
  - _Requirements: 8.1, 8.3_

- [ ]* 4.4 Test Research Tools MCP server independently
  - Write unit tests for report generation
  - Verify markdown format is correct
  - Test file creation and naming

## Phase 2: Python Application Core

### 5. Implement MCP Tool Router

- [x] 5.1 Create mcp_tool_router.py
  - Import MCP SDK (ClientSession, stdio_client, StdioServerParameters)
  - Create MCPToolRouter class with __init__ accepting MCP config
  - _Requirements: 3.1_

- [x] 5.2 Implement MCP server connections
  - Implement connect_all() method to start all MCP servers as subprocesses
  - Use stdio transport to communicate with each server
  - Store sessions for each MCP server
  - Discover tools from each server using list_tools()
  - Build tool registry mapping tool names to servers
  - _Requirements: 3.1, 3.2_

- [x] 5.3 Implement get_tool_definitions()
  - Collect tool definitions from all connected MCP servers
  - Convert to Claude-compatible format
  - Return list of tool definitions
  - _Requirements: 3.3_

- [x] 5.4 Implement execute_tool()
  - Accept tool_name and tool_input
  - Look up which MCP server owns the tool
  - Call tool via MCP session.call_tool()
  - Return tool result
  - _Requirements: 3.4, 3.7_

- [x] 5.5 Add error handling and retry logic
  - Handle MCP server failures gracefully
  - Implement exponential backoff retry (3 attempts)
  - Report errors to Claude
  - Log all tool executions with timing
  - _Requirements: 3.5, 3.6, 3.7, 8.4, 8.5_

- [ ]* 5.6 Test MCP Tool Router
  - Write unit tests with mocked MCP servers
  - Test tool routing logic
  - Test error handling and retries

### 6. Implement Claude Client

- [x] 6.1 Create claude_client.py
  - Import anthropic Python SDK
  - Create ClaudeClient class
  - Initialize with ANTHROPIC_API_KEY
  - _Requirements: 1.1, 7.1_

- [x] 6.2 Implement call_with_tools()
  - Accept messages list and tools list
  - Call anthropic.messages.create() with tools
  - Use model: claude-3-5-sonnet-20241022
  - Return Claude response
  - _Requirements: 1.1, 1.2_

- [x] 6.3 Add retry logic for Claude API failures
  - Implement exponential backoff (3 attempts)
  - Log all Claude API calls
  - _Requirements: 8.4, 8.1_

- [ ]* 6.4 Test Claude Client
  - Write unit tests with mocked Anthropic API
  - Test retry logic
  - Test error handling

### 7. Implement Agent Orchestrator

- [x] 7.1 Create agent_orchestrator.py
  - Create AgentOrchestrator class
  - Initialize with ClaudeClient and MCPToolRouter
  - _Requirements: 1.1_

- [x] 7.2 Implement process_query() main pipeline
  - Accept query, max_sources, include_report parameters
  - Get tool definitions from MCP Tool Router
  - Call Claude with query and tools
  - Handle tool use loop: while Claude wants to use tools, execute them and return results
  - Extract final synthesis from Claude
  - Store results via Memory MCP Server
  - Optionally generate report via Research Tools MCP Server
  - Return ResearchResult with query_id, answer, sources, report_path, processing_time
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

- [x] 7.3 Add logging and error handling
  - Log query processing steps
  - Handle errors gracefully
  - Return user-friendly error messages
  - _Requirements: 8.1, 8.2, 8.3, 8.6_

- [ ]* 7.4 Test Agent Orchestrator
  - Write integration tests with mocked components
  - Test full query processing flow
  - Test error scenarios

### 8. Implement Redis Memory Store

- [x] 8.1 Create memory_store.py
  - Import redis library
  - Create MemoryStore class
  - Connect to Redis using REDIS_URL
  - _Requirements: 4.1, 7.3_

- [x] 8.2 Implement store() method
  - Accept query, results, sources
  - Generate unique query_id
  - Store in Redis hash
  - Set 30-day expiration
  - Add to sorted set for chronological retrieval
  - Return query_id
  - _Requirements: 4.2, 4.3, 4.5_

- [x] 8.3 Implement get_history() method
  - Accept limit and offset parameters
  - Retrieve query IDs from sorted set
  - Fetch query data from Redis
  - Return list of HistoryEntry objects
  - _Requirements: 4.4_

- [x] 8.4 Add error handling
  - Handle Redis connection failures gracefully
  - Log errors
  - _Requirements: 4.6, 8.1_

- [ ]* 8.5 Test Memory Store
  - Write unit tests for store and retrieve
  - Test expiration logic
  - Test error handling

### 9. Implement Report Generator

- [x] 9.1 Create report_generator.py
  - Create ReportGenerator class
  - Initialize with output_dir from REPORT_OUTPUT_DIR
  - _Requirements: 5.1, 7.4_

- [x] 9.2 Implement list_reports() method
  - List all generated reports from output directory
  - Return report metadata
  - _Requirements: 5.6_

- [x] 9.3 Implement get_report() method
  - Retrieve report content by ID
  - Handle file not found errors
  - _Requirements: 5.6_

- [ ]* 9.4 Test Report Generator
  - Write unit tests for report generation
  - Verify markdown format
  - Test file creation

## Phase 3: FastAPI REST API

### 10. Implement FastAPI Server

- [x] 10.1 Create main.py with FastAPI app
  - Initialize FastAPI application
  - Add CORS middleware
  - Load environment variables
  - Initialize all components (Claude Client, MCP Tool Router, Memory Store, Report Generator, Agent Orchestrator)
  - Connect to MCP servers on startup
  - _Requirements: 6.1, 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 10.2 Implement POST /api/research/query endpoint
  - Accept ResearchRequest (query, max_sources, include_report)
  - Call agent_orchestrator.process_query()
  - Return ResearchResponse with query_id, answer, sources, report_path, processing_time
  - Handle errors with appropriate HTTP status codes
  - Include request ID in response
  - _Requirements: 6.1, 6.6, 6.7, 1.1, 1.7_

- [x] 10.3 Implement GET /api/research/history endpoint
  - Accept limit and offset query parameters
  - Call memory_store.get_history()
  - Return HistoryResponse with queries list
  - _Requirements: 6.2_

- [x] 10.4 Implement GET /api/reports endpoint
  - List all generated reports from REPORT_OUTPUT_DIR
  - Return ReportsListResponse with report metadata
  - _Requirements: 6.3, 5.6_

- [x] 10.5 Implement GET /api/reports/{report_id} endpoint
  - Read report file from disk
  - Return report content
  - Handle file not found errors
  - _Requirements: 6.4_

- [x] 10.6 Implement GET /health endpoint
  - Check Redis connection
  - Check MCP servers connection status
  - Return HealthResponse with status
  - _Requirements: 6.5_

- [x] 10.7 Add structured logging
  - Use structlog for JSON logging
  - Log all requests with request IDs
  - Log query processing, tool calls, errors
  - _Requirements: 8.1, 8.2, 8.3_

- [x] 10.8 Add startup validation
  - Check ANTHROPIC_API_KEY is set, fail with clear error if missing
  - Check POSTMAN_API_KEY is set
  - Check REDIS_URL is set
  - Warn if Redis or MCP servers unavailable (degraded mode)
  - _Requirements: 7.6, 7.7_

- [ ]* 10.9 Test FastAPI endpoints
  - Write integration tests for all endpoints
  - Test error handling
  - Test request validation

## Phase 4: Integration & Testing

### 11. End-to-end testing

- [ ] 11.1 Test complete query flow
  - Start Redis
  - Start FastAPI application (which starts MCP servers)
  - Submit test query via POST /api/research/query
  - Verify Claude calls MCP tools (search_apis, call_api)
  - Verify synthesized answer is returned
  - Verify sources are included
  - Verify query is stored in Redis
  - Verify report is generated if requested
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 4.2, 5.1_

- [ ] 11.2 Test history retrieval
  - Submit multiple queries
  - Call GET /api/research/history
  - Verify all queries are returned in chronological order
  - _Requirements: 4.4_

- [ ] 11.3 Test report listing and retrieval
  - Generate multiple reports
  - Call GET /api/reports
  - Verify all reports are listed
  - Call GET /api/reports/{report_id}
  - Verify report content is returned
  - _Requirements: 5.6, 6.3, 6.4_

- [ ] 11.4 Test error handling
  - Test with missing API keys
  - Test with Redis unavailable
  - Test with MCP server failures
  - Verify graceful degradation
  - Verify error messages are user-friendly
  - _Requirements: 7.6, 7.7, 8.4, 8.5, 8.6_

- [ ] 11.5 Test health endpoint
  - Call GET /health
  - Verify status includes Redis and MCP server connection status
  - _Requirements: 6.5_

### 12. Documentation and Demo

- [ ] 12.1 Create README.md
  - Document project purpose (MCP demonstration)
  - Include setup instructions
  - Document environment variables
  - Include example API calls
  - Explain MCP architecture
  - _Requirements: All_

- [ ] 12.2 Create demo script
  - Create demo.py showing key features
  - Demonstrate query processing
  - Show Claude using MCP tools autonomously
  - Display generated reports
  - _Requirements: All_

- [ ] 12.3 Create .env.example
  - Include all required environment variables
  - Add comments explaining each variable
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

---

## Development Notes

**Implementation Order:**
1. Phase 1: Build all three MCP servers first (can be done in parallel)
2. Phase 2: Build Python application components
3. Phase 3: Wire everything together in FastAPI
4. Phase 4: Test and document

**Key Success Criteria:**
1. Three custom MCP servers expose tools to Claude
2. Claude autonomously decides which tools to use
3. Agent processes queries and returns synthesized results
4. Query history is stored in Redis
5. Reports are generated in markdown format
6. All endpoints work correctly
7. Error handling is graceful

**Testing Strategy:**
- Unit tests for individual components (marked with *)
- Integration tests for full workflows
- Manual testing for demo preparation
- Focus on core functionality first, optional tests can be added later

**MCP Architecture:**
- Python app calls Claude directly via anthropic SDK
- Claude receives tool definitions from MCP servers
- Claude decides when to use tools
- Python app routes tool calls to appropriate MCP server via MCP SDK
- MCP servers execute tools and return results
- Claude synthesizes final response
