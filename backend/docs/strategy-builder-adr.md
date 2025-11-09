# Architecture Decision Records (ADR) - Strategy Builder

## ADR-001: Code Generation Engine Selection (Jinja2)

**Status**: Accepted
**Date**: 2025-01-15
**Deciders**: Backend Architecture Team

### Context

Need to convert visual logic flows to executable Python code. The generated code must be:
- Readable and maintainable
- Customizable per node type
- Easy to debug and modify
- Template-based for consistency

### Decision

Use **Jinja2** as the primary code generation template engine.

### Rationale

**Advantages**:
1. **Mature and Proven**: Industry-standard template engine used by Flask, Ansible, SaltStack
2. **Python-Native**: Seamless integration with Python ecosystem
3. **Rich Features**: Control structures (if/for), filters, macros, template inheritance
4. **Readable Templates**: Template syntax is easy to read and maintain
5. **Debugging Support**: Clear error messages with line numbers
6. **No Performance Concerns**: Templates compile to bytecode, execution is fast
7. **Team Familiarity**: Team already familiar with Jinja2 syntax

**Alternatives Considered**:
- **String Formatting** (`f-strings`, `str.format()`): Too brittle, no control flow
- **AST Manipulation** (`ast` module): Complex, error-prone, harder to maintain
- **Black Box LLM**: Non-deterministic, costly, latency concerns

**Trade-offs**:
- Template files need maintenance when node types change
- Requires careful escaping to avoid injection vulnerabilities
- Templates can become complex for nested logic

### Consequences

**Positive**:
- Maintainable templates in `/templates/code_generation/` directory
- Easy to add new node types by creating new templates
- Generated code is consistent and follows best practices
- Non-developers can review template logic

**Negative**:
- Need to create and test template for each node type
- Template debugging requires understanding Jinja2 syntax
- Risk of template injection if user input not sanitized

**Mitigation**:
- Use `autoescape=True` for Jinja2 environment
- Never pass unsanitized user input to templates
- Validate all parameters before template rendering
- Comprehensive test suite for each template

### Implementation Notes

```python
# Template directory structure
/templates/code_generation/
├── base_strategy.py.j2         # Base strategy class
├── nodes/
│   ├── indicator_node.py.j2    # INDICATOR node code
│   ├── condition_node.py.j2    # CONDITION node code
│   ├── signal_node.py.j2       # SIGNAL node code
│   ├── position_node.py.j2     # POSITION sizing code
│   ├── stop_loss_node.py.j2    # STOP_LOSS logic
│   └── stop_profit_node.py.j2  # STOP_PROFIT logic
└── utils/
    └── macros.j2               # Reusable macros
```

---

## ADR-002: Asynchronous Quick Test Execution

**Status**: Accepted
**Date**: 2025-01-15
**Deciders**: Backend Architecture Team

### Context

Quick backtest execution can take 10-30 seconds or more. Blocking HTTP requests for this duration:
- Increases risk of timeout errors
- Degrades user experience
- Wastes server resources (connection pool)
- Prevents concurrent requests from same user

### Decision

Implement **asynchronous execution** with **background task queue** for quick tests.

### Rationale

**Pattern**:
1. User submits quick test request
2. API creates `QuickTest` record (status=PENDING)
3. API submits task to background queue
4. API returns `test_id` immediately (HTTP 202 Accepted)
5. Client polls `/quick-test/{test_id}` for results
6. Background worker executes test and updates status

**Advantages**:
- **Non-blocking**: HTTP request completes in <100ms
- **Scalable**: Background workers can scale independently
- **Resilient**: Failed tasks can be retried
- **Observable**: Test status tracked in database
- **User-friendly**: Client can cancel or navigate away

**Alternatives Considered**:
- **Synchronous Execution**: Simple but blocks connection, poor UX
- **WebSocket**: Real-time updates but complex client/server logic
- **Server-Sent Events (SSE)**: Good for updates but requires persistent connection

**Trade-offs**:
- More complex implementation (task queue, polling)
- Additional infrastructure (Celery/RQ/task scheduler)
- Need timeout/cleanup for abandoned tasks

### Consequences

**Positive**:
- Better user experience (no waiting for HTTP response)
- Server can handle more concurrent requests
- Easy to implement cancellation
- Clear separation of concerns (API vs execution)

