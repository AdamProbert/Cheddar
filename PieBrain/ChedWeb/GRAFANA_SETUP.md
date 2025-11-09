# Grafana Cloud Monitoring Setup

This guide covers setting up Grafana Cloud monitoring for ChedWeb services running on the Raspberry Pi.

## 📊 What is Grafana Cloud?

**Grafana Cloud** is a hosted observability platform that provides:

- **Grafana**: Visualization and dashboarding for metrics, logs, and traces
- **Prometheus**: Time-series metrics storage and querying
- **Loki**: Log aggregation and querying
- **Tempo**: Distributed tracing (optional)
- **Alerting**: Alert rules and notification channels

### Free Tier Limits (Forever Free)

The Grafana Cloud free tier is generous and sufficient for hobby projects:

- **Metrics**: 10,000 active series, 14-day retention
- **Logs**: 50 GB ingestion/month, 14-day retention
- **Traces**: 50 GB ingestion/month, 14-day retention
- **Users**: 3 users
- **Dashboards**: Unlimited
- **Alerts**: 20 alert rules

Perfect for monitoring a Raspberry Pi rover! 🤖

## 🔧 What is Grafana Alloy?

**Grafana Alloy** is a vendor-agnostic OpenTelemetry Collector distribution that:

- Runs on your Raspberry Pi as a systemd service
- Collects logs from journald (systemd services)
- Collects system metrics (CPU, memory, disk, network)
- Pushes data to Grafana Cloud
- Uses minimal resources (ideal for Pi)

Think of it as the data collection agent that ships telemetry to Grafana Cloud.

### Architecture

```
┌─────────────────────────────────────┐
│      Raspberry Pi (CheddarPi)       │
│                                     │
│  ┌────────────────────────────┐    │
│  │  cheddar-backend.service   │    │
│  │  (logs to journald)        │    │
│  └────────────────────────────┘    │
│               ▲                     │
│               │                     │
│  ┌────────────────────────────┐    │
│  │  cheddar-frontend.service  │    │
│  │  (logs to journald)        │    │
│  └────────────────────────────┘    │
│               ▲                     │
│               │                     │
│  ┌────────────┴────────────────┐   │      ┌──────────────────┐
│  │     Grafana Alloy           │   │      │  Grafana Cloud   │
│  │  - Reads journald logs      │───┼─────>│                  │
│  │  - Collects system metrics  │   │      │  ┌────────────┐  │
│  │  - Pushes to cloud          │   │      │  │ Prometheus │  │
│  └─────────────────────────────┘   │      │  │ (metrics)  │  │
│                                     │      │  └────────────┘  │
└─────────────────────────────────────┘      │                  │
                                             │  ┌────────────┐  │
                                             │  │   Loki     │  │
                                             │  │  (logs)    │  │
                                             │  └────────────┘  │
                                             │                  │
                                             │  ┌────────────┐  │
                                             │  │  Grafana   │  │
                                             │  │ (dashboards│  │
                                             │  └────────────┘  │
                                             └──────────────────┘
```

## 🚀 First-Time Setup

### Step 1: Create Grafana Cloud Account

