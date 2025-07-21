# Wake-on-LAN API

A **simple and lightweight REST API** built with FastAPI to remotely wake devices using Wake-on-LAN (WoL) magic packets. Send HTTP requests to wake up computers and devices on your network.

## ✨ Features

- **RESTful API** with FastAPI framework
- **Wake devices by MAC address** via HTTP requests
- **Default MAC configuration** for quick access
- **Docker support** with multi-stage builds
- **Security-focused** with non-root container user
- **Lightweight** Python 3.12-slim base image
- **Environment-based configuration**

## 🚀 Quick Start

### Using Docker Compose (Recommended)

1. **Clone the repository**

```
git clone https://github.com/cleeryy/wakeonlan-api
cd wakeonlan-api
```

2. **Configure environment**

```
cp .env.example .env
```

Edit .env with your default MAC address

3. **Start the service**

```
docker compose up --build -d
```

The API will be available at `http://localhost:8080`

### Local Installation

1. **Install Python dependencies**

```
pip install -r requirements.txt
```

2. **Set environment variables**

```
export DEFAULT_MAC="AA:BB:CC:DD:EE:FF"
```

3. **Run the application**

```
cd app
uvicorn main:app --host 0.0.0.0 --port 8080
```

## ⚙️ Configuration

Create a `.env` file in the project root:

```
# Default MAC address for /wake endpoint

DEFAULT_MAC=AA:BB:CC:DD:EE:FF

# Optional: Custom port (default: 8080)

PORT=8080
```

### Environment Variables

| Variable      | Description                              | Default | Required |
| ------------- | ---------------------------------------- | ------- | -------- |
| `DEFAULT_MAC` | Default MAC address for `/wake` endpoint | None    | Yes      |
| `PORT`        | HTTP port for the API                    | 8080    | No       |

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

### Build Image

```
docker build -t wakeonlan-api .
```

### Run Container

```
docker run -d \
 -p 8080:8080 \
 -e DEFAULT_MAC="AA:BB:CC:DD:EE:FF" \
 --name wakeonlan-api \
 wakeonlan-api
```

### Docker Compose

```
# Start services

docker-compose up -d

# View logs

docker-compose logs -f

# Stop services

docker-compose down
```

## 🔒 Security Considerations

- **Network Access**: Ensure the API is only accessible from trusted networks
- **Firewall Rules**: Configure appropriate firewall rules for port 8080
- **Container Security**: The application runs as a non-root user inside the container
- **MAC Address Validation**: Consider implementing MAC address format validation for production use

## 🛠️ Development

### Project Structure

```
wakeonlan-api/
├── app/
│ ├── **init**.py
│ └── main.py # FastAPI application
├── docker-compose.yml # Docker Compose configuration
├── Dockerfile # Docker image definition
├── requirements.txt # Python dependencies
├── .env.example # Environment template
└── LICENSE # MIT License
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

---

**Made with ❤️ by [Cléry A-Ferradou](https://github.com/cleeryy)**
