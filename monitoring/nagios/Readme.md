# Monitoring Setup — Weather Dashboard
## Nagios Configuration Summary

### What We Monitor

| Service Check | Endpoint | Interval | Alert Condition |
|---|---|---|---|
| HTTP Port 5000 | `:5000` | 1 min | Port not reachable |
| Health Endpoint | `/health` | 1 min | HTTP ≠ 200 or "healthy" missing |
| Response Time | `/health` | 2 min | Warn > 2s / Critical > 5s |
| API Endpoint | `/api/recent` | 5 min | HTTP ≠ 200 or "status" missing |

### Alert Flow

```
Service DOWN (3 consecutive failures)
        ↓
Nagios triggers contact notification
        ↓
Email sent to: your-email@university.edu
        ↓
Service RECOVERY → Recovery email sent
```

### Accessing Nagios Dashboard

When running via docker-compose:

```
URL      : http://localhost:8080
Username : nagiosadmin
Password : nagios123
```

Navigate to:
- **Services** → see all 4 checks with status (OK / WARNING / CRITICAL)
- **Host Detail** → `weather-app` host and its uptime
- **Event Log** → history of state changes

### Thresholds Explained

- **check_interval: 1** — Nagios pings the service every 1 minute
- **max_check_attempts: 3** — must fail 3 times in a row before alerting (avoids false alarms)
- **retry_interval: 1** — re-checks every 1 minute after a failure
- **notification_interval: 30** — re-alerts every 30 minutes if still down

### Adding More Checks (optional for demo)

To monitor disk space or CPU inside the container, install `nagios-nrpe-server`
in the app container and add:

```nagios
define service {
    host_name           weather-app
    service_description CPU Usage
    check_command       check_nrpe!check_load
    ...
}
```