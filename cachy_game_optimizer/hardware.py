"""
CachyOS Game Optimizer - Hardware Detection Module (Optimized)
Fast hardware detection with parallel execution and caching.
"""

import os
import re
import json
import subprocess
import concurrent.futures
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from pathlib import Path
from functools import lru_cache


@dataclass
class CPUInfo:
    model: str
    cores: int
    threads: int
    base_clock: float
    boost_clock: float
    cache_l3: str
    architecture: str
    governor: str = "unknown"
    max_freq: float = 0.0
    min_freq: float = 0.0


@dataclass
class GPUInfo:
    vendor: str
    model: str
    vram_mb: int
    driver: str
    driver_version: str
    vulkan_support: bool = False
    opencl_support: bool = False
    pcie_gen: str = "unknown"
    pcie_width: str = "unknown"


@dataclass
class MemoryInfo:
    total_gb: float
    available_gb: float
    type: str  # DDR3, DDR4, DDR5
    speed_mhz: int
    channels: int
    usage_percent: float = 0.0


@dataclass
class StorageInfo:
    device: str
    type: str  # NVMe, SSD, HDD
    size_gb: float
    mount_point: str
    filesystem: str
    read_speed_mb: float = 0.0
    write_speed_mb: float = 0.0


@dataclass
class KernelInfo:
    version: str
    cmdline: str
    scheduler: str
    transparent_hugepages: str
    swappiness: int


@dataclass
class SystemProfile:
    cpu: CPUInfo
    gpu: GPUInfo
    memory: MemoryInfo
    storage: List[StorageInfo]
    kernel: KernelInfo
    distro: str
    desktop: str
    is_laptop: bool = False
    thermal_throttling: bool = False


# ============================================================
# FAST SUBPROCESS HELPERS
# ============================================================

