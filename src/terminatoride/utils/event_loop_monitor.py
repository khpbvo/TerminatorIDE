import asyncio
import heapq
import json
import logging
import os
import sys
import time
import traceback
import uuid
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

import psutil  # You might need to pip install psutil


class EventLoopMonitor:
    # Maximum log file size (10 MB)
    MAX_LOG_SIZE = 10 * 1024 * 1024

    # Number of backup files to keep
    MAX_LOG_BACKUPS = 2  # This means 3 files total (main + 2 backups)

    def __init__(self, check_interval=1.0):
        self.check_interval = check_interval
        self.running = False
        self.task = None
        self.session_id = str(uuid.uuid4())[:8]  # Generate a unique session ID

        # Super verbose direct console output
        self._verbose_print(
            f"[MONITOR] Initializing EventLoopMonitor with session ID: {self.session_id}"
        )

        # Clean up old logs before creating new ones
        self._cleanup_old_logs()

        # Dump system info
        self._dump_system_info()

        # Set up logging
        self.logger = self._setup_logger()

    def _cleanup_old_logs(self):
        """Clean up old log files, keeping only the most recent ones."""
        try:
            log_dirs = [
                Path.home() / ".terminatoride" / "logs",
                Path.home() / "Documents" / "TerminatorIDE" / "logs",
                Path(os.getcwd()) / "logs",
                Path("/tmp/terminatoride_logs"),
            ]

            for log_dir in log_dirs:
                if not log_dir.exists():
                    continue

                self._verbose_print(f"Cleaning up old logs in: {log_dir}")

                # Clean up regular log files
                self._cleanup_logs_in_dir(log_dir, "event_loop_monitor_*.log")

                # Clean up block logs
                self._cleanup_logs_in_dir(log_dir, "block_*.json")

                # Clean up system info files
                self._cleanup_logs_in_dir(log_dir, "system_info_*.json")

                # Clean up marker files older than 7 days
                self._cleanup_old_markers(log_dir)

        except Exception as e:
            self._verbose_print(f"Error cleaning up old logs: {e}")

    def _cleanup_logs_in_dir(self, log_dir, pattern, max_files=10):
        """Clean up log files matching pattern in the directory."""
        try:
            files = list(log_dir.glob(pattern))

            # Skip if no files or just a few
            if len(files) <= max_files:
                return

            # Get files with their modification times
            file_times = [(f.stat().st_mtime, f) for f in files if f.is_file()]

            # Sort by modification time (oldest first)
            file_times.sort()

            # Delete all but the newest max_files
            for _, file_path in file_times[:-max_files]:
                try:
                    file_path.unlink()
                    self._verbose_print(f"Deleted old log file: {file_path}")
                except Exception as e:
                    self._verbose_print(f"Failed to delete {file_path}: {e}")

        except Exception as e:
            self._verbose_print(f"Error cleaning up {pattern} in {log_dir}: {e}")

    def _cleanup_old_markers(self, log_dir):
        """Clean up marker files older than 7 days."""
        try:
            now = time.time()
            week_seconds = 7 * 24 * 60 * 60

            for marker in log_dir.glob("*MONITOR_*.marker"):
                if marker.is_file():
                    mtime = marker.stat().st_mtime
                    if now - mtime > week_seconds:
                        try:
                            marker.unlink()
                            self._verbose_print(f"Deleted old marker: {marker}")
                        except Exception as e:
                            self._verbose_print(f"Failed to delete {marker}: {e}")

        except Exception as e:
            self._verbose_print(f"Error cleaning up old markers in {log_dir}: {e}")

    def _verbose_print(self, message):
        """Print with timestamp and session ID."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}][ELM-{self.session_id}] {message}", flush=True)

    def _dump_system_info(self):
        """Dump detailed system information as JSON."""
        try:
            system_info = {
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
                "python_version": sys.version,
                "platform": sys.platform,
                "cwd": os.getcwd(),
                "pid": os.getpid(),
                "ppid": os.getppid(),
                "event_loop": str(asyncio.get_event_loop()),
                "env_vars": {
                    k: v for k, v in os.environ.items() if not k.startswith("_")
                },
                "cpu_count": os.cpu_count(),
                "process_memory": psutil.Process().memory_info().rss
                / (1024 * 1024),  # MB
                "total_memory": psutil.virtual_memory().total / (1024 * 1024),  # MB
                "available_memory": psutil.virtual_memory().available
                / (1024 * 1024),  # MB,
                "disk_usage": {
                    "total": psutil.disk_usage("/").total / (1024 * 1024 * 1024),  # GB
                    "used": psutil.disk_usage("/").used / (1024 * 1024 * 1024),  # GB
                    "free": psutil.disk_usage("/").free / (1024 * 1024 * 1024),  # GB
                },
                "user_home": str(Path.home()),
            }

            # Dump as JSON to console
            json_str = json.dumps(system_info, indent=2)
            self._verbose_print(f"SYSTEM INFO:\n{json_str}")

            # Also write to a dedicated file
            try:
                info_path = (
                    Path.home()
                    / ".terminatoride"
                    / "logs"
                    / f"system_info_{self.session_id}.json"
                )
                os.makedirs(os.path.dirname(info_path), exist_ok=True)
                with open(info_path, "w") as f:
                    f.write(json_str)
                self._verbose_print(f"Wrote system info to: {info_path}")
            except Exception as e:
                self._verbose_print(f"Failed to write system info file: {e}")

        except Exception as e:
            self._verbose_print(f"Error dumping system info: {e}")
            traceback.print_exc()

    def _setup_logger(self):
        """Set up a dedicated logger for the event loop monitor."""
        try:
            # Create multiple possible log directories
            log_paths = [
                Path.home() / ".terminatoride" / "logs",
                Path.home() / "Documents" / "TerminatorIDE" / "logs",
                Path(os.getcwd()) / "logs",
                Path("/tmp/terminatoride_logs"),
            ]

            # Try each location until one works
            log_dir = None
            log_path = None

            for path in log_paths:
                self._verbose_print(f"Trying log directory: {path}")
                try:
                    # Ensure directory exists
                    os.makedirs(str(path), exist_ok=True)

                    # Test file creation
                    test_file = path / f"test_{self.session_id}.log"
                    with open(str(test_file), "w") as f:
                        f.write(
                            f"Test log file created at {datetime.now().isoformat()}\n"
                        )

                    # If we get here, we found a working directory
                    log_dir = path
                    log_path = path / f"event_loop_monitor_{self.session_id}.log"
                    self._verbose_print(
                        f"Successfully created test file at: {test_file}"
                    )
                    self._verbose_print(f"Will use log file: {log_path}")
                    break
                except Exception as e:
                    self._verbose_print(f"Failed to use log directory {path}: {e}")

            if not log_dir:
                self._verbose_print(
                    "CRITICAL: Could not find a writable log directory!"
                )
                raise RuntimeError("No writable log directory found")

            # Create logger with a very specific name including session ID
            logger_name = f"event_loop_monitor_{self.session_id}"
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.DEBUG)

            # Remove existing handlers to avoid duplicates
            if logger.hasHandlers():
                logger.handlers.clear()
                self._verbose_print(
                    f"Cleared existing handlers for logger: {logger_name}"
                )

            # Create a rotating file handler that limits size and keeps backups
            file_handler = RotatingFileHandler(
                filename=str(log_path),
                maxBytes=self.MAX_LOG_SIZE,
                backupCount=self.MAX_LOG_BACKUPS,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)

            self._verbose_print(
                f"Created rotating file handler: max_size={self.MAX_LOG_SIZE/1024/1024}MB, backups={self.MAX_LOG_BACKUPS}"
            )

            # Create JSON formatter
            class JsonFormatter(logging.Formatter):
                def format(self, record):
                    log_data = {
                        "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                        "session_id": (
                            self.session_id
                            if hasattr(self, "session_id")
                            else "unknown"
                        ),
                        "level": record.levelname,
                        "logger": record.name,
                        "message": record.getMessage(),
                        "module": record.module,
                        "function": record.funcName,
                        "line": record.lineno,
                        "process_id": record.process,
                        "thread_id": record.thread,
                    }

                    # Add exception info if present
                    if record.exc_info:
                        log_data["exception"] = {
                            "type": str(record.exc_info[0].__name__),
                            "message": str(record.exc_info[1]),
                            "traceback": "".join(
                                traceback.format_exception(*record.exc_info)
                            ),
                        }

                    return json.dumps(log_data)

            # Add session ID to formatter
            json_formatter = JsonFormatter()
            json_formatter.session_id = self.session_id
            file_handler.setFormatter(json_formatter)

            # Add handler to logger
            logger.addHandler(file_handler)

            # Also create a text formatter for console output
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(
                logging.INFO
            )  # Set to INFO for less verbosity on console
            text_formatter = logging.Formatter(
                f"[%(asctime)s][{self.session_id}][%(levelname)s] %(message)s"
            )
            console_handler.setFormatter(text_formatter)
            logger.addHandler(console_handler)

            # Test logger with messages at all levels
            logger.debug("EventLoopMonitor logger initialized - DEBUG test")
            logger.info("EventLoopMonitor logger initialized - INFO test")
            logger.warning("EventLoopMonitor logger initialized - WARNING test")
            logger.error("EventLoopMonitor logger initialized - ERROR test")

            self._verbose_print(
                f"Logger setup complete with JSON and text output to {log_path}"
            )

            # Create a special marker file to show logging is active
            marker_path = log_dir / f"ACTIVE_MONITOR_{self.session_id}.marker"
            with open(marker_path, "w") as f:
                f.write(f"Monitor active since: {datetime.now().isoformat()}\n")
                f.write(f"Log file: {log_path}\n")
                f.write(
                    f"Log rotation: max_size={self.MAX_LOG_SIZE/1024/1024}MB, backups={self.MAX_LOG_BACKUPS}\n"
                )

            # Add log stats to the marker file
            try:
                log_stats = self._get_log_directory_stats(log_dir)
                with open(marker_path, "a") as f:
                    f.write(
                        f"\nLog directory stats: {json.dumps(log_stats, indent=2)}\n"
                    )
            except Exception as e:
                self._verbose_print(f"Failed to write log stats: {e}")

            return logger

        except Exception as e:
            self._verbose_print(f"ERROR setting up logger: {e}")
            traceback.print_exc()

            # Last resort - create a file directly in the current directory
            desperate_log = f"emergency_log_{self.session_id}.txt"
            try:
                with open(desperate_log, "w") as f:
                    f.write(
                        f"Emergency log created at {datetime.now().isoformat()} due to error: {e}\n"
                    )
                    f.write(traceback.format_exc())
                self._verbose_print(f"Created emergency log: {desperate_log}")
            except Exception as emergency_err:
                self._verbose_print(
                    f"FATAL: Even emergency logging failed! Error: {emergency_err}"
                )

            # Create a basic fallback logger that just prints to console
            console_logger = logging.getLogger(f"fallback_{self.session_id}")
            console_logger.setLevel(logging.DEBUG)

            if console_logger.hasHandlers():
                console_logger.handlers.clear()

            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(f"[FALLBACK-{self.session_id}] %(message)s")
            console_handler.setFormatter(formatter)
            console_logger.addHandler(console_handler)

            console_logger.warning(f"Using fallback logger due to critical error: {e}")
            return console_logger

    def _get_log_directory_stats(self, log_dir):
        """Get statistics about the log directory."""
        try:
            stats = {
                "total_size_mb": 0,
                "file_count": 0,
                "file_types": {},
                "largest_files": [],
            }

            # Get all files in the directory
            all_files = list(log_dir.glob("*"))
            stats["file_count"] = len(all_files)

            # Track largest files
            largest_files = []

            for file_path in all_files:
                if not file_path.is_file():
                    continue

                # Get file size
                size_mb = file_path.stat().st_size / (1024 * 1024)
                stats["total_size_mb"] += size_mb

                # Track file type
                ext = file_path.suffix
                if ext not in stats["file_types"]:
                    stats["file_types"][ext] = {"count": 0, "size_mb": 0}

                stats["file_types"][ext]["count"] += 1
                stats["file_types"][ext]["size_mb"] += size_mb

                # Track largest files
                heapq.heappush(largest_files, (size_mb, str(file_path.name)))
                if len(largest_files) > 5:  # Keep top 5
                    heapq.heappop(largest_files)

            # Format largest files for output
            stats["largest_files"] = [
                {"name": name, "size_mb": round(size, 2)}
                for size, name in sorted(largest_files, reverse=True)
            ]

            # Round values for readability
            stats["total_size_mb"] = round(stats["total_size_mb"], 2)
            for ext in stats["file_types"]:
                stats["file_types"][ext]["size_mb"] = round(
                    stats["file_types"][ext]["size_mb"], 2
                )

            return stats
        except Exception as e:
            self._verbose_print(f"Error getting log directory stats: {e}")
            return {"error": str(e)}

    # The rest of the methods (start, stop, monitor, etc.) remain the same
    # ...