1. Go to [grafana.com](https://grafana.com)
2. Click "Sign up for free"
3. Create account (GitHub/Google/email)
4. Choose a stack name (e.g., `cheddar-monitoring`)
5. Select a region close to you (e.g., `prod-gb-south-1` for UK)

### Step 2: Get Alloy Installation Script

1. In Grafana Cloud, navigate to **Connections** → **Add new connection**
2. Search for and select **Linux Server**
3. Click **Install Grafana Alloy**
4. Copy the installation script that includes your credentials

The script will look like:

```bash
GCLOUD_HOSTED_METRICS_ID="..." \
GCLOUD_HOSTED_METRICS_URL="https://prometheus-prod-XX-prod-XX.grafana.net/api/prom/push" \
GCLOUD_HOSTED_LOGS_ID="..." \
GCLOUD_HOSTED_LOGS_URL="https://logs-prod-XXX.grafana.net/loki/api/v1/push" \
GCLOUD_FM_URL="https://fleet-management-prod-XXX.grafana.net" \
GCLOUD_FM_POLL_FREQUENCY="60s" \
GCLOUD_FM_HOSTED_ID="..." \
ARCH="arm64" \
GCLOUD_RW_API_KEY="glc_..." \
/bin/sh -c "$(curl -fsSL https://storage.googleapis.com/cloud-onboarding/alloy/scripts/install-linux.sh)"
```

### Step 3: Install Alloy on Raspberry Pi

SSH into your Pi and run the installation script:

```bash
ssh adamprobert@<pi-ip>

# Paste and run the installation script from Grafana Cloud
GCLOUD_HOSTED_METRICS_ID="..." ... /bin/sh -c "$(curl -fsSL ...)"
```

This will:

- Download and install Grafana Alloy
- Create systemd service at `/usr/lib/systemd/system/alloy.service`
- Create environment config at `/etc/systemd/system/alloy.service.d/env.conf`
- Start and enable the service
- Create basic config at `/etc/alloy/config.alloy`

### Step 4: Deploy ChedWeb-Specific Configuration

The default Alloy config only sets up remote endpoints but doesn't collect any data. We need to deploy our custom config:

```bash
# From your Mac, copy the config
cd ~/projects/Cheddar
scp PieBrain/ChedWeb/config.alloy adamprobert@<pi-ip>:/tmp/

# On the Pi, replace the default config
ssh adamprobert@<pi-ip>
sudo cp /etc/alloy/config.alloy /etc/alloy/config.alloy.backup
sudo mv /tmp/config.alloy /etc/alloy/config.alloy
sudo systemctl restart alloy
```

### Step 5: Verify Data Collection

Check that Alloy is running and collecting data:

```bash
# On the Pi
sudo systemctl status alloy
journalctl -u alloy -f
```

You should see log lines like:

```
level=info msg="reading from journal" component=journal
level=info msg="scraped metrics" component=scrape
level=info msg="remote write sent" samples=123
```

### Step 6: View Data in Grafana Cloud

1. Go to your Grafana Cloud instance
2. Navigate to **Explore**
3. **For Logs:**
   - Select **Loki** as data source
   - Query: `{job="cheddar-backend"}`
   - You should see logs from your backend service
4. **For Metrics:**
   - Select **Prometheus** as data source
   - Query: `node_cpu_seconds_total{host="CheddarPi"}`
   - You should see CPU metrics from your Pi

## 📈 Creating Dashboards

### Pre-built Dashboard

1. In Grafana Cloud, go to **Dashboards** → **New** → **Import**
2. Enter dashboard ID: `1860` (Node Exporter Full)
3. Select your Prometheus data source
4. Click **Import**

This gives you a comprehensive system dashboard.

### Custom ChedWeb Dashboard

Create a custom dashboard for ChedWeb services:

1. Go to **Dashboards** → **New** → **New Dashboard**
2. Add panels:

**Panel 1: Backend Logs**

- Visualization: Logs
- Query: `{job="cheddar-backend"} |= ""`

**Panel 2: Frontend Logs**

- Visualization: Logs
- Query: `{job="cheddar-frontend"} |= ""`

**Panel 3: CPU Usage**

- Visualization: Time series
- Query: `100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle",host="CheddarPi"}[5m])) * 100)`

**Panel 4: Memory Usage**

- Visualization: Gauge
- Query: `(1 - (node_memory_MemAvailable_bytes{host="CheddarPi"} / node_memory_MemTotal_bytes{host="CheddarPi"})) * 100`

**Panel 5: Disk Usage**

- Visualization: Gauge
- Query: `100 - ((node_filesystem_avail_bytes{host="CheddarPi",mountpoint="/"} * 100) / node_filesystem_size_bytes{host="CheddarPi",mountpoint="/"})`

**Panel 6: Network Traffic**

- Visualization: Time series
- Query:
  - Receive: `rate(node_network_receive_bytes_total{host="CheddarPi",device="wlan0"}[5m])`
  - Transmit: `rate(node_network_transmit_bytes_total{host="CheddarPi",device="wlan0"}[5m])`

## 🔔 Setting Up Alerts

### Example: High CPU Alert

1. Go to **Alerting** → **Alert rules** → **New alert rule**
2. Configure:
   - **Name**: CheddarPi High CPU
   - **Query**: `100 - (avg(rate(node_cpu_seconds_total{mode="idle",host="CheddarPi"}[5m])) * 100) > 80`
   - **Condition**: When above 80% for 5 minutes
   - **Notification**: Create contact point (email, Slack, Discord, etc.)

### Example: Service Down Alert

1. Create alert rule:
   - **Name**: Cheddar Backend Down
   - **Query**: `count_over_time({job="cheddar-backend"}[5m]) == 0`
   - **Condition**: No logs in last 5 minutes
   - **Notification**: Immediate alert

## 🔍 Useful Log Queries

### Filter by log level

```logql
{job="cheddar-backend"} |= "ERROR"
{job="cheddar-backend"} |= "WARNING"
```

### Search for specific text

```logql
{job="cheddar-backend"} |= "WebRTC"
{job="cheddar-frontend"} |= "connection"
```

### Parse JSON logs

```logql
{job="cheddar-backend"} | json | line_format "{{.message}}"
```

### Count errors

```logql
sum(count_over_time({job="cheddar-backend"} |= "ERROR" [5m]))
```

## 🔍 Useful Metric Queries

### System Overview

```promql
# CPU cores
count(node_cpu_seconds_total{mode="idle",host="CheddarPi"})

# Total memory (GB)
node_memory_MemTotal_bytes{host="CheddarPi"} / 1024 / 1024 / 1024

# Uptime (days)
(time() - node_boot_time_seconds{host="CheddarPi"}) / 86400
```

### Resource Usage

```promql
# CPU usage per core
100 - (avg by(cpu) (rate(node_cpu_seconds_total{mode="idle",host="CheddarPi"}[5m])) * 100)

# Available memory (GB)
node_memory_MemAvailable_bytes{host="CheddarPi"} / 1024 / 1024 / 1024

# Disk I/O operations
rate(node_disk_io_time_seconds_total{host="CheddarPi"}[5m])
```

### Network Stats

```promql
# Network errors
rate(node_network_transmit_errs_total{host="CheddarPi"}[5m])

# WiFi signal strength (if available)
node_wifi_station_signal_dbm{host="CheddarPi"}
```

## 🛠️ Configuration Files

### Alloy Config Location

- **Config file**: `/etc/alloy/config.alloy`
- **Environment vars**: `/etc/systemd/system/alloy.service.d/env.conf`
- **Service file**: `/usr/lib/systemd/system/alloy.service`

### Our Custom Config

The config at `PieBrain/ChedWeb/config.alloy` includes:

1. **Remote configuration**: Syncs with Grafana Cloud Fleet Management
2. **Journal log sources**: Collects from `cheddar-backend`, `cheddar-frontend`, and `alloy` services
3. **System metrics**: CPU, memory, disk, network via prometheus.exporter.unix
4. **Remote write endpoints**: Sends to Grafana Cloud Prometheus and Loki

### Updating Config

After modifying `config.alloy`:

```bash
# From Mac
scp PieBrain/ChedWeb/config.alloy adamprobert@<pi-ip>:/tmp/

# On Pi
sudo mv /tmp/config.alloy /etc/alloy/config.alloy
sudo systemctl restart alloy
journalctl -u alloy -f
```

## 🐛 Troubleshooting

### "Test Alloy connection" fails in Grafana Cloud

This is **expected** and can be ignored. Alloy listens on `127.0.0.1:12345` (localhost only) for security. The test tries to reach Alloy from the internet, which fails. Data flow works the opposite way - Alloy **pushes** to Grafana Cloud.

### No logs appearing

```bash
# Check Alloy is running
sudo systemctl status alloy

# Check Alloy logs for errors
journalctl -u alloy -n 100

# Verify services are producing logs
journalctl -u cheddar-backend -n 20
journalctl -u cheddar-frontend -n 20

# Check Alloy can read journals
sudo journalctl _SYSTEMD_UNIT=cheddar-backend.service -n 5
```

### No metrics appearing

```bash
# Check if prometheus.exporter.unix is working
curl http://localhost:12345/metrics

# Should show Alloy's internal metrics and unix exporter metrics
```

### High memory usage

Alloy's default memory limit is sufficient for most cases. If needed:

```bash
# Edit service override
sudo systemctl edit alloy

# Add:
[Service]
MemoryMax=256M

# Save and restart
sudo systemctl daemon-reload
sudo systemctl restart alloy
```

### Authentication errors

If you see "401 Unauthorized" in logs:

```bash
# Check API key is set correctly
sudo cat /etc/systemd/system/alloy.service.d/env.conf

# Should show GCLOUD_RW_API_KEY starting with "glc_..."
# If missing or wrong, edit:
sudo nano /etc/systemd/system/alloy.service.d/env.conf

# Then reload
sudo systemctl daemon-reload
sudo systemctl restart alloy
```

## 📚 Additional Resources

- **Grafana Alloy Docs**: <https://grafana.com/docs/alloy/latest/>
- **Grafana Cloud**: <https://grafana.com/docs/grafana-cloud/>
- **PromQL Guide**: <https://prometheus.io/docs/prometheus/latest/querying/basics/>
- **LogQL Guide**: <https://grafana.com/docs/loki/latest/logql/>

## 🎯 Quick Reference

### Common Commands

```bash
# Alloy service management
sudo systemctl status alloy
sudo systemctl restart alloy
sudo systemctl stop alloy
sudo systemctl start alloy

# View logs
journalctl -u alloy -f              # Follow Alloy logs
journalctl -u alloy -n 100          # Last 100 lines
journalctl -u alloy --since "1h ago" # Last hour

# Check configuration
sudo alloy fmt /etc/alloy/config.alloy  # Format and validate config
sudo cat /etc/alloy/config.alloy        # View current config

# Check what Alloy is exposing
curl http://localhost:12345/metrics     # Alloy's metrics endpoint
```

### Service URLs

- **Grafana Dashboard**: https://\<your-stack\>.grafana.net
- **Prometheus**: <https://prometheus-\><region\>.grafana.net
- **Loki**: <https://logs-\><region\>.grafana.net
- **Fleet Management**: <https://fleet-management-\><region\>.grafana.net

---

**Last Updated:** 2025-11-09  
**Maintainer:** Adam Probert
