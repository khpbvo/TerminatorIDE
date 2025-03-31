# Add this to terminatoride/utils/event_loop_monitor.py
import asyncio
import logging
import time
from pathlib import Path


class EventLoopMonitor:
    def __init__(self, check_interval=1.0):
        self.check_interval = check_interval
        self.running = False
        self.task = None

        # Set up logging
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """Set up a dedicated logger for the event loop monitor."""
        # Create logs directory if it doesn't exist
        log_dir = Path.home() / ".terminatoride" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create logger
        logger = logging.getLogger("event_loop_monitor")
        logger.setLevel(logging.DEBUG)

        # Remove existing handlers to avoid duplicates
        if logger.hasHandlers():
            logger.handlers.clear()

        # Create file handler
        log_path = log_dir / "event_loop_monitor.log"
        file_handler = logging.FileHandler(str(log_path))
        file_handler.setLevel(logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(file_handler)

        # Also add console output for immediate visibility
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

    async def start(self):
        """Start monitoring the event loop."""
        if self.running:
            return

        self.running = True
        self.task = asyncio.create_task(self._monitor())
        self.logger.info("Event loop monitor started")

    async def _monitor(self):
        """Monitor the event loop for blockages."""
        last_time = time.time()

        while self.running:
            await asyncio.sleep(self.check_interval)

            current_time = time.time()
            elapsed = current_time - last_time - self.check_interval

            # If there was a significant delay, the loop was blocked
            if elapsed > 0.1:  # 100ms threshold
                self.logger.warning(f"EVENT LOOP BLOCKED for {elapsed:.2f}s")

                # Log info about all running tasks
                tasks = [
                    t for t in asyncio.all_tasks() if t is not asyncio.current_task()
                ]

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
                                frame_info.append(f"{filename}:{lineno} in {name}()")

                            self.logger.info(
                                f"Task {i} blocked at: {' -> '.join(frame_info)}"
                            )

            last_time = current_time

    async def stop(self):
        """Stop the event loop monitor."""
        if not self.running:
            return

        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        self.logger.info("Event loop monitor stopped")
