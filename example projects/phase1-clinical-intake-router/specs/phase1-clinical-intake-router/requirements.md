# Requirements Document - Phase 1: Clinical Intake Router

## Introduction

The Clinical Intake Router is a proof-of-concept system demonstrating structured output from LLMs using LangGraph and Pydantic. The system processes unstructured patient intake messages (symptoms, concerns, medical history) and extracts guaranteed valid JSON output containing triage priority, clinical specialty routing, and structured medical entities. This project teaches the 2025 standard for forcing LLMs to return clean, typed data suitable for integration with downstream healthcare systems.

**Learning Objectives:**
- Master structured output using Instructor/Pydantic with OpenAI/Anthropic APIs
- Build stateful workflows with LangGraph (not plain LangChain)
- Deploy as FastAPI endpoint with proper validation
- Achieve 100% valid structured output on test cases

## Glossary

- **Clinical_Intake_Router**: The complete system that processes patient intake messages and returns structured triage data
- **Intake_Message**: Unstructured text from patients describing symptoms, concerns, or medical history
- **Triage_Priority**: Urgency classification (emergency, urgent, routine, informational)
- **Specialty_Routing**: Recommended clinical specialty (cardiology, nephrology, endocrinology, general_medicine, mental_health)
- **Medical_Entity**: Structured clinical data extracted from text (symptoms, vital_signs, medications, chronic_conditions, temporal_info)
- **Structured_Output_Schema**: Pydantic model defining the exact JSON structure with type validation
- **LangGraph_Workflow**: Stateful processing graph with nodes for extraction, validation, and retry logic
- **Instructor_Library**: Python library that guarantees structured output from LLM APIs
- **Confidence_Score**: Float between 0.0-1.0 indicating classification certainty
- **Test_Dataset**: 50 diverse patient intake messages with expected structured outputs

## Requirements

### Requirement 1

**User Story:** As a healthcare data engineer, I want to process unstructured patient intake messages and receive guaranteed valid JSON output, so that I can reliably integrate with downstream clinical systems without parsing errors.

#### Acceptance Criteria

1. WHEN the Clinical_Intake_Router receives an Intake_Message, THE Clinical_Intake_Router SHALL return a JSON object conforming to the predefined Pydantic schema
2. THE Clinical_Intake_Router SHALL use Instructor library to enforce structured output from the LLM API
3. WHEN the LLM returns invalid or incomplete data, THE Clinical_Intake_Router SHALL automatically retry with corrected prompts up to 2 times
4. THE Clinical_Intake_Router SHALL validate all required fields (triage_priority, specialty_routing, medical_entities, confidence_score, timestamp) are present
5. THE Clinical_Intake_Router SHALL achieve 100% valid JSON output on all test cases without manual post-processing

### Requirement 2

**User Story:** As a triage nurse, I want patient messages automatically classified by urgency and routed to the appropriate specialty, so that critical cases are prioritized and patients reach the right care team.

#### Acceptance Criteria

1. WHEN the Clinical_Intake_Router analyzes an Intake_Message, THE Clinical_Intake_Router SHALL classify triage priority as one of: emergency, urgent, routine, or informational
2. THE Clinical_Intake_Router SHALL identify the most appropriate clinical specialty from: cardiology, nephrology, endocrinology, general_medicine, or mental_health
3. WHEN emergency keywords are detected (chest pain, difficulty breathing, severe bleeding), THE Clinical_Intake_Router SHALL assign emergency priority with confidence >= 0.9
4. THE Clinical_Intake_Router SHALL provide a brief clinical reasoning explanation for the triage and routing decisions
5. THE Clinical_Intake_Router SHALL assign a confidence score between 0.0-1.0 for each classification

### Requirement 3

**User Story:** As a clinical data scientist, I want structured medical entities extracted from free-text messages, so that I can populate structured fields in the EHR without manual data entry.

#### Acceptance Criteria

