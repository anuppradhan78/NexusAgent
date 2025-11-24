# Requirements Document

## Introduction

NeuralECG is a browser-based proof-of-concept application designed to analyze 12-lead ECG data for dialysis patients. The system accepts ECG CSV files, computes comprehensive cardiovascular metrics including cross-correlation matrices and clinical intervals, visualizes the data through interactive charts, and leverages AI (LLM + RAG) to provide plain-English summaries and predictive insights specific to dialysis patient cardiovascular risks. The application integrates Weaviate for vector storage, FriendliAI and OpenAI for language model capabilities, and follows patterns established in the medical-rag-app reference implementation.

## Glossary

- **NeuralECG System**: The complete browser-based application including frontend UI, backend API, and AI integration components
- **ECG Data**: Electrocardiogram time-series data containing 12 standard leads (aVR, aVL, aVF, V1-V6, D1-D3)
- **Lead**: A specific electrical view of the heart's activity (e.g., V1, aVR)
- **Correlation Matrix**: A 12x12 numerical matrix showing correlation coefficients between all pairs of ECG leads
- **Clinical Intervals**: Measured time durations in ECG including PR interval, QRS duration, QT interval, and corrected QT (QTc)
- **Electrical Axis**: The mean direction of electrical activity in the heart's frontal plane, measured in degrees
- **RAG Pipeline**: Retrieval-Augmented Generation system combining vector search (Weaviate) with LLM responses
- **Risk Flags**: Rule-based alerts generated from ECG metrics indicating potential cardiovascular concerns
- **LLM Provider**: The language model service used (OpenAI or FriendliAI)
- **Weaviate Instance**: Vector database storing medical document embeddings for RAG queries
- **Analytics JSON**: Structured data object containing all computed ECG metrics, statistics, and risk flags
- **Dialysis Patient Context**: Patient metadata including dialysis status and duration relevant to cardiovascular risk assessment
- **Opik**: LLM evaluation and observability platform from Comet.com for tracking and analyzing LLM performance
- **Trace**: A recorded execution of an LLM call including inputs, outputs, metadata, and metrics
- **Evaluation Dashboard**: Backend-only web interface for viewing LLM performance metrics and traces

## Requirements

### Requirement 1

**User Story:** As a clinician, I want to upload a 12-lead ECG CSV file, so that I can analyze cardiovascular metrics for my dialysis patients

#### Acceptance Criteria

1. WHEN the user selects a CSV file containing ECG data with columns for time and 12 leads (aVR, aVL, aVF, V1-V6, D1-D3), THE NeuralECG System SHALL accept the file upload via multipart form data
2. WHEN the uploaded CSV file is parsed, THE NeuralECG System SHALL validate that all required lead columns are present
3. IF the uploaded CSV file is missing required columns or contains invalid data, THEN THE NeuralECG System SHALL return an error message specifying which columns are missing or invalid
4. WHEN a valid ECG CSV file is processed, THE NeuralECG System SHALL compute and return the Analytics JSON containing all derived metrics within 5 seconds
5. WHERE the user has not uploaded a file, THE NeuralECG System SHALL provide a "Use Sample ECG" option that loads pre-bundled sample data

### Requirement 2

**User Story:** As a clinician, I want to view a 12-lead correlation matrix heatmap, so that I can understand the relationships between different ECG leads

#### Acceptance Criteria

1. WHEN the ECG data is analyzed, THE NeuralECG System SHALL compute a 12x12 correlation matrix using Pearson correlation coefficients for all lead pairs
2. THE NeuralECG System SHALL display the correlation matrix as a color-coded heatmap with lead labels on both axes
3. WHEN the user hovers over a cell in the correlation heatmap, THE NeuralECG System SHALL display a tooltip showing the exact correlation coefficient value
4. THE NeuralECG System SHALL use a color gradient where values near 1.0 are displayed in green, values near 0 are displayed in yellow, and values near -1.0 are displayed in red
5. THE NeuralECG System SHALL label all matrix axes with the 12 lead names (aVR, aVL, aVF, V1, V2, V3, V4, V5, V6, D1, D2, D3)

### Requirement 3

**User Story:** As a clinician, I want to see overlaid time-series plots of selected ECG leads, so that I can visually compare waveform morphology

#### Acceptance Criteria

1. WHEN the ECG data is analyzed, THE NeuralECG System SHALL select two representative leads (V2 and V5) for overlay visualization
2. THE NeuralECG System SHALL extract a 1-2 second window of data around a detected QRS peak for the overlay plot
3. THE NeuralECG System SHALL display the two selected leads as distinct colored lines (orange and blue) on a shared time axis
4. THE NeuralECG System SHALL label each plotted line with its corresponding lead name
5. THE NeuralECG System SHALL display time in seconds on the x-axis and voltage amplitude on the y-axis

### Requirement 4

**User Story:** As a clinician, I want to see computed ECG intervals and heart rate, so that I can assess basic cardiac function

#### Acceptance Criteria

