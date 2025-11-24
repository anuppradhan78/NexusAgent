# Design Document - Phase 1: Clinical Intake Router

## Overview

The Clinical Intake Router is a production-grade system demonstrating 2025 best practices for structured output from LLMs. Built with LangGraph for stateful workflows and Instructor/Pydantic for guaranteed valid JSON, the system processes unstructured patient intake messages and extracts structured triage data suitable for EHR integration. The architecture emphasizes reliability, type safety, and observability - core skills for senior GenAI engineers.

## Architecture

### High-Level Architecture

**System Architecture Diagram:**

```text
CLIENT LAYER:
  [Web Interface] [Mobile App] [EHR System]
           |            |            |
           +------------+------------+
                        |
                        v
API LAYER:
                 [FastAPI Server]
                        |
                 [API Key Auth]
                        |
                 [Rate Limiter]
                        |
                        v
LANGGRAPH WORKFLOW:
              [Input Processing] -----> [Logging]
                        |
              [Entity Extraction] <--+
                        |            |
              [Triage Classification]|
                        |            |
              [Validation Node]      |
                   /        \        |
              Valid      Invalid     |
                 |            |      |
            [Output]    [Retry] -----+
                 |
                 v
           [Instructor Library]
                 |
        +--------+--------+
        |        |        |        |
    [OpenAI] [Anthropic] [Groq] [Grok/xAI]
        |        |        |        |
     (GPT-4o) (Claude) (Llama) (Grok-Beta)

OBSERVABILITY:
  [Structured Logging] [Prometheus Metrics]
```

**Component Flow:**
1. Client applications (Web/Mobile/EHR) send requests to FastAPI
2. API layer handles authentication and rate limiting
3. LangGraph workflow processes the intake message through multiple nodes
4. Instructor library ensures structured output from LLM providers
5. Observability layer tracks all operations

### Technology Stack

**Core Framework:**
- Python 3.11+
- LangGraph 0.2+ (stateful workflows)
- Instructor 1.0+ (structured output)
- Pydantic 2.0+ (data validation)
- FastAPI 0.110+ (REST API)

**LLM Providers:**
- OpenAI (gpt-4o, gpt-4o-mini)
- Anthropic (claude-3-5-sonnet, claude-3-haiku)
- Groq (llama-3.1-70b, mixtral-8x7b)
- Grok/xAI (grok-beta, grok-2-latest)
- Fireworks (optional)

**Observability:**
- Python logging (structured JSON logs)
- Prometheus client (metrics)
- OpenTelemetry (optional tracing)

**Development:**
- pytest (testing)
- ruff (linting)
- black (formatting)
- mypy (type checking)

## Components and Interfaces

### 1. FastAPI Server (main.py)

**Purpose**: REST API exposing the intake router as a service

**Endpoints:**

```python
@app.post("/api/intake/process")
async def process_intake(request: IntakeRequest) -> IntakeResponse:
    """
    Process patient intake message and return structured triage data
    
    Request:
        {
            "intake_message": "Patient reports chest pain...",
            "request_id": "optional-uuid"
        }
    
    Response:
        {
            "request_id": "uuid",
            "triage_priority": "emergency",
            "specialty_routing": "cardiology",
            "medical_entities": [...],
            "confidence_score": 0.95,
            "clinical_reasoning": "...",
            "timestamp": "2025-11-18T10:30:00Z",
            "processing_time_ms": 1250
        }
    """

@app.get("/api/health")
async def health_check() -> dict:
    """
    Service health check
    Returns: {"status": "healthy", "llm_provider": "openai", "version": "1.0.0"}
    """

@app.post("/api/intake/batch")
async def process_batch(requests: list[IntakeRequest]) -> list[IntakeResponse]:
    """
    Process multiple intake messages in batch
    Max 10 messages per batch
    """
```

**Middleware:**
- CORS (configurable origins)
- Request ID injection
- Request/response logging
- Error handling with structured responses
- Timeout enforcement (10 seconds per request)

