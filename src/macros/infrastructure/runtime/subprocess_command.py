"""SubprocessCommandAdapter -- runs shell commands via subprocess (the sensor)."""

import subprocess


class SubprocessCommandAdapter:
    """Implements CommandPort by running shell commands via subprocess."""

    def run_command(self, command: str, cwd: str | None = None) -> tuple[int, str]:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=300,
        )
        combined = result.stdout + result.stderr
        return result.returncode, combined
