# Strategy Builder Data Flow Diagrams

This document contains Mermaid diagrams illustrating critical workflows in the Strategy Builder system.

## Table of Contents
1. [Code Generation Flow](#code-generation-flow)
2. [Quick Test Execution Flow](#quick-test-execution-flow)
3. [Session Auto-Save Flow](#session-auto-save-flow)
4. [Logic Flow Validation Flow](#logic-flow-validation-flow)
5. [Overall System Architecture](#overall-system-architecture)

---

## Code Generation Flow

This flow shows how visual logic flows are converted to executable Python code.

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant CodeGeneratorService
    participant ValidationService
    participant BuilderService
    participant CodeGenerationRepo
    participant Database

    Client->>API: POST /generate-code
    Note over Client,API: {instance_id, logic_flow, parameters}

    API->>CodeGeneratorService: generate_code()

    %% Step 1: Validate Logic Flow
    CodeGeneratorService->>BuilderService: validate_logic_flow()
    BuilderService->>BuilderService: check_schema()
    BuilderService->>BuilderService: detect_circular_dependency()
    BuilderService->>BuilderService: validate_port_types()

    alt Logic Flow Invalid
        BuilderService-->>CodeGeneratorService: ValidationError
        CodeGeneratorService-->>API: ValidationError
        API-->>Client: 422 Unprocessable Entity
    end

    %% Step 2: Topological Sort
    BuilderService->>BuilderService: topological_sort_nodes()
    BuilderService-->>CodeGeneratorService: sorted_nodes

    %% Step 3: Generate Code for Each Node
    loop For each node (in topological order)
        CodeGeneratorService->>CodeGeneratorService: generate_node_code()
        CodeGeneratorService->>CodeGeneratorService: render_template()
        Note over CodeGeneratorService: Use Jinja2 templates
    end

    %% Step 4: Combine Code
    CodeGeneratorService->>CodeGeneratorService: combine_node_code()
    Note over CodeGeneratorService: Create complete strategy class

    %% Step 5: Calculate Hash
    CodeGeneratorService->>CodeGeneratorService: calculate_code_hash()
    Note over CodeGeneratorService: SHA-256 hash for deduplication

    %% Step 6: Check Duplicate
    CodeGeneratorService->>CodeGenerationRepo: get_by_code_hash()
    CodeGenerationRepo->>Database: SELECT WHERE code_hash=...

    alt Code Duplicate Found
        Database-->>CodeGenerationRepo: Existing record
        CodeGenerationRepo-->>CodeGeneratorService: CodeGeneration
        CodeGeneratorService-->>API: Existing CodeGeneration
        API-->>Client: 200 OK (duplicate)
        Note over Client: Show "Duplicate of previous generation"
    else No Duplicate
        %% Step 7: Validate Code
        CodeGeneratorService->>ValidationService: validate_code()
        ValidationService->>ValidationService: validate_syntax()
        ValidationService->>ValidationService: validate_security()
        ValidationService->>ValidationService: analyze_imports()
        ValidationService->>ValidationService: calculate_complexity()
        ValidationService-->>CodeGeneratorService: ValidationResult

        %% Step 8: Store Code Generation
        CodeGeneratorService->>CodeGenerationRepo: create()
        CodeGenerationRepo->>Database: INSERT INTO code_generations
        Database-->>CodeGenerationRepo: Created record
        CodeGenerationRepo-->>CodeGeneratorService: CodeGeneration

        CodeGeneratorService-->>API: CodeGeneration
        API-->>Client: 200 OK
        Note over Client: Display generated code
    end
```

---

## Quick Test Execution Flow

This flow demonstrates asynchronous quick backtest execution with background task queue.

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant QuickTestService
    participant QuickTestRepo
    participant TaskQueue
    participant BackgroundWorker
    participant BacktestService
    participant Database

    %% Submit Quick Test
    Client->>API: POST /quick-test
    Note over Client,API: {instance_id, test_config}

    API->>QuickTestService: execute_quick_test()

    %% Validate Instance Exists
    QuickTestService->>Database: Get strategy instance
    alt Instance Not Found
        Database-->>QuickTestService: NULL
        QuickTestService-->>API: ResourceNotFoundError
        API-->>Client: 404 Not Found
    end

    %% Create Quick Test Record
    QuickTestService->>QuickTestRepo: create()
    Note over QuickTestRepo: status=PENDING, snapshot logic_flow
    QuickTestRepo->>Database: INSERT INTO quick_tests
    Database-->>QuickTestRepo: Created record
    QuickTestRepo-->>QuickTestService: QuickTest (id=test_123)

    %% Submit to Task Queue
    QuickTestService->>TaskQueue: submit_task()
    Note over TaskQueue: task_type="quick_test_execution"<br/>task_data={"test_id": "test_123"}
    TaskQueue-->>QuickTestService: Task queued

    %% Return Immediately
    QuickTestService-->>API: QuickTest (status=PENDING)
    API-->>Client: 202 Accepted
    Note over Client: Display "Test queued..."<br/>Start polling for results

    %% Background Execution (Async)
    Note over TaskQueue,BackgroundWorker: Asynchronous Execution

    TaskQueue->>BackgroundWorker: Dequeue task
    BackgroundWorker->>QuickTestService: execute_quick_test_worker()

    %% Update Status to RUNNING
    QuickTestService->>QuickTestRepo: update_status(RUNNING)
    QuickTestRepo->>Database: UPDATE status=RUNNING, started_at=NOW()

    %% Execute Backtest
    QuickTestService->>BacktestService: execute_backtest()
    Note over BacktestService: Run backtest with simplified config
    BacktestService->>BacktestService: calculate_metrics()

    alt Backtest Success
        BacktestService-->>QuickTestService: BacktestResult

        %% Extract Metrics
        QuickTestService->>QuickTestService: extract_metrics_summary()

        %% Complete Test
        QuickTestService->>QuickTestRepo: complete_quick_test()
        QuickTestRepo->>Database: UPDATE status=COMPLETED, metrics=..., completed_at=NOW()
    else Backtest Failure
        BacktestService-->>QuickTestService: ExecutionError

        %% Mark as Failed
        QuickTestService->>QuickTestRepo: update_status(FAILED, error_message)
        QuickTestRepo->>Database: UPDATE status=FAILED, error_message=...
    end

    %% Client Polling
    loop Client polls every 2 seconds
        Client->>API: GET /quick-test/{test_id}
        API->>QuickTestService: get_quick_test_result()
        QuickTestService->>QuickTestRepo: get()
        QuickTestRepo->>Database: SELECT FROM quick_tests
        Database-->>QuickTestRepo: QuickTest
        QuickTestRepo-->>QuickTestService: QuickTest
        QuickTestService-->>API: QuickTest
        API-->>Client: QuickTest

        alt Test Completed
            Note over Client: Display results<br/>Stop polling
        else Test Still Running
            Note over Client: Show progress<br/>Continue polling
        end
    end
```

---

## Session Auto-Save Flow

This flow shows how user sessions are automatically saved to prevent data loss.

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant BuilderService
    participant BuilderSessionRepo
    participant Database

    Note over Client: User edits logic flow

    %% Client-Side Debouncing
    Client->>Client: Detect user edit
    Client->>Client: Start debounce timer (2s)
    Note over Client: Wait for edit pause...

    alt User continues editing
        Client->>Client: Reset debounce timer
        Note over Client: Wait again...
    end

    %% After 2 seconds of inactivity
    Client->>Client: Debounce timer expires
    Client->>Client: Start auto-save

    %% Send Auto-Save Request
    Client->>API: POST /sessions
    Note over Client,API: {instance_id, draft_logic_flow,<br/>draft_parameters, draft_metadata}

    API->>BuilderService: create_or_update_session()

    %% Check for Existing Session
    BuilderService->>BuilderSessionRepo: get_active_by_instance_and_user()
    BuilderSessionRepo->>Database: SELECT FROM builder_sessions<br/>WHERE instance_id=... AND user_id=...<br/>AND is_active=true

    alt Session Exists
        Database-->>BuilderSessionRepo: Existing session
        BuilderSessionRepo-->>BuilderService: BuilderSession (id=sess_123)

        %% Update Existing Session
        BuilderService->>BuilderSessionRepo: update_activity()
        Note over BuilderSessionRepo: Update draft_logic_flow,<br/>draft_parameters,<br/>last_activity_at=NOW()
        BuilderSessionRepo->>Database: UPDATE builder_sessions<br/>SET ... WHERE id=sess_123
        Database-->>BuilderSessionRepo: Updated record
        BuilderSessionRepo-->>BuilderService: BuilderSession

    else No Session Exists
        %% Create New Session
        BuilderService->>BuilderSessionRepo: create()
        Note over BuilderSessionRepo: instance_id, user_id,<br/>draft_logic_flow,<br/>expires_at=NOW()+24h
        BuilderSessionRepo->>Database: INSERT INTO builder_sessions
        Database-->>BuilderSessionRepo: Created record
        BuilderSessionRepo-->>BuilderService: BuilderSession
    end

    BuilderService-->>API: BuilderSession
    API-->>Client: 200 OK
    Note over Client: Show "Saved at HH:MM:SS"

    %% Background Cleanup (Separate Process)
    Note over Database: Background Cleanup Task<br/>(Runs hourly via cron)

    loop Every hour
        Note over BuilderService: cleanup_expired_sessions()
        BuilderService->>BuilderSessionRepo: get_expired_sessions(24h)
        BuilderSessionRepo->>Database: SELECT FROM builder_sessions<br/>WHERE last_activity_at < NOW()-24h
        Database-->>BuilderSessionRepo: Expired sessions

        loop For each expired session
            BuilderService->>BuilderSessionRepo: delete(session_id)
            BuilderSessionRepo->>Database: UPDATE is_deleted=true
        end
    end
```

---

## Logic Flow Validation Flow

This flow illustrates multi-layer validation of logic flows before code generation.

```mermaid
flowchart TD
    Start([User submits logic flow]) --> SchemaValidation{Schema<br/>Valid?}

    SchemaValidation -->|No| SchemaError[Return Schema Error]
    SchemaError --> End([Return 422])

    SchemaValidation -->|Yes| GraphValidation{Graph<br/>Valid?}

    GraphValidation --> CheckCycles{Circular<br/>Dependency?}
    CheckCycles -->|Yes| CycleError[Return Cycle Error]
    CycleError --> End

    CheckCycles -->|No| CheckDisconnected{Disconnected<br/>Nodes?}
    CheckDisconnected -->|Yes| DisconnectedWarning[Add Warning]
    DisconnectedWarning --> TypeValidation

    CheckDisconnected -->|No| TypeValidation{Port Types<br/>Compatible?}

    TypeValidation -->|No| TypeError[Return Type Error]
    TypeError --> End

    TypeValidation -->|Yes| ParameterValidation{Parameters<br/>Valid?}

    ParameterValidation --> JSONSchema[Validate with JSON Schema]
    JSONSchema -->|Invalid| ParamError[Return Parameter Error]
    ParamError --> End

    JSONSchema -->|Valid| SemanticValidation{Semantic<br/>Rules OK?}

    SemanticValidation --> CheckSignalOrder{Signal before<br/>Position?}
    CheckSignalOrder -->|No| SemanticWarning[Add Warning]
    SemanticWarning --> Success

    CheckSignalOrder -->|Yes| CheckComplete{All Required<br/>Nodes Present?}
    CheckComplete -->|No| CompletenessWarning[Add Warning]
    CompletenessWarning --> Success

    CheckComplete -->|Yes| Success[Return Success]
    Success --> CodeGen([Proceed to Code Generation])

    style SchemaError fill:#ff6b6b
    style CycleError fill:#ff6b6b
    style TypeError fill:#ff6b6b
    style ParamError fill:#ff6b6b
    style DisconnectedWarning fill:#ffd93d
    style SemanticWarning fill:#ffd93d
    style CompletenessWarning fill:#ffd93d
    style Success fill:#51cf66
```

---

## Overall System Architecture

This diagram shows how Strategy Builder integrates with other modules.

```mermaid
graph TB
    subgraph Client["Client (React)"]
        UI[Strategy Builder UI]
        FlowEditor[Visual Flow Editor]
        CodeViewer[Code Viewer]
    end

    subgraph StrategyBuilderAPI["Strategy Builder API Layer"]
        NodeTemplateAPI[Node Template API]
        CodeGenAPI[Code Generation API]
        QuickTestAPI[Quick Test API]
        SessionAPI[Session API]
        FactorAPI[Factor Integration API]
    end

    subgraph StrategyBuilderServices["Strategy Builder Services"]
        BuilderService[BuilderService]
        CodeGeneratorService[CodeGeneratorService]
        ValidationService[ValidationService]
        QuickTestService[QuickTestService]
    end

    subgraph StrategyBuilderRepos["Strategy Builder Repositories"]
        NodeTemplateRepo[NodeTemplateRepository]
        CodeGenerationRepo[CodeGenerationRepository]
        QuickTestRepo[QuickTestRepository]
        BuilderSessionRepo[BuilderSessionRepository]
    end

    subgraph Database["Database (MySQL)"]
        NodeTemplatesTable[(node_templates)]
        CodeGenerationsTable[(code_generations)]
        QuickTestsTable[(quick_tests)]
        BuilderSessionsTable[(builder_sessions)]
        StrategyInstancesTable[(strategy_instances)]
    end

    subgraph IndicatorModule["Indicator Module"]
        IndicatorService[IndicatorService]
        FactorRepo[FactorRepository]
    end

    subgraph BacktestModule["Backtest Module"]
        BacktestExecService[BacktestExecutionService]
        BacktestRepo[BacktestRepository]
    end

    subgraph TaskModule["Task Scheduling Module"]
        TaskQueue[Task Queue]
        BackgroundWorker[Background Workers]
    end

    subgraph CodeTemplates["Code Templates (Jinja2)"]
        IndicatorTemplate[indicator_node.py.j2]
        ConditionTemplate[condition_node.py.j2]
        SignalTemplate[signal_node.py.j2]
        PositionTemplate[position_node.py.j2]
    end

    %% Client to API
    UI --> NodeTemplateAPI
    FlowEditor --> SessionAPI
    FlowEditor --> CodeGenAPI
    CodeViewer --> CodeGenAPI
    UI --> QuickTestAPI
    UI --> FactorAPI

    %% API to Services
    NodeTemplateAPI --> BuilderService
    CodeGenAPI --> CodeGeneratorService
    QuickTestAPI --> QuickTestService
    SessionAPI --> BuilderService
    FactorAPI --> BuilderService

    %% Services to Services
    CodeGeneratorService --> ValidationService
    CodeGeneratorService --> BuilderService
    QuickTestService --> BuilderService

    %% Services to Repos
    BuilderService --> NodeTemplateRepo
    BuilderService --> BuilderSessionRepo
    CodeGeneratorService --> CodeGenerationRepo
    QuickTestService --> QuickTestRepo

    %% Repos to Database
    NodeTemplateRepo --> NodeTemplatesTable
    CodeGenerationRepo --> CodeGenerationsTable
    QuickTestRepo --> QuickTestsTable
    BuilderSessionRepo --> BuilderSessionsTable
    QuickTestRepo --> StrategyInstancesTable

    %% Integration with Other Modules
    BuilderService --> IndicatorService
    IndicatorService --> FactorRepo

    QuickTestService --> BacktestExecService
    BacktestExecService --> BacktestRepo

    QuickTestService --> TaskQueue
    TaskQueue --> BackgroundWorker
    BackgroundWorker --> QuickTestService

    %% Code Generation Templates
    CodeGeneratorService --> CodeTemplates
    CodeTemplates --> IndicatorTemplate
    CodeTemplates --> ConditionTemplate
    CodeTemplates --> SignalTemplate
    CodeTemplates --> PositionTemplate

    %% Styling
    style Client fill:#e3f2fd
    style StrategyBuilderAPI fill:#fff3e0
    style StrategyBuilderServices fill:#f3e5f5
    style StrategyBuilderRepos fill:#e8f5e9
    style Database fill:#fce4ec
    style IndicatorModule fill:#f1f8e9
    style BacktestModule fill:#f1f8e9
    style TaskModule fill:#f1f8e9
    style CodeTemplates fill:#fff9c4
```

---

## Component Interaction Flow

This diagram shows request flow through all layers for code generation.

```mermaid
sequenceDiagram
    box Client Layer
    participant Client
    end

    box API Layer
    participant API
    participant Dependencies
    end

    box Service Layer
    participant CodeGenService
    participant ValidationService
    participant BuilderService
    end

    box Repository Layer
    participant CodeGenRepo
    participant NodeTemplateRepo
    end

    box Data Layer
    participant Database
    end

    Client->>API: POST /generate-code
    API->>Dependencies: get_current_user()
    Dependencies-->>API: user_id

    API->>CodeGenService: generate_code(instance_id, logic_flow, parameters)

    %% Validation Layer
    CodeGenService->>BuilderService: validate_logic_flow(logic_flow)
    BuilderService->>NodeTemplateRepo: get_by_ids(template_ids)
    NodeTemplateRepo->>Database: SELECT FROM node_templates
    Database-->>NodeTemplateRepo: Templates
    NodeTemplateRepo-->>BuilderService: Templates
    BuilderService-->>CodeGenService: ValidationResult

    %% Code Generation
    CodeGenService->>CodeGenService: topological_sort()
    CodeGenService->>CodeGenService: generate_node_code()
    CodeGenService->>CodeGenService: render_template()
    CodeGenService->>CodeGenService: combine_code()

    %% Security Validation
    CodeGenService->>ValidationService: validate_code(code)
    ValidationService-->>CodeGenService: SecurityResult

    %% Deduplication Check
    CodeGenService->>CodeGenService: calculate_hash()
    CodeGenService->>CodeGenRepo: get_by_code_hash(hash)
    CodeGenRepo->>Database: SELECT FROM code_generations
    Database-->>CodeGenRepo: Existing or NULL
    CodeGenRepo-->>CodeGenService: Existing or NULL

    alt No Duplicate
        CodeGenService->>CodeGenRepo: create(code_generation)
        CodeGenRepo->>Database: INSERT INTO code_generations
        Database-->>CodeGenRepo: Created
        CodeGenRepo-->>CodeGenService: CodeGeneration
    else Duplicate Found
        Note over CodeGenService: Return existing record
    end

    CodeGenService-->>API: CodeGeneration
    API-->>Client: 200 OK
```

---

## State Transition Diagrams

### Quick Test Status Lifecycle

```mermaid
stateDiagram-v2
    [*] --> PENDING: Test created
    PENDING --> RUNNING: Worker picks up task
    PENDING --> CANCELLED: User cancels

    RUNNING --> COMPLETED: Test succeeds
    RUNNING --> FAILED: Test fails
    RUNNING --> CANCELLED: User cancels
    RUNNING --> FAILED: Timeout (30 min)

    COMPLETED --> [*]
    FAILED --> [*]
    CANCELLED --> [*]

    note right of PENDING
        Test queued in task queue
        Waiting for worker
    end note

    note right of RUNNING
        Backtest executing
        Cannot be modified
    end note

    note right of COMPLETED
        Results available
        Metrics stored
    end note

    note right of FAILED
        Error message stored
        Can retry
    end note
```

### Builder Session Lifecycle

```mermaid
stateDiagram-v2
    [*] --> ACTIVE: Session created
    ACTIVE --> ACTIVE: Auto-save updates
    ACTIVE --> INACTIVE: 24h of inactivity
    ACTIVE --> INACTIVE: User saves strategy
    ACTIVE --> INACTIVE: User discards draft

    INACTIVE --> DELETED: Cleanup task runs
    DELETED --> [*]

    note right of ACTIVE
        is_active=true
        last_activity_at updated
        on auto-save
    end note

    note right of INACTIVE
        is_active=false
        Eligible for cleanup
    end note

    note right of DELETED
        is_deleted=true
        Soft deleted
    end note
```

---

## Performance Considerations

### Code Generation Performance

```mermaid
graph LR
    A[Logic Flow Input] --> B{Validation}
    B -->|Pass| C[Topological Sort]
    B -->|Fail| Z[Error Response]

    C --> D[Generate Node Code]
    D --> E[Combine Code]
    E --> F[Calculate Hash]
    F --> G{Hash Exists?}

    G -->|Yes| H[Return Cached]
    G -->|No| I[Validate Code]
    I --> J[Store Result]

    H --> K[Return]
    J --> K

    style A fill:#e3f2fd
    style C fill:#fff3e0
    style D fill:#f3e5f5
    style F fill:#e8f5e9
    style H fill:#c8e6c9
    style K fill:#c8e6c9

    A -.->|10ms| B
    C -.->|50ms| D
    D -.->|100ms| E
    F -.->|20ms| G
    I -.->|50ms| J
```

**Total Latency**:
- **Best Case** (cache hit): ~100ms
- **Average Case**: ~250ms
- **Worst Case** (complex validation): ~500ms

---

## Error Handling Flow

```mermaid
flowchart TD
    Request[API Request] --> TryCatch{Try-Catch}

    TryCatch -->|Success| Response[Success Response]

    TryCatch -->|ValidationError| Val[ValidationError Handler]
    Val --> Return400[Return 400 Bad Request]

    TryCatch -->|ResourceNotFoundError| NotFound[NotFoundError Handler]
    NotFound --> Return404[Return 404 Not Found]

    TryCatch -->|AuthorizationError| Auth[AuthError Handler]
    Auth --> Return403[Return 403 Forbidden]

    TryCatch -->|LogicFlowError| Logic[LogicFlowError Handler]
    Logic --> Return422[Return 422 Unprocessable Entity]

    TryCatch -->|DatabaseError| DB[DatabaseError Handler]
    DB --> LogError[Log Error]
    LogError --> Return500[Return 500 Internal Server Error]

    TryCatch -->|UnexpectedError| Unexpected[Generic Error Handler]
    Unexpected --> LogCritical[Log Critical]
    LogCritical --> Return500

    Return400 --> LogWarn[Log Warning]
    Return404 --> LogInfo[Log Info]
    Return403 --> LogWarn
    Return422 --> LogWarn

    Response --> Client[Return to Client]
    Return400 --> Client
    Return404 --> Client
    Return403 --> Client
    Return422 --> Client
    Return500 --> Client

    style Request fill:#e3f2fd
    style Response fill:#c8e6c9
    style Return400 fill:#ffe082
    style Return404 fill:#ffe082
    style Return403 fill:#ffe082
    style Return422 fill:#ffe082
    style Return500 fill:#ef5350
```

---

## Caching Strategy (Future Enhancement)

```mermaid
graph TD
    Request[API Request] --> CheckCache{Cache Hit?}

    CheckCache -->|Yes| ReturnCached[Return Cached Result]
    CheckCache -->|No| ProcessRequest[Process Request]

    ProcessRequest --> ComputeResult[Compute Result]
    ComputeResult --> StoreCache[Store in Cache]
    StoreCache --> ReturnResult[Return Result]

    subgraph "Cache Layers"
        L1[L1: In-Memory<br/>Redis]
        L2[L2: Database<br/>Query Cache]
    end

    subgraph "Cache Keys"
        K1[node_templates:all]
        K2[factors:category:{cat}]
        K3[code_gen:{instance}:{hash}]
    end

    subgraph "TTL Strategy"
        T1[Templates: 1 hour]
        T2[Factors: 30 min]
        T3[Code Gen: 24 hours]
    end

    ReturnCached -.-> L1
    StoreCache -.-> L1
    L1 -.-> K1
    L1 -.-> K2
    L1 -.-> K3
```