**Authentication:**
```python
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key not in settings.valid_api_keys:
        raise HTTPException(status_code=401, detail="Invalid API key")
```

### 2. LangGraph Workflow (workflow.py)

**Purpose**: Stateful processing graph with retry logic and validation

**Graph Structure:**

```python
from langgraph.graph import StateGraph, END

class IntakeState(TypedDict):
    """State maintained across workflow nodes"""
    intake_message: str
    request_id: str
    
    # Extracted data
    medical_entities: Optional[MedicalEntities]
    triage_priority: Optional[TriagePriority]
    specialty_routing: Optional[Specialty]
    confidence_score: Optional[float]
    clinical_reasoning: Optional[str]
    
    # Workflow control
    retry_count: int
    validation_errors: list[str]
    node_history: list[str]

# Define workflow
workflow = StateGraph(IntakeState)

# Add nodes
workflow.add_node("input_processing", process_input)
workflow.add_node("entity_extraction", extract_entities)
workflow.add_node("triage_classification", classify_triage)
workflow.add_node("validation", validate_output)
workflow.add_node("retry", handle_retry)
workflow.add_node("output_formatting", format_output)

# Define edges
workflow.set_entry_point("input_processing")
workflow.add_edge("input_processing", "entity_extraction")
workflow.add_edge("entity_extraction", "triage_classification")
workflow.add_edge("triage_classification", "validation")

# Conditional routing from validation
workflow.add_conditional_edges(
    "validation",
    should_retry,
    {
        "valid": "output_formatting",
        "retry": "retry",
        "failed": END
    }
)

workflow.add_edge("retry", "entity_extraction")
workflow.add_edge("output_formatting", END)

app = workflow.compile()
```

**Node Implementations:**

```python
def process_input(state: IntakeState) -> IntakeState:
    """
    Validate and preprocess input message
    - Check message length (10-5000 chars)
    - Basic sanitization
    - Initialize state fields
    """
    state["node_history"].append("input_processing")
    state["retry_count"] = 0
    return state

def extract_entities(state: IntakeState) -> IntakeState:
    """
    Extract structured medical entities using Instructor
    - Symptoms with severity, duration, location
    - Vital signs with values and units
    - Medications with dosage and frequency
    - Chronic conditions
    """
    state["node_history"].append("entity_extraction")
    
    # Use Instructor to guarantee structured output
    entities = instructor_client.chat.completions.create(
        model=settings.model_name,
        response_model=MedicalEntities,
        messages=[
            {"role": "system", "content": ENTITY_EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": state["intake_message"]}
        ],
        max_retries=2
    )
    
    state["medical_entities"] = entities
    return state

def classify_triage(state: IntakeState) -> IntakeState:
    """
    Classify triage priority and specialty routing
    Uses extracted entities as context
    """
    state["node_history"].append("triage_classification")
    
    # Build context from extracted entities
    entity_summary = format_entities_for_context(state["medical_entities"])
    
    # Use Instructor for structured classification
    classification = instructor_client.chat.completions.create(
        model=settings.model_name,
        response_model=TriageClassification,
        messages=[
            {"role": "system", "content": TRIAGE_SYSTEM_PROMPT},
            {"role": "user", "content": f"Patient message: {state['intake_message']}\n\nExtracted entities: {entity_summary}"}
        ],
        max_retries=2
    )
    
    state["triage_priority"] = classification.priority
    state["specialty_routing"] = classification.specialty
    state["confidence_score"] = classification.confidence
    state["clinical_reasoning"] = classification.reasoning
    return state

def validate_output(state: IntakeState) -> IntakeState:
    """
    Validate all required fields are present and valid
    Check confidence thresholds
    """
    state["node_history"].append("validation")
    state["validation_errors"] = []
    
    # Check required fields
    if not state.get("medical_entities"):
        state["validation_errors"].append("Missing medical entities")
    if not state.get("triage_priority"):
        state["validation_errors"].append("Missing triage priority")
    if not state.get("specialty_routing"):
        state["validation_errors"].append("Missing specialty routing")
    
    # Check confidence threshold
    if state.get("confidence_score", 0) < 0.3:
        state["validation_errors"].append("Confidence score too low")
    
    return state

def should_retry(state: IntakeState) -> str:
    """
    Determine if retry is needed based on validation
    """
    if not state["validation_errors"]:
        return "valid"
    
    if state["retry_count"] >= 2:
        return "failed"
    
    return "retry"

def handle_retry(state: IntakeState) -> IntakeState:
    """
    Increment retry count and adjust prompts for next attempt
    """
    state["node_history"].append("retry")
    state["retry_count"] += 1
    
    # Log retry reason
    logger.warning(
        f"Retry attempt {state['retry_count']} for request {state['request_id']}",
        extra={"validation_errors": state["validation_errors"]}
    )
    
    return state

def format_output(state: IntakeState) -> IntakeState:
    """
    Format final output with all required fields
    """
    state["node_history"].append("output_formatting")
    return state
```

