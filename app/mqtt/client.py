"""MQTT client for publishing Wake-on-LAN events."""
import asyncio
from typing import Any, Dict, Optional

import aiomqtt

from app.core.config import settings
from app.logging_config import get_application_logger

logger = get_application_logger()


class MQTTClient:
    """Async MQTT client for publishing WoL events."""

    def __init__(self) -> None:
        self.client: Optional[aiomqtt.Client] = None
        self.connected: bool = False

    async def connect(self) -> None:
        """Connect to MQTT broker."""
        if not settings.MQTT_BROKER:
            logger.info("MQTT broker not configured, skipping connection")
            return

        try:
            client_config: Dict[str, Any] = {
                "hostname": settings.MQTT_BROKER,
                "port": settings.MQTT_PORT,
                "keepalive": settings.MQTT_KEEPALIVE,
            }
            if settings.MQTT_USER and settings.MQTT_PASSWORD:
                client_config["username"] = settings.MQTT_USER
                client_config["password"] = settings.MQTT_PASSWORD

            self.client = aiomqtt.Client(**client_config)
            await self.client.__aenter__()
            self.connected = True
            logger.info(
                "Connected to MQTT broker",
                broker=settings.MQTT_BROKER,
                port=settings.MQTT_PORT,
            )
        except Exception as e:
            logger.error("MQTT connection failed", error=str(e))
            self.connected = False

    async def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        if self.client and self.connected:
            try:
                await self.client.__aexit__(None, None, None)
                self.connected = False
                logger.info("Disconnected from MQTT broker")
            except Exception as e:
                logger.error("MQTT disconnect error", error=str(e))

    async def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        qos: int = 1,
        retain: bool = False,
    ) -> bool:
        """Publish a message to an MQTT topic.

        Args:
            topic: MQTT topic (without prefix)
            payload: JSON-serializable payload
            qos: Quality of Service (0, 1, 2)
            retain: Whether to retain the message

        Returns:
            True if published successfully, False otherwise
        """
        if not self.client or not self.connected:
            logger.warning("MQTT not connected, skipping publish", topic=topic)
            return False

        import json

        payload_json = json.dumps(payload)
        full_topic = f"{settings.MQTT_TOPIC_PREFIX}/{topic}"

        try:
            await self.client.publish(
                full_topic,
                payload=payload_json.encode("utf-8"),
                qos=qos,
                retain=retain,
            )
            logger.debug("MQTT message published", topic=full_topic, qos=qos)
            return True
        except Exception as e:
            logger.error("MQTT publish failed", topic=full_topic, error=str(e))
            return False

    async def publish_device_status(
        self,
        device_name: str,
        online: bool,
        latency_ms: Optional[float] = None,
        method: Optional[str] = None,
    ) -> None:
        """Publish device status event."""
        topic = f"device/{device_name}/status"
        payload = {
            "device": device_name,
            "online": online,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        if latency_ms is not None:
            payload["latency_ms"] = latency_ms
        if method:
            payload["method"] = method
        await self.publish(topic, payload)

    async def publish_wake_event(
        self,
        device_name: str,
        mac_address: str,
        success: bool,
        triggered_by: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """Publish wake event."""
        topic = "events/wake"
        payload = {
            "device": device_name,
            "mac_address": mac_address,
            "success": success,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        if triggered_by:
            payload["triggered_by"] = triggered_by
        if error:
            payload["error"] = error
        await self.publish(topic, payload)


# Global MQTT client instance
mqtt_client = MQTTClient()


async def get_mqtt_client() -> MQTTClient:
    """Get the global MQTT client instance."""
    return mqtt_client