def run_cmd(cmd: List[str], timeout: float = 2.0) -> str:
    """Run command with timeout, return empty string on failure."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout
    except Exception:
        return ""


def run_cmds_parallel(commands: Dict[str, List[str]], timeout: float = 2.0) -> Dict[str, str]:
    """Run multiple commands in parallel."""
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(commands)) as executor:
        futures = {name: executor.submit(run_cmd, cmd, timeout) for name, cmd in commands.items()}
        for name, future in futures.items():
            try:
                results[name] = future.result(timeout=timeout + 0.5)
            except Exception:
                results[name] = ""
    return results


# ============================================================
# CACHED DETECTION FUNCTIONS
# ============================================================

@lru_cache(maxsize=1)
def _get_cpuinfo() -> str:
    return Path('/proc/cpuinfo').read_text()

@lru_cache(maxsize=1)
def _get_meminfo() -> str:
    return Path('/proc/meminfo').read_text()

@lru_cache(maxsize=1)
def _get_cmdline() -> str:
    return Path('/proc/cmdline').read_text()

@lru_cache(maxsize=1)
def _get_version() -> str:
    return Path('/proc/version').read_text()


def detect_cpu_fast() -> CPUInfo:
    """Fast CPU detection using cached /proc/cpuinfo + parallel lscpu."""
    cpuinfo = _get_cpuinfo()
    
    model_match = re.search(r'model name\s+:\s+(.+)', cpuinfo)
    model = model_match.group(1).strip() if model_match else "Unknown"
    
    cores = len(re.findall(r'^processor\s+:', cpuinfo, re.MULTILINE))
    cache_match = re.search(r'cache size\s+:\s+(.+)', cpuinfo)
    cache_l3 = cache_match.group(1).strip() if cache_match else "Unknown"
    
    # Parallel: lscpu + governor + frequencies
    cmds = {
        'lscpu': ['lscpu'],
        'governor': ['cat', '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor'],
        'max_freq': ['cat', '/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq'],
        'min_freq': ['cat', '/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq'],
    }
    results = run_cmds_parallel(cmds, timeout=1.5)
    
    # Parse lscpu
    threads = cores
    architecture = "x86_64"
    lscpu_out = results.get('lscpu', '')
    if lscpu_out:
        threads_match = re.search(r'Thread\(s\) per core:\s+(\d+)', lscpu_out)
        if threads_match:
            threads = cores * int(threads_match.group(1))
        arch_match = re.search(r'Architecture:\s+(\S+)', lscpu_out)
        if arch_match:
            architecture = arch_match.group(1)
    
    governor = results.get('governor', 'powersave').strip() or 'powersave'
    
    try:
        max_freq = float(results.get('max_freq', '0')) / 1000
    except Exception:
        max_freq = 0.0
    try:
        min_freq = float(results.get('min_freq', '0')) / 1000
    except Exception:
        min_freq = 0.0
    
    base_clock = 0.0
    freq_match = re.search(r'@\s*([\d.]+)\s*GHz', model)
    if freq_match:
        base_clock = float(freq_match.group(1))
    
    return CPUInfo(
        model=model, cores=cores, threads=threads,
        base_clock=base_clock, boost_clock=0.0,
        cache_l3=cache_l3, architecture=architecture,
        governor=governor, max_freq=max_freq, min_freq=min_freq
    )


def detect_gpu_fast() -> GPUInfo:
    """Fast GPU detection with parallel commands - accurate VRAM and model."""
    cmds = {
        'lspci_nn': ['lspci', '-nn'],
        'lspci_v': ['lspci', '-v'],
        'glxinfo': ['glxinfo', '-B'],
        'vulkaninfo': ['vulkaninfo', '--summary'],
        'clinfo': ['clinfo', '-l'],
    }
    results = run_cmds_parallel(cmds, timeout=2.0)
    
    vendor = "Unknown"
    model = "Unknown"
    vram_mb = 0
    driver_version = "Unknown"
    vulkan_support = False
    opencl_support = False
    pcie_gen = "unknown"
    pcie_width = "unknown"
    
    # Parse lspci -nn for vendor/model IDs
    lspci_nn = results.get('lspci_nn', '')
    gpu_pci_id = None
    gpu_device_id = None
    gpu_vendor_id = None
    for line in lspci_nn.split('\n'):
        if 'VGA' in line or 'Display' in line or '3D' in line:
            # Extract vendor:device IDs from [1002:6fdf]
            id_match = re.search(r'\[([0-9a-f]{4}):([0-9a-f]{4})\]', line)
            if id_match:
                gpu_vendor_id = id_match.group(1)
                gpu_device_id = id_match.group(2)
            
            if 'AMD' in line or 'ATI' in line:
                vendor = "AMD"
            elif 'NVIDIA' in line:
                vendor = "NVIDIA"
            elif 'Intel' in line:
                vendor = "Intel"
            
            # Try to get model name from the text description
            # Format: [0300]: Advanced Micro Devices, Inc. [AMD/ATI] Polaris 20 XL/XTR [Radeon RX 580 2048SP / RX 590 GME] [1002:6fdf]
            model_match = re.search(r'\]\s+(.+?)\s+\[[0-9a-f]{4}:[0-9a-f]{4}\]', line)
            if model_match:
                model = model_match.group(1).strip()
            else:
                # Fallback: get everything after the class code
                fallback_match = re.search(r'\[[0-9a-f]{4}\]:\s+(.+)', line)
                if fallback_match:
                    model = fallback_match.group(1).strip()
    
    # Parse glxinfo for renderer name (often more descriptive)
    glxinfo = results.get('glxinfo', '')
    if glxinfo:
        renderer_match = re.search(r'Renderer:\s+(.+)', glxinfo)
        if renderer_match:
            renderer = renderer_match.group(1).strip()
            # Prefer glxinfo renderer if it's more descriptive
            if len(renderer) > len(model) and 'AMD' not in model and 'NVIDIA' not in model and 'Intel' not in model:
                model = renderer
        version_match = re.search(r'OpenGL version string:\s+(.+)', glxinfo)
        if version_match:
            driver_version = version_match.group(1).strip()
    
    # VRAM from /sys/class/drm/ (accurate for AMD/NVIDIA)
    vram_mb = 0
    try:
        for card_path in Path('/sys/class/drm').glob('card*'):
            mem_file = card_path / 'device' / 'mem_info_vram_total'
            if mem_file.exists():
                vram_bytes = int(mem_file.read_text().strip())
                vram_mb = vram_bytes // (1024 * 1024)
                if vram_mb > 0:
                    break
    except Exception:
        pass
    
    # Fallback: VRAM from lspci -v (first BAR only, often incomplete)
    if vram_mb == 0:
        lspci_v = results.get('lspci_v', '')
        for section in lspci_v.split('\n\n'):
            if 'VGA' in section or 'Display' in section:
                mem_match = re.search(r'Memory at.*size=(\d+)([KMGT])', section)
                if mem_match:
                    size = int(mem_match.group(1))
                    unit = mem_match.group(2)
                    if unit == 'M':
                        vram_mb = size
                    elif unit == 'G':
                        vram_mb = size * 1024
    
    # Vulkan
    vulkan_support = 'Vulkan' in results.get('vulkaninfo', '')
    
    # OpenCL
    opencl_support = 'Platform' in results.get('clinfo', '')
    
    # PCIe info from lspci -vv (run if we have device ID)
    if gpu_device_id:
        try:
            lspci_vv = run_cmd(['lspci', '-vv', '-s', '01:00.0'], timeout=2.0)
            speed_match = re.search(r'LnkSta:.*Speed\s+([\d.]+)GT/s', lspci_vv)
            if speed_match:
                speed = float(speed_match.group(1))
                if speed >= 16:
                    pcie_gen = "5.0"
                elif speed >= 8:
                    pcie_gen = "4.0"
                elif speed >= 5:
                    pcie_gen = "3.0"
                elif speed >= 2.5:
                    pcie_gen = "2.0"
            
            width_match = re.search(r'Width\s+x(\d+)', lspci_vv)
            if width_match:
                pcie_width = f"x{width_match.group(1)}"
        except Exception:
            pass
    
    # Clean up model name
    if model and model != "Unknown":
        # Remove redundant vendor prefixes
        model = re.sub(r'^(Advanced Micro Devices, Inc\. \[AMD/ATI\]\s+)', '', model)
        model = re.sub(r'^(NVIDIA Corporation\s+)', '', model)
        model = re.sub(r'^(Intel Corporation\s+)', '', model)
    
    return GPUInfo(
        vendor=vendor, model=model, vram_mb=vram_mb,
        driver=vendor, driver_version=driver_version,
        vulkan_support=vulkan_support, opencl_support=opencl_support,
        pcie_gen=pcie_gen, pcie_width=pcie_width
    )


def detect_memory_fast() -> MemoryInfo:
    """Fast memory detection."""
    meminfo = _get_meminfo()
    
    total_kb = int(re.search(r'MemTotal:\s+(\d+)', meminfo).group(1))
    available_kb = int(re.search(r'MemAvailable:\s+(\d+)', meminfo).group(1))
    
    total_gb = total_kb / 1024 / 1024
    available_gb = available_kb / 1024 / 1024
    usage_percent = ((total_kb - available_kb) / total_kb) * 100
    
    # Guess DDR type from CPU (fast, no dmidecode)
    cpuinfo = _get_cpuinfo()
    mem_type = "DDR3"
    speed_mhz = 1333
    if 'Intel' in cpuinfo:
        if any(x in cpuinfo for x in ['6th Gen', '7th Gen', '8th Gen', '9th Gen', '10th Gen', '11th Gen', '12th Gen', '13th Gen', '14th Gen']):
            mem_type = "DDR4"
            speed_mhz = 2133
        elif any(x in cpuinfo for x in ['12th Gen', '13th Gen', '14th Gen']):
            mem_type = "DDR5"
            speed_mhz = 4800
    
    return MemoryInfo(
        total_gb=round(total_gb, 1), available_gb=round(available_gb, 1),
        type=mem_type, speed_mhz=speed_mhz, channels=2,
        usage_percent=round(usage_percent, 1)
    )


def detect_storage_fast() -> List[StorageInfo]:
    """Fast storage detection."""
    try:
        output = run_cmd(['lsblk', '-J', '-o', 'NAME,TYPE,SIZE,MOUNTPOINT,FSTYPE'], timeout=1.5)
        import json as json_module
        data = json_module.loads(output)
        
        storage = []
        for device in data.get('blockdevices', []):
            if device.get('type') == 'disk':
                for part in device.get('children', []):
                    if part.get('mountpoint'):
                        name = part.get('name', '')
                        if 'nvme' in name:
                            dev_type = "NVMe"
                        elif device.get('rota') == '0' or device.get('rota') == 0:
                            dev_type = "SSD"
                        else:
                            dev_type = "HDD"
                        
                        size_str = part.get('size', '0G')
                        size_gb = parse_size_fast(size_str)
                        
                        storage.append(StorageInfo(
                            device=f"/dev/{part['name']}", type=dev_type,
                            size_gb=size_gb, mount_point=part.get('mountpoint', ''),
                            filesystem=part.get('fstype', 'unknown')
                        ))
        return storage
    except Exception:
        return []


def parse_size_fast(size_str: str) -> float:
    size_str = size_str.upper()
    if 'T' in size_str:
        return float(size_str.replace('T', '').replace('G', '')) * 1024
    elif 'G' in size_str:
        return float(size_str.replace('G', ''))
    elif 'M' in size_str:
        return float(size_str.replace('M', '')) / 1024
    return 0.0


def detect_kernel_fast() -> KernelInfo:
    """Fast kernel detection."""
    version = _get_version().strip()
    cmdline = _get_cmdline().strip()
    
    # I/O scheduler
    scheduler = "none"
    try:
        for block in Path('/sys/block').glob('*'):
            sched_path = block / 'queue' / 'scheduler'
            if sched_path.exists():
                content = sched_path.read_text().strip()
                match = re.search(r'\[(\w+)\]', content)
                if match:
                    scheduler = match.group(1)
                    break
    except Exception:
        pass
    
    # THP
    thp = "unknown"
    try:
        thp_content = Path('/sys/kernel/mm/transparent_hugepage/enabled').read_text().strip()
        match = re.search(r'\[(\w+)\]', thp_content)
        if match:
            thp = match.group(1)
    except Exception:
        pass
    
    # Swappiness
    swappiness = 60
    try:
        swappiness = int(Path('/proc/sys/vm/swappiness').read_text().strip())
    except Exception:
        pass
    
    return KernelInfo(
        version=version, cmdline=cmdline, scheduler=scheduler,
        transparent_hugepages=thp, swappiness=swappiness
    )


def detect_distro_fast() -> str:
    try:
        os_release = Path('/etc/os-release').read_text()
        match = re.search(r'PRETTY_NAME="(.+)"', os_release)
        if match:
            return match.group(1)
    except Exception:
        pass
    return "Unknown"


def detect_desktop_fast() -> str:
    for var in ['XDG_CURRENT_DESKTOP', 'DESKTOP_SESSION']:
        val = os.environ.get(var, '')
        if val:
            return val
    return "Unknown"


# ============================================================
# MAIN DETECTOR CLASS
# ============================================================

class HardwareDetector:
    """Fast hardware detector with parallel execution."""
    
    def __init__(self):
        self._profile: Optional[SystemProfile] = None
    
    def get_full_profile(self) -> SystemProfile:
        """Get complete system profile - runs all detections in parallel."""
        if self._profile:
            return self._profile
        
        # Run all detections in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = {
                'cpu': executor.submit(detect_cpu_fast),
                'gpu': executor.submit(detect_gpu_fast),
                'memory': executor.submit(detect_memory_fast),
                'storage': executor.submit(detect_storage_fast),
                'kernel': executor.submit(detect_kernel_fast),
            }
            
            cpu = futures['cpu'].result(timeout=5.0)
            gpu = futures['gpu'].result(timeout=5.0)
            memory = futures['memory'].result(timeout=5.0)
            storage = futures['storage'].result(timeout=5.0)
            kernel = futures['kernel'].result(timeout=5.0)
        
        distro = detect_distro_fast()
        desktop = detect_desktop_fast()
        is_laptop = Path('/sys/class/power_supply/BAT0').exists()
        
        self._profile = SystemProfile(
            cpu=cpu, gpu=gpu, memory=memory, storage=storage,
            kernel=kernel, distro=distro, desktop=desktop, is_laptop=is_laptop
        )
        return self._profile
    
    def get_optimization_recommendations(self) -> List[Dict]:
        """Get hardware-specific optimization recommendations."""
        if not self._profile:
            self.get_full_profile()
        
        profile = self._profile
        recommendations = []
        
        cpu = profile.cpu
        if cpu.governor != 'performance':
            recommendations.append({
                'category': 'CPU', 'priority': 'HIGH',
                'title': 'Set CPU Governor to Performance',
                'description': f'Current governor is {cpu.governor}. Switch to performance for gaming.',
                'action': 'cpu_governor_performance'
            })
        
        mem = profile.memory
        if mem.total_gb <= 16:
            recommendations.append({
                'category': 'Memory', 'priority': 'HIGH',
                'title': 'Optimize Memory for Low RAM',
                'description': f'Only {mem.total_gb}GB RAM. Enable zram, reduce swappiness, use earlyoom.',
                'action': 'memory_optimize_low_ram'
            })
        
        if mem.type == 'DDR3':
            recommendations.append({
                'category': 'Memory', 'priority': 'MEDIUM',
                'title': 'DDR3 Memory Detected',
                'description': 'DDR3 is slower. Enable huge pages and optimize memory allocation.',
                'action': 'memory_ddr3_optimize'
            })
        
        gpu = profile.gpu
        if gpu.vendor == 'AMD':
            recommendations.append({
                'category': 'GPU', 'priority': 'HIGH',
                'title': 'AMD GPU Optimizations',
                'description': 'Enable RADV_PERFTEST, set power profile to high, use FSR.',
                'action': 'gpu_amd_optimize'
            })
        
        if gpu.vram_mb > 0 and gpu.vram_mb <= 2048:
            recommendations.append({
                'category': 'GPU', 'priority': 'HIGH',
                'title': 'Low VRAM (≤2GB) Optimization',
                'description': f'Only {gpu.vram_mb}MB VRAM. Enable texture compression, reduce texture quality.',
                'action': 'gpu_low_vram'
            })
        
        for disk in profile.storage:
            if disk.type == 'NVMe':
                recommendations.append({
                    'category': 'Storage', 'priority': 'MEDIUM',
                    'title': 'NVMe Optimizations',
                    'description': 'Enable write cache, tune I/O scheduler for NVMe.',
                    'action': 'storage_nvme_optimize'
                })
                break
        
        kernel = profile.kernel
        if kernel.swappiness > 10:
            recommendations.append({
                'category': 'Kernel', 'priority': 'HIGH',
                'title': 'Reduce Swappiness',
                'description': f'Current swappiness is {kernel.swappiness}. Set to 10 for gaming.',
                'action': 'kernel_swappiness'
            })
        
        if kernel.transparent_hugepages != 'madvise':
            recommendations.append({
                'category': 'Kernel', 'priority': 'MEDIUM',
                'title': 'Optimize Transparent Hugepages',
                'description': 'Set to madvise for better gaming performance.',
                'action': 'kernel_thp'
            })
        
        if 'cachyos' not in kernel.version.lower():
            recommendations.append({
                'category': 'Kernel', 'priority': 'MEDIUM',
                'title': 'Consider CachyOS Kernel',
                'description': 'CachyOS kernel has gaming optimizations (BORE, sched-ext, etc).',
                'action': 'kernel_cachyos'
            })
        
        return recommendations


# Singleton
_detector = None

def get_detector() -> HardwareDetector:
    global _detector
    if _detector is None:
        _detector = HardwareDetector()
    return _detector