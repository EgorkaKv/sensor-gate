# Google Cloud Run Deployment Guide

This guide provides step-by-step instructions for deploying SensorGate to Google Cloud Run.

## Prerequisites

- Google Cloud Platform account with billing enabled
- `gcloud` CLI installed and authenticated
- Docker installed (for local testing)
- Project with the following APIs enabled:
  - Cloud Run API
  - Cloud Build API
  - Pub/Sub API
  - Container Registry API

## Quick Deployment

### Option 1: Automated Deployment Script

The easiest way to deploy SensorGate to Cloud Run:

```bash
# Make the script executable (Linux/macOS)
chmod +x deploy-cloudrun.sh

# Run the deployment script
./deploy-cloudrun.sh YOUR_GCP_PROJECT_ID us-central1
```

### Option 2: Manual Deployment

#### Step 1: Set up environment

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"

# Set active project
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable pubsub.googleapis.com
```

#### Step 2: Create Pub/Sub topics

```bash
# Create topics for each sensor type
gcloud pubsub topics create sensor-temperature
gcloud pubsub topics create sensor-humidity
gcloud pubsub topics create sensor-ndir
```

#### Step 3: Build and deploy

```bash
# Build using Cloud Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/sensorgate

# Deploy to Cloud Run
gcloud run deploy sensorgate \
    --image gcr.io/$PROJECT_ID/sensorgate \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8000 \
    --memory 512Mi \
    --cpu 1 \
    --concurrency 80 \
    --max-instances 10 \
    --set-env-vars "SENSORGATE_GCP_PROJECT_ID=$PROJECT_ID" \
    --timeout 300
```

## Configuration

### Environment Variables

Set these environment variables in the Cloud Run console or via CLI:

#### Required Variables
```bash
SENSORGATE_GCP_PROJECT_ID=your-gcp-project-id
```

#### Optional Variables
```bash
# Authentication (leave empty for public access during testing)
SENSORGATE_API_KEYS=prod-key-123,backup-key-456

# Public access mode (set to 'true' for testing without API keys)
SENSORGATE_PUBLIC_ACCESS=false

# Application settings
SENSORGATE_DEBUG=false

# Pub/Sub topic names (defaults shown)
SENSORGATE_PUBSUB_TOPIC_TEMPERATURE=sensor-temperature
SENSORGATE_PUBSUB_TOPIC_HUMIDITY=sensor-humidity
SENSORGATE_PUBSUB_TOPIC_NDIR=sensor-ndir

# Circuit breaker settings
SENSORGATE_CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
SENSORGATE_CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60

# InfluxDB configuration (for historical data endpoints)
SENSORGATE_INFLUXDB_URL=https://your-influxdb-instance.com
SENSORGATE_INFLUXDB_TOKEN=your-influxdb-token
SENSORGATE_INFLUXDB_ORG=your-organization
SENSORGATE_INFLUXDB_BUCKET=iot-sensors
```

### Setting Environment Variables

#### Via gcloud CLI:
```bash
gcloud run services update sensorgate \
    --region=$REGION \
    --set-env-vars="SENSORGATE_API_KEYS=your-api-keys,SENSORGATE_PUBLIC_ACCESS=false"
```

#### Via Cloud Console:
1. Go to Cloud Run in the Google Cloud Console
2. Click on your service name (`sensorgate`)
3. Click "Edit & Deploy New Revision"
4. Go to "Variables & Secrets" tab
5. Add environment variables as needed

## Authentication Setup

### Option 1: Service Account (Recommended for Production)

Cloud Run will automatically use the default service account, which has access to Pub/Sub in the same project. For production, create a dedicated service account:

```bash
# Create service account
gcloud iam service-accounts create sensorgate-sa \
    --display-name="SensorGate Service Account"

# Grant Pub/Sub permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sensorgate-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/pubsub.publisher"

# Update Cloud Run service to use the service account
gcloud run services update sensorgate \
    --region=$REGION \
    --service-account=sensorgate-sa@$PROJECT_ID.iam.gserviceaccount.com