### 3. Instructor Integration (instructor_client.py)

**Purpose**: Guarantee structured output from LLM APIs using Pydantic schemas

**Configuration:**

```python
import instructor
from openai import OpenAI
from anthropic import Anthropic

# Initialize based on provider
if settings.llm_provider == "openai":
    client = instructor.from_openai(OpenAI(api_key=settings.openai_api_key))
elif settings.llm_provider == "anthropic":
    client = instructor.from_anthropic(Anthropic(api_key=settings.anthropic_api_key))
elif settings.llm_provider == "groq":
    client = instructor.from_openai(
        OpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1"
        )
    )
elif settings.llm_provider == "grok":
    client = instructor.from_openai(
        OpenAI(
            api_key=settings.grok_api_key,
            base_url="https://api.x.ai/v1"
        )
    )
```

**Usage Pattern:**

```python
# Instructor automatically validates and retries
response = client.chat.completions.create(
    model="gpt-4o",
    response_model=MedicalEntities,  # Pydantic model
    messages=[...],
    max_retries=2,  # Automatic retry on validation failure
    validation_context={"strict": True}
)

# response is guaranteed to be a valid MedicalEntities instance
assert isinstance(response, MedicalEntities)
```

### 4. Pydantic Data Models (models.py)

**Purpose**: Define strict schemas for all structured data

**Core Models:**

