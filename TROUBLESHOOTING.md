# Troubleshooting Guide - Adaptive Research Agent

## Application Startup Issue - MCP Server Connection

### Problem
The application was hanging during startup when trying to initialize MCP (Model Context Protocol) connections to Anthropic and Postman servers.

### Root Cause
The MCP server packages specified in the code don't exist on npm:
- `@anthropic-ai/mcp-server-anthropic` - **Does not exist**
- `@postman/mcp-server` - **Does not exist**

When the application tried to run `npx -y @anthropic-ai/mcp-server-anthropic`, npm would search for the package indefinitely, causing the startup to hang.

### Solution Implemented
1. **Added connection timeouts** (30 seconds) to prevent indefinite hanging
2. **Modified startup to continue in degraded mode** if MCP initialization fails
3. **Added proper error handling** to catch `CancelledError` from timeout

### Current Status
✅ **Server is running successfully** at `http://localhost:8000`
- Redis: Connected
- Memory Store: Initialized
- Alert Engine: Initialized  
- Report Generator: Initialized
- Session Manager: Initialized
- Agent Orchestrator: Initialized
- Query Scheduler: Initialized (1 scheduled query loaded)

⚠️ **MCP functionality unavailable**
- Claude API calls won't work
- Postman API discovery won't work
- Application runs in "degraded mode"

### Testing the Server

```bash
# Check health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"adaptive-research-agent","version":"1.0.0",...}
```

### Next Steps to Enable Full Functionality

#### Option 1: Use Anthropic SDK Directly
Replace MCP client calls with direct Anthropic SDK calls:
```bash
npm install @anthropic-ai/sdk
```

Then modify `mcp_client.py` to use the SDK directly instead of through MCP.

#### Option 2: Find Correct MCP Server Packages
Research the actual MCP server packages or implementation method. The MCP protocol may require:
- Custom server implementation
- Different package names
- Local server setup

#### Option 3: Mock MCP for Development
Create mock MCP responses for development and testing without external dependencies.

### Files Modified
- `backend/mcp_client.py` - Added timeouts to connection methods
- `backend/main.py` - Added error handling to continue without MCP

### Logs Location
- Server output: Check the terminal window where `python main.py` is running
- Structured logs: JSON format with request IDs for tracing

### Stopping the Server
```bash
# If running in background process
# Use Ctrl+C in the terminal

# Or use the shutdown script
.\shutdown.bat  # Windows
./shutdown.sh   # Linux/Mac
```

## Additional Notes

The application architecture assumes MCP servers exist and are available via npx. This appears to be based on documentation or examples that may not reflect the current state of MCP server availability. The codebase would benefit from either:

1. Direct API integration (bypassing MCP)
2. Updated MCP server references
3. Local MCP server implementation

For now, the server runs successfully but with limited AI/API functionality.
