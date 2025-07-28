import shutil
import os

from .utils import get
from ..config import config


class Storage:

    @staticmethod
    def get_usage():
        filesystems = {}

        if config.get("machine", "custom_storage"):
            storage = config.get("machine", "storage")
            for item in storage:
                filesystems[item] = [storage[item], nice_path(storage[item])[1]]

        else:
            filesystems = Storage._detect_physical_storage()

        result = {}

        for fs in filesystems:
            try:
                usage = os.statvfs(filesystems[fs][0])
            except PermissionError:
                continue
            except FileNotFoundError:
                continue

            # ext4 fs dirty-improvement to show nicely rounded storage size
            inode_overhead = 0
            if len(filesystems[fs]) > 2 and filesystems[fs][2] == "ext4":
                inode_size = 256        # Default for mkfs.ext4
                correction = 1.2
                inode_overhead = inode_size * usage.f_files * correction

            result[fs] = {
                "icon": filesystems[fs][1],
                "total": usage.f_bsize * usage.f_blocks + inode_overhead,
                "available": usage.f_bsize * usage.f_bavail
            }

        return result

    @staticmethod
    def _detect_physical_storage():
        """Detect only physical storage devices, filtering out virtual filesystems"""
        filesystems = {}
        mounts = get("/proc/mounts").split("\n")
        listed_devices = []

        # List of pseudo-filesystems to skip (virtual filesystems)
        pseudo_fs = [
            "tmpfs", "proc", "sysfs", "overlay", "devtmpfs", "devpts", "cgroup", "squashfs", "mqueue",
            "fuse.lxcfs", "rpc_pipefs", "nsfs", "securityfs", "cgroup2", "pstore", "autofs", "hugetlbfs",
            "binfmt_misc", "fusectl", "tracefs", "configfs", "debugfs", "fuse.gvfsd-fuse", "fuse.portal",
            "fuse.snapd", "fuse", "cuse", "fuseblk", "zfs", "fuse.sshfs", "fuse.rclone", "fuse.mergerfs"
        ]

        # List of paths to skip (system paths, not storage)
        skip_paths = [
            "/proc", "/sys", "/dev", "/run", "/tmp", "/var/run", "/var/lock", "/var/tmp",
            "/boot/efi", "/boot/grub", "/snap", "/var/snap", "/var/lib/snapd"
        ]

        for mount in mounts:
            if not mount.strip():
                continue
            line = mount.split(" ")
            if len(line) < 3:
                continue
            mount_source = line[0]
            mount_target = line[1]
            fs_type = line[2]

            # Skip pseudo filesystems
            if fs_type in pseudo_fs:
                continue

            # Skip system paths
            if any(mount_target.startswith(path) for path in skip_paths):
                continue

            # Skip boot partition if configured
            if config.get("machine", "hide_boot_partition"):
                if mount_target.startswith("/boot"):
                    continue

            # Skip blacklisted storage if configured
            if config.get("machine", "enable_storage_blacklist"):
                if mount_target in config.get("machine", "storage_blacklist"):
                    continue

            # Only include physical storage devices
            # Look for device files that represent actual storage
            if mount_source.startswith("/dev/"):
                # Skip loop devices unless they're specifically storage
                if "loop" in mount_source:
                    continue
                
                # Check if this is a real storage device
                if Storage._is_physical_storage(mount_source, mount_target):
                    # Only add if not already listed
                    key = f"{mount_source}:{mount_target}"
                    if key not in listed_devices:
                        name = Storage._get_storage_name(mount_target)
                        icon = Storage._get_storage_icon(mount_target, fs_type)
                        filesystems[name] = [mount_target, icon, fs_type]
                        listed_devices.append(key)

        return filesystems

    @staticmethod
    def _is_physical_storage(device_path, mount_path):
        """Check if this is a physical storage device"""
        # Always include /mnt paths (TrueNAS datasets)
        if mount_path.startswith("/mnt/"):
            return True
        
        # Include root filesystem
        if mount_path == "/":
            return True
        
        # Include common storage paths
        storage_paths = ["/home", "/var", "/opt", "/usr/local"]
        if any(mount_path.startswith(path) for path in storage_paths):
            return True
        
        # Skip if it's a system device
        system_devices = ["/dev/loop", "/dev/shm", "/dev/pts", "/dev/mqueue"]
        if any(device_path.startswith(dev) for dev in system_devices):
            return False
        
        return True

    @staticmethod
    def _get_storage_name(mount_path):
        """Get a nice name for the storage device"""
        if mount_path == "/":
            return "System"
        elif mount_path.startswith("/mnt/"):
            # Extract dataset/pool name
            parts = mount_path.split("/")
            if len(parts) >= 3:
                return parts[2].title()  # /mnt/ssd -> "Ssd"
            return mount_path.split("/")[-1].title()
        elif mount_path.startswith("/home"):
            return "Home"
        elif mount_path.startswith("/var"):
            return "Data"
        else:
            return mount_path.split("/")[-1].title()

    @staticmethod
    def _get_storage_icon(mount_path, fs_type):
        """Get appropriate icon for storage type"""
        if mount_path.startswith("/mnt/"):
            return "database"  # ZFS pools/datasets
        elif fs_type in ["ext4", "xfs", "btrfs"]:
            return "storage"
        else:
            return "folder"


def nice_path(path):
    if path == "/":
        return ["OS", "settings"]

    elif path.startswith("/boot"):
        return ["Boot", "sprint"]

    return [path.split("/")[-1].title(), "folder"]
