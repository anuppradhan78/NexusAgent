# Implementation Plan

## Phase 1: MVP (Afternoon Build - Core Proof of Concept)

This phase focuses on getting a working end-to-end demo with minimal features: upload ECG CSV, compute correlation matrix, and display heatmap visualization.

- [x] MVP-1. Set up minimal project structure





  - Create backend directory with main.py, config.py, requirements.txt (FastAPI, pandas, numpy, scipy, pydantic, python-multipart, uvicorn, python-dotenv)
  - Create frontend directory with React app (using Vite for speed)
  - Copy .env file from C:\Users\anupp\Documents\dev\medical-rag-app\.env to backend/.env (contains WEAVIATE_URL, WEAVIATE_API_KEY, FRIENDLI_TOKEN, OPENAI_API_KEY)
  - Add SAMPLE_ECG_PATH=../data/sample_ecg.csv to .env file
  - Create .env.example with placeholder values for documentation
  - Add simple sample ECG CSV file in data/sample_ecg.csv with 12-lead data (can use synthetic or simplified data)
  - Note: For Phase 4 (RAG), create a new Weaviate sandbox cluster at https://console.weaviate.cloud and update WEAVIATE_URL and WEAVIATE_API_KEY
  - _Requirements: 1.1, 9.6_

- [x] MVP-2. Implement basic ECG correlation analysis





  - Create ecg_engine.py with CSV parsing and column validation
  - Implement compute_correlation_matrix function using numpy corrcoef
  - Create minimal AnalyticsJSON response with just correlation data
  - _Requirements: 1.2, 2.1_

- [x] MVP-3. Create minimal backend API





  - Set up FastAPI app with CORS for localhost:5173 (Vite default)
  - Implement POST /api/ecg/analyze endpoint (accept CSV, return correlation matrix)
  - Implement GET /api/ecg/sample endpoint (load sample CSV, return correlation matrix)
  - Implement GET /health endpoint
  - _Requirements: 1.1, 1.5, 12.1, 12.2, 12.5_

- [x] MVP-4. Create minimal frontend with upload and heatmap





  - Initialize React app with Vite
  - Install recharts or react-chartjs-2 for heatmap
  - Create simple single-page layout with upload button and "Use Sample" button
  - Implement file upload that calls /api/ecg/analyze
  - Display 12x12 correlation heatmap with color gradient and lead labels
  - Add basic error handling and loading states
  - _Requirements: 1.1, 1.5, 2.1, 2.2, 2.5_

- [x] MVP-5. Test end-to-end flow





  - Start backend (uvicorn main:app --reload)
  - Start frontend (npm run dev)
  - Test sample ECG button - verify heatmap displays
  - Test CSV upload with valid file - verify heatmap updates
  - Test error cases (invalid file, missing columns)
  - _Requirements: 1.1, 1.3, 1.4_

**MVP Complete! You now have a working ECG analyzer with visualization. Proceed to Phase 2 to add clinical metrics.**

---

## Phase 2: Clinical Metrics (Add ECG Intervals & Axis)

- [x] 2A. Extend ECG engine with interval calculations





  - Implement peak detection and HR/PR/QRS/QT/QTc calculations
  - Implement electrical axis calculation
  - Implement risk flag generation
  - Update AnalyticsJSON to include intervals, axis, and risk_flags
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 6.1-6.6_

- [x] 2B. Add time-series overlay to analytics





  - Implement extract_overlay_window function for V2 and V5 leads
  - Add time_series_overlay to AnalyticsJSON response
  - _Requirements: 3.1, 3.2_

- [x] 2C. Create insights panel in frontend





  - Add metric tiles component (HR, PR, QRS, QT, QTc, Axis) with color coding
  - Add axis radial chart component
  - Add risk flags list component
  - Add lead overlay chart component
  - _Requirements: 3.3, 3.4, 4.6, 5.5, 5.6, 6.6, 6.7_

**Phase 2 Complete! You now have comprehensive ECG analysis with clinical metrics.**

---

## Phase 3: AI Integration (Add LLM Summary)

- [x] 3A. Set up LLM client





  - Add OpenAI/FriendliAI configuration to .env
  - Create llm_client.py with provider abstraction
  - Implement call_llm method and prompt templates
  - _Requirements: 7.2, 7.3, 9.1, 9.2, 9.3_

- [x] 3B. Create summary API endpoint





  - Create POST /api/ecg/summary endpoint
  - Implement summary generation with patient context support
  - _Requirements: 7.1, 7.4, 7.5, 7.6, 11.2, 11.3, 12.3_

- [x] 3C. Add AI summary card to frontend





  - Create summary card component with "Generate Summary" button
  - Add patient context input fields (age, years on dialysis)
  - Add LLM provider selector
  - Display generated summary with model attribution
  - _Requirements: 7.5, 7.6, 11.1, 11.2_

**Phase 3 Complete! You now have AI-powered ECG interpretation.**

---

## Phase 4: RAG Integration (Add Medical Literature Q&A)

- [x] 4A. Set up Weaviate and document loader




  - Create a new Weaviate sandbox cluster at https://console.weaviate.cloud (free tier, select region)
  - Update .env with new WEAVIATE_URL and WEAVIATE_API_KEY from the new cluster
  - Install weaviate-client in requirements.txt
  - Create rag_service.py with Weaviate client setup and MedicalDoc schema
  - Create load_docs.py script for PDF ingestion (install PyPDF2 or pdfplumber)
  - Add a few sample medical PDFs to data/medical_docs directory (dialysis cardiovascular guidelines, QT prolongation in ESRD, etc.)
  - Run load_docs.py to ingest documents into Weaviate
  - _Requirements: 9.4, 9.5, 10.1-10.6_

- [x] 4B. Create RAG query endpoint






  - Implement RAG query logic in rag_service.py
  - Create POST /api/rag/query endpoint
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 12.4_

- [x] 4C. Add RAG query card to frontend






  - Create Q&A card component with textarea and button
  - Display answers with citations
  - _Requirements: 8.5_

**Phase 4 Complete! Full NeuralECG application with RAG-enhanced Q&A.**

---

## Phase 5: Opik Integration (LLM Evaluation & Observability)

- [x] 5A. Set up Opik configuration and client





  - Add Opik environment variables to .env (OPIK_API_KEY, OPIK_WORKSPACE, OPIK_PROJECT_NAME)
  - Install opik package in requirements.txt
  - Create opik_tracker.py with OpikTracker class
  - Initialize Opik client with graceful fallback if not configured
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [x] 5B. Instrument LLM client with Opik tracking





  - Add tracking decorator to LLM client call_llm method
  - Capture input prompts, output text, provider, model name
  - Measure and log response time in milliseconds
  - Extract and log token counts from LLM responses
  - Tag traces with provider (openai/friendli) and trace type (summary/rag)
  - Handle Opik logging failures gracefully without blocking responses
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7_

- [x] 5C. Create evaluation dashboard backend





  - Create dashboard.py with HTML template for metrics display
  - Implement GET /dashboard endpoint serving HTML page
  - Implement GET /api/evaluation/metrics endpoint returning JSON metrics
  - Fetch aggregated metrics from Opik (total calls, avg response time, token usage by provider)
  - Display recent 10 traces with timestamp, provider, and response time
  - Add link to full Opik dashboard on Comet.com
  - Handle case when Opik is not configured (show disabled message)
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7_

- [x] 5D. Test Opik integration end-to-end










  - Generate ECG summary with OpenAI and verify trace appears in Opik
  - Generate ECG summary with FriendliAI and verify trace appears in Opik
  - Perform RAG query and verify trace with retrieved context
  - Access /dashboard endpoint and verify metrics display correctly
  - Test with Opik disabled (no API key) and verify graceful degradation
  - Verify traces visible in Comet.com Opik dashboard
  - _Requirements: 13.1, 13.2, 14.1_

**Phase 5 Complete! LLM evaluation and observability integrated.**

---

## Phase 6: Polish & Testing (Optional)

- [ ]* 6A. Add comprehensive unit tests
  - Write tests for ECG engine functions
  - Write tests for LLM client with mocked responses
  - Write tests for RAG service
  - _Requirements: 1.2, 2.1, 4.1, 5.1, 6.1, 8.2_

- [ ]* 6B. Add API integration tests
  - Test all endpoints with FastAPI TestClient
  - Test error handling paths
  - Verify response schemas
  - _Requirements: 12.1-12.7_

- [x] 6C. Create comprehensive README





  - Document all prerequisites and setup steps
  - Add usage instructions for all features
  - Include troubleshooting guide
  - _Requirements: 9.1-9.6, 10.1_

---

## Original Full Task List (Reference)

Below is the complete detailed task breakdown for reference. The phased approach above covers all these tasks in a more incremental manner.

- [ ] 1. Set up project structure and configuration
  - Create backend directory with FastAPI application structure (main.py, config.py, requirements.txt)
  - Create frontend directory with React application structure
  - Set up .env.example file with all required environment variables (OPENAI_API_KEY, FRIENDLI_API_KEY, WEAVIATE_HOST, etc.)
  - Create .gitignore to exclude .env, venv, node_modules, and build artifacts
  - Add sample ECG CSV file in data/sample_ecg.csv with 12-lead data
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

- [ ] 2. Implement backend configuration and health check
  - [ ] 2.1 Create config.py with pydantic Settings class
    - Define all environment variables (LLM keys, Weaviate connection, paths)
    - Implement .env file loading using pydantic BaseSettings
    - Add validation for required environment variables
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_
  
  - [ ] 2.2 Create main.py with FastAPI app and health endpoint
    - Initialize FastAPI application with CORS middleware
    - Configure CORS to allow localhost:3000 origin
    - Implement GET /health endpoint returning service status
    - _Requirements: 12.5, 12.6_

- [ ] 3. Implement ECG analytics engine
  - [ ] 3.1 Create ecg_engine.py with data validation
    - Implement CSV parsing function that validates required columns (time, aVR, aVL, aVF, V1-V6, D1-D3)
    - Create AnalyticsJSON pydantic model matching the schema
    - Implement column name normalization (case-insensitive)
    - _Requirements: 1.2, 1.3_
  
  - [ ] 3.2 Implement correlation matrix computation
    - Use numpy corrcoef to compute 12x12 correlation matrix across all leads
    - Return matrix as nested list with lead labels
    - Verify matrix is symmetric with diagonal values of 1.0
    - _Requirements: 2.1, 2.5_
  
  - [ ] 3.3 Implement peak detection and interval calculations
    - Use scipy.signal.find_peaks to detect R peaks in a chosen lead (V2)
    - Compute heart rate from R-R intervals
    - Estimate PR, QRS, QT intervals using fixed offsets from R peaks (POC-level)
    - Calculate QTc using Bazett formula (QT / sqrt(RR))
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ] 3.4 Implement electrical axis calculation
    - Extract lead I (D1) and aVF values at R peak
    - Calculate frontal plane axis using arctan2(aVF, lead_I) * 180 / pi
    - Classify axis as normal (-30° to 90°), left deviation (< -30°), or right deviation (> 90°)
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  
  - [ ] 3.5 Implement risk flag generation
    - Check QTc thresholds (> 450ms male, > 460ms female) for prolonged_qtc flag
    - Check QRS duration (> 120ms) for wide_qrs flag
    - Check heart rate (> 100 BPM for tachycardia, < 50 BPM for bradycardia)
    - Check axis deviation thresholds for axis flags
    - Return list of risk flags with severity and message
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
  
  - [ ] 3.6 Implement time-series overlay extraction
    - Select V2 and V5 leads for overlay visualization
    - Extract 1-2 second window around detected QRS peak
    - Return time array and values for both leads
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [ ] 3.7 Implement lead statistics computation
    - Calculate mean, std, max, min for each of the 12 leads
    - Return as dictionary keyed by lead name
    - _Requirements: 1.4_

- [ ] 4. Implement ECG analysis API endpoints
  - [ ] 4.1 Create POST /api/ecg/analyze endpoint
    - Accept multipart/form-data file upload
    - Parse CSV file into pandas DataFrame
    - Call ECG analytics engine with DataFrame
    - Return Analytics JSON with 200 status code
    - Handle validation errors with 400 status and descriptive message
    - Handle processing errors with 500 status
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 12.1, 12.6, 12.7_
  
  - [ ] 4.2 Create GET /api/ecg/sample endpoint
    - Load sample ECG CSV from configured SAMPLE_ECG_PATH
    - Call ECG analytics engine with sample data
    - Return Analytics JSON with 200 status code
    - _Requirements: 1.5, 12.2, 12.6, 12.7_

- [ ] 5. Implement LLM client wrapper
  - [ ] 5.1 Create llm_client.py with provider abstraction
    - Implement LLMClient class with provider selection (openai or friendli)
    - Configure OpenAI client with API key from environment
    - Configure FriendliAI client using OpenAI client with custom base_url
    - Implement call_llm method that accepts system and user prompts
    - Return response text and model name used
    - _Requirements: 9.1, 9.2, 9.3, 7.6_
  
  - [ ] 5.2 Create prompt templates for ECG summary
    - Define SUMMARY_SYSTEM_PROMPT for cardiology assistant role
    - Define SUMMARY_USER_PROMPT_TEMPLATE with placeholders for analytics and patient context
    - Implement function to format analytics JSON into concise text summary for prompt
    - _Requirements: 7.2, 7.3, 7.4_
  
  - [ ] 5.3 Implement embedding generation method
    - Add get_embedding method to LLMClient for document ingestion
    - Use OpenAI embeddings API (text-embedding-ada-002 or similar)
    - Support both OpenAI and FriendliAI embedding endpoints
    - _Requirements: 10.4_

- [ ] 6. Implement ECG summary API endpoint
  - [ ] 6.1 Create pydantic models for summary request/response
    - Define SummaryRequest with analytics dict and optional patient_context
    - Define SummaryResponse with summary_text and model_used
    - _Requirements: 7.1, 11.2_
  
  - [ ] 6.2 Create POST /api/ecg/summary endpoint
    - Accept SummaryRequest with analytics and patient context
    - Format analytics and context into LLM prompt using templates
    - Call LLM client with formatted prompt
    - Return SummaryResponse with generated text and model name
    - Handle LLM errors with appropriate status codes and messages
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 11.2, 11.3, 12.3, 12.6, 12.7_

- [ ] 7. Implement Weaviate integration and RAG service
  - [ ] 7.1 Create rag_service.py with Weaviate client setup
    - Initialize Weaviate client using environment variables (scheme, host, API key)
    - Define MedicalDoc schema with properties (title, source, text_chunk, chunk_index)
    - Implement function to create schema if it doesn't exist
    - _Requirements: 9.4, 9.5, 10.6_
  
  - [ ] 7.2 Implement RAG query logic
    - Create RAGService class with query method
    - Implement construct_search_query to combine user question with key ECG findings
    - Query Weaviate for top 3 most relevant document chunks using vector search
    - Compose RAG prompt with retrieved chunks, analytics summary, and user question
    - Call LLM client with composed prompt
    - Return answer text with citations (title, source)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_
  
  - [ ] 7.3 Create POST /api/rag/query endpoint
    - Define RAGQueryRequest pydantic model (question, analytics)
    - Define RAGQueryResponse pydantic model (answer, citations, model_used)
    - Implement endpoint that calls RAG service
    - Handle Weaviate connection errors with 500 status
    - Handle empty results gracefully with note in response
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 12.4, 12.6, 12.7_

- [ ] 8. Implement document loader script
  - [ ] 8.1 Create load_docs.py CLI script
    - Accept --docs-path argument for PDF directory location
    - Read all PDF files from specified directory using PyPDF2 or pdfplumber
    - Extract text content from each PDF
    - _Requirements: 10.1, 10.2_
  
  - [ ] 8.2 Implement document chunking and embedding
    - Chunk extracted text into 500-1000 token segments at paragraph boundaries
    - Generate embeddings for each chunk using LLM client
    - Store chunks in Weaviate with metadata (title, source, text, embedding)
    - Log progress and completion status
    - _Requirements: 10.3, 10.4, 10.5_

- [ ] 9. Create frontend React application structure
  - [ ] 9.1 Initialize React app and install dependencies
    - Create React app using create-react-app or Vite
    - Install chart library (react-chartjs-2 or recharts)
    - Install Tailwind CSS for styling
    - Install axios or configure fetch for API calls
    - _Requirements: 1.1, 2.1, 3.1, 4.1_
  
  - [ ] 9.2 Create main layout component
    - Implement three-panel layout (left: upload, middle: visualizations, right: insights)
    - Set up state management for analytics data, loading states, and errors
    - Implement error toast/alert component for displaying API errors
    - _Requirements: 1.1, 1.3_

- [ ] 10. Implement upload panel component
  - [ ] 10.1 Create file upload UI
    - Add file input button for CSV upload
    - Add "Use Sample ECG" button
    - Implement file validation (CSV type, max 10MB size)
    - Display upload progress or loading indicator
    - _Requirements: 1.1, 1.5_
  
  - [ ] 10.2 Implement API calls for ECG analysis
    - Create function to POST file to /api/ecg/analyze endpoint
    - Create function to GET /api/ecg/sample endpoint
    - Handle successful responses by updating analytics state
    - Handle errors by displaying user-friendly messages
    - _Requirements: 1.1, 1.3, 1.4, 1.5_
  
  - [ ] 10.3 Create patient context input fields
    - Add optional input fields for age and years on dialysis
    - Add LLM provider dropdown (OpenAI / FriendliAI)
    - Store values in component state for use in summary requests
    - _Requirements: 11.1, 11.2_

- [ ] 11. Implement visualization panel components
  - [ ] 11.1 Create correlation heatmap component
    - Render 12x12 grid using chart library with color scale (red → yellow → green)
    - Label axes with 12 lead names (aVR, aVL, aVF, V1-V6, D1-D3)
    - Implement tooltip on hover showing exact correlation coefficient
    - Use correlation matrix data from analytics prop
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  
  - [ ] 11.2 Create lead overlay chart component
    - Render dual-line chart with V2 (orange) and V5 (blue) leads
    - Use time-series overlay data from analytics prop
    - Add legend identifying each lead by color
    - Label axes (time in seconds, voltage amplitude)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 12. Implement insights panel components
  - [ ] 12.1 Create metric tiles component
    - Display HR, PR, QRS, QT, QTc, and Axis values in grid layout
    - Color-code each tile (green for normal, yellow for borderline, red for abnormal)
    - Use intervals data from analytics prop
    - Add units to each metric (BPM, ms, degrees)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 6.7_
  
  - [ ] 12.2 Create axis radial chart component
    - Render pie/radial chart showing axis deviation zones
    - Color-code segments (green for normal, yellow/red for deviations)
    - Display arrow pointing to measured axis direction
    - Use axis data from analytics prop
    - _Requirements: 5.2, 5.5, 5.6_
  
  - [ ] 12.3 Create risk flags list component
    - Display risk flags as bullet list with severity badges
    - Color-code severity (mild: yellow, moderate: orange, severe: red)
    - Show descriptive message for each flag
    - Use risk_flags array from analytics prop
    - _Requirements: 6.6, 6.7_
  
  - [ ] 12.4 Create AI summary card component
    - Add "Generate AI Summary" button
    - Implement POST request to /api/ecg/summary with analytics and patient context
    - Display returned summary text in card
    - Show which model was used (OpenAI or FriendliAI)
    - Display loading indicator while waiting for response
    - _Requirements: 7.1, 7.5, 7.6, 11.2, 11.3_
  
  - [ ] 12.5 Create RAG query card component
    - Add textarea for user to enter questions
    - Add "Ask Question" button
    - Implement POST request to /api/rag/query with question and analytics
    - Display answer text and citations list
    - Show loading indicator while waiting for response
    - _Requirements: 8.1, 8.4, 8.5_

- [ ] 13. Wire all components together and test end-to-end flow
  - Connect upload panel to visualization and insights panels via shared state
  - Ensure analytics data flows correctly from API to all display components
  - Test complete user flow: upload → visualize → generate summary → ask question
  - Verify all charts render correctly with sample data
  - Test error handling for invalid uploads and API failures
  - _Requirements: 1.1, 1.4, 1.5_

- [ ]* 14. Create unit tests for backend components
  - Write tests for ECG engine functions (correlation, intervals, axis, risk flags)
  - Write tests for LLM client with mocked API responses
  - Write tests for RAG service with mocked Weaviate responses
  - Verify all test cases pass
  - _Requirements: 1.2, 2.1, 4.1, 5.1, 6.1, 8.2_

- [ ]* 15. Create API integration tests
  - Write tests for all API endpoints using FastAPI TestClient
  - Test /api/ecg/analyze with valid and invalid CSV files
  - Test /api/ecg/sample endpoint
  - Test /api/ecg/summary endpoint with various analytics inputs
  - Test /api/rag/query endpoint
  - Verify response schemas match pydantic models
  - Test error handling paths (400, 500 status codes)
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7_

- [ ] 16. Create README with setup and usage instructions
  - Document prerequisites (Python 3.9+, Node.js 16+, API keys)
  - Provide step-by-step backend setup instructions (venv, pip install, .env configuration)
  - Provide step-by-step frontend setup instructions (npm install, npm run dev)
  - Document how to run document loader script
  - Include example .env file with placeholder values
  - Add usage instructions for uploading ECG files and using features
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 10.1_
