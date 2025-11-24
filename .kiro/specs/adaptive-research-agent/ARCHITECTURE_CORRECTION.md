# Architecture Correction - MCP Implementation

## Critical Issue Identified

The original specification had a **fundamental misunderstanding** of how MCP (Model Context Protocol) works.

### ❌ Original (Incorrect) Architecture

```
Application → MCP Client → MCP Server (Anthropic) → Claude API
Application → MCP Client → MCP Server (Postman) → Postman API
```

**Problem**: Tried to use MCP as a proxy to call Claude and Postman APIs. These MCP servers don't exist.

### ✅ Correct Architecture

```
Application → Claude API (direct via @anthropic-ai/sdk)
     ↓
Claude uses tools via MCP
     ↓
Custom MCP Servers (we build these)
     ↓
External APIs (Postman, databases, etc.)
```

**Solution**: Call Claude directly, then build custom MCP servers that expose tools for Claude to use.

## What MCP Actually Does

**MCP Purpose**: Provides a standardized way for AI assistants (like Claude) to access external tools and data sources.

**MCP is NOT**: A way to call LLM APIs. You call the LLM directly, then the LLM uses MCP servers as tools.

## Corrected System Architecture

### Layer 1: Application Core
- FastAPI REST API
- Agent Orchestrator
- Learning Engine
- Memory Store (Redis)

### Layer 2: AI Integration
- **Direct Claude API calls** using `@anthropic-ai/sdk`
- Claude receives tool definitions from our MCP servers
- Claude decides when to use tools

### Layer 3: Custom MCP Servers (We Build These)
1. **Postman API MCP Server**
   - Tool: `search_apis` - Search Postman Public API Network
   - Tool: `call_api` - Execute API requests
   - Tool: `get_api_details` - Get API documentation

2. **Memory MCP Server**
   - Tool: `search_memory` - Semantic search past queries
   - Tool: `store_result` - Save query results
   - Tool: `get_patterns` - Retrieve learned patterns

3. **Research Tools MCP Server**
   - Tool: `generate_report` - Create markdown reports
   - Tool: `evaluate_urgency` - Assess if alert needed
   - Tool: `refine_query` - Improve query based on history

### Layer 4: External Services
- Postman Public API Network
- Redis Vector Store
- File system (for reports)

## Required Changes

### 1. Requirements Document
- Remove references to "Claude via MCP"
- Add requirements for custom MCP server implementation
- Clarify Claude is called directly
- Specify MCP servers as tools Claude can use

### 2. Design Document
- Redesign MCP client to be MCP **server** implementation
- Add Claude SDK integration
- Define tool schemas for each MCP server
- Update architecture diagrams

### 3. Tasks Document
- Remove tasks for connecting to non-existent MCP servers
- Add tasks for building custom MCP servers
- Add tasks for Claude SDK integration
- Add tasks for tool definition and registration

## Implementation Approach

### Phase 1: Core Infrastructure
1. Install and configure Anthropic SDK
2. Set up basic Claude API integration
3. Implement direct API calls for reasoning/synthesis

### Phase 2: Build Custom MCP Servers
1. Create Postman API MCP Server (TypeScript/Node.js)
2. Create Memory MCP Server (TypeScript/Node.js)
3. Create Research Tools MCP Server (TypeScript/Node.js)
4. Test each server independently

### Phase 3: Integration
1. Register MCP servers with application
2. Configure Claude to use MCP tools
3. Implement tool calling workflow
4. Test end-to-end with Claude using tools

### Phase 4: Learning & Optimization
1. Implement feedback loops
2. Add learning engine
3. Enable self-improvement metrics

## Technology Stack Changes

### Add:
- `@anthropic-ai/sdk` - Direct Claude API access
- `@modelcontextprotocol/sdk` - For building MCP servers
- TypeScript/Node.js - For MCP server implementation

### Keep:
- Python/FastAPI - Application core
- Redis - Vector memory
- All existing learning/alert/report logic

## Benefits of Correct Architecture

1. ✅ **Actually works** - Uses real, available packages
2. ✅ **Demonstrates MCP properly** - Shows how to build and use MCP servers
3. ✅ **More powerful** - Claude can intelligently choose when to use tools
4. ✅ **Extensible** - Easy to add new tools/capabilities
5. ✅ **Educational** - Shows proper MCP implementation

## Next Steps

1. **Review this document** - Confirm the corrected architecture
2. **Update requirements.md** - Reflect correct MCP usage
3. **Update design.md** - New architecture and components
4. **Update tasks.md** - New implementation plan
5. **Execute in order** - Build with correct architecture

## Estimated Effort

- Spec updates: 1-2 hours
- MCP server implementation: 4-6 hours
- Claude SDK integration: 2-3 hours
- Testing and integration: 2-3 hours
- **Total: 9-14 hours of development**

This is more complex than the original (incorrect) design, but it's the **correct way** to use MCP and will result in a working, demonstrable system.
