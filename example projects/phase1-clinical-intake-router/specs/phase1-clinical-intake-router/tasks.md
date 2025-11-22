# Tasks - Phase 1: Clinical Intake Router

## Task 1: Project Setup and Configuration

**Description:** Initialize project structure, dependencies, and configuration management

**Subtasks:**
1. Create project directory structure
   - `src/` - Source code
   - `tests/` - Test files
   - `data/` - Test datasets
   - `docs/` - Documentation
2. Initialize Python virtual environment
3. Create `requirements.txt` with dependencies:
   - fastapi
   - uvicorn
   - langgraph
   - instructor
   - pydantic
   - openai
   - anthropic
   - pytest
   - ruff
   - black
   - mypy
4. Create `.env.example` with configuration template
5. Create `pyproject.toml` for project metadata
6. Setup `.gitignore` for Python projects
7. Initialize git repository

**Acceptance Criteria:**
- Project structure matches design document
- All dependencies install without errors
- Environment variables documented in `.env.example`

**Estimated Time:** 1 hour

---

## Task 2: Pydantic Data Models

**Description:** Implement all Pydantic models for structured data validation

**Subtasks:**
1. Create `src/models.py`
2. Implement enums:
   - `TriagePriority`
   - `Specialty`
   - `Severity`
3. Implement entity models:
   - `Symptom`
   - `VitalSign`
   - `Medication`
   - `ChronicCondition`
   - `MedicalEntities`
4. Implement classification models:
   - `TriageClassification`
5. Implement API models:
   - `IntakeRequest`
   - `IntakeResponse`
   - `ErrorResponse`
6. Add field validators where needed
7. Add JSON schema examples

**Acceptance Criteria:**
- All models pass mypy type checking
- Field validators work correctly
- Models serialize/deserialize to JSON properly
- Example data validates successfully

**Estimated Time:** 2 hours

---

## Task 3: Instructor Client Setup

**Description:** Configure Instructor library for structured LLM output

**Subtasks:**
1. Create `src/instructor_client.py`
2. Implement provider-agnostic client initialization
3. Support OpenAI provider
4. Support Anthropic provider
5. Support Groq provider
6. Support Grok/xAI provider
7. Add retry configuration
8. Add error handling for API failures
9. Create helper functions for common operations

**Acceptance Criteria:**
- Client initializes correctly for each provider (OpenAI, Anthropic, Groq, Grok)
- Automatic retries work on validation failures
- Structured output matches Pydantic models
- API errors are caught and handled gracefully

**Estimated Time:** 2 hours

---

## Task 4: Prompt Templates

**Description:** Create system and user prompts for entity extraction and triage

**Subtasks:**
1. Create `src/prompts.py`
2. Write entity extraction system prompt
3. Write entity extraction user prompt template
4. Write triage classification system prompt
5. Write triage classification user prompt template
6. Add prompt formatting utilities
7. Test prompts with sample inputs

**Acceptance Criteria:**
- Prompts are clear and specific
- Prompts include examples where helpful
- Prompts enforce structured output format
- Prompts handle edge cases (missing info, ambiguous symptoms)

**Estimated Time:** 1.5 hours

---

## Task 5: LangGraph Workflow - Core Nodes

**Description:** Implement LangGraph workflow nodes for processing pipeline

**Subtasks:**
1. Create `src/workflow.py`
2. Define `IntakeState` TypedDict
3. Implement `process_input()` node
4. Implement `extract_entities()` node
5. Implement `classify_triage()` node
6. Implement `validate_output()` node
7. Implement `handle_retry()` node
8. Implement `format_output()` node
9. Add logging to each node

**Acceptance Criteria:**
- Each node updates state correctly
- Nodes handle errors gracefully
- Logging provides visibility into processing
- State transitions are tracked

**Estimated Time:** 3 hours

---

## Task 6: LangGraph Workflow - Graph Assembly

**Description:** Assemble nodes into complete LangGraph workflow with conditional routing

**Subtasks:**
1. Create StateGraph with IntakeState
2. Add all nodes to graph
3. Define entry point
4. Add sequential edges
5. Implement `should_retry()` conditional function
6. Add conditional edges from validation node
7. Compile graph into executable app
8. Test graph execution with sample inputs

**Acceptance Criteria:**
- Graph compiles without errors
- Workflow executes from start to end
- Conditional routing works correctly
- Retry logic activates when needed
- Graph completes within timeout

