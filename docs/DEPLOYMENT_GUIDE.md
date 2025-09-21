# Deployment Guide

## Overview

This guide covers different deployment scenarios for SensorGate, from local development to production Kubernetes deployments.

## Prerequisites

- Python 3.12+
- Google Cloud Project with Pub/Sub API enabled
- Service Account with Pub/Sub Publisher permissions
- Docker (for containerized deployments)
- Kubernetes cluster (for K8s deployments)

## Local Development

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd SensorGate

# Copy environment template
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` file:
```bash
# Required
SENSORGATE_GCP_PROJECT_ID=your-gcp-project-id
SENSORGATE_API_KEYS=dev-key-123,test-key-456

# Optional (defaults shown)
SENSORGATE_DEBUG=true
SENSORGATE_HOST=0.0.0.0
SENSORGATE_PORT=8000
SENSORGATE_LOG_LEVEL=INFO
```

### 3. Google Cloud Setup

Option A - Service Account Key:
```bash
# Download service account key from GCP Console
SENSORGATE_GCP_CREDENTIALS_PATH=/path/to/service-account.json
```

Option B - Application Default Credentials:
```bash
gcloud auth application-default login
```

### 4. Install Dependencies

Using Poetry (recommended):
```bash
poetry install
poetry shell
```


### 5. Create Pub/Sub Topics

```bash
# Create topics for each sensor type
gcloud pubsub topics create sensor-temperature
gcloud pubsub topics create sensor-humidity
gcloud pubsub topics create sensor-ndir
```

### 6. Run the Service

```bash
# Development mode with auto-reload
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Verify Installation

```bash
# Health check
curl http://localhost:8000/api/v1/health

# API documentation (debug mode only)
open http://localhost:8000/docs
```

## Docker Deployment

### 1. Create Dockerfile

```dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/live || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Build and Run

```bash
# Build image
docker build -t sensorgate:latest .

# Run container
docker run -d \
    --name sensorgate \
    -p 8000:8000 \
    -e SENSORGATE_GCP_PROJECT_ID=your-project \
    -e SENSORGATE_API_KEYS=your-api-keys \
    -v /path/to/service-account.json:/app/credentials.json \
    -e SENSORGATE_GCP_CREDENTIALS_PATH=/app/credentials.json \
    sensorgate:latest
```

### 3. Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  sensorgate:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SENSORGATE_GCP_PROJECT_ID=your-project-id
      - SENSORGATE_API_KEYS=your-api-keys
      - SENSORGATE_DEBUG=false
      - SENSORGATE_LOG_LEVEL=INFO
    volumes:
      - ./credentials.json:/app/credentials.json:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run with:
```bash
docker-compose up -d
```

## Kubernetes Deployment

### 1. Create Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: sensorgate
```

### 2. Create Secret for Credentials

```bash
# Create secret from service account key
kubectl create secret generic gcp-credentials \
    --from-file=key.json=/path/to/service-account.json \
    -n sensorgate

# Create secret for API keys
kubectl create secret generic api-keys \
    --from-literal=keys="prod-key-123,backup-key-456" \
    -n sensorgate
```

### 3. ConfigMap for Configuration

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: sensorgate-config
  namespace: sensorgate
data:
  GCP_PROJECT_ID: "your-gcp-project-id"
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  LOG_FORMAT: "json"
  METRICS_ENABLED: "true"
  PUBSUB_TOPIC_TEMPERATURE: "sensor-temperature"
  PUBSUB_TOPIC_HUMIDITY: "sensor-humidity"
  PUBSUB_TOPIC_NDIR: "sensor-ndir"
```

### 4. Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sensorgate
  namespace: sensorgate
  labels:
    app: sensorgate
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sensorgate
  template:
    metadata:
      labels:
        app: sensorgate
    spec:
      containers:
      - name: sensorgate
        image: sensorgate:latest
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: SENSORGATE_GCP_PROJECT_ID
          valueFrom:
            configMapKeyRef:
              name: sensorgate-config
              key: GCP_PROJECT_ID
        - name: SENSORGATE_API_KEYS
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: keys
        - name: SENSORGATE_GCP_CREDENTIALS_PATH
          value: "/app/credentials/key.json"
        - name: SENSORGATE_DEBUG
          valueFrom:
            configMapKeyRef:
              name: sensorgate-config
              key: DEBUG
        - name: SENSORGATE_LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: sensorgate-config
              key: LOG_LEVEL
        - name: SENSORGATE_METRICS_ENABLED
          valueFrom:
            configMapKeyRef:
              name: sensorgate-config
              key: METRICS_ENABLED
        volumeMounts:
        - name: gcp-credentials
          mountPath: /app/credentials
          readOnly: true
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/v1/health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 5
      volumes:
      - name: gcp-credentials
        secret:
          secretName: gcp-credentials
```

### 5. Service

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: sensorgate-service
  namespace: sensorgate
  labels:
    app: sensorgate
spec:
  selector:
    app: sensorgate
  ports:
  - name: http
    port: 80
    targetPort: 8000
    protocol: TCP
  type: ClusterIP
```

### 6. Ingress (Optional)

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: sensorgate-ingress
  namespace: sensorgate
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - sensorgate.yourdomain.com
    secretName: sensorgate-tls
  rules:
  - host: sensorgate.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: sensorgate-service
            port:
              number: 80
```

### 7. Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# Check deployment status
kubectl get pods -n sensorgate
kubectl logs -f deployment/sensorgate -n sensorgate
```

## Production Considerations

### 1. Security

- Use strong, unique API keys
- Enable HTTPS/TLS
- Regularly rotate credentials
- Use Kubernetes secrets for sensitive data
- Enable pod security policies

### 2. Monitoring

- Deploy Prometheus and Grafana
- Set up alerting rules
- Monitor key application health indicators:
  - Request rate and latency
  - Error rates
  - Pub/Sub connectivity
  - Resource usage

### 3. Logging

- Use centralized logging (ELK, Fluentd)
- Configure log retention policies
- Set up log-based alerting
- Ensure logs don't contain sensitive data

### 4. Scaling

- Use Horizontal Pod Autoscaler:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sensorgate-hpa
  namespace: sensorgate
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sensorgate
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 5. Backup and Recovery

- Backup Kubernetes manifests
- Document recovery procedures
- Test disaster recovery scenarios
- Monitor Pub/Sub topic backlogs

## Troubleshooting

### Common Issues

1. **Pub/Sub Connection Failed**
   - Check service account permissions
   - Verify credentials path
   - Ensure topics exist

2. **Authentication Errors**
   - Verify API keys configuration
   - Check header format
   - Review logs for details

3. **High Memory Usage**
   - Adjust resource limits
   - Monitor for memory leaks
   - Check Pub/Sub client settings

4. **Slow Response Times**
   - Monitor Pub/Sub latency
   - Check circuit breaker status
   - Review resource allocation

### Health Check Endpoints

Use these for monitoring and debugging:
- `/api/v1/health` - Full health check
- `/api/v1/health/live` - Liveness probe
- `/api/v1/health/ready` - Readiness probe

### Useful Commands

```bash
# Check logs
kubectl logs -f deployment/sensorgate -n sensorgate

# Get pod status
kubectl get pods -n sensorgate -o wide

# Describe deployment
kubectl describe deployment sensorgate -n sensorgate

# Port forward for local access
kubectl port-forward svc/sensorgate-service 8000:80 -n sensorgate

# Exec into pod
kubectl exec -it deployment/sensorgate -n sensorgate -- /bin/bash
```
