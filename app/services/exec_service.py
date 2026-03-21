import asyncio
import logging
import shlex

logger = logging.getLogger(__name__)

class ExecService:
    @staticmethod
    async def run_detached(command: str):
        """
        Executes a shell command without waiting for its completion or output.
        Useful for background tasks like camera/mic.
        """
        try:
            # We don't use pipes here to ensure the process is fully detached
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            # We don't communicate or wait here, we just let it run.
            return True
        except Exception as e:
            logger.error(f"ExecService Detached Error: {str(e)}")
            return False

    @staticmethod
    async def run_command(command: str, timeout: int = 15, max_chars: int = 3800) -> str:
        """
        Executes a shell command asynchronously and returns the output.
        Includes timeout and output size protection.
        """
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                # Wait for the command to finish with a timeout
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                
                # Combine output and error
                output = stdout.decode('utf-8', errors='replace').strip()
                error = stderr.decode('utf-8', errors='replace').strip()
                
                result = ""
                if output:
                    result += output
                if error:
                    if result: result += "\n"
                    result += f"Error Output:\n{error}"
                
                if not result:
                    result = "(Command finished with no output)"

            except asyncio.TimeoutError:
                # Kill the process if it times out
                try:
                    process.kill()
                except:
                    pass
                return f"❌ Execution Timeout ({timeout}s)"

            # Truncate if too long
            if len(result) > max_chars:
                result = result[:max_chars] + "\n\n...(truncated)"
                
            return result

        except Exception as e:
            logger.error(f"ExecService Error: {str(e)}")
            return f"❌ Local Error: {str(e)}"