1. WHEN the ECG data is analyzed, THE NeuralECG System SHALL compute heart rate in beats per minute (BPM) from R-R intervals
2. THE NeuralECG System SHALL compute PR interval duration in milliseconds
3. THE NeuralECG System SHALL compute QRS complex duration in milliseconds
4. THE NeuralECG System SHALL compute QT interval duration in milliseconds
5. THE NeuralECG System SHALL compute corrected QT interval (QTc) in milliseconds using the Bazett formula
6. THE NeuralECG System SHALL display all computed intervals as numeric values with appropriate units

### Requirement 5

**User Story:** As a clinician, I want to see the electrical axis calculation and deviation category, so that I can identify conduction abnormalities

#### Acceptance Criteria

1. WHEN the ECG data is analyzed, THE NeuralECG System SHALL compute the frontal plane electrical axis in degrees using limb lead data
2. THE NeuralECG System SHALL categorize the axis as normal range, left axis deviation, or right axis deviation based on degree thresholds
3. WHERE the computed axis is less than -30 degrees, THE NeuralECG System SHALL classify it as left axis deviation
4. WHERE the computed axis is greater than 90 degrees, THE NeuralECG System SHALL classify it as right axis deviation
5. THE NeuralECG System SHALL display the axis value and category using a radial pie chart with color-coded segments
6. THE NeuralECG System SHALL display an arrow on the radial chart pointing to the measured axis direction

### Requirement 6

**User Story:** As a clinician, I want to see rule-based risk flags for abnormal ECG findings, so that I can quickly identify potential concerns

#### Acceptance Criteria

1. WHEN the computed QTc exceeds 460 milliseconds for female patients or 450 milliseconds for male patients, THE NeuralECG System SHALL generate a "prolonged_qtc" risk flag
2. WHEN the computed QRS duration exceeds 120 milliseconds, THE NeuralECG System SHALL generate a "wide_qrs" risk flag
3. WHEN the computed heart rate exceeds 100 BPM, THE NeuralECG System SHALL generate a "tachycardia" risk flag
4. WHEN the computed heart rate is below 50 BPM, THE NeuralECG System SHALL generate a "bradycardia" risk flag
5. WHEN the electrical axis indicates left or right axis deviation, THE NeuralECG System SHALL generate an appropriate axis deviation risk flag
6. THE NeuralECG System SHALL display each risk flag with a severity level (mild, moderate, severe) and descriptive message
7. THE NeuralECG System SHALL color-code displayed metrics as green for normal, yellow for borderline, and red for abnormal values

### Requirement 7

**User Story:** As a clinician, I want to generate an AI-powered ECG summary, so that I can get plain-English interpretation of the findings

#### Acceptance Criteria

1. WHEN the user clicks the "Generate AI Summary" button, THE NeuralECG System SHALL send the Analytics JSON and patient context to the configured LLM Provider
2. THE NeuralECG System SHALL construct a prompt that includes the ECG metrics, risk flags, and dialysis patient context
3. THE NeuralECG System SHALL request the LLM to provide a 3-5 sentence summary of main findings
4. THE NeuralECG System SHALL request the LLM to list 3-5 potential cardiovascular risks relevant to dialysis patients
5. WHEN the LLM response is received, THE NeuralECG System SHALL display the summary text in a dedicated card on the UI
6. THE NeuralECG System SHALL indicate which LLM Provider (OpenAI or FriendliAI) was used to generate the summary

### Requirement 8

**User Story:** As a clinician, I want to ask questions about ECG findings using RAG, so that I can get evidence-based answers from medical literature

#### Acceptance Criteria

1. WHEN the user enters a question in the RAG query textarea, THE NeuralECG System SHALL construct a search query incorporating the question and relevant ECG metrics
2. THE NeuralECG System SHALL query the Weaviate Instance to retrieve the top 3 most relevant medical document chunks
3. THE NeuralECG System SHALL compose a prompt containing the retrieved document chunks, the user question, and ECG analytics summary
4. THE NeuralECG System SHALL send the composed prompt to the configured LLM Provider
5. WHEN the LLM response is received, THE NeuralECG System SHALL display the answer text along with citation titles and sources
6. IF no relevant documents are found in the Weaviate Instance, THEN THE NeuralECG System SHALL indicate that the answer may not be supported by available literature

### Requirement 9

**User Story:** As a system administrator, I want to configure LLM and vector database connections via environment variables, so that I can deploy the application in different environments

#### Acceptance Criteria

1. THE NeuralECG System SHALL read OPENAI_API_KEY from environment variables for OpenAI authentication
2. THE NeuralECG System SHALL read FRIENDLI_API_KEY and FRIENDLI_BASE_URL from environment variables for FriendliAI configuration
3. THE NeuralECG System SHALL read LLM_PROVIDER from environment variables to determine which LLM service to use (openai or friendli)
4. THE NeuralECG System SHALL read WEAVIATE_SCHEME, WEAVIATE_HOST, and WEAVIATE_API_KEY from environment variables for Weaviate connection
5. THE NeuralECG System SHALL read DOCS_PATH from environment variables to locate medical documents for RAG ingestion
6. THE NeuralECG System SHALL read SAMPLE_ECG_PATH from environment variables to locate the bundled sample ECG file
7. IF required environment variables are missing, THEN THE NeuralECG System SHALL log an error and fail to start with a descriptive message

