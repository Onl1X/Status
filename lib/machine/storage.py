import shutil
import os
import json

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
			# TrueNAS SCALE specific storage detection
			filesystems = Storage._detect_truenas_storage()
			
			# Fallback to standard Linux detection if no TrueNAS storage found
			if not filesystems:
				filesystems = Storage._detect_standard_storage()

		result = {}

		for fs in filesystems:
			try:
				usage = os.statvfs(filesystems[fs][0])

			except PermissionError:
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
	def _detect_truenas_storage():
		"""Detect TrueNAS SCALE storage pools and datasets"""
		filesystems = {}
		
		# Check if we're running on TrueNAS SCALE
		try:
			with open('/etc/os-release', 'r') as f:
				os_info = f.read()
				if 'truenas' not in os_info.lower():
					return {}
		except:
			return {}
		
		# Look for ZFS pools and datasets
		try:
			# Check for common TrueNAS mount points
			truenas_paths = [
				'/mnt',  # Main mount point for TrueNAS datasets
				'/var/db/system',  # System datasets
				'/var/lib/middleware',  # Middleware data
			]
			
			for base_path in truenas_paths:
				if os.path.exists(base_path):
					# Scan for datasets
					for root, dirs, files in os.walk(base_path):
						# Limit depth to avoid scanning too deep
						if root.count('/') - base_path.count('/') > 2:
							continue
						
						# Check if this looks like a dataset (has content or is a mount point)
						if os.path.ismount(root) or any(os.listdir(root)):
							# Get dataset name
							dataset_name = root.split('/')[-1] if root != base_path else 'Root'
							if dataset_name and dataset_name not in ['proc', 'sys', 'dev', 'tmp']:
								icon = "database" if "system" in root else "folder"
								filesystems[dataset_name] = [root, icon]
			
			# Also check for specific pool directories
			for item in os.listdir('/mnt'):
				item_path = os.path.join('/mnt', item)
				if os.path.isdir(item_path) and not item.startswith('.'):
					filesystems[item] = [item_path, "database"]
					
		except Exception as e:
			# If TrueNAS detection fails, return empty dict to fall back to standard detection
			pass
		
		return filesystems

	@staticmethod
	def _detect_standard_storage():
		"""Standard Linux storage detection (original logic)"""
		filesystems = {}
		mounts = get("/proc/mounts").split("\n")
		listed_devices = []
		
		for mount in mounts:
			if mount.startswith("/dev/"):
				line = mount.split(" ")
				stuff = nice_path(line[1])
				if config.get("machine", "hide_boot_partition"):
					if line[1].startswith("/boot"):
						continue
				if config.get("machine", "enable_storage_blacklist"):
					if line[1] in config.get("machine", "storage_blacklist"):
						continue
				if line[0] not in listed_devices:
					filesystems[stuff[0]] = [line[1], stuff[1], line[2]]
				listed_devices.append(line[0])
		
		return filesystems


def nice_path(path):
	if path == "/":
		return ["OS", "settings"]

	elif path.startswith("/boot"):
		return ["Boot", "sprint"]

	return [path.split("/")[-1].title(), "folder"]
