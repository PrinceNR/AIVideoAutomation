from pathlib import Path
import time


SAFE_UNLINK_ATTEMPTS = 3
SAFE_UNLINK_DELAY_SECONDS = 0.2
WINDOWS_SHARING_VIOLATION = 32


def safe_unlink(
    path,
    attempts=SAFE_UNLINK_ATTEMPTS,
    delay_seconds=SAFE_UNLINK_DELAY_SECONDS,
):
    """Delete a temporary file without allowing cleanup to crash a task."""
    path = Path(path)
    attempts = max(1, int(attempts))

    for attempt in range(1, attempts + 1):
        try:
            path.unlink(missing_ok=True)
            return True
        except PermissionError as error:
            is_windows_lock = (
                getattr(error, "winerror", None)
                == WINDOWS_SHARING_VIOLATION
            )

            if not is_windows_lock or attempt >= attempts:
                break

            time.sleep(float(delay_seconds))
        except OSError:
            break

    print(
        "WARNING: Temporary audio file is still locked; "
        "cleanup deferred."
    )
    return False