```python
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from datetime import datetime

class TriagePriority(str, Enum):
    EMERGENCY = "emergency"
    URGENT = "urgent"
    ROUTINE = "routine"
    INFORMATIONAL = "informational"

class Specialty(str, Enum):
    CARDIOLOGY = "cardiology"
    NEPHROLOGY = "nephrology"
    ENDOCRINOLOGY = "endocrinology"
    GENERAL_MEDICINE = "general_medicine"
    MENTAL_HEALTH = "mental_health"

class Severity(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"

class Symptom(BaseModel):
    """Structured symptom with clinical details"""
    name: str = Field(..., description="Symptom name (e.g., 'chest pain', 'shortness of breath')")
    severity: Severity = Field(..., description="Symptom severity")
    duration: Optional[str] = Field(None, description="Duration (e.g., '2 hours', '3 days')")
    body_location: Optional[str] = Field(None, description="Body location if applicable")
    
    @field_validator('name')
    def validate_name(cls, v):
        if len(v) < 2:
            raise ValueError("Symptom name too short")
        return v.lower()

class VitalSign(BaseModel):
    """Structured vital sign measurement"""
    type: str = Field(..., description="Type: blood_pressure, heart_rate, temperature, etc.")
    value: str = Field(..., description="Measured value")
    unit: str = Field(..., description="Unit of measurement")
    timestamp_mentioned: Optional[str] = Field(None, description="When measurement was taken")

class Medication(BaseModel):
    """Structured medication information"""
    name: str = Field(..., description="Medication name")
    dosage: Optional[str] = Field(None, description="Dosage (e.g., '10mg', '2 tablets')")
    frequency: Optional[str] = Field(None, description="Frequency (e.g., 'twice daily', 'as needed')")
    indication: Optional[str] = Field(None, description="Why patient is taking it")

class ChronicCondition(BaseModel):
    """Structured chronic condition"""
    condition_name: str = Field(..., description="Condition name")
    diagnosed_date: Optional[str] = Field(None, description="When diagnosed")
    current_status: Optional[str] = Field(None, description="Current status (controlled, uncontrolled, etc.)")

class MedicalEntities(BaseModel):
    """Complete set of extracted medical entities"""
    symptoms: list[Symptom] = Field(default_factory=list, description="List of symptoms")
    vital_signs: list[VitalSign] = Field(default_factory=list, description="List of vital signs")
    medications: list[Medication] = Field(default_factory=list, description="List of medications")
    chronic_conditions: list[ChronicCondition] = Field(default_factory=list, description="List of chronic conditions")
    temporal_info: Optional[str] = Field(None, description="Timeline information (e.g., 'started yesterday')")

class TriageClassification(BaseModel):
    """Triage priority and routing decision"""
    priority: TriagePriority = Field(..., description="Urgency level")
    specialty: Specialty = Field(..., description="Recommended specialty")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    reasoning: str = Field(..., description="Clinical reasoning for classification")
    
    @field_validator('reasoning')
    def validate_reasoning(cls, v):
        if len(v) < 20:
            raise ValueError("Reasoning too brief")
        return v

class IntakeRequest(BaseModel):
    """API request model"""
    intake_message: str = Field(..., min_length=10, max_length=5000)
    request_id: Optional[str] = Field(None, description="Optional request ID for tracking")

class IntakeResponse(BaseModel):
    """API response model"""
    request_id: str
    triage_priority: TriagePriority
    specialty_routing: Specialty
    medical_entities: MedicalEntities
    confidence_score: float
    clinical_reasoning: str
    timestamp: datetime
    processing_time_ms: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "triage_priority": "urgent",
                "specialty_routing": "cardiology",
                "medical_entities": {
                    "symptoms": [
                        {
                            "name": "chest pain",
                            "severity": "moderate",
                            "duration": "2 hours",
                            "body_location": "left chest"
                        }
                    ],
                    "vital_signs": [],
                    "medications": [],
                    "chronic_conditions": []
                },
                "confidence_score": 0.92,
                "clinical_reasoning": "Patient reports chest pain with moderate severity lasting 2 hours. Given cardiac symptoms, urgent cardiology evaluation recommended.",
                "timestamp": "2025-11-18T10:30:00Z",
                "processing_time_ms": 1250
            }
        }
```

## Data Models

### Prompt Templates

**Entity Extraction System Prompt:**

```python
ENTITY_EXTRACTION_SYSTEM_PROMPT = """You are a medical intake specialist extracting structured information from patient messages.

Extract the following entities:
- Symptoms: Include name, severity (mild/moderate/severe), duration, and body location
- Vital signs: Include type, value, unit, and when measured
- Medications: Include name, dosage, frequency, and indication
- Chronic conditions: Include condition name, when diagnosed, and current status
- Temporal information: Any timeline details

Be thorough but only extract information explicitly mentioned. Do not infer or assume.
If a field is not mentioned, leave it as null."""
```

**Triage Classification System Prompt:**

```python
TRIAGE_SYSTEM_PROMPT = """You are a clinical triage specialist classifying patient intake messages.

Classify into one of these priority levels:
- EMERGENCY: Life-threatening symptoms (chest pain, difficulty breathing, severe bleeding, stroke symptoms)
- URGENT: Serious symptoms requiring same-day attention (high fever, severe pain, concerning lab values)
- ROUTINE: Non-urgent medical concerns (medication refills, follow-up questions, mild symptoms)
- INFORMATIONAL: General questions, appointment scheduling, administrative matters

Route to appropriate specialty:
- CARDIOLOGY: Heart-related symptoms, chest pain, palpitations, hypertension
- NEPHROLOGY: Kidney-related issues, dialysis concerns, electrolyte abnormalities
- ENDOCRINOLOGY: Diabetes, thyroid issues, hormone-related concerns
- GENERAL_MEDICINE: General symptoms, multiple concerns, unclear specialty
- MENTAL_HEALTH: Anxiety, depression, psychiatric concerns

Provide confidence score (0-1) and clinical reasoning for your classification.

CRITICAL: Assign EMERGENCY priority for any life-threatening symptoms with confidence >= 0.9."""
```