**Negative**:
- Client must poll for results (adds complexity)
- Need task queue infrastructure (Redis + workers)
- More failure modes (queue failures, worker crashes)

**Mitigation**:
- Use existing `task_scheduling` module infrastructure
- Implement timeout detection for stuck tasks
- Provide WebSocket option in future for real-time updates
- Clear error messages when queue unavailable

### Implementation Notes

```python
# API endpoint returns immediately
@router.post("/quick-test", status_code=202)
async def execute_quick_test(...):
    # 1. Create QuickTest record (PENDING)
    quick_test = await service.create_quick_test(...)

    # 2. Submit to background queue
    await task_service.submit_task(
        task_type="quick_test_execution",
        task_data={"test_id": quick_test.id}
    )

    # 3. Return immediately
    return {"test_id": quick_test.id, "status": "PENDING"}

# Background worker
async def execute_quick_test_worker(test_id: str):
    # Update status to RUNNING
    # Execute backtest
    # Store results and update status to COMPLETED/FAILED
    pass
```

---

## ADR-003: Logic Flow Validation Strategy

**Status**: Accepted
**Date**: 2025-01-15
**Deciders**: Backend Architecture Team

### Context

Visual logic flows can have errors:
- Missing node connections (incomplete graphs)
- Type mismatches (connecting incompatible ports)
- Circular dependencies (cycles in graph)
- Invalid parameter values

Need to validate before code generation.

### Decision

Implement **multi-layer validation** with **fail-fast** approach:

1. **Schema Validation**: JSON structure validation (nodes, edges format)
2. **Graph Validation**: Topological checks (cycles, disconnected nodes)
3. **Type Validation**: Port type compatibility checks
4. **Parameter Validation**: JSON Schema validation of node parameters
5. **Semantic Validation**: Business rule checks (e.g., signals before positions)

### Rationale

**Advantages**:
- **Early Error Detection**: Catch errors before code generation
- **Clear Error Messages**: Each layer provides specific error messages
- **Separation of Concerns**: Each validator has single responsibility
- **Extensible**: Easy to add new validation rules
- **Performance**: Fail-fast stops on first error (optional strict mode)

**Validation Order** (fail-fast):
```
Schema Valid? → Graph Valid? → Types Valid? → Parameters Valid? → Semantic Valid?
     ↓ NO             ↓ NO          ↓ NO            ↓ NO               ↓ NO
   Error           Error         Error           Error              Error
```

**Alternatives Considered**:
- **Single-Pass Validation**: Simpler but less clear error messages
- **No Validation**: Fast but breaks code generation
- **Client-Side Only**: Unreliable (can be bypassed)

**Trade-offs**:
- Multiple validation passes add latency (acceptable: <100ms)
- More complex codebase (mitigated by clear separation)
- Need to maintain validation rules

### Consequences

**Positive**:
- Prevents invalid code generation
- Users get clear, actionable error messages
- Easier to debug strategy building issues
- Reduces support burden

**Negative**:
- Additional latency before code generation
- More code to maintain and test
- False positives require refinement

**Mitigation**:
- Cache validation results (same logic flow)
- Optimize topological sort algorithm (O(V+E))
- Provide validation feedback in real-time (client-side preview)

### Implementation Notes

```python
class LogicFlowValidator:
    async def validate(self, logic_flow: dict) -> ValidationResult:
        # 1. Schema validation
        if not self._validate_schema(logic_flow):
            return ValidationResult(errors=[...])

        # 2. Graph validation (circular dependency)
        cycle = await self._detect_cycle(logic_flow)
        if cycle:
            return ValidationResult(errors=["Circular dependency detected"])

        # 3. Type validation (port compatibility)
        type_errors = await self._validate_types(logic_flow)
        if type_errors:
            return ValidationResult(errors=type_errors)

        # 4. Parameter validation (JSON Schema)
        param_errors = await self._validate_parameters(logic_flow)
        if param_errors:
            return ValidationResult(errors=param_errors)

        # 5. Semantic validation (business rules)
        semantic_warnings = await self._validate_semantics(logic_flow)

        return ValidationResult(
            is_valid=True,
            warnings=semantic_warnings
        )
```

