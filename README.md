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

A **simple and lightweight REST API** built with FastAPI to remotely wake devices using Wake-on-LAN (WoL) magic packets. Send HTTP requests to wake up computers and devices on your network.

## ✨ Features

- **RESTful API** with FastAPI framework
- **Wake devices by MAC address** via HTTP requests
- **Default MAC configuration** for quick access
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
# Edit .env with your default MAC address
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

| Variable      | Description                              | Default | Required |
| ------------- | ---------------------------------------- | ------- | -------- |
| `DEFAULT_MAC` | Default MAC address for `/wake` endpoint | None    | Yes      |

### For Docker Run

Set environment variables directly in the `docker run` command:

```
docker run -d \
  --network host \
  -e DEFAULT_MAC="AA:BB:CC:DD:EE:FF" \
  --name wakeonlan-api \
  ghcr.io/cleeryy/wakeonlan-api:latest
```

### For Docker Compose

Create a `.env` file in your project directory:

```
# Default MAC address for /wake endpoint
DEFAULT_MAC=AA:BB:CC:DD:EE:FF
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

### GET `/wake`

**Wake default device** - Send WoL packet to the configured default MAC address

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

### GET `/wake/{mac_address}`

**Wake specific device** - Send WoL packet to a specific MAC address

**Parameters:**

- `mac_address` (path): Target device MAC address (format: `AA:BB:CC:DD:EE:FF`)

**Response (Success):**

```
{
  "message": "Wake-on-LAN packet sent successfully to AA:BB:CC:DD:EE:FF device!"
}
```

## 💡 Usage Examples

### Using curl

```
# Check API status
curl http://localhost:8080/

# Wake default device
curl http://localhost:8080/wake

# Wake specific device
curl http://localhost:8080/wake/AA:BB:CC:DD:EE:FF
```

### Using HTTPie

```
# Wake default device
http GET localhost:8080/wake

# Wake specific device
http GET localhost:8080/wake/AA:BB:CC:DD:EE:FF
```

### Using Python

```
import requests

# Wake default device
response = requests.get("http://localhost:8080/wake")
print(response.json())

# Wake specific device
mac_address = "AA:BB:CC:DD:EE:FF"
response = requests.get(f"http://localhost:8080/wake/{mac_address}")
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

- **Network Access**: Ensure the API is only accessible from trusted networks
- **Host Networking**: Container shares host's network namespace for WoL functionality
- **Container Security**: The application runs as a non-root user inside the container
- **MAC Address Validation**: Consider implementing MAC address format validation for production use
- **Firewall Rules**: Configure appropriate firewall rules if needed

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
│   └── main.py              # FastAPI application
├── docker-compose.yml       # Docker Compose configuration
├── Dockerfile              # Docker image definition
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
└── LICENSE                # MIT License
```

## 🔧 Requirements

- **Python 3.12+**
- **FastAPI** - Web framework
- **wakeonlan** - Python Wake-on-LAN library
- **uvicorn** - ASGI server
- **python-dotenv** - Environment variables support

## ❓ Troubleshooting

### Common Issues

**Q: Wake-on-LAN packet sent but device doesn't wake up?**

- Ensure Wake-on-LAN is enabled in device BIOS/UEFI
- Check network adapter WoL settings
- Verify the device is connected via Ethernet (not WiFi)
- Ensure the MAC address format is correct (`AA:BB:CC:DD:EE:FF`)
- **Verify host networking is enabled** - this is the most common issue!

**Q: API returns connection errors?**

- Verify the API is running: `docker logs wakeonlan-api`
- Check if the container is using host networking: `docker inspect wakeonlan-api | grep NetworkMode`
- Ensure Docker is running properly

**Q: Container can't access the network?**

- Make sure you're using `--network host` or `network_mode: host`
- Check that the host system can send WoL packets
- Verify firewall settings on the host

---

**Made with ❤️ by [Cléry Arque-Ferradou](https://github.com/cleeryy)**