### Requirement 10

**User Story:** As a system administrator, I want to load medical documents into Weaviate, so that the RAG pipeline can provide evidence-based answers

#### Acceptance Criteria

1. THE NeuralECG System SHALL provide a command-line script for loading medical documents from PDF files
2. WHEN the document loader script is executed, THE NeuralECG System SHALL read all PDF files from the configured DOCS_PATH directory
3. THE NeuralECG System SHALL chunk each PDF document into segments of 500-1000 tokens
4. THE NeuralECG System SHALL generate embeddings for each chunk using the configured LLM Provider embedding endpoint
5. THE NeuralECG System SHALL store each chunk in the Weaviate Instance with properties including title, source, text content, and embedding vector
6. THE NeuralECG System SHALL create a MedicalDoc class in Weaviate if it does not already exist

### Requirement 11

**User Story:** As a clinician, I want to optionally provide patient context like dialysis duration, so that AI summaries are more personalized

#### Acceptance Criteria

1. THE NeuralECG System SHALL provide input fields for optional patient metadata including age and years on dialysis
2. WHEN patient context is provided, THE NeuralECG System SHALL include this information in LLM prompts for summary generation
3. WHEN patient context indicates the patient is on dialysis, THE NeuralECG System SHALL emphasize dialysis-specific cardiovascular risks in the LLM prompt
4. WHERE patient context is not provided, THE NeuralECG System SHALL generate summaries using only the ECG analytics data

### Requirement 12

**User Story:** As a developer, I want the backend to expose RESTful API endpoints, so that the frontend can interact with ECG analysis and AI services

#### Acceptance Criteria

1. THE NeuralECG System SHALL expose a POST endpoint at /api/ecg/analyze that accepts ECG CSV files and returns Analytics JSON
2. THE NeuralECG System SHALL expose a GET endpoint at /api/ecg/sample that returns Analytics JSON for a pre-loaded sample ECG
3. THE NeuralECG System SHALL expose a POST endpoint at /api/ecg/summary that accepts Analytics JSON and patient context and returns an LLM-generated summary
4. THE NeuralECG System SHALL expose a POST endpoint at /api/rag/query that accepts a question and Analytics JSON and returns a RAG-enhanced answer
5. THE NeuralECG System SHALL expose a GET endpoint at /health for service health checks
6. THE NeuralECG System SHALL return appropriate HTTP status codes (200 for success, 400 for bad requests, 500 for server errors)
7. THE NeuralECG System SHALL return all responses in JSON format with appropriate content-type headers

### Requirement 13

**User Story:** As a developer, I want to track and evaluate all LLM interactions, so that I can monitor performance and compare providers

#### Acceptance Criteria

1. WHEN an LLM call is made for ECG summary generation, THE NeuralECG System SHALL log the trace to Opik with input prompt, output text, provider name, and model name
2. WHEN an LLM call is made for RAG query, THE NeuralECG System SHALL log the trace to Opik with question, retrieved context, answer, and citations
3. THE NeuralECG System SHALL automatically capture response time in milliseconds for each LLM call
4. THE NeuralECG System SHALL automatically capture token count (input and output) for each LLM call when available from the provider
5. THE NeuralECG System SHALL tag each trace with the LLM provider used (openai or friendli)
6. THE NeuralECG System SHALL associate each trace with the ECG analysis session using a unique trace ID
7. THE NeuralECG System SHALL handle Opik logging failures gracefully without blocking LLM responses

### Requirement 14

**User Story:** As a developer, I want to view LLM performance metrics in a dashboard, so that I can analyze and optimize the system

#### Acceptance Criteria

1. THE NeuralECG System SHALL provide a backend evaluation dashboard accessible at /dashboard
2. THE NeuralECG System SHALL display total number of LLM calls grouped by provider (OpenAI vs FriendliAI)
3. THE NeuralECG System SHALL display average response time for each provider
4. THE NeuralECG System SHALL display total token usage for each provider
5. THE NeuralECG System SHALL provide a link to the full Opik dashboard on Comet.com for detailed trace analysis
6. THE NeuralECG System SHALL display the most recent 10 traces with timestamp, provider, and response time
7. WHERE Opik is not configured, THE NeuralECG System SHALL display a message indicating evaluation features are disabled

### Requirement 15

**User Story:** As a system administrator, I want to configure Opik integration via environment variables, so that I can enable or disable evaluation features

#### Acceptance Criteria

1. THE NeuralECG System SHALL read OPIK_API_KEY from environment variables for Opik authentication
2. THE NeuralECG System SHALL read OPIK_WORKSPACE from environment variables to specify the Comet workspace
3. THE NeuralECG System SHALL read OPIK_PROJECT_NAME from environment variables to organize traces by project
4. WHERE OPIK_API_KEY is not provided, THE NeuralECG System SHALL disable Opik logging and continue normal operation
5. THE NeuralECG System SHALL log a warning message when Opik is disabled due to missing configuration
