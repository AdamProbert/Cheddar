"""Prometheus metrics for ChedWeb backend monitoring."""

from prometheus_client import Counter, Gauge, Histogram, Info
import psutil
import time

# ========================================
# APPLICATION INFO
# ========================================

app_info = Info("chedweb_backend", "ChedWeb backend application information")
app_info.info(
    {
        "version": "0.1.0",
        "component": "backend",
    }
)

# ========================================
# HTTP/API METRICS
# ========================================

http_requests_total = Counter(
    "chedweb_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "chedweb_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

http_requests_in_progress = Gauge(
    "chedweb_http_requests_in_progress",
    "Number of HTTP requests in progress",
    ["method", "endpoint"],
)

# ========================================
# WEBRTC METRICS
# ========================================

webrtc_connections_total = Counter(
    "chedweb_webrtc_connections_total",
    "Total WebRTC connections attempted",
    ["status"],  # success, failed
)

webrtc_connections_active = Gauge(
    "chedweb_webrtc_connections_active",
    "Number of active WebRTC peer connections",
)

webrtc_data_channel_messages_total = Counter(
    "chedweb_webrtc_datachannel_messages_total",
    "Total data channel messages",
    ["direction"],  # sent, received
)

webrtc_ice_candidates_total = Counter(
    "chedweb_webrtc_ice_candidates_total",
    "Total ICE candidates processed",
)

webrtc_connection_state_changes = Counter(
    "chedweb_webrtc_connection_state_changes_total",
    "WebRTC connection state changes",
    ["state"],  # new, connecting, connected, disconnected, failed, closed
)

# ========================================
# CAMERA METRICS
# ========================================

camera_enabled = Gauge(
    "chedweb_camera_enabled",
    "Camera enabled status (1=enabled, 0=disabled)",
)

camera_frames_total = Counter(
    "chedweb_camera_frames_total",
    "Total camera frames captured",
)

camera_frame_errors_total = Counter(
    "chedweb_camera_frame_errors_total",
    "Total camera frame capture errors",
)

camera_fps = Gauge(
    "chedweb_camera_fps",
    "Current camera frames per second",
)

camera_resolution = Info(
    "chedweb_camera_resolution",
    "Camera resolution settings",
)

camera_settings_changes_total = Counter(
    "chedweb_camera_settings_changes_total",
    "Total camera settings changes",
    ["setting"],  # awb_mode, color_gains, framerate, resolution
)

# ========================================
# MOTION DRIVER METRICS
# ========================================

motion_driver_connected = Gauge(
    "chedweb_motion_driver_connected",
    "Motion driver connection status (1=connected, 0=disconnected)",
)

motion_driver_commands_total = Counter(
    "chedweb_motion_driver_commands_total",
    "Total motion driver commands sent",
    ["command_type"],  # motor, servo, emergency_stop, etc.
)

motion_driver_command_errors_total = Counter(
    "chedweb_motion_driver_command_errors_total",
    "Total motion driver command errors",
    ["error_type"],  # timeout, invalid, serial_error
)

motion_driver_serial_bytes_total = Counter(
    "chedweb_motion_driver_serial_bytes_total",
    "Total bytes transferred over serial",
    ["direction"],  # sent, received
)

# ========================================
# SYSTEM METRICS (Process-specific)
# ========================================

process_cpu_usage = Gauge(
    "chedweb_process_cpu_percent",
    "CPU usage percentage of the backend process",
)

process_memory_bytes = Gauge(
    "chedweb_process_memory_bytes",
    "Memory usage in bytes of the backend process",
    ["type"],  # rss, vms
)

process_open_fds = Gauge(
    "chedweb_process_open_file_descriptors",
    "Number of open file descriptors",
)

process_threads = Gauge(
    "chedweb_process_threads",
    "Number of threads in the process",
)

# ========================================
# CONTROL COMMAND METRICS
# ========================================

control_commands_total = Counter(
    "chedweb_control_commands_total",
    "Total control commands received",
    ["source"],  # datachannel, api
)

control_command_processing_duration = Histogram(
    "chedweb_control_command_processing_seconds",
    "Time to process control commands",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
)

deadman_switch_timeouts_total = Counter(
    "chedweb_deadman_switch_timeouts_total",
    "Total deadman switch timeout events",
)

# ========================================
# ERROR METRICS
# ========================================

errors_total = Counter(
    "chedweb_errors_total",
    "Total errors by type",
    ["error_type", "component"],
)

# ========================================
# HELPER FUNCTIONS
# ========================================


def update_process_metrics():
    """Update process-specific system metrics."""
    try:
        process = psutil.Process()

        # CPU usage
        process_cpu_usage.set(process.cpu_percent(interval=0.1))

        # Memory usage
        mem_info = process.memory_info()
        process_memory_bytes.labels(type="rss").set(mem_info.rss)
        process_memory_bytes.labels(type="vms").set(mem_info.vms)

        # File descriptors (Unix-like systems)
        try:
            process_open_fds.set(process.num_fds())
        except AttributeError:
            # Windows doesn't support num_fds()
            pass

        # Threads
        process_threads.set(process.num_threads())

    except Exception as e:
        errors_total.labels(error_type="metrics_update", component="system").inc()
