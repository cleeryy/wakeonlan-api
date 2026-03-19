<div align="center">

# 🌐 Wake-on-LAN API v2

### ⚡ A full-featured REST API to remotely manage and wake devices with authentication, webhooks, MQTT, and real-time updates

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker&logoColor=white)](https://hub.docker.com/)
[![GitHub Container Registry](https://img.shields.io/badge/GitHub%20Container%20Registry-ghcr.io-blue?logo=github)](https://ghcr.io/cleeryy/wakeonlan-api)

[![GitHub stars](https://img.shields.io/github/stars/cleeryy/wakeonlan-api?style=social)](https://github.com/cleeryy/wakeonlan-api/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/cleeryy/wakeonlan-api?style=social)](https://github.com/cleeryy/wakeonlan-api/network/members)
[![GitHub issues](https://img.shields.io/github/issues/cleeryy/wakeonlan-api)](https://github.com/cleeryy/wakeonlan-api/issues)

**🚀 Quick Start:** `docker run -d --network host -e DEFAULT_MAC="AA:BB:CC:DD:EE:FF" ghcr.io/cleeryy/wakeonlan-api`

</div>

---

## 📖 Overview

Wake-on-LAN API v2 is a production-ready, feature-rich API for remotely waking devices on your network. It goes beyond simple magic packet sending to provide a complete device management platform with security, observability, and integration capabilities.

### Key Features

- 🔐 **API Key Authentication** – Secure access with hashed API keys, key rotation, and deactivation
- ⚡ **Rate Limiting** – Per-endpoint and per-API-key limits to prevent abuse
- 📋 **Device Registry** – Store and manage devices with names, MAC addresses, IPs, and custom ports
- 🔍 **Device Status Checking** – Ping or ARP-based online detection with caching
- 📜 **Wake History** – Comprehensive audit log of all wake attempts with timestamps and outcomes
- 🔗 **Webhook Notifications** – Configurable outgoing webhooks with HMAC signatures and exponential backoff retry
- 📡 **MQTT Integration** – Publish wake events to an MQTT broker for home automation (Home Assistant, etc.)
- ⚡ **Server-Sent Events (SSE)** – Real-time event streaming for live dashboards and notifications
- 🏗️ **Async Architecture** – Built on FastAPI with async SQLAlchemy for high performance
- 📦 **Docker Ready** – Pre-built images, host networking support, and entrypoint migrations
- 🧪 **Tested** – Comprehensive test suite with CI/CD via GitHub Actions

---

## 🚀 Quick Start

### Using Docker (Easiest)

```bash
# Pull the latest image
docker pull ghcr.io/cleeryy/wakeonlan-api:latest

# Run with host networking and a default MAC
docker run -d \
  --network host \
  -e DEFAULT_MAC="AA:BB:CC:DD:EE:FF" \
  --name wakeonlan-api \
  ghcr.io/cleeryy/wakeonlan-api:latest
```

The API will be available at `http://localhost:8080`.

### Using Docker Compose

1. **Create `docker-compose.yml`**

```yaml
services:
  wakeonlan-api:
    image: ghcr.io/cleeryy/wakeonlan-api:latest
    network_mode: host
    environment:
      - DEFAULT_MAC=${DEFAULT_MAC}
      - DB_URL=sqlite+aiosqlite:///./wakeonlan.db
      # Optional: enable MQTT
      # - MQTT_BROKER=localhost
      # - FEATURE_MQTT_ENABLED=true
    env_file:
      - .env
    restart: unless-stopped
```

2. **Create `.env` file**

```bash
DEFAULT_MAC=AA:BB:CC:DD:EE:FF
# Optional: generate an initial API key
API_KEY_INITIAL=$(openssl rand -hex 16)
```

3. **Start the service**

```bash
docker compose up -d
```

### Local Development

```bash
# Clone repository
git clone https://github.com/cleeryy/wakeonlan-api
cd wakeonlan-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (or copy .env.example to .env)
export DEFAULT_MAC="AA:BB:CC:DD:EE:FF"
export DB_URL="sqlite+aiosqlite:///./wakeonlan.db"

# Run migrations (optional, tables created automatically in dev)
alembic upgrade head

# Start the server
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

---

## 🔒 Why Host Networking?

Wake-on-LAN magic packets are **broadcast packets** that must reach all devices on the physical network. Docker's default bridge network isolates containers and blocks broadcasts. **Host networking** (`--network host`) gives the container direct access to the host's network interface, allowing magic packets to properly broadcast.

Without host networking, WoL packets will be trapped inside Docker's internal network and won't reach your devices.

---

## ⚙️ Configuration

All configuration is done via environment variables. Copy `.env.example` to `.env` and customize.

### Core Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DEFAULT_MAC` | Default MAC address for `/wake` endpoint | None | No (but recommended) |
| `DB_URL` | Database connection URL | `sqlite+aiosqlite:///./wakeonlan.db` | No |
| `API_KEY_INITIAL` | Initial API key to auto-create on first startup | None | No |

### Authentication & Rate Limiting

| Variable | Description | Default |
|----------|-------------|---------|
| `RATE_LIMIT_DEFAULT` | Default rate limit (e.g., `60/minute`) | `60/minute` |
| `RATE_LIMIT_WAKE` | Rate limit for wake endpoints | `10/minute` |
| `RATE_LIMIT_HEALTH` | Rate limit for health check | `60/minute` |
| `RATE_LIMIT_PER_KEY` | Apply rate limiting per API key when available | `true` |

### Webhooks

| Variable | Description | Default |
|----------|-------------|---------|
| `WEBHOOK_MAX_RETRIES` | Maximum retry attempts for failed webhooks | `5` |
| `WEBHOOK_RETRY_BASE_DELAY` | Base delay for exponential backoff (seconds) | `1.0` |
| `WEBHOOK_RETRY_MAX_DELAY` | Maximum delay between retries (seconds) | `60.0` |
| `WEBHOOK_TIMEOUT` | HTTP request timeout (seconds) | `10.0` |
| `FEATURE_WEBHOOKS_ENABLED` | Enable/disable webhook feature | `true` |

### MQTT (Optional)

| Variable | Description | Default |
|----------|-------------|---------|
| `MQTT_BROKER` | MQTT broker host (e.g., `localhost`) | None |
| `MQTT_PORT` | MQTT broker port | `1883` |
| `MQTT_USER` | MQTT username (optional) | None |
| `MQTT_PASSWORD` | MQTT password (optional) | None |
| `MQTT_TOPIC_PREFIX` | MQTT topic prefix (default: `wol`) | `wol` |
| `MQTT_KEEPALIVE` | MQTT keepalive interval (seconds) | `60` |
| `FEATURE_MQTT_ENABLED` | Enable MQTT integration | `false` |

### Device Status Checking

| Variable | Description | Default |
|----------|-------------|---------|
| `STATUS_PING_TIMEOUT` | ICMP ping timeout (seconds) | `1.0` |
| `STATUS_PING_COUNT` | Number of ping attempts | `1` |
| `STATUS_ARP_ENABLED` | Enable ARP cache fallback (Linux only) | `true` |
| `STATUS_CACHE_TTL` | Cache TTL for status checks (seconds) | `5` |

### Server-Sent Events (SSE)

| Variable | Description | Default |
|----------|-------------|---------|
| `SSE_HEARTBEAT_INTERVAL` | Heartbeat interval (seconds) | `15` |
| `SSE_MAX_QUEUE_SIZE` | Max events queued per client | `1000` |
| `FEATURE_SSE_ENABLED` | Enable SSE endpoint | `true` |

### Logging

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |
| `LOG_FORMAT` | Log format (`json` or `console`) | `json` |
| `LOG_DEST` | Log destination (`stdout` or `file`) | `stdout` |
| `LOG_FILE` | Log file path if `LOG_DEST=file` | None |

---

## 🔑 Authentication

All protected endpoints require an API key passed in the `X-API-Key` header.

### Creating an API Key

Use the `/auth/keys` endpoint (requires an existing API key) or set `API_KEY_INITIAL` to auto-create an initial admin key on first startup.

```bash
# Create a new API key (using existing key)
curl -X POST "http://localhost:8080/auth/keys" \
  -H "X-API-Key: YOUR_EXISTING_KEY" \
  -H "Content-Type: application/json" \
  -d '{"key_name": "My Laptop", "is_active": true}'
```

Response:

```json
{
  "api_key": "a1b2c3d4e5f6...",  // Plaintext key - store it securely!
  "id": 1,
  "key_name": "My Laptop",
  "is_active": true,
  "created_at": "2026-03-19T15:00:00Z",
  "last_used_at": null
}
```

**Important:** The plaintext API key is only shown once upon creation. Store it securely; you cannot retrieve it later.

### Managing API Keys

- **List keys:** `GET /auth/keys`
- **Deactivate:** `POST /auth/keys/{id}/deactivate`
- **Reactivate:** `POST /auth/keys/{id}/reactivate`

---

## 📡 API Reference

### Public Endpoints (No Auth)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Welcome message |
| `GET` | `/health` | Health check (returns `{"status":"healthy"}`) |

### Device Management (Auth Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/devices` | Create a new device |
| `GET` | `/devices` | List all devices (query `?enabled=true|false`) |
| `GET` | `/devices/{id}` | Get device details |
| `PUT` | `/devices/{id}` | Update a device |
| `DELETE` | `/devices/{id}` | Delete a device |
| `GET` | `/devices/{id}/status` | Check if device is online (ping/ARP) |

**Device Schema (Create/Update):**

```json
{
  "name": "My PC",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "ip_address": "192.168.1.100",
  "port": 9,
  "enabled": true
}
```

### Wake Endpoints (Auth Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/wake` | Wake the default MAC (from `DEFAULT_MAC` env) |
| `GET` | `/wake/{mac_address}` | Wake a specific device by MAC |

**Response (Success):**

```json
{
  "message": "Wake packet sent to AA:BB:CC:DD:EE:FF"
}
```

**Response (Error):** `500` with `{"detail": "Failed to send WoL packet: ..."}`

### Webhook Management (Auth Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/webhooks` | Create webhook configuration |
| `GET` | `/webhooks` | List all webhooks |
| `GET` | `/webhooks/{id}` | Get webhook details |
| `PUT` | `/webhooks/{id}` | Update webhook |
| `DELETE` | `/webhooks/{id}` | Delete webhook |

**Webhook Schema (Create/Update):**

```json
{
  "name": "Discord Notification",
  "url": "https://discord.com/api/webhooks/...",
  "event_types": ["wol_sent", "wol_success", "wol_failure"],
  "headers": {
    "Authorization": "Bearer token"
  },
  "secret": "hmac-secret-key",  // optional, for signature
  "is_active": true,
  "max_retries": 5,
  "retry_base_delay": 1.0,
  "retry_max_delay": 60.0,
  "timeout": 10.0
}
```

**Event Types:** `wol_sent`, `wol_success`, `wol_failure`, `device_online` (future)

**Webhook Payload Example:**

```json
{
  "event_type": "wol_sent",
  "payload": {
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "device_name": "My PC",
    "triggered_by": "Admin API Key"
  },
  "timestamp": "2026-03-19T15:00:00Z"
}
```

If a `secret` is configured, the request includes an `X-Webhook-Signature` header with HMAC-SHA256 of the JSON body.

### Server-Sent Events (SSE) (Auth Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/events` | Stream real-time events |

**Query Parameters:**
- `event_types` (optional): Comma-separated list of event types to filter (e.g., `wake,device_status`)

**Response:** `text/event-stream` with messages in SSE format:

```
data: {"event":"wake","data":{"mac_address":"AA:BB:...","success":true,...},"timestamp":"..."}
```

Heartbeat comments are sent periodically to keep connections alive.

---

## 🔌 Webhooks

Webhooks allow you to integrate WoL events with external systems like Discord, Slack, Home Assistant, or custom monitoring.

### Setup

1. Create a webhook configuration via API or admin UI (future)
2. Provide the target URL, select event types, optionally set a secret for HMAC signing
3. When a wake event occurs, a delivery record is created and queued for retry
4. The background worker attempts delivery with exponential backoff (1s, 5s, 30s, 5m, 30m) up to `max_retries`
5. Delivery status is tracked in `webhook_deliveries` table

### Retry Logic

- Failed deliveries are retried with exponential backoff
- After `max_retries` attempts, the delivery is marked as failure
- Circuit breaker pattern can be implemented per-webhook (future)

---

## 📡 MQTT Integration

Publish wake events to an MQTT broker for integration with home automation platforms like Home Assistant.

### Configuration

Set the following environment variables:

```bash
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_TOPIC_PREFIX=wol
FEATURE_MQTT_ENABLED=true
```

If your broker requires authentication, set `MQTT_USER` and `MQTT_PASSWORD`.

### Topics

Events are published to topics under the configured prefix:

- `wol/device/{device_name}/status` – Device status updates (online/offline)
- `wol/events/wake` – Wake events

Payloads are JSON with fields like `event_type`, `payload`, `timestamp`.

Example MQTT message:

```json
{
  "event_type": "wake",
  "payload": {
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "device_name": "Gaming PC",
    "triggered_by": "Admin API Key"
  },
  "timestamp": "2026-03-19T15:00:00Z"
}
```

---

## ⚡ Server-Sent Events (SSE)

Connect to `/events` to receive real-time updates in your browser or application.

### Usage

```javascript
const eventSource = new EventSource('http://localhost:8080/events?event_types=wake,device_status', {
  headers: { 'X-API-Key': 'your-api-key' }
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.event, data.data);
};

eventSource.onerror = (err) => {
  console.error('SSE error:', err);
};
```

Events are broadcast when:
- A wake packet is sent (success or failure)
- Device status changes (future)
- Webhook deliveries occur (future)

---

## 🏗️ Architecture

### Technology Stack

- **FastAPI** – Modern, fast web framework with automatic OpenAPI docs
- **SQLAlchemy 2.0** – Async ORM with PostgreSQL/MySQL/SQLite support
- **Alembic** – Database migrations
- **slowapi** – Rate limiting with in-memory store (Redis ready)
- **structlog** – Structured JSON logging
- **httpx** – Async HTTP client for webhooks
- **aiomqtt** – Async MQTT client
- **ping3** – ICMP ping for device status
- **passlib[bcrypt]** – API key hashing
- **wakeonlan** – Magic packet sending

### Project Structure

```
wakeonlan-api/
├── app/
│   ├── main.py                 # FastAPI app with all routes
│   ├── core/
│   │   └── config.py           # Pydantic settings
│   ├── db/
│   │   ├── database.py         # Async engine & session
│   │   └── session.py          # Re-exports
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── device.py
│   │   ├── api_key.py
│   │   ├── wake_history.py
│   │   ├── webhook_config.py
│   │   └── webhook_delivery.py
│   ├── schemas/                # Pydantic request/response schemas
│   ├── crud/                   # CRUD operations for all models
│   ├── auth/
│   │   └── api_key.py         # API key authentication dependency
│   ├── rate_limit/
│   │   └── __init__.py        # slowapi configuration
│   ├── status/
│   │   └── checker.py         # Device status (ping/ARP)
│   ├── webhooks/
│   │   ├── sender.py          # Webhook HTTP sender with HMAC
│   │   └── worker.py          # Retry background task
│   ├── mqtt/
│   │   └── client.py          # MQTT client wrapper
│   ├── events/
│   │   └── broadcast.py       # SSE broadcast manager
│   ├── logging_config.py      # Structured logging setup
│   └── middleware.py          # Request logging middleware
├── alembic/
│   ├── versions/
│   │   └── 20260319_initial.py
│   └── env.py
├── tests/
│   ├── conftest.py             # Pytest fixtures
│   ├── test_auth.py
│   ├── test_rate_limit.py
│   ├── test_devices.py
│   ├── test_status.py
│   ├── test_webhooks.py
│   ├── test_sse.py
│   └── test_mqtt.py
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh
├── requirements.txt
├── pytest.ini
└── .env.example
```

---

## 🧪 Testing

The project includes a comprehensive test suite using `pytest` and `pytest-asyncio`.

### Running Tests

```bash
# Install dev dependencies (already in requirements.txt)
pip install -r requirements.txt

# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v

# Generate coverage report
pytest --cov=app --cov-report=html
```

### CI/CD

GitHub Actions workflow (`.github/workflows/test.yml`) runs on every push and pull request:

- Syntax check (`python -m compileall`)
- Pytest with coverage
- Uploads coverage and test results as artifacts

---

## 🐳 Docker Deployment

### Build from Source

```bash
docker build -t wakeonlan-api .
docker run -d --network host -e DEFAULT_MAC="AA:BB:CC:DD:EE:FF" wakeonlan-api
```

### Using Docker Compose

```bash
docker compose up -d
```

### Entrypoint Script

The `entrypoint.sh` script performs the following on container start:

1. Wait for database to be ready (PostgreSQL only)
2. Run Alembic migrations (`alembic upgrade head`)
3. Start Uvicorn server

This ensures the database schema is always up-to-date.

---

## 📊 Database Migrations

Alembic is configured for async migrations. The initial migration (`alembic/versions/20260319_initial.py`) creates all tables:

- `devices`
- `api_keys`
- `wake_history`
- `webhook_configs`
- `webhook_deliveries`

### Running Migrations Manually

```bash
# Upgrade to latest
alembic upgrade head

# Generate a new migration (after model changes)
alembic revision --autogenerate -m "description"
```

---

## 🛡️ Security Considerations

- **API Keys** are hashed with bcrypt; plaintext keys are only shown once upon creation
- **Rate Limiting** prevents brute-force and DoS attacks
- **HMAC Signatures** for webhooks ensure payload integrity
- **Structured Logging** includes request IDs for audit trails
- **Non-root Container User** reduces attack surface
- **Host Networking** requirement limits exposure; do not expose directly to the internet without additional firewall/VPN

**Never expose this API directly to the public internet** without:
- VPN or reverse proxy with additional authentication
- Strict firewall rules
- TLS encryption (use a reverse proxy like Nginx/Traefik)

---

## 🧩 Integration Examples

### Home Assistant (MQTT)

```yaml
# configuration.yaml
mqtt:
  sensor:
    - name: "PC Status"
      state_topic: "wol/device/gaming_pc/status"
      value_template: "{{ value_json.online }}"
```

### Discord Webhook

Create a webhook pointing to your Discord webhook URL, subscribe to `wol_sent` and `wol_success` events.

### Custom Dashboard (SSE)

```javascript
// Connect to SSE stream
const source = new EventSource('http://localhost:8080/events?event_types=wake', {
  headers: { 'X-API-Key': 'your-key' }
});

source.onmessage = (e) => {
  const event = JSON.parse(e.data);
  if (event.event === 'wake') {
    console.log(`${event.data.device_name} woke!`);
  }
};
```

---

## 🐛 Troubleshooting

### WoL packets not waking devices

- Ensure Wake-on-LAN is enabled in BIOS/UEFI and network adapter settings
- Verify the device is connected via Ethernet (WiFi often doesn't support WoL)
- Confirm the MAC address is correct
- **Verify host networking is enabled** (`--network host`)
- Check that the host firewall allows UDP broadcast on port 9 (or custom port)

### API returns 401

- Ensure you're sending `X-API-Key` header with a valid, active API key
- Check that the key hasn't been deactivated

### Rate limit exceeded

- Reduce request frequency or request a higher limit
- Use multiple API keys (each has its own limit if `RATE_LIMIT_PER_KEY=true`)

### MQTT connection fails

- Verify `MQTT_BROKER` is reachable from the container
- Check credentials if required
- Ensure `FEATURE_MQTT_ENABLED=true`

### Webhooks not delivering

- Check webhook URL is reachable and returns `2xx`
- Verify the webhook is active
- Look at `webhook_deliveries` table for error messages
- Ensure outbound HTTP is allowed from the container

---

## 📝 License

MIT License – see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with ❤️ by [Cléry Arque-Ferradou](https://github.com/cleeryy)

Inspired by the need for a secure, production-ready WoL API for home labs and small networks.
