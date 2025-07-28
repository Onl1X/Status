# TrueNAS Scale Status App Setup Guide

## Problem Description
The status app was not detecting storage properly in TrueNAS Scale containers due to:
1. Container isolation preventing access to host mount information
2. Incorrect parsing of /proc/mounts in containerized environment  
3. Missing environment variables for host root path access

## Solution Overview
The updated solution includes:
1. **Enhanced storage.py** with better mount detection and host root path support
2. **Proper Docker Compose configuration** with required environment variables and volume mounts
3. **Custom storage configuration** for explicit mount point definition
4. **Fallback detection** when /proc/mounts is not accessible

## Files Modified

### 1. lib/machine/storage.py
- Added support for `STATUS_CUSTOM_ROOT_PATH` environment variable
- Improved mount point filtering to include `/mnt/` directories
- Added fallback storage detection method
- Enhanced error handling for containerized environments
- Better filesystem type detection and pseudo-filesystem filtering

### 2. docker-compose.yml
- Added `STATUS_CUSTOM_ROOT_PATH=/host_root` environment variable
- Proper volume mounts for host system access
- Maintains your existing volume configuration

### 3. config.json
- Enabled custom storage configuration
- Pre-configured with your TrueNAS Scale mount points
- Easy to modify for your specific setup

## Deployment Instructions

### Option 1: Using Custom Storage (Recommended)
This approach explicitly defines which storage locations to monitor.

1. **Update your Docker Compose file** with the provided configuration
2. **Copy the config.json** to your config directory (`/mnt/ssd/t/config.json`)
3. **Customize the storage section** in config.json to match your actual mount points:

```json
{
    "machine": {
        "custom_storage": true,
        "storage": {
            "OS": "/",
            "SSD": "/mnt/ssd",
            "General": "/mnt/General",
            "Apps": "/mnt/Apps",
            "Homeassistant": "/mnt/Homeassistant", 
            "Media": "/mnt/Media",
            "Config": "/mnt/Config"
        }
    }
}
```

4. **Deploy the container** using your updated docker-compose.yml

### Option 2: Using Automatic Detection
If you prefer automatic detection, set `custom_storage: false` in config.json. The app will now properly detect mounted filesystems including your `/mnt/ssd` directory.

## Configuration Options

### Storage Configuration
- **custom_storage**: Set to `true` to use explicit mount points, `false` for auto-detection
- **storage**: Dictionary of display names and their corresponding mount paths
- **hide_boot_partition**: Hide /boot partitions from display
- **enable_storage_blacklist**: Enable filtering of specific mount points
- **storage_blacklist**: Array of mount points to exclude

### Environment Variables
- **STATUS_CUSTOM_ROOT_PATH**: Set to `/host_root` to access host filesystem from container

## Testing

You can test the storage detection using the provided test script:

```bash
# From the host system (outside container)
python3 test_storage.py
```

This will show:
- Current configuration status
- Detected storage devices and their usage
- Mount point detection results

## Troubleshooting

### Storage Not Detected
1. **Check volume mounts**: Ensure all required directories are mounted in the container
2. **Verify environment variable**: `STATUS_CUSTOM_ROOT_PATH` should be set to `/host_root`
3. **Check permissions**: Ensure the container can read the mounted directories
4. **Review config.json**: Verify storage paths are correct

### Permission Errors
1. **Add `:ro` suffix** to volume mounts for read-only access
2. **Check TrueNAS permissions** on the mounted directories
3. **Verify container user** has read access to mounted paths

### Container Won't Start
1. **Check volume paths exist** on the host system
2. **Verify config.json syntax** is valid JSON
3. **Review container logs** for specific error messages

## Your Specific Setup

Based on your screenshot, your TrueNAS Scale has these storage locations:
- **Mnt**: 112 GB total (your main storage pool)
- **Ssd**: 188 GB total (your SSD for apps)
- **General**: 188 GB total
- **Apps**: 188 GB total  
- **Homeassistant**: 188 GB total
- **Media**: 188 GB total
- **Config**: 188 GB total

The provided config.json is pre-configured for these mount points. Adjust the storage section if your actual mount paths differ.

## Expected Result

After applying these changes, your status app should display:
- OS root filesystem usage
- SSD storage usage (/mnt/ssd)
- All your TrueNAS datasets under /mnt/
- Proper storage capacity and usage statistics
- Clean, organized display with appropriate icons

The app will now properly detect and monitor your physical disk storage as requested.