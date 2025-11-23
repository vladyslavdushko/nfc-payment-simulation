# 🐳 Docker Deployment Guide

## Quick Start

### Prerequisites
- Docker Desktop installed
- Git repository cloned

### Local Development

```bash
# Build and start all services
docker compose up --build

# Or run in background
docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Access Services

- **Frontend**: http://localhost:80
- **Backend API**: http://localhost:8443
- **Health Check**: http://localhost:8443/health
- **API Docs**: http://localhost:8443/docs

---

## Commands Reference

### Build Images

```bash
# Build only backend
docker build -t nfc-backend:latest ./back

# Build only frontend
docker build -t nfc-frontend:latest ./web/dashboard

# Build all via compose
docker compose build
```

### Run Containers

```bash
# Start all services
docker compose up

# Start in detached mode
docker compose up -d

# Restart specific service
docker compose restart backend
docker compose restart frontend
```

### View & Debug

```bash
# Show running containers
docker compose ps

# View logs (all services)
docker compose logs

# View logs (specific service)
docker compose logs backend
docker compose logs frontend

# Follow logs in real-time
docker compose logs -f backend

# Execute commands in container
docker compose exec backend bash
docker compose exec frontend sh
```

### Stop & Clean

```bash
# Stop all services
docker compose down

# Stop and remove volumes
docker compose down -v

# Remove all images
docker compose down --rmi all

# Full cleanup
docker system prune -a
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 80 (Windows)
netstat -ano | findstr :80
taskkill /PID <PID> /F

# Find process using port 80 (Linux/Mac)
lsof -ti:80 | xargs kill
```

### Container Won't Start

```bash
# Check logs
docker compose logs backend

# Rebuild without cache
docker compose build --no-cache

# Remove old containers
docker compose down
docker compose up --force-recreate
```

### MongoDB Connection Issues

```bash
# Add MongoDB to docker-compose.yml
services:
  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
```

---

## Production Deployment

### Using Docker Compose

```bash
# Production compose file
docker compose -f docker-compose.prod.yml up -d
```

### Using Pre-built Images

```bash
# Pull images from registry
docker pull ghcr.io/your-username/nfc-backend:latest
docker pull ghcr.io/your-username/nfc-frontend:latest

# Run backend
docker run -d \
  --name nfc-backend \
  -p 8443:8443 \
  -e MONGO_URI=your_mongodb_uri \
  ghcr.io/your-username/nfc-backend:latest

# Run frontend
docker run -d \
  --name nfc-frontend \
  -p 80:80 \
  ghcr.io/your-username/nfc-frontend:latest
```

---

## Environment Variables

### Backend (.env)

```bash
MONGO_URI=mongodb://localhost:27017/nfc_payments
DEBUG=false
API_URL=https://api.example.com
```

### Frontend (.env)

```bash
VITE_API_BASE=https://api.example.com
```

---

## Docker Image Sizes

| Image | Size | Build Time |
|-------|------|------------|
| Backend | ~150 MB | ~60s |
| Frontend | ~25 MB | ~60s |
| Total | ~175 MB | ~2min |

---

## Health Checks

### Backend

```bash
curl http://localhost:8443/health
# Expected: {"ok": true}
```

### Frontend

```bash
curl http://localhost:80
# Expected: HTML content
```

### Full Stack Test

```bash
# Test API from frontend
curl http://localhost:80/api/health
```

---

## CI/CD Integration

Pipeline automatically:
1. ✅ Builds Docker images
2. ✅ Tests with docker compose
3. ✅ Validates health checks
4. ✅ Ready for deployment

See `CI_CD_PIPELINE.md` for details.

---

**Need Help?** Check logs: `docker compose logs -f`

