# Wake-on-LAN API

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
# Pull and run the latest image
docker run -d \
  -p 8080:8080 \
  -e DEFAULT_MAC="AA:BB:CC:DD:EE:FF" \
  --name wakeonlan-api \
  ghcr.io/cleeryy/wakeonlan-api:latest
```

The API will be available at `http://localhost:8080`

**Replace `AA:BB:CC:DD:EE:FF` with your device's actual MAC address.**

### Using Docker Compose

1. **Create a docker-compose.yml file**
```
services:
  wakeonlan-api:
    image: ghcr.io/cleeryy/wakeonlan-api:latest
    ports:
      - "${PORT:-8080}:8080"
    environment:
      - DEFAULT_MAC=${DEFAULT_MAC}
    env_file:
      - .env
    restart: unless-stopped
```

2. **Create a .env file**
```
DEFAULT_MAC=AA:BB:CC:DD:EE:FF
PORT=8080
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

3. **Start the service**
```
docker compose up --build -d
```

The API will be available at `http://localhost:8080`

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

## ⚙️ Configuration

### Environment Variables

| Variable      | Description                              | Default | Required |
| ------------- | ---------------------------------------- | ------- | -------- |
| `DEFAULT_MAC` | Default MAC address for `/wake` endpoint | None    | Yes      |
| `PORT`        | HTTP port for the API                    | 8080    | No       |

### For Docker Run
Set environment variables directly in the `docker run` command:
```
docker run -d \
  -p 8080:8080 \
  -e DEFAULT_MAC="AA:BB:CC:DD:EE:FF" \
  -e PORT=8080 \
  --name wakeonlan-api \
  ghcr.io/cleeryy/wakeonlan-api:latest
```

### For Docker Compose
Create a `.env` file in your project directory:
```
# Default MAC address for /wake endpoint
DEFAULT_MAC=AA:BB:CC:DD:EE:FF

# Optional: Custom port (default: 8080)
PORT=8080
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
  -p 8080:8080 \
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

# Run built image
docker run -d \
  -p 8080:8080 \
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
- **Firewall Rules**: Configure appropriate firewall rules for port 8080
- **Container Security**: The application runs as a non-root user inside the container
- **MAC Address Validation**: Consider implementing MAC address format validation for production use
- **Image Security**: Pre-built images are automatically scanned for vulnerabilities

## 🛠️ Development

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

### Adding New Features

1. Fork the repository
2. Create a feature branch
3. Make your changes in `app/main.py`
4. Test with `uvicorn main:app --reload`
5. Submit a pull request

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

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

**Q: API returns connection errors?**  
- Verify the API is running on the correct port
- Check firewall settings
- Ensure Docker container networking is configured properly

**Q: Docker pull fails?**
- Make sure you have internet connectivity
- Try: `docker pull ghcr.io/cleeryy/wakeonlan-api:latest`
- Check if Docker is running properly

---

**Made with ❤️ by [Cléry A-Ferradou](https://github.com/cleeryy)**