## Error Handling

### Error Categories

```python
class IntakeRouterError(Exception):
    """Base exception for intake router"""
    pass

class ValidationError(IntakeRouterError):
    """Raised when output validation fails after retries"""
    pass

class LLMError(IntakeRouterError):
    """Raised when LLM API calls fail"""
    pass

class TimeoutError(IntakeRouterError):
    """Raised when processing exceeds timeout"""
    pass
```

### Error Response Format

```python
class ErrorResponse(BaseModel):
    error_type: str
    message: str
    request_id: str
    timestamp: datetime
    details: Optional[dict] = None

# Example error response
{
    "error_type": "ValidationError",
    "message": "Failed to extract valid structured output after 2 retries",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-11-18T10:30:00Z",
    "details": {
        "validation_errors": ["Missing triage priority", "Confidence score too low"],
        "retry_count": 2
    }
}
```

### Retry Strategy

1. **Automatic Retries (Instructor)**: Up to 2 retries for validation failures
2. **Workflow Retries (LangGraph)**: Up to 2 retries through retry node
3. **Exponential Backoff**: For rate limit errors (1s, 2s, 4s)
4. **Fallback**: Return structured error response after all retries exhausted

## Testing Strategy

### Unit Tests

```python
# test_models.py
def test_symptom_validation():
    """Test Pydantic validation for Symptom model"""
    symptom = Symptom(
        name="Chest Pain",
        severity=Severity.MODERATE,
        duration="2 hours"
    )
    assert symptom.name == "chest pain"  # Lowercase normalization

def test_triage_classification_confidence():
    """Test confidence score validation"""
    with pytest.raises(ValidationError):
        TriageClassification(
            priority=TriagePriority.EMERGENCY,
            specialty=Specialty.CARDIOLOGY,
            confidence=1.5,  # Invalid: > 1.0
            reasoning="Test"
        )

# test_workflow.py
def test_workflow_happy_path():
    """Test complete workflow with valid input"""
    state = {
        "intake_message": "I have chest pain for 2 hours",
        "request_id": "test-123",
        "retry_count": 0,
        "validation_errors": [],
        "node_history": []
    }
    
    result = app.invoke(state)
    
    assert result["triage_priority"] == TriagePriority.EMERGENCY
    assert result["specialty_routing"] == Specialty.CARDIOLOGY
    assert result["confidence_score"] >= 0.9
    assert "output_formatting" in result["node_history"]

def test_workflow_retry_logic():
    """Test retry mechanism on validation failure"""
    # Mock LLM to return invalid data first, then valid
    with patch('instructor_client.chat.completions.create') as mock_llm:
        mock_llm.side_effect = [
            MedicalEntities(symptoms=[]),  # Invalid: empty
            MedicalEntities(symptoms=[Symptom(name="chest pain", severity=Severity.SEVERE)])  # Valid
        ]
        
        state = {"intake_message": "chest pain", "request_id": "test", "retry_count": 0}
        result = app.invoke(state)
        
        assert result["retry_count"] == 1
        assert "retry" in result["node_history"]
```

### Integration Tests

