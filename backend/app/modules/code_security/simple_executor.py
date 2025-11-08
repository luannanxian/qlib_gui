"""
Simple Code Executor - Lightweight Version

Provides basic code execution with security constraints:
- Timeout protection using multiprocessing
- Memory limits using resource module
- Process isolation
- Error handling and recovery
- Stdout/stderr capture

For personal use - provides essential protection without complex sandboxing.
"""

import io
import sys
import time
import traceback
import resource
from dataclasses import dataclass, field
from multiprocessing import Process, Queue
from typing import Any, Dict, Optional


# ==================== Custom Exceptions ====================


class ExecutionError(Exception):
    """Base exception for code execution errors."""
    pass


class TimeoutError(ExecutionError):
    """Raised when code execution exceeds timeout limit."""
    pass


class MemoryLimitError(ExecutionError):
    """Raised when code execution exceeds memory limit."""
    pass


# ==================== Result Data Class ====================


@dataclass
class ExecutionResult:
    """
    Result of code execution.

    Attributes:
        success: Whether execution completed successfully
        stdout: Captured standard output
        stderr: Captured standard error
        error: Exception object if execution failed
        execution_time: Time taken to execute (seconds)
        locals_dict: Local variables after execution (if captured)
        memory_used_mb: Approximate memory used (MB)
    """
    success: bool
    stdout: str = ""
    stderr: str = ""
    error: Optional[Exception] = None
    execution_time: float = 0.0
    locals_dict: Optional[Dict[str, Any]] = None
    memory_used_mb: float = 0.0


# ==================== Simple Code Executor ====================


