import asyncio
import logging
import os
import sys
import time
import traceback
from pathlib import Path


class EventLoopMonitor:
    def __init__(self, check_interval=1.0):
        self.check_interval = check_interval
        self.running = False
        self.task = None

        # First, print directly to stdout for immediate feedback
        print("Initializing EventLoopMonitor")

        # Set up logging
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """Set up a dedicated logger for the event loop monitor."""
        try:
            # Create logs directory if it doesn't exist
            log_dir = Path.home() / ".terminatoride" / "logs"
            print(f"Log directory path: {log_dir}")

            # Make sure directory exists
            log_dir.mkdir(parents=True, exist_ok=True)

            if not log_dir.exists():
                print(f"Failed to create log directory: {log_dir}")
                # Try with direct OS commands as a fallback
                os.makedirs(str(log_dir), exist_ok=True)
                print(f"Retried directory creation: {os.path.exists(str(log_dir))}")

            # Create logger
            logger = logging.getLogger("event_loop_monitor")
            logger.setLevel(logging.DEBUG)

            # Remove existing handlers to avoid duplicates
            if logger.hasHandlers():
                logger.handlers.clear()

            # Create file handler
            log_path = log_dir / "event_loop_monitor.log"
            print(f"Log file path: {log_path}")

            # Try with direct file creation to check for permission issues
            try:
                with open(str(log_path), "a") as f:
                    f.write("Logger initialization test\n")
                print("Successfully wrote test line to log file")
            except Exception as e:
                print(f"Error writing to log file: {e}")

            file_handler = logging.FileHandler(str(log_path))
            file_handler.setLevel(logging.DEBUG)

            # Create formatter
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            file_handler.setFormatter(formatter)

            # Add handler to logger
            logger.addHandler(file_handler)

            # Also add console output for immediate visibility
            console_handler = logging.StreamHandler(sys.stdout)  # Explicitly use stdout
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            # Test logger
            logger.info("EventLoopMonitor logger initialized")
            print("Logger setup complete")

            return logger

        except Exception as e:
            print(f"Error setting up logger: {e}")
            traceback.print_exc()

            # Create a basic fallback logger that just prints to console
            logger = logging.getLogger("event_loop_monitor_fallback")
            logger.setLevel(logging.DEBUG)

            if logger.hasHandlers():
                logger.handlers.clear()

            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            logger.warning(f"Using fallback logger due to error: {e}")
            return logger

    async def start(self):
        """Start monitoring the event loop."""
        try:
            print("Starting event loop monitor")
            if self.running:
                print("Monitor already running")
                return

            self.running = True
            self.task = asyncio.create_task(self._monitor())
            self.logger.info("Event loop monitor started")
            print("Event loop monitor task created and started")
        except Exception as e:
            print(f"Error starting monitor: {e}")
            traceback.print_exc()

    async def _monitor(self):
        """Monitor the event loop for blockages."""
        try:
            print("Monitor loop starting")
            last_time = time.time()

            while self.running:
                await asyncio.sleep(self.check_interval)

                current_time = time.time()
                elapsed = current_time - last_time - self.check_interval

                # Log to console on first few iterations to confirm it's running
                static_counter = getattr(self, "_counter", 0)
                if static_counter < 5:
                    print(f"Monitor tick {static_counter}: elapsed={elapsed:.4f}s")
                    setattr(self, "_counter", static_counter + 1)

                # If there was a significant delay, the loop was blocked
                if elapsed > 0.1:  # 100ms threshold
                    message = f"EVENT LOOP BLOCKED for {elapsed:.2f}s"
                    print(message)  # Direct console output
                    self.logger.warning(message)

                    # Log info about all running tasks
                    tasks = [
                        t
                        for t in asyncio.all_tasks()
                        if t is not asyncio.current_task()
                    ]

                    print(f"Running tasks: {len(tasks)}")
                    self.logger.info(f"Running tasks: {len(tasks)}")

                    for i, task in enumerate(tasks):
                        # Get stack for running tasks to see where they're stuck
                        if not task.done():
                            stack = task.get_stack()
                            if stack:
                                # Format the most recent frames
                                frame_info = []
                                for frame in stack[:5]:  # Get top 5 frames
                                    filename = frame.filename.split("/")[-1]
                                    lineno = frame.lineno
                                    name = frame.name
                                    frame_info.append(
                                        f"{filename}:{lineno} in {name}()"
                                    )

                                task_info = (
                                    f"Task {i} blocked at: {' -> '.join(frame_info)}"
                                )
                                print(task_info)  # Direct console output
                                self.logger.info(task_info)

                last_time = current_time

        except asyncio.CancelledError:
            print("Monitor task cancelled")
            raise
        except Exception as e:
            print(f"Error in monitor loop: {e}")
            traceback.print_exc()
            self.logger.error(f"Monitor loop error: {e}")

    async def stop(self):
        """Stop the event loop monitor."""
        try:
            print("Stopping event loop monitor")
            if not self.running:
                print("Monitor not running")
                return

            self.running = False
            if self.task:
                print("Cancelling monitor task")
                self.task.cancel()
                try:
                    await self.task
                    print("Monitor task cancelled successfully")
                except asyncio.CancelledError:
                    print("Monitor task cancel acknowledged")
                    pass

            self.logger.info("Event loop monitor stopped")
            print("Event loop monitor stopped")
        except Exception as e:
            print(f"Error stopping monitor: {e}")
            traceback.print_exc()
