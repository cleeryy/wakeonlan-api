"""Server-Sent Events (SSE) broadcast manager."""
import asyncio
import json
from datetime import datetime
from typing import Any, Dict

from app.logging_config import get_application_logger

logger = get_application_logger()


class BroadcastManager:
    """Manages SSE client connections and broadcasts events."""

    def __init__(self, heartbeat_interval: int = 15) -> None:
        self._queues: Dict[int, asyncio.Queue] = {}
        self._heartbeat_interval = heartbeat_interval
        self._next_client_id = 0
        self._lock = asyncio.Lock()

    async def connect(self) -> int:
        """Register a new client and return its ID.

        Returns:
            Client ID (integer) to identify the connection
        """
        async with self._lock:
            client_id = self._next_client_id
            self._next_client_id += 1
            self._queues[client_id] = asyncio.Queue(maxsize=1000)
            logger.debug("SSE client connected", client_id=client_id, total_clients=len(self._queues))
            return client_id

    async def disconnect(self, client_id: int) -> None:
        """Unregister a client."""
        async with self._lock:
            if client_id in self._queues:
                del self._queues[client_id]
                logger.debug("SSE client disconnected", client_id=client_id, total_clients=len(self._queues))

    async def broadcast(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast an event to all connected clients.

        Args:
            event_type: Event type string (e.g., 'wake', 'device_status')
            data: JSON-serializable data payload
        """
        message = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        message_str = f"data: {json.dumps(message)}\n\n"

        # Copy client IDs and queues to avoid modification during iteration
        async with self._lock:
            clients = list(self._queues.items())  # (client_id, queue)

        # Put message in each client's queue, dropping oldest if full
        for client_id, queue in clients:
            try:
                if queue.full():
                    # Drop oldest message to make room
                    try:
                        queue.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                await queue.put(message_str)
            except Exception as e:
                logger.warning("SSE broadcast failed", client_id=client_id, error=str(e))

    async def generate(self, client_id: int):
        """Generate SSE stream for a specific client.

        This is an async generator that yields SSE-formatted strings.
        It sends heartbeats periodically to keep the connection alive.

        Args:
            client_id: Client ID from connect()

        Yields:
            SSE formatted strings
        """
        queue = self._queues.get(client_id)
        if not queue:
            return

        try:
            while True:
                # Wait for a message with timeout to send heartbeats
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=self._heartbeat_interval)
                    yield message
                except asyncio.TimeoutError:
                    # Send heartbeat comment
                    yield f": heartbeat {datetime.utcnow().isoformat()}Z\n\n"
        except asyncio.CancelledError:
            # Client disconnected
            logger.debug("SSE generator cancelled", client_id=client_id)
            raise
        except Exception as e:
            logger.error("SSE generator error", client_id=client_id, error=str(e))
        finally:
            await self.disconnect(client_id)


# Global broadcast manager instance
broadcast_manager = BroadcastManager()


async def get_broadcast_manager() -> BroadcastManager:
    """Get the global broadcast manager instance."""
    return broadcast_manager