**Estimated Time:** 2 hours

---

## Task 7: FastAPI Server - Core Endpoints

**Description:** Implement REST API with FastAPI

**Subtasks:**
1. Create `src/main.py`
2. Initialize FastAPI app
3. Implement `/api/health` endpoint
4. Implement `/api/intake/process` endpoint
5. Implement `/api/intake/batch` endpoint
6. Add request ID generation
7. Add request/response logging
8. Add error handling middleware
9. Add CORS middleware
10. Add timeout enforcement

**Acceptance Criteria:**
- All endpoints return correct status codes
- Request/response models validate properly
- Errors return structured error responses
- CORS allows configured origins
- Timeouts prevent hanging requests

**Estimated Time:** 3 hours

---

## Task 8: Authentication and Rate Limiting

**Description:** Implement API key authentication and rate limiting

**Subtasks:**
1. Create `src/auth.py`
2. Implement API key header validation
3. Load valid API keys from environment
4. Add authentication dependency to endpoints
5. Implement simple rate limiting (optional: use slowapi)
6. Add rate limit headers to responses
7. Test authentication with valid/invalid keys

**Acceptance Criteria:**
- Invalid API keys return 401
- Valid API keys allow access
- Rate limiting prevents abuse
- Rate limit headers inform clients

**Estimated Time:** 1.5 hours

---

## Task 9: Configuration Management

**Description:** Implement environment-based configuration

**Subtasks:**
1. Create `src/config.py`
2. Define Settings class with pydantic-settings
3. Add LLM provider configuration (openai, anthropic, groq, grok, fireworks)
4. Add API key configuration (OPENAI_API_KEY, ANTHROPIC_API_KEY, GROQ_API_KEY, GROK_API_KEY)
5. Add model name configuration
6. Add retry and timeout configuration
7. Add logging configuration
8. Validate required settings on startup
9. Create `.env.example` with all settings

**Acceptance Criteria:**
- Settings load from environment variables
- Missing required settings cause startup failure
- Settings are type-safe and validated
- Different environments supported (dev, prod)
- All LLM providers (OpenAI, Anthropic, Groq, Grok) configurable

**Estimated Time:** 1 hour

---

## Task 10: Structured Logging

**Description:** Implement structured JSON logging for observability

**Subtasks:**
1. Create `src/logging_config.py`
2. Configure structlog for JSON output
3. Add request ID to log context
4. Add log statements to all workflow nodes
5. Add log statements to API endpoints
6. Log errors with full context
7. Test log output format

**Acceptance Criteria:**
- Logs are valid JSON
- Logs include request ID for tracing
- Logs include relevant context (priority, confidence, etc.)
- Error logs include stack traces
- Log level configurable via environment

**Estimated Time:** 1.5 hours

---

## Task 11: Prometheus Metrics

**Description:** Add Prometheus metrics for monitoring

**Subtasks:**
1. Create `src/metrics.py`
2. Define Counter for total requests
3. Define Histogram for processing time
4. Define Histogram for confidence scores
5. Define Gauge for active requests
6. Add metrics recording to endpoints
7. Expose `/metrics` endpoint
8. Test metrics collection

**Acceptance Criteria:**
- Metrics are exposed in Prometheus format
- Metrics update correctly on requests
- Metrics include relevant labels (priority, specialty)
- Metrics endpoint accessible

**Estimated Time:** 1.5 hours

---

## Task 12: Golden Dataset Creation

**Description:** Create test dataset of 50 labeled patient intake messages

**Subtasks:**
1. Create `data/golden_dataset.json`
2. Write 10 emergency cases (chest pain, difficulty breathing, etc.)
3. Write 15 urgent cases (high fever, severe pain, etc.)
4. Write 15 routine cases (medication refills, mild symptoms, etc.)
5. Write 10 informational cases (questions, scheduling, etc.)
6. Label each with expected:
   - Triage priority
   - Specialty routing
   - Key medical entities
7. Ensure diversity (age, conditions, complexity)
8. Validate JSON format

**Acceptance Criteria:**
- 50 diverse test cases
- Realistic patient messages
- Expert-validated labels
- JSON format valid
- Covers all priority levels and specialties

**Estimated Time:** 3 hours

---

## Task 13: Evaluation Script

**Description:** Create script to run evaluation against golden dataset

