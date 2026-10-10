"""Bounded subprocesses. Never expose subprocess output in errors or logs."""
import subprocess

class OperationError(RuntimeError):
    pass

class Runner:
    def run(self, args):
        try:
            result = subprocess.run(args, capture_output=True, text=True,
                                    timeout=25, check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise OperationError("Command unavailable or timed out") from None
        if result.returncode:
            raise OperationError("Command failed; check dependencies and connection")
        return result.stdout

    def launch(self, args):
        """Desktop applications must outlive the bounded operation worker."""
        try:
            subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
        except OSError:
            raise OperationError("Desktop application is unavailable") from None
