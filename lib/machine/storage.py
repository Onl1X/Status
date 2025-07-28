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
			# Get mount information from host system
			mounts_content = get("/proc/mounts")
			if not mounts_content:
				# Fallback: try to detect common mount points directly
				return Storage._get_fallback_storage()
			
			mounts = mounts_content.split("\n")
			listed_devices = []
			
			for mount in mounts:
				if not mount.strip():
					continue
					
				line = mount.split()
				if len(line) < 3:
					continue
					
				device = line[0]
				mount_point = line[1]
				fs_type = line[2]
				
				# Skip pseudo filesystems
				pseudo_fs = [
					"tmpfs", "proc", "sysfs", "overlay", "devtmpfs", "devpts", 
					"cgroup", "squashfs", "mqueue", "fuse.lxcfs", "rpc_pipefs", 
					"nsfs", "securityfs", "cgroup2", "pstore", "autofs", "hugetlbfs",
					"binfmt_misc", "fusectl", "tracefs", "configfs", "debugfs", 
					"fuse.gvfsd-fuse", "fuse.portal", "fuse.snapd", "fuse", "cuse", "fuseblk"
				]
				
				if fs_type in pseudo_fs:
					continue
				
				# Filter for relevant mount points - include both /dev/ mounts and important directories
				is_relevant = (
					device.startswith("/dev/") or 
					mount_point.startswith("/mnt/") or
					mount_point == "/" or
					mount_point.startswith("/home") or
					mount_point.startswith("/var") or
					mount_point.startswith("/boot")
				)
				
				if not is_relevant:
					continue
				
				# Apply configuration filters
				if config.get("machine", "hide_boot_partition"):
					if mount_point.startswith("/boot"):
						continue
						
				if config.get("machine", "enable_storage_blacklist"):
					if mount_point in config.get("machine", "storage_blacklist"):
						continue
				
				stuff = nice_path(mount_point)
				
				# Avoid duplicates based on device
				if device not in listed_devices:
					filesystems[stuff[0]] = [mount_point, stuff[1], fs_type]
					listed_devices.append(device)

		result = {}

		for fs in filesystems:
			mount_path = filesystems[fs][0]
			
			# Use host root path if available
			try:
				from .utils import CUSTOM_ROOT_PATH
				if CUSTOM_ROOT_PATH and not mount_path.startswith(CUSTOM_ROOT_PATH):
					if mount_path.startswith("/"):
						check_path = CUSTOM_ROOT_PATH + mount_path
					else:
						check_path = mount_path
				else:
					check_path = mount_path
				
				# Try to get usage stats
				usage = os.statvfs(check_path)
				
			except (PermissionError, FileNotFoundError, OSError) as e:
				# If host root path fails, try original path
				try:
					usage = os.statvfs(mount_path)
				except (PermissionError, FileNotFoundError, OSError):
					continue

			# ext4 fs dirty-improvement to show nicely rounded storage size
			inode_overhead = 0
			if len(filesystems[fs]) > 2 and filesystems[fs][2] == "ext4":
				inode_size = 256		# Default for mkfs.ext4
				correction = 1.2
				inode_overhead = inode_size * usage.f_files * correction

			result[fs] = {
				"icon": filesystems[fs][1],
				"total": usage.f_bsize * usage.f_blocks + inode_overhead,
				"available": usage.f_bsize * usage.f_bavail
			}

		return result

	@staticmethod
	def _get_fallback_storage():
		"""Fallback method to detect storage when /proc/mounts is not accessible"""
		common_paths = [
			("/", "OS"),
			("/mnt/ssd", "SSD"),
			("/mnt", "Storage"),
			("/home", "Home"),
			("/var", "Var")
		]
		
		filesystems = {}
		for path, name in common_paths:
			try:
				# Check if path exists and is accessible
				from .utils import CUSTOM_ROOT_PATH
				if CUSTOM_ROOT_PATH:
					check_path = CUSTOM_ROOT_PATH + path
				else:
					check_path = path
					
				if os.path.exists(check_path) and os.access(check_path, os.R_OK):
					stuff = nice_path(path)
					filesystems[name] = [path, stuff[1]]
			except:
				continue
				
		return filesystems


def nice_path(path):
	if path == "/":
		return ["OS", "settings"]

	elif path.startswith("/boot"):
		return ["Boot", "sprint"]
	
	elif path.startswith("/mnt/ssd"):
		return ["SSD", "folder"]
	
	elif path.startswith("/mnt/"):
		# Extract the mount name from /mnt/xxx
		mount_name = path.split("/")[2] if len(path.split("/")) > 2 else "Storage"
		return [mount_name.title(), "folder"]

	return [path.split("/")[-1].title(), "folder"]