---

## ADR-004: Session Auto-Save Mechanism

**Status**: Accepted
**Date**: 2025-01-15
**Deciders**: Backend Architecture Team

### Context

Users need draft auto-save to prevent work loss when:
- Browser crashes
- Network disconnects
- User forgets to save
- Editing for extended periods

Need to balance between data freshness and server load.

### Decision

Implement **client-driven auto-save** with **debouncing**:

- **Auto-save interval**: Client sends save request every **30 seconds** of activity
- **Debouncing**: Client delays save if user is actively editing (debounce 2 seconds)
- **Session expiration**: 24 hours of inactivity
- **Upsert operation**: Create or update session (no duplicates)

### Rationale

**Client-Driven Approach**:
- Client knows when user is active (mouse/keyboard events)
- Client controls debouncing (prevents server spam)
- Server receives only meaningful updates
- No need for WebSocket or polling

**30-Second Interval**:
- Balances data freshness vs server load
- User loses max 30 seconds of work (acceptable)
- ~120 requests/hour per active session (manageable)

**24-Hour Expiration**:
- Long enough for multi-day projects
- Short enough to avoid bloat
- Background cleanup task (hourly cron)

**Alternatives Considered**:
- **Real-time Save** (on every change): Too many requests, overloads server
- **Manual Save Only**: Poor UX, users forget to save
- **60-Second Interval**: Loses more work, not significantly less load
- **15-Second Interval**: Better UX but 2x server load (acceptable trade-off)

**Trade-offs**:
- 30-second interval may lose recent work (mitigated by manual save button)
- Sessions accumulate over time (mitigated by cleanup task)
- Client complexity (debouncing logic)

### Consequences

**Positive**:
- Users don't lose work due to crashes
- Can resume work after browser close
- Minimal server load (controlled by client)
- Simple backend implementation (upsert operation)

**Negative**:
- Max 30 seconds of work lost on crash
- Old sessions accumulate (need cleanup)
- Client must implement debouncing

**Mitigation**:
- Provide manual "Save Draft" button for immediate save
- Show "Last saved at HH:MM:SS" indicator in UI
- Background cleanup task runs hourly
- Session table indexed on `last_activity_at` for fast cleanup

### Implementation Notes

```javascript
// Client-side (pseudocode)
let autoSaveTimer = null;
let lastChange = null;

function onUserEdit() {
    lastChange = Date.now();

    // Clear existing timer
    clearTimeout(autoSaveTimer);

    // Debounce: wait 2 seconds after last edit
    autoSaveTimer = setTimeout(() => {
        if (Date.now() - lastChange >= 2000) {
            sendAutoSave();
        }
    }, 2000);
}

function sendAutoSave() {
    fetch('/api/strategy-builder/sessions', {
        method: 'POST',
        body: JSON.stringify({
            draft_logic_flow: getCurrentLogicFlow(),
            draft_parameters: getCurrentParameters()
        })
    });
}

// Auto-save every 30 seconds if active
setInterval(() => {
    if (isUserActive() && hasPendingChanges()) {
        sendAutoSave();
    }
}, 30000);
```

```python
# Server-side cleanup (background task)
async def cleanup_expired_sessions():
    """Run every hour via cron/scheduler"""
    expiration_threshold = datetime.now() - timedelta(hours=24)

    expired_sessions = await session_repo.get_expired_sessions(
        expiration_hours=24
    )

    for session in expired_sessions:
        await session_repo.delete(session.id, soft=True)

    logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
```

---

## ADR-005: Code Security Validation Approach

**Status**: Accepted
**Date**: 2025-01-15
**Deciders**: Backend Architecture Team

### Context

Generated Python code will be executed in backtest environment. Need to prevent:
- Malicious code injection
- Resource exhaustion attacks
- Data exfiltration
- System compromise

Security is critical but must not block legitimate use cases.

### Decision

Implement **multi-layer security validation**:

1. **Static AST Analysis**: Parse code and detect dangerous patterns
2. **Import Whitelist**: Only allow safe imports (numpy, pandas, qlib, talib)
3. **Function Blacklist**: Block eval, exec, __import__, file I/O
4. **Complexity Limits**: Reject overly complex code (cyclomatic complexity > 20)
5. **(Future) Sandboxed Execution**: Execute in isolated environment with resource limits

