import sys
import io
import contextlib
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class EvalService:
    @staticmethod
    async def run_python(code: str) -> str:
        """Executes Python code and captures the output."""
        stdout = io.StringIO()
        stderr = io.StringIO()
        
        # We use a restricted environment for the execution (basic)
        # However, since this is for Admin use on their own Termux, 
        # we don't need to be extremely strict unless specified.
        
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                # We can't use 'exec' with await directly unless wrapped.
                # For sync code:
                exec(code, {"__name__": "__main__"}, {})
            
            output = stdout.getvalue()
            errors = stderr.getvalue()
            
            if errors:
                return f"Output:\n{output}\n\nErrors:\n{errors}"
            return output or "Code executed successfully (No output)."
            
        except Exception as e:
            return f"Exception occurred:\n{str(e)}"
        finally:
            stdout.close()
            stderr.close()
