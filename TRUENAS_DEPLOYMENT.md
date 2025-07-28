# TrueNAS Scale Deployment Guide

This guide explains how to deploy the status-app in TrueNAS Scale with proper storage detection.

## Problem Resolution

The original issue was that the status-app couldn't detect storage in TrueNAS Scale. This has been resolved by:

1. **Fixed storage.py**: Modified to handle missing mount points gracefully
2. **Created proper config.json**: Configured for custom storage detection
3. **Updated docker-compose.yml**: Corrected volume mounts and configuration

## Configuration Files

### config.json
```json
{
  "server": {
    "port": 8080,
    "address": "0.0.0.0"
  },
  "machine": {
    "custom_storage": true,
    "storage": {
      "SSD": "/mnt/ssd",
      "Mnt": "/mnt"
    },
    "hide_boot_partition": true,
    "enable_storage_blacklist": false,
    "storage_blacklist": []
  },
  "misc": {
    "debug": false
  }
}
```

### docker-compose.yml
```yaml
services:
  status-app:
    container_name: status-app
    image: onl1x/status-app:latest
    network_mode: host
    restart: unless-stopped
    volumes:
      - /etc/os-release:/host_root/etc/os-release:ro
      - /etc/hostname:/host_root/etc/hostname:ro
      - /proc:/host_root/proc:ro
      - /sys:/host_root/sys:ro
      - /dev:/host_root/dev:ro
      - /mnt/ssd:/mnt/ssd:ro
      - /mnt:/mnt:ro
      - /var:/var:ro
      - /boot:/boot:ro
      - /tmp:/tmp:ro
      - ./config.json:/app/config.json:ro
      - /:/host_root:ro
```

## Key Changes Made

### 1. Storage Detection Logic
- Added graceful handling of missing mount points
- Improved error handling for FileNotFoundError and PermissionError
- Added specific path handling for `/mnt/ssd` and `/mnt`

### 2. Configuration
- Enabled `custom_storage` to specify exact mount points
- Configured storage paths for your TrueNAS setup
- Set proper server configuration

### 3. Docker Configuration
- Corrected volume mounts to include all necessary paths
- Added config.json mount at `/app/config.json`
- Ensured proper read-only access to system paths

## Deployment Steps

1. **Copy the configuration files** to your TrueNAS Scale system
2. **Ensure mount points exist**: `/mnt/ssd` and `/mnt` should be available
3. **Deploy using docker-compose**:
   ```bash
   docker-compose up -d
   ```

## Expected Results

When properly deployed in TrueNAS Scale, you should see:

- **SSD**: Your `/mnt/ssd` mount point with storage information
- **Mnt**: Your `/mnt` mount point with storage information
- Proper icons and storage usage statistics

## Troubleshooting

### If storage still doesn't appear:
1. Check that mount points exist: `ls -la /mnt/ssd /mnt`
2. Verify Docker has access to the mount points
3. Check container logs: `docker logs status-app`
4. Test storage detection manually: `python3 test_storage.py`

### If you need to modify mount points:
1. Edit the `config.json` file
2. Update the `storage` section with your desired paths
3. Restart the container: `docker-compose restart`

## Testing

Use the included `test_storage.py` script to verify storage detection:

```bash
python3 test_storage.py
```

This will show you exactly what storage is being detected and whether your mount points are accessible.