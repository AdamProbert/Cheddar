# ChedWeb Backend Metrics

The ChedWeb backend exposes Prometheus metrics on the `/metrics` endpoint (port 8000) for monitoring application health and performance.

## Metrics Endpoint

**URL**: `http://localhost:8000/metrics`  
**Format**: Prometheus text format  
**Scrape interval**: 15 seconds (configured in Alloy)

## Available Metrics

### Application Information

- `chedweb_backend_info` - Application version and component information

### HTTP/API Metrics

- `chedweb_http_requests_total` - Total HTTP requests by method, endpoint, and status
- `chedweb_http_request_duration_seconds` - HTTP request latency histogram
- `chedweb_http_requests_in_progress` - Current number of in-progress HTTP requests

### WebRTC Metrics

- `chedweb_webrtc_connections_total` - Total WebRTC connections (success/failed)
- `chedweb_webrtc_connections_active` - Number of active peer connections
- `chedweb_webrtc_datachannel_messages_total` - Data channel messages sent/received
- `chedweb_webrtc_ice_candidates_total` - ICE candidates processed
- `chedweb_webrtc_connection_state_changes_total` - Connection state transitions

### Camera Metrics

- `chedweb_camera_enabled` - Camera enabled status (0/1)
- `chedweb_camera_frames_total` - Total frames captured
- `chedweb_camera_frame_errors_total` - Frame capture errors
- `chedweb_camera_fps` - Current frames per second
- `chedweb_camera_resolution` - Resolution settings (width, height, framerate)
- `chedweb_camera_settings_changes_total` - Camera setting changes by type

### Motion Driver Metrics

- `chedweb_motion_driver_connected` - Connection status (0/1)
- `chedweb_motion_driver_commands_total` - Commands sent by type
- `chedweb_motion_driver_command_errors_total` - Command errors by type
- `chedweb_motion_driver_serial_bytes_total` - Serial data transfer (sent/received)

### Control Command Metrics

- `chedweb_control_commands_total` - Control commands by source
- `chedweb_control_command_processing_seconds` - Command processing latency
- `chedweb_deadman_switch_timeouts_total` - Safety timeout events

### System/Process Metrics

- `chedweb_process_cpu_percent` - Backend process CPU usage
- `chedweb_process_memory_bytes` - Memory usage (RSS/VMS)
- `chedweb_process_open_file_descriptors` - Open file descriptors
- `chedweb_process_threads` - Thread count

### Error Metrics

- `chedweb_errors_total` - Errors by type and component

## Grafana Alloy Configuration

The metrics are scraped by Grafana Alloy and forwarded to Grafana Cloud. Configuration is in `config.alloy`:

```hcl
prometheus.scrape "cheddar_backend" {
 targets = [{
  __address__ = "localhost:8000",
  job         = "cheddar-backend",
 }]
 
 metrics_path   = "/metrics"
 scrape_interval = "15s"
 forward_to     = [prometheus.relabel.cheddar_backend.receiver]
}
```

## Usage Examples

### Query Examples in Grafana

**Request rate by endpoint**:

```promql
rate(chedweb_http_requests_total[5m])
```

**99th percentile response time**:

```promql
histogram_quantile(0.99, rate(chedweb_http_request_duration_seconds_bucket[5m]))
```

**WebRTC connection success rate**:

```promql
rate(chedweb_webrtc_connections_total{status="success"}[5m]) / 
rate(chedweb_webrtc_connections_total[5m])
```

**Camera FPS**:

```promql
chedweb_camera_fps
```

**Backend process memory usage**:

```promql
chedweb_process_memory_bytes{type="rss"}
```

## Testing Metrics Locally

You can verify metrics are being exposed:

```bash
# Check metrics endpoint
curl http://localhost:8000/metrics

# Check specific metric
curl -s http://localhost:8000/metrics | grep chedweb_camera_enabled
```

## Updating Metrics on the Pi

After deploying changes:

1. Install the new dependency:

```bash
source /home/cheddar/chedweb-backend/venv/bin/activate
pip install -r requirements.txt
```

2. Restart the backend service:

```bash
sudo systemctl restart cheddar-backend
```

3. Verify metrics are available:

```bash
curl http://localhost:8000/metrics
```

4. Restart Alloy to pick up config changes:

```bash
sudo systemctl restart alloy
```

5. Check Alloy is scraping successfully:

```bash
sudo journalctl -u alloy -f
```