class SimpleCodeExecutor:
    """
    Lightweight code executor with basic security constraints.

    Features:
    - Timeout protection (default: 5 minutes)
    - Memory limits (default: 1GB)
    - Process isolation using multiprocessing
    - Stdout/stderr capture
    - Error handling

    Example:
        >>> executor = SimpleCodeExecutor(timeout=10, max_memory_mb=512)
        >>> result = executor.execute("print('Hello, World!')")
        >>> print(result.stdout)
        Hello, World!
    """

    def __init__(
        self,
        timeout: int = 300,
        max_memory_mb: int = 1024,
    ):
        """
        Initialize the code executor.

        Args:
            timeout: Maximum execution time in seconds (default: 300 = 5 minutes)
            max_memory_mb: Maximum memory usage in MB (default: 1024 = 1GB)

        Raises:
            ValueError: If timeout or memory limit is not positive
        """
        if timeout <= 0:
            raise ValueError("Timeout must be positive")
        if max_memory_mb <= 0:
            raise ValueError("Memory limit must be positive")

        self.timeout = timeout
        self.max_memory_mb = max_memory_mb

    def execute(
        self,
        code: str,
        globals_dict: Optional[Dict[str, Any]] = None,
        locals_dict: Optional[Dict[str, Any]] = None,
        capture_locals: bool = False,
    ) -> ExecutionResult:
        """
        Execute Python code in an isolated process with security constraints.

        Args:
            code: Python code to execute
            globals_dict: Global variables for execution context
            locals_dict: Local variables for execution context
            capture_locals: Whether to capture local variables after execution

        Returns:
            ExecutionResult: Result object containing execution details

        Example:
            >>> executor = SimpleCodeExecutor()
            >>> result = executor.execute("x = 1 + 1", capture_locals=True)
            >>> print(result.locals_dict['x'])
            2
        """
        # Create queue for inter-process communication
        result_queue = Queue()

        # Create and start execution process
        process = Process(
            target=self._run_in_process,
            args=(code, globals_dict, locals_dict, capture_locals, result_queue)
        )

        start_time = time.time()
        process.start()

        # Wait for process to complete or timeout
        process.join(timeout=self.timeout)
        execution_time = time.time() - start_time

        # Check if process timed out
        if process.is_alive():
            process.terminate()
            process.join(timeout=1)  # Give it 1 second to terminate gracefully
            if process.is_alive():
                process.kill()  # Force kill if still alive
                process.join()

            return ExecutionResult(
                success=False,
                error=TimeoutError(f"Code execution timeout after {self.timeout} seconds"),
                execution_time=execution_time,
            )

        # Get result from queue
        if not result_queue.empty():
            result_data = result_queue.get()

            # Reconstruct result
            if result_data["success"]:
                return ExecutionResult(
                    success=True,
                    stdout=result_data.get("stdout", ""),
                    stderr=result_data.get("stderr", ""),
                    execution_time=execution_time,
                    locals_dict=result_data.get("locals_dict"),
                    memory_used_mb=result_data.get("memory_used_mb", 0.0),
                )
            else:
                # Reconstruct exception
                error_type = result_data.get("error_type", "Exception")
                error_message = result_data.get("error_message", "Unknown error")

                # Create appropriate exception type
                if error_type == "TimeoutError":
                    error = TimeoutError(error_message)
                elif error_type == "MemoryLimitError":
                    error = MemoryLimitError(error_message)
                elif error_type == "MemoryError":
                    error = MemoryError(error_message)
                elif error_type == "SyntaxError":
                    error = SyntaxError(error_message)
                elif error_type == "NameError":
                    error = NameError(error_message)
                elif error_type == "ValueError":
                    error = ValueError(error_message)
                elif error_type == "ZeroDivisionError":
                    error = ZeroDivisionError(error_message)
                else:
                    error = ExecutionError(error_message)

                return ExecutionResult(
                    success=False,
                    stdout=result_data.get("stdout", ""),
                    stderr=result_data.get("stderr", ""),
                    error=error,
                    execution_time=execution_time,
                )

        # No result in queue - process failed without reporting
        return ExecutionResult(
            success=False,
            error=ExecutionError("Code execution failed without error message"),
            execution_time=execution_time,
        )

    def _run_in_process(
        self,
        code: str,
        globals_dict: Optional[Dict[str, Any]],
        locals_dict: Optional[Dict[str, Any]],
        capture_locals: bool,
        result_queue: Queue,
    ):
        """
        Run code in isolated process with resource limits.

        This method is executed in a separate process and communicates
        results back through the queue.

        Args:
            code: Python code to execute
            globals_dict: Global variables
            locals_dict: Local variables
            capture_locals: Whether to capture locals after execution
            result_queue: Queue for returning results
        """
        try:
            # Set memory limit (soft and hard limit)
            max_memory_bytes = self.max_memory_mb * 1024 * 1024
            try:
                resource.setrlimit(
                    resource.RLIMIT_AS,
                    (max_memory_bytes, max_memory_bytes)
                )
            except (ValueError, OSError):
                # Memory limit setting may fail on some systems (e.g., macOS)
                # Continue without memory limit in such cases
                pass

            # Capture stdout and stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()

            # Prepare execution context
            if globals_dict is None:
                globals_dict = {"__builtins__": __builtins__}
            if locals_dict is None:
                locals_dict = {}

            # Execute code
            exec(code, globals_dict, locals_dict)

            # Get captured output
            stdout_value = sys.stdout.getvalue()
            stderr_value = sys.stderr.getvalue()

            # Restore stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr

            # Get memory usage (approximate)
            try:
                memory_used = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                # Convert to MB (ru_maxrss is in KB on Linux, bytes on macOS)
                if sys.platform == 'darwin':
                    memory_used_mb = memory_used / (1024 * 1024)
                else:
                    memory_used_mb = memory_used / 1024
            except:
                memory_used_mb = 0.0

            # Prepare result
            result_data = {
                "success": True,
                "stdout": stdout_value,
                "stderr": stderr_value,
                "memory_used_mb": memory_used_mb,
            }

            # Capture locals if requested
            if capture_locals:
                # Filter out builtins and internal variables
                filtered_locals = {
                    k: v for k, v in locals_dict.items()
                    if not k.startswith('__')
                }
                result_data["locals_dict"] = filtered_locals

            result_queue.put(result_data)

        except MemoryError as e:
            # Memory limit exceeded
            result_queue.put({
                "success": False,
                "error_type": "MemoryError",
                "error_message": f"Memory limit exceeded: {str(e)}",
                "stdout": "",
                "stderr": "",
            })

        except SyntaxError as e:
            # Syntax error in code
            result_queue.put({
                "success": False,
                "error_type": "SyntaxError",
                "error_message": str(e),
                "stdout": "",
                "stderr": traceback.format_exc(),
            })

        except Exception as e:
            # Other execution errors
            try:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
            except:
                pass

            result_queue.put({
                "success": False,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "stdout": "",
                "stderr": traceback.format_exc(),
            })
