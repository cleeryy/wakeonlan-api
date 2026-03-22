<div align="center">

# 🌐 Wake-on-LAN API

### ⚡ A lightweight REST API to remotely wake devices using HTTP requests

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker&logoColor=white)](https://hub.docker.com/)
[![GitHub Container Registry](https://img.shields.io/badge/GitHub%20Container%20Registry-ghcr.io-blue?logo=github)](https://ghcr.io/cleeryy/wakeonlan-api)

[![GitHub stars](https://img.shields.io/github/stars/cleeryy/wakeonlan-api?style=social)](https://github.com/cleeryy/wakeonlan-api/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/cleeryy/wakeonlan-api?style=social)](https://github.com/cleeryy/wakeonlan-api/network/members)
[![GitHub issues](https://img.shields.io/github/issues/cleeryy/wakeonlan-api)](https://github.com/cleeryy/wakeonlan-api/issues)

**🚀 Quick Start:** `docker run -d --network host -e DEFAULT_MAC="AA:BB:CC:DD:EE:FF" ghcr.io/cleeryy/wakeonlan-api`

---

</div>

A **simple and lightweight REST API** built with FastAPI to remotely wake devices using Wake-on-LAN (WoL) magic packets. Send HTTP requests to wake up computers and devices on your network.

## ✨ Features

- **RESTful API** with FastAPI framework
- **Wake devices by MAC address** via HTTP requests
- **Device Registry** - Store and manage named devices with JSON persistence
- **Wake by name** - Wake registered devices using friendly names instead of MAC addresses
- **Default MAC configuration** for quick access
- **API Key Authentication** - Secure your API with configurable API keys
- **Rate Limiting** - Built-in protection against abuse (configurable requests per minute)
- **MAC Address Validation** - Automatic validation of MAC address formats (XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX)
- **Health Check Endpoint** - `/health` for monitoring and Docker HEALTHCHECK
- **Broadcast IP Configuration** - Customize broadcast address for specialized network setups
- **WoL Packet Retry Logic** - Automatic retry with configurable attempts and delays
- **Pre-built Docker images** available on GitHub Container Registry
- **Docker support** with multi-stage builds
- **Security-focused** with non-root container user
- **Lightweight** Python 3.12-slim base image
- **Environment-based configuration**

## 🚀 Quick Start

### Using Pre-built Docker Image (Easiest)

**No need to clone the repository!** Just run the pre-built image:

```
# Pull and run the latest image with host networking
docker run -d \
  --network host \
  -e DEFAULT_MAC="AA:BB:CC:DD:EE:FF" \
  --name wakeonlan-api \
  ghcr.io/cleeryy/wakeonlan-api:latest
```

The API will be available at `http://localhost:8080`

**Replace `AA:BB:CC:DD:EE:FF` with your device's actual MAC address.**

### Using Docker Compose (Recommended)

1. **Create a docker-compose.yml file**

```
services:
  wakeonlan-api:
    image: ghcr.io/cleeryy/wakeonlan-api:latest
    network_mode: host
    environment:
      - DEFAULT_MAC=${DEFAULT_MAC}
    env_file:
      - .env
    restart: unless-stopped
```

2. **Create a .env file**

```
DEFAULT_MAC=AA:BB:CC:DD:EE:FF
```

3. **Start the service**

```
docker compose up -d
```

### Using Docker Compose (Build from Source)

1. **Clone the repository**

```
git clone https://github.com/cleeryy/wakeonlan-api
cd wakeonlan-api
```

2. **Configure environment**

```
cp .env.example .env
# Edit .env with your desired configuration
```

3. **Update docker-compose.yml for host networking**

```
services:
  wakeonlan-api:
    build: .
    network_mode: host
    environment:
      - DEFAULT_MAC=${DEFAULT_MAC}
    env_file:
      - .env
    restart: unless-stopped
```

4. **Start the service**

```
docker compose up --build -d
```

## 🔌 Why Host Networking is Required

**Wake-on-LAN requires host networking mode** for the following reasons:

- **Broadcast Packets**: WoL magic packets are broadcast packets that need to reach devices on your **physical network**
- **Docker Isolation**: Docker's default bridge networking creates an isolated network that **prevents broadcasts** from reaching their intended targets
- **Network Access**: Host networking gives the container **direct access** to the host's network interface, allowing magic packets to properly broadcast to all network devices

**Without host networking**, the Wake-on-LAN packets will be trapped within Docker's internal network and won't reach the devices you want to wake up.

## ⚙️ Configuration

### Environment Variables

| Variable                    | Description                                                                 | Default              | Required |
| --------------------------- | --------------------------------------------------------------------------- | -------------------- | -------- |
| `DEFAULT_MAC`               | Default MAC address for `/wake` endpoint                                   | None                 | Yes      |
| `API_KEY`                   | API key(s) for authentication. Single key or comma-separated list          | "" (disabled)        | No       |
| `RATE_LIMIT_REQUESTS`       | Number of requests allowed per time window                                 | `5`                  | No       |
| `RATE_LIMIT_WINDOW_SECONDS` | Time window in seconds for rate limiting                                  | `60`                 | No       |
| `DEVICES_FILE`              | Path to device registry JSON file                                          | `devices.json`       | No       |
| `BROADCAST_IP`              | Custom broadcast IP address for WoL packets (optional)                    | System default       | No       |
| `WOL_RETRIES`               | Number of retry attempts for failed WoL packets                           | `3`                  | No       |
| `WOL_RETRY_DELAY`           | Delay between retry attempts in seconds                                   | `0.5`                | No       |

### For Docker Run

Set environment variables directly in the `docker run` command:

```
docker run -d \
  --network host \
  -e DEFAULT_MAC="AA:BB:CC:DD:EE:FF" \
  -e API_KEY="your-secret-key" \
  -e RATE_LIMIT_REQUESTS="10" \
  -e RATE_LIMIT_WINDOW_SECONDS="60" \
  --name wakeonlan-api \
  ghcr.io/cleeryy/wakeonlan-api:latest
```

### For Docker Compose

Create a `.env` file in your project directory:

```
# Default MAC address for /wake endpoint
DEFAULT_MAC=AA:BB:CC:DD:EE:FF

# API Key(s) - single or comma-separated
API_KEY=your-secret-key

# Rate limiting: 10 requests per 60 seconds
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=60

# Custom broadcast IP (optional)
# BROADCAST_IP=255.255.255.255

# WoL retry settings (optional)
WOL_RETRIES=3
WOL_RETRY_DELAY=0.5

# Device registry file path
DEVICES_FILE=devices.json
```

## 📡 API Endpoints

### GET `/`

**Welcome endpoint** - Check if the API is running

**Response:**

```
{
  "status": 200,
  "message": "Welcome to the Wake-on-LAN API!"
}
```

### GET `/health`

**Health check endpoint** - Used for monitoring and Docker HEALTHCHECK

**Response:**

```
{
  "status": "healthy",
  "service": "wakeonlan-api",
  "timestamp": "2025-03-22T12:34:56.789Z"
}
```

### GET `/wake`

**Wake default device** - Send WoL packet to the configured default MAC address

**Headers (if API_KEY is set):**
- `X-API-Key: your-api-key`

**Response (Success):**

```
{
  "message": "Wake-on-LAN packet sent successfully"
}
```

**Response (Error):**

```
{
  "error": "Failed to send Wake-on-LAN packet: [error details]"
}
```

**Status Codes:**
- `200` - Success
- `403` - Invalid or missing API key (if API_KEY is configured)
- `429` - Rate limit exceeded
- `500` - Failed to send WoL packet

### GET `/wake/{mac_address}`

**Wake specific device** - Send WoL packet to a specific MAC address

**Parameters:**
- `mac_address` (path): Target device MAC address (format: `AA:BB:CC:DD:EE:FF` or `AA-BB-CC-DD-EE-FF`)

**Headers (if API_KEY is set):**
- `X-API-Key: your-api-key`

**Response (Success):**

```
{
  "message": "Wake-on-LAN packet sent successfully to AA:BB:CC:DD:EE:FF device!"
}
```

**Response (Error - Invalid MAC):**

```
{
  "error": "Invalid MAC address format: 'invalid-mac'. Must be XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX"
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid MAC address format
- `403` - Invalid or missing API key (if API_KEY is configured)
- `429` - Rate limit exceeded
- `500` - Failed to send WoL packet

### GET `/devices`

**List all registered devices** - Returns a dictionary of device names and their MAC addresses

**Headers (if API_KEY is set):**
- `X-API-Key: your-api-key`

**Response (Success):**

```
{
  "pc1": "AA:BB:CC:DD:EE:FF",
  "laptop": "11:22:33:44:55:66"
}
```

**Status Codes:**
- `200` - Success
- `403` - Invalid or missing API key (if API_KEY is configured)
- `429` - Rate limit exceeded

### POST `/devices`

**Add a new device** - Register a device with a friendly name

**Headers (if API_KEY is set):**
- `X-API-Key: your-api-key`

**Body (form data):**
- `name` (string, required): Device name (alphanumeric, dashes, underscores)
- `mac` (string, required): MAC address in valid format

**Example using curl:**
```bash
curl -X POST "http://localhost:8080/devices" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=my-pc&mac=AA:BB:CC:DD:EE:FF"
```

**Response (Success):**

```
{
  "message": "Device 'my-pc' added successfully"
}
```

**Response (Error - Duplicate):**

```
{
  "error": "Device 'my-pc' already exists"
}
```

**Response (Error - Invalid MAC):**

```
{
  "error": "Invalid MAC address format: 'invalid-mac'"
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid MAC address format
- `403` - Invalid or missing API key (if API_KEY is configured)
- `409` - Device name already exists
- `429` - Rate limit exceeded
- `500` - Failed to save device

### DELETE `/devices/{name}`

**Delete a device** - Remove a device from the registry by name

**Parameters:**
- `name` (path): Device name to delete

**Headers (if API_KEY is set):**
- `X-API-Key: your-api-key`

**Response (Success):**

```
{
  "message": "Device 'my-pc' deleted successfully"
}
```

**Response (Error - Not Found):**

```
{
  "error": "Device 'my-pc' not found"
}
```

**Status Codes:**
- `200` - Success
- `403` - Invalid or missing API key (if API_KEY is configured)
- `404` - Device not found
- `429` - Rate limit exceeded
- `500` - Failed to delete device

### GET `/wake/device/{name}`

**Wake device by name** - Wake a registered device using its friendly name

**Parameters:**
- `name` (path): Registered device name

**Headers (if API_KEY is set):**
- `X-API-Key: your-api-key`

**Response (Success):**

```
{
  "message": "Wake-on-LAN packet sent successfully to my-pc (AA:BB:CC:DD:EE:FF)!"
}
```

**Response (Error - Not Found):**

```
{
  "error": "Device 'my-pc' not found in registry"
}
```

**Status Codes:**
- `200` - Success
- `403` - Invalid or missing API key (if API_KEY is configured)
- `404` - Device not found in registry
- `429` - Rate limit exceeded
- `500` - Failed to send WoL packet

## 💡 Usage Examples

### Using curl

```bash
# Check API status
curl http://localhost:8080/

# Health check
curl http://localhost:8080/health

# Wake default device
curl http://localhost:8080/wake

# Wake specific device by MAC
curl http://localhost:8080/wake/AA:BB:CC:DD:EE:FF

# List registered devices (if API_KEY configured)
curl -H "X-API-Key: your-secret-key" http://localhost:8080/devices

# Add a new device (if API_KEY configured)
curl -X POST "http://localhost:8080/devices" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=my-pc&mac=AA:BB:CC:DD:EE:FF"

# Delete a device (if API_KEY configured)
curl -X DELETE -H "X-API-Key: your-secret-key" http://localhost:8080/devices/my-pc

# Wake device by name (if API_KEY configured)
curl -H "X-API-Key: your-secret-key" http://localhost:8080/wake/device/my-pc
```

### Using HTTPie

```bash
# Health check
http GET localhost:8080/health

# Wake default device
http GET localhost:8080/wake

# Wake specific device
http GET localhost:8080/wake/AA:BB:CC:DD:EE:FF

# List devices
http GET localhost:8080/devices X-API-Key:your-secret-key

# Add device
http --form POST localhost:8080/devices name=my-pc mac=AA:BB:CC:DD:EE:FF X-API-Key:your-secret-key

# Delete device
http DELETE localhost:8080/devices/my-pc X-API-Key:your-secret-key

# Wake by name
http GET localhost:8080/wake/device/my-pc X-API-Key:your-secret-key
```

### Using Python

```python
import requests

BASE_URL = "http://localhost:8080"
API_KEY = "your-secret-key"  # Set to None if no API key configured
HEADERS = {"X-API-Key": API_KEY} if API_KEY else {}

# Check API status
response = requests.get(f"{BASE_URL}/")
print(response.json())

# Health check
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# Wake default device
response = requests.get(f"{BASE_URL}/wake", headers=HEADERS)
print(response.json())

# Wake specific device by MAC
mac_address = "AA:BB:CC:DD:EE:FF"
response = requests.get(f"{BASE_URL}/wake/{mac_address}", headers=HEADERS)
print(response.json())

# List registered devices
response = requests.get(f"{BASE_URL}/devices", headers=HEADERS)
print(response.json())

# Add a new device
data = {"name": "my-pc", "mac": "AA:BB:CC:DD:EE:FF"}
response = requests.post(f"{BASE_URL}/devices", data=data, headers=HEADERS)
print(response.json())

# Delete a device
response = requests.delete(f"{BASE_URL}/devices/my-pc", headers=HEADERS)
print(response.json())

# Wake device by name
response = requests.get(f"{BASE_URL}/wake/device/my-pc", headers=HEADERS)
print(response.json())
```

## 🐳 Docker

### Pull Pre-built Image

```
# Pull the latest image
docker pull ghcr.io/cleeryy/wakeonlan-api:latest

# Or pull a specific version
docker pull ghcr.io/cleeryy/wakeonlan-api:v1.0.0
```

### Run Pre-built Container

```
docker run -d \
  --network host \
  -e DEFAULT_MAC="AA:BB:CC:DD:EE:FF" \
  --name wakeonlan-api \
  ghcr.io/cleeryy/wakeonlan-api:latest
```

### Build from Source

```
# Clone repository first
git clone https://github.com/cleeryy/wakeonlan-api
cd wakeonlan-api

# Build image
docker build -t wakeonlan-api .

# Run built image with host networking
docker run -d \
  --network host \
  -e DEFAULT_MAC="AA:BB:CC:DD:EE:FF" \
  --name wakeonlan-api \
  wakeonlan-api
```

### Docker Management Commands

```
# View logs
docker logs wakeonlan-api

# Stop container
docker stop wakeonlan-api

# Remove container
docker rm wakeonlan-api

# Using Docker Compose
docker compose logs -f        # View logs
docker compose down          # Stop services
docker compose pull         # Update to latest image
```

## 🔒 Security Considerations

- **API Key Authentication**: Always set `API_KEY` in production to prevent unauthorized access. Use strong, random keys and consider using multiple keys for different clients.
- **Network Access**: Ensure the API is only accessible from trusted networks. Consider using a reverse proxy with additional authentication if exposed to the internet.
- **Host Networking**: Container shares host's network namespace for WoL functionality. Only run trusted containers with host networking.
- **Container Security**: The application runs as a non-root user inside the container for improved security.
- **MAC Address Validation**: All MAC addresses are validated to prevent injection attacks.
- **Rate Limiting**: Configure appropriate rate limits to prevent abuse. Default is 5 requests per minute.
- **Firewall Rules**: Configure appropriate firewall rules to restrict access to the API port (8080).

## 🛠️ Development

### Local Installation

1. **Clone the repository**

```
git clone https://github.com/cleeryy/wakeonlan-api
cd wakeonlan-api
```

2. **Install Python dependencies**

```
pip install -r requirements.txt
```

3. **Set environment variables**

```
export DEFAULT_MAC="AA:BB:CC:DD:EE:FF"
# Optional: export API_KEY="your-secret-key"
```

4. **Run the application**

```
cd app
uvicorn main:app --host 0.0.0.0 --port 8080
```

### Project Structure

```
wakeonlan-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── devices.py           # Device registry with JSON persistence
│   └── utils.py             # Utilities (MAC validation)
├── tests/
│   ├── test_auth.py         # API key authentication tests
│   ├── test_devices.py      # Device registry tests
│   ├── test_ratelimit.py    # Rate limiting tests
│   ├── test_broadcast.py    # Broadcast IP tests
│   └── test_retry.py        # WoL retry logic tests
├── docker-compose.yml       # Docker Compose configuration
├── Dockerfile              # Docker image definition
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── devices.json           # Device registry data (created automatically)
├── coverage.xml           # Test coverage report
└── LICENSE                # MIT License
```

### Testing

Run the test suite:

```
pytest tests/ -v
```

Generate coverage report:

```
pytest tests/ --cov=app --cov-report=xml
```

## 🔧 Requirements

- **Python 3.12+**
- **FastAPI** - Web framework
- **wakeonlan** - Python Wake-on-LAN library
- **uvicorn** - ASGI server
- **python-dotenv** - Environment variables support
- **slowapi** - Rate limiting middleware

## ❓ Troubleshooting

### Common Issues

**Q: Wake-on-LAN packet sent but device doesn't wake up?**

- Ensure Wake-on-LAN is enabled in device BIOS/UEFI
- Check network adapter WoL settings
- Verify the device is connected via Ethernet (not WiFi)
- Ensure the MAC address format is correct (`AA:BB:CC:DD:EE:FF`)
- **Verify host networking is enabled** - this is the most common issue!
- Check that the target device is in a sleep/soft-off state (not fully powered off)

**Q: API returns connection errors?**

- Verify the API is running: `docker logs wakeonlan-api`
- Check if the container is using host networking: `docker inspect wakeonlan-api | grep NetworkMode`
- Ensure Docker is running properly
- Check that port 8080 is accessible: `curl http://localhost:8080/`

**Q: Container can't access the network?**

- Make sure you're using `--network host` or `network_mode: host`
- Check that the host system can send WoL packets
- Verify firewall settings on the host
- Test WoL from the host directly using `wakeonlan` CLI tool

**Q: Receiving 429 Too Many Requests?**

- The API has rate limiting enabled. Wait a moment and try again.
- Adjust `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS` to increase limits if needed.
- Rate limits are per IP address. Distributed clients will have separate limits.

**Q: Receiving 403 Forbidden errors?**

- If `API_KEY` is set, you must include the `X-API-Key` header in all requests.
- Verify your API key matches the configured value(s). Multiple keys can be configured as a comma-separated list.
- If you want to disable authentication, set `API_KEY=""` (empty string) or remove the variable.

**Q: Docker HEALTHCHECK fails?**

- The HEALTHCHECK calls `/health` endpoint. Verify the API is responding.
- Check container logs for errors: `docker logs wakeonlan-api`
- Ensure port 8080 is not blocked by a firewall inside the container.
- If using custom network configuration, verify the health check can reach `localhost:8080`.

**Q: Device registry not persisting?**

- The `devices.json` file is created in the working directory (`/app/app` inside container).
- For Docker, ensure the file is persisted by mounting a volume: `-v ./devices.json:/app/app/devices.json`
- Check file permissions - the container runs as non-root user `appuser`.

**Q: WoL packets not reaching devices on a different subnet?**

- WoL typically works within a local network segment. Cross-subnet WoL requires router configuration.
- Use `BROADCAST_IP` to specify the broadcast address for your target network (e.g., `192.168.1.255`).
- Ensure your router allows WoL traffic and has proper broadcast forwarding configured.

---

**Made with ❤️ by [Cléry Arque-Ferradou](https://github.com/cleeryy)**