### Rationale

**Defense in Depth**:
- Multiple layers reduce attack surface
- Failure of one layer doesn't compromise security
- Each layer catches different types of threats

**Whitelist > Blacklist**:
- Safer to allow known-good than block known-bad
- New dangerous modules don't bypass security
- Clear communication to users (what's allowed)

**AST Analysis vs Runtime Checks**:
- AST is static, catches issues before execution
- No runtime overhead
- Can provide clear error messages with line numbers

**Allowed Imports** (whitelist):
```python
{
    # Data manipulation
    "numpy", "pandas", "scipy",
    # Qlib framework
    "qlib", "qlib.data", "qlib.contrib",
    # Technical indicators
    "talib",
    # Standard library (safe)
    "math", "statistics", "random", "datetime", "time",
    "collections", "itertools", "typing"
}
```

**Forbidden Patterns**:
```python
{
    # Dynamic execution
    "eval", "exec", "compile", "__import__",
    # File I/O
    "open", "file", "read", "write",
    # System access
    "os", "sys", "subprocess", "shutil",
    # Network
    "socket", "urllib", "requests", "http"
}
```

**Alternatives Considered**:
- **Sandboxing Only**: Not sufficient, need pre-execution checks
- **No Validation**: Unacceptable security risk
- **Manual Review**: Doesn't scale, slow feedback

**Trade-offs**:
- Whitelist may block legitimate advanced use cases (can be extended)
- AST analysis has false positives (can be refined)
- Complexity limits may reject valid complex strategies (adjustable)

### Consequences

**Positive**:
- Protects system from malicious code
- Catches accidental dangerous operations
- Clear error messages guide users
- Can be audited and improved over time

**Negative**:
- May reject legitimate complex code
- Users may feel restricted
- Requires maintenance as Python evolves

**Mitigation**:
- Provide clear documentation of allowed operations
- Allow users to request whitelist additions (with review)
- Log rejected code for security monitoring
- Future: Sandboxed execution for advanced users (opt-in)

### Implementation Notes

```python
class CodeSecurityValidator:
    ALLOWED_IMPORTS = {...}  # Whitelist
    FORBIDDEN_FUNCTIONS = {...}  # Blacklist
    MAX_COMPLEXITY = 20

    async def validate(self, code: str) -> SecurityResult:
        # 1. Parse AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return SecurityResult(
                is_safe=False,
                violations=[{
                    "severity": "CRITICAL",
                    "message": f"Syntax error: {e}"
                }]
            )

        # 2. Check imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in self.ALLOWED_IMPORTS:
                        return SecurityResult(
                            is_safe=False,
                            violations=[{
                                "severity": "CRITICAL",
                                "line": node.lineno,
                                "message": f"Forbidden import: {alias.name}"
                            }]
                        )

        # 3. Check function calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node)
                if func_name in self.FORBIDDEN_FUNCTIONS:
                    return SecurityResult(
                        is_safe=False,
                        violations=[{
                            "severity": "CRITICAL",
                            "line": node.lineno,
                            "message": f"Forbidden function: {func_name}"
                        }]
                    )

        # 4. Check complexity
        complexity = self._calculate_complexity(tree)
        if complexity > self.MAX_COMPLEXITY:
            return SecurityResult(
                is_safe=False,
                violations=[{
                    "severity": "HIGH",
                    "message": f"Code too complex: {complexity} > {self.MAX_COMPLEXITY}"
                }]
            )

        return SecurityResult(is_safe=True, violations=[])
```

---

## ADR-006: Code Deduplication Strategy (SHA-256 Hash)

**Status**: Accepted
**Date**: 2025-01-15
**Deciders**: Backend Architecture Team

### Context

Users may generate same code multiple times:
- Tweaking parameters then reverting
- Experimenting with variations
- Collaborative editing (future)

Storing duplicate code wastes:
- Database space
- Query performance
- Confusing history view

### Decision

Use **SHA-256 hash** for code deduplication:

- Calculate hash of `generated_code` (normalized)
- Store `code_hash` in `code_generations` table (indexed)
- Before saving new generation, check if hash exists
- If duplicate: Don't create new record, return existing
- Display in history: "Generated (duplicate of HH:MM:SS)"

### Rationale

**SHA-256 Properties**:
- **Cryptographically Secure**: Collision probability is negligible
- **Fast**: Hash calculation is ~10-20 microseconds for typical code
- **Fixed Size**: 64 hex characters (256 bits), efficient indexing
- **Deterministic**: Same code always produces same hash

**Normalization** (before hashing):
```python
def normalize_code(code: str) -> str:
    # Remove comments
    # Normalize whitespace
    # Sort imports
    # Consistent formatting (use Black)
    return normalized_code
```

**Alternatives Considered**:
- **MD5**: Faster but deprecated, collision concerns
- **Full Text Comparison**: Slow for large code (O(n)), no indexing
- **Simpler Hash** (CRC32): Fast but high collision probability
- **No Deduplication**: Wastes space, confuses users

**Trade-offs**:
- Hash calculation adds ~20μs latency (negligible)
- Normalization adds ~100ms for Black formatting (acceptable)
- False negatives if normalization misses semantic equivalence (rare)

### Consequences

**Positive**:
- Saves database space (~10KB per duplicate avoided)
- Faster history queries (fewer records)
- Clear history view (no duplicate noise)
- Can track "how many times user generated same code"

**Negative**:
- Hash calculation overhead (~100ms with normalization)
- Semantically equivalent code with different formatting may not dedupe
- Need to maintain normalization logic

**Mitigation**:
- Use Black formatter for consistent code formatting
- Index `code_hash` for fast lookups
- Show "duplicate of..." message to user
- Allow manual "Save Anyway" override (future)

### Implementation Notes

```python
import hashlib
import black

class CodeHasher:
    @staticmethod
    def calculate_hash(code: str) -> str:
        """Calculate SHA-256 hash of normalized code."""
        # 1. Normalize with Black formatter
        try:
            normalized = black.format_str(code, mode=black.Mode())
        except Exception:
            # If Black fails, use original code
            normalized = code

        # 2. Remove comments (optional, may cause false negatives)
        # normalized = self._remove_comments(normalized)

        # 3. Calculate SHA-256
        hash_obj = hashlib.sha256(normalized.encode('utf-8'))
        return hash_obj.hexdigest()

    @staticmethod
    async def check_duplicate(
        instance_id: str,
        code_hash: str
    ) -> Optional[CodeGeneration]:
        """Check if code with same hash exists."""
        return await code_generation_repo.get_by_code_hash(
            instance_id, code_hash
        )

# Usage in CodeGeneratorService
async def generate_code(...) -> CodeGeneration:
    # Generate code
    code = await self._generate_code_from_flow(...)

    # Calculate hash
    code_hash = CodeHasher.calculate_hash(code)

    # Check for duplicate
    duplicate = await CodeHasher.check_duplicate(instance_id, code_hash)
    if duplicate:
        logger.info(f"Code duplicate detected: {duplicate.id}")
        return duplicate  # Return existing record

    # Save new record
    return await code_generation_repo.create({
        "generated_code": code,
        "code_hash": code_hash,
        ...
    })
```

```sql
-- Database index for fast duplicate lookup
CREATE INDEX idx_codegen_hash_instance
ON code_generations(code_hash, instance_id, is_deleted);
```

---

## Summary Table

| ADR | Decision | Rationale | Trade-offs |
|-----|----------|-----------|------------|
| ADR-001 | Jinja2 for code generation | Mature, readable, extensible | Templates need maintenance |
| ADR-002 | Async quick test execution | Better UX, scalable, resilient | Client polling complexity |
| ADR-003 | Multi-layer validation | Early error detection, clear messages | Additional latency |
| ADR-004 | 30-second auto-save | Balances freshness vs server load | Max 30s work loss |
| ADR-005 | Whitelist + AST security | Defense in depth, safe by default | May block advanced uses |
| ADR-006 | SHA-256 deduplication | Saves space, fast, secure | Hash calculation overhead |

---

## References

- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [Python AST Module](https://docs.python.org/3/library/ast.html)
- [Black Code Formatter](https://black.readthedocs.io/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Qlib Documentation](https://qlib.readthedocs.io/)