1. WHEN the Clinical_Intake_Router processes an Intake_Message, THE Clinical_Intake_Router SHALL extract medical entities in structured format
2. THE Clinical_Intake_Router SHALL identify and structure symptoms with fields: name, severity (mild/moderate/severe), duration, body_location
3. THE Clinical_Intake_Router SHALL identify and structure vital signs with fields: type (blood_pressure/heart_rate/temperature), value, unit, timestamp_mentioned
4. THE Clinical_Intake_Router SHALL identify and structure medications with fields: name, dosage, frequency, indication
5. THE Clinical_Intake_Router SHALL identify and structure chronic conditions with fields: condition_name, diagnosed_date, current_status
6. WHEN no entities of a specific type are found, THE Clinical_Intake_Router SHALL return an empty list for that entity type

### Requirement 4

**User Story:** As a backend developer, I want the system built with LangGraph for stateful processing, so that I can implement retry logic, validation steps, and conditional routing in a production-ready architecture.

#### Acceptance Criteria

1. THE Clinical_Intake_Router SHALL implement a LangGraph workflow with distinct nodes for: input_processing, entity_extraction, triage_classification, validation, and output_formatting
2. THE Clinical_Intake_Router SHALL maintain state across nodes including extracted entities, confidence scores, and retry attempts
3. WHEN validation fails, THE Clinical_Intake_Router SHALL route to a retry node that adjusts the prompt and re-invokes the LLM
4. THE Clinical_Intake_Router SHALL limit retry attempts to 2 iterations before returning a structured error response
5. THE Clinical_Intake_Router SHALL log all state transitions and node executions for debugging and observability

### Requirement 5

**User Story:** As a DevOps engineer, I want the router exposed as a FastAPI REST endpoint with proper error handling, so that multiple applications can integrate with the service reliably.

#### Acceptance Criteria

1. THE Clinical_Intake_Router SHALL expose a POST endpoint at /api/intake/process accepting JSON with an "intake_message" field
2. WHEN a valid request is received, THE Clinical_Intake_Router SHALL return HTTP 200 with the structured output JSON
3. WHEN an invalid request is received, THE Clinical_Intake_Router SHALL return HTTP 422 with validation error details
4. THE Clinical_Intake_Router SHALL implement a 10-second timeout for LLM processing
5. THE Clinical_Intake_Router SHALL expose a GET endpoint at /api/health for service health checks
6. THE Clinical_Intake_Router SHALL log all requests with unique request IDs for tracing

### Requirement 6

**User Story:** As a QA engineer, I want the system validated against a comprehensive test dataset, so that I can verify 100% structured output reliability before production deployment.

#### Acceptance Criteria

1. THE Clinical_Intake_Router SHALL process a test dataset of 50 diverse patient intake messages
2. THE Clinical_Intake_Router SHALL achieve 100% valid JSON output conforming to the Pydantic schema on all 50 test cases
3. THE Clinical_Intake_Router SHALL achieve >= 85% accuracy on triage priority classification compared to expert labels
4. THE Clinical_Intake_Router SHALL achieve >= 80% accuracy on specialty routing compared to expert labels
5. THE Clinical_Intake_Router SHALL complete processing of all 50 test cases within 120 seconds total
6. WHEN a test case fails, THE Clinical_Intake_Router SHALL log the failure with input message, expected output, actual output, and error details

### Requirement 7

**User Story:** As a system administrator, I want the system configurable via environment variables, so that I can deploy to different environments with different LLM providers.

#### Acceptance Criteria

1. THE Clinical_Intake_Router SHALL read LLM_PROVIDER from environment variables (openai, anthropic, groq, grok, fireworks)
2. THE Clinical_Intake_Router SHALL read API keys from environment variables (OPENAI_API_KEY, ANTHROPIC_API_KEY, GROQ_API_KEY, GROK_API_KEY, etc.)
3. THE Clinical_Intake_Router SHALL read MODEL_NAME from environment variables with sensible defaults (gpt-4o, claude-3-5-sonnet, grok-beta)
4. THE Clinical_Intake_Router SHALL read MAX_RETRIES and TIMEOUT_SECONDS from environment variables
5. IF required environment variables are missing, THEN THE Clinical_Intake_Router SHALL fail to start with a clear error message listing missing variables