```

### Option 2: Default Service Account

The default Cloud Run service account already has Pub/Sub permissions in the same project, so no additional setup is needed for basic functionality.

## Testing the Deployment

### 1. Health Check
```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe sensorgate --platform managed --region $REGION --format 'value(status.url)')

# Test health endpoint
curl $SERVICE_URL/api/v1/health
```

### 2. Submit Test Data
```bash
# With API key authentication
curl -X POST "$SERVICE_URL/api/v1/sensors/data" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "device_id": 12345,
    "sensor_type": "temperature",
    "value": 23.5,
    "latitude": 55.7558,
    "longitude": 37.6176,
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }'

# With public access enabled (no API key needed)
curl -X POST "$SERVICE_URL/api/v1/sensors/data" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 12345,
    "sensor_type": "temperature",
    "value": 23.5,
    "latitude": 55.7558,
    "longitude": 37.6176,
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }'
```

### 3. Check Pub/Sub Messages
```bash
# Create a subscription to test message delivery
gcloud pubsub subscriptions create test-subscription \
    --topic=sensor-temperature

# Pull messages to verify they were published
gcloud pubsub subscriptions pull test-subscription --auto-ack --limit=5
```

## Monitoring and Logging

### Cloud Run Metrics
Monitor your service in the Cloud Console:
1. Go to Cloud Run
2. Click on your service
3. View the "Metrics" tab for:
   - Request count
   - Request latency
   - Error rate
   - Memory and CPU usage

### Logs
View logs in Cloud Logging:
```bash
# View recent logs
gcloud logs tail "projects/$PROJECT_ID/logs/run.googleapis.com%2Fstdout" --limit=50

# Stream logs in real-time
gcloud logs tail "projects/$PROJECT_ID/logs/run.googleapis.com%2Fstdout" --follow
```

## Scaling Configuration

Cloud Run automatically scales based on incoming requests. You can configure scaling parameters:

```bash
gcloud run services update sensorgate \
    --region=$REGION \
    --min-instances=1 \
    --max-instances=100 \
    --concurrency=80 \
    --cpu=1 \
    --memory=512Mi
```

## Security Considerations

### 1. API Authentication
- Use strong, unique API keys for production
- Rotate API keys regularly
- Consider using Google Cloud Identity and Access Management for more advanced authentication

### 2. Network Security
- Cloud Run services are HTTPS-only by default
- Consider using VPC connectors for private network access
- Use IAM policies to control access to the service

### 3. Service Account Permissions
- Use minimal required permissions
- Consider using Workload Identity for enhanced security

## Troubleshooting

### Common Issues

1. **Build Failures**
   ```bash
   # Check build logs
   gcloud builds log $(gcloud builds list --limit=1 --format='value(id)')
   ```

2. **Service Won't Start**
   ```bash
   # Check service logs
   gcloud logs tail "projects/$PROJECT_ID/logs/run.googleapis.com%2Fstdout" --limit=50
   ```

3. **Authentication Errors**
   - Verify service account permissions
   - Check environment variables
   - Ensure Pub/Sub topics exist

4. **High Latency**
   - Check if container is cold starting
   - Consider setting minimum instances
   - Review resource allocation

### Useful Commands

```bash
# Get service information
gcloud run services describe sensorgate --region=$REGION

# Update service configuration
gcloud run services update sensorgate --region=$REGION [OPTIONS]

# View service logs
gcloud logs tail "projects/$PROJECT_ID/logs/run.googleapis.com%2Fstdout"

# Delete service (if needed)
gcloud run services delete sensorgate --region=$REGION
```

## Cost Optimization

1. **Right-size Resources**: Start with minimal resources and scale up as needed
2. **Use Minimum Instances Carefully**: Only set minimum instances if you need to avoid cold starts
3. **Monitor Usage**: Use Cloud Monitoring to track resource usage and optimize accordingly
4. **Clean Up**: Remove unused services and images to avoid storage costs

## Next Steps

After successful deployment:
1. Set up monitoring and alerting
2. Configure proper authentication for production
3. Set up CI/CD pipeline for automated deployments
4. Consider setting up custom domains
5. Implement proper backup and disaster recovery procedures