```python
# test_api.py
from fastapi.testclient import TestClient

client = TestClient(app)

def test_process_intake_endpoint():
    """Test /api/intake/process endpoint"""
    response = client.post(
        "/api/intake/process",
        json={"intake_message": "I have severe chest pain for 2 hours"},
        headers={"X-API-Key": "test-key"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["triage_priority"] == "emergency"
    assert data["specialty_routing"] == "cardiology"
    assert data["confidence_score"] >= 0.9

def test_invalid_api_key():
    """Test authentication failure"""
    response = client.post(
        "/api/intake/process",
        json={"intake_message": "test"},
        headers={"X-API-Key": "invalid"}
    )
    
    assert response.status_code == 401

def test_batch_processing():
    """Test batch endpoint"""
    response = client.post(
        "/api/intake/batch",
        json=[
            {"intake_message": "chest pain"},
            {"intake_message": "medication refill"}
        ],
        headers={"X-API-Key": "test-key"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["triage_priority"] == "emergency"
    assert data[1]["triage_priority"] == "routine"
```

### Evaluation Tests

```python
# test_evaluation.py
def test_golden_dataset():
    """Test against 50 labeled examples"""
    golden_dataset = load_golden_dataset("tests/data/golden_50.json")
    
    results = []
    for case in golden_dataset:
        response = process_intake(case["intake_message"])
        results.append({
            "expected": case["expected_priority"],
            "actual": response.triage_priority,
            "correct": case["expected_priority"] == response.triage_priority
        })
    
    accuracy = sum(r["correct"] for r in results) / len(results)
    assert accuracy >= 0.85, f"Accuracy {accuracy} below threshold"
    
    # Test 100% valid JSON
    assert all(isinstance(r, IntakeResponse) for r in results)
```

## Deployment Architecture

### Local Development

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with API keys

# Run
uvicorn main:app --reload --port 8000

# Test
pytest tests/ -v
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Configuration

```bash
# .env.example

# LLM Provider Configuration
LLM_PROVIDER=openai  # openai, anthropic, groq, grok, fireworks
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
GROK_API_KEY=xai-...

# Model Selection
MODEL_NAME=gpt-4o  # gpt-4o, claude-3-5-sonnet, llama-3.1-70b, grok-beta

# API Configuration
API_KEYS=key1,key2,key3  # Comma-separated valid API keys
MAX_RETRIES=2
TIMEOUT_SECONDS=10

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json  # json or text
```

### Production Considerations

1. **Scaling**: Deploy behind load balancer, horizontal scaling with multiple instances
2. **Caching**: Add Redis for caching common intake patterns
3. **Rate Limiting**: Implement per-API-key rate limits
4. **Monitoring**: Prometheus metrics + Grafana dashboards
5. **Alerting**: Alert on high error rates, slow response times
6. **Security**: HTTPS only, API key rotation, input sanitization

## Performance Targets

- **Latency**: p95 < 2000ms for single intake processing
- **Throughput**: 100 requests/minute per instance
- **Accuracy**: >= 85% triage classification accuracy
- **Reliability**: 100% valid JSON output (no parsing errors)
- **Availability**: 99.9% uptime

## Observability

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

# Log with context
logger.info(
    "intake_processed",
    request_id=request_id,
    triage_priority=result.triage_priority,
    confidence=result.confidence_score,
    processing_time_ms=processing_time,
    retry_count=state["retry_count"]
)
```

### Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
intake_requests_total = Counter(
    "intake_requests_total",
    "Total intake requests",
    ["priority", "specialty", "status"]
)

intake_processing_time = Histogram(
    "intake_processing_time_seconds",
    "Time to process intake",
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0]
)

intake_confidence_score = Histogram(
    "intake_confidence_score",
    "Confidence scores",
    buckets=[0.3, 0.5, 0.7, 0.9, 1.0]
)

# Record metrics
intake_requests_total.labels(
    priority=result.triage_priority,
    specialty=result.specialty_routing,
    status="success"
).inc()

intake_processing_time.observe(processing_time)
intake_confidence_score.observe(result.confidence_score)
```

## Future Enhancements

1. **Multi-language Support**: Process intake messages in multiple languages
2. **Voice Input**: Transcribe and process voice messages
3. **Historical Context**: Consider patient history in triage decisions
4. **Active Learning**: Collect feedback to improve classification
5. **Explainability**: Provide detailed reasoning for triage decisions
6. **Integration**: Direct integration with EHR systems via HL7 FHIR