**Subtasks:**
1. Create `evaluate.py` script
2. Load golden dataset
3. Process all 50 cases through workflow
4. Calculate triage accuracy
5. Calculate specialty routing accuracy
6. Verify 100% valid JSON output
7. Measure processing time
8. Generate evaluation report
9. Display results summary

**Acceptance Criteria:**
- Script runs all 50 cases
- Accuracy metrics calculated correctly
- 100% valid JSON output achieved
- Processing time within limits
- Report shows detailed results

**Estimated Time:** 2 hours

---

## Task 14: Documentation

**Description:** Write comprehensive documentation

**Subtasks:**
1. Create `README.md` with:
   - Project overview
   - Setup instructions
   - Usage examples
   - API documentation
   - Configuration guide
2. Create `docs/API.md` with endpoint details
3. Create `docs/DEPLOYMENT.md` with deployment guide
4. Add docstrings to all functions
5. Add inline comments for complex logic
6. Create example requests/responses

**Acceptance Criteria:**
- README is clear and complete
- Setup instructions work on fresh system
- API documentation covers all endpoints
- Code is well-documented
- Examples are runnable

**Estimated Time:** 2 hours

---

## Task 15: Docker Configuration

**Description:** Create Docker setup for easy deployment

**Subtasks:**
1. Create `Dockerfile`
2. Create `docker-compose.yml`
3. Create `.dockerignore`
4. Test Docker build
5. Test Docker run
6. Document Docker usage in README

**Acceptance Criteria:**
- Docker image builds successfully
- Container runs and serves API
- Environment variables configurable
- Health check works
- Docker instructions in README

**Estimated Time:** 1.5 hours

---

## Task 16: Final Integration and Testing

**Description:** End-to-end testing and final improvements

**Subtasks:**
1. Run complete test suite
2. Test with all LLM providers (OpenAI, Anthropic, Groq, Grok)
3. Test error scenarios
4. Verify logging output
5. Verify metrics collection
6. Performance testing (latency, throughput)
7. Code cleanup and formatting
8. Final documentation review
9. Create demo video or screenshots

**Acceptance Criteria:**
- All tests pass
- All providers work correctly (OpenAI, Anthropic, Groq, Grok)
- Performance meets targets
- Code is clean and formatted
- Documentation is complete
- Demo materials ready

**Estimated Time:** 3 hours

---

## OPTIONAL TASKS (For Production Readiness)

### Optional Task A: Unit Tests - Models

**Description:** Write unit tests for Pydantic models

**Subtasks:**
1. Create `tests/test_models.py`
2. Test all model validation
3. Test field validators
4. Test JSON serialization

**Estimated Time:** 2 hours

---

### Optional Task B: Unit Tests - Workflow

**Description:** Write unit tests for LangGraph workflow nodes

**Subtasks:**
1. Create `tests/test_workflow.py`
2. Mock Instructor client
3. Test all workflow nodes
4. Test retry logic

**Estimated Time:** 3 hours

---

### Optional Task C: Integration Tests - API

**Description:** Write integration tests for FastAPI endpoints

**Subtasks:**
1. Create `tests/test_api.py`
2. Test all endpoints
3. Test authentication
4. Test error handling

**Estimated Time:** 2.5 hours

---

### Optional Task D: CI/CD Pipeline

**Description:** Setup GitHub Actions for automated testing

**Subtasks:**
1. Create `.github/workflows/test.yml`
2. Configure Python environment
3. Run linting and type checking
4. Run tests with coverage

**Estimated Time:** 1.5 hours

---

## Summary

**Core Tasks Total Time:** 35-40 hours
**Optional Tasks Total Time:** 9 hours

**Recommended Order:**
1. Tasks 1-4: Foundation (models, config, prompts)
2. Tasks 5-6: Core workflow
3. Tasks 7-11: API and observability
4. Tasks 12-13: Dataset and evaluation
5. Tasks 14-16: Documentation and polish
6. Optional Tasks: Add when needed for production

**Milestones:**
- **Week 1:** Tasks 1-11 (Core implementation)
- **Week 2:** Tasks 12-16 (Evaluation, documentation, polish)
- **Optional:** Tasks A-D (Testing and CI/CD)

**Dependencies:**
- Task 5 depends on Tasks 2, 3, 4
- Task 6 depends on Task 5
- Task 7 depends on Task 6
- Task 13 depends on Task 12
