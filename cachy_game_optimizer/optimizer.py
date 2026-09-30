"""
CachyOS Game Optimizer - Optimization Engine
Applies hardware-specific optimizations for maximum gaming performance.
"""

import subprocess
import os
import sys
import json
import shutil
from pathlib import Path
from typing import List, Dict, Callable, Optional
from dataclasses import dataclass
from enum import Enum

from .hardware import get_detector, SystemProfile


class OptimizationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class OptimizationResult:
    action_id: str
    status: OptimizationStatus
    message: str
    requires_reboot: bool = False
    details: Dict = None


class OptimizationEngine:
    """Applies gaming optimizations based on hardware profile."""
    
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.detector = get_detector()
        self.profile: Optional[SystemProfile] = None
        self.results: List[OptimizationResult] = []
        self.log_callback = log_callback or (lambda msg: None)
        
        # Register optimization actions
        self.actions: Dict[str, Callable] = {
            # CPU
            'cpu_governor_performance': self._cpu_governor_performance,
            'cpu_disable_mitigations': self._cpu_disable_mitigations,
            'cpu_enable_pstate': self._cpu_enable_pstate,
            
            # Memory
            'memory_optimize_low_ram': self._memory_optimize_low_ram,
            'memory_ddr3_optimize': self._memory_ddr3_optimize,
            'memory_enable_hugepages': self._memory_enable_hugepages,
            'memory_setup_zram': self._memory_setup_zram,
            'memory_earlyoom': self._memory_earlyoom,
            
            # GPU
            'gpu_amd_optimize': self._gpu_amd_optimize,
            'gpu_low_vram': self._gpu_low_vram,
            'gpu_enable_amdgpu_ppfeature': self._gpu_enable_amdgpu_ppfeature,
            
            # Kernel
            'kernel_swappiness': self._kernel_swappiness,
            'kernel_thp': self._kernel_thp,
            'kernel_cachyos': self._kernel_cachyos,
            'kernel_boore_scheduler': self._kernel_boore_scheduler,
            
            # Storage
            'storage_nvme_optimize': self._storage_nvme_optimize,
            'storage_scheduler': self._storage_scheduler,
            
            # Gaming
            'gaming_mode_enable': self._gaming_mode_enable,
            'gaming_feral_gamemode': self._gaming_feral_gamemode,
            'gaming_mangohud': self._gaming_mangohud,
            'gaming_vkbasalt': self._gaming_vkbasalt,
            
            # Wine/Proton
            'wine_esync_fsync': self._wine_esync_fsync,
            'wine_dxvk_cache': self._wine_dxvk_cache,
            'wine_gstreamer': self._wine_gstreamer,
        }
    
    def load_profile(self) -> SystemProfile:
        """Load hardware profile."""
        self.profile = self.detector.get_full_profile()
        return self.profile
    
    def get_recommendations(self) -> List[Dict]:
        """Get optimization recommendations."""
        if not self.profile:
            self.load_profile()
        return self.detector.get_optimization_recommendations()
    
    def run_action(self, action_id: str) -> OptimizationResult:
        """Run a single optimization action."""
        if action_id not in self.actions:
            return OptimizationResult(
                action_id=action_id,
                status=OptimizationStatus.FAILED,
                message=f"Unknown action: {action_id}"
            )
        
        self.log_callback(f"⚡ Starting: {action_id}")
        
        result = OptimizationResult(
            action_id=action_id,
            status=OptimizationStatus.RUNNING,
            message="Running..."
        )
        self.results.append(result)
        
        try:
            action_result = self.actions[action_id]()
            result.status = action_result.status
            result.message = action_result.message
            result.requires_reboot = action_result.requires_reboot
            result.details = action_result.details
            
            if result.status == OptimizationStatus.SUCCESS:
                self.log_callback(f"✓ {action_id}: {result.message}")
            elif result.status == OptimizationStatus.FAILED:
                self.log_callback(f"✗ {action_id}: {result.message}")
            elif result.status == OptimizationStatus.SKIPPED:
                self.log_callback(f"⊘ {action_id}: {result.message}")
                
        except Exception as e:
            result.status = OptimizationStatus.FAILED
            result.message = f"Error: {str(e)}"
            self.log_callback(f"✗ {action_id}: {result.message}")
        
        return result

    def _run_privileged(self, action: str, *args) -> dict:
        """Run a privileged action via pkexec."""
        import json
        import subprocess
        
        helper_path = Path(__file__).parent / "privileged_helper.py"
        python_path = sys.executable
        
        cmd = ["pkexec", python_path, str(helper_path), action] + list(args)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return json.loads(result.stdout.strip())
            else:
                return {"success": False, "error": result.stderr or "pkexec failed"}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout"}
        except json.JSONDecodeError:
            return {"success": False, "error": f"Invalid JSON output: {result.stdout}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_all_recommended(self) -> List[OptimizationResult]:
        """Run all recommended optimizations."""
        self.results = []
        recommendations = self.get_recommendations()
        
        for rec in recommendations:
            action_id = rec.get('action')
            if action_id and action_id in self.actions:
                self.run_action(action_id)
        
        return self.results
    
    def run_category(self, category: str) -> List[OptimizationResult]:
        """Run all optimizations for a category."""
        self.results = []
        recommendations = self.get_recommendations()
        
        for rec in recommendations:
            if rec.get('category', '').lower() == category.lower():
                action_id = rec.get('action')
                if action_id and action_id in self.actions:
                    self.run_action(action_id)
        
        return self.results
    
    # ===== CPU Optimizations =====
    
    def _cpu_governor_performance(self) -> OptimizationResult:
        """Set CPU governor to performance."""
        try:
            # Set via cpupower
            subprocess.run(['cpupower', 'frequency-set', '-g', 'performance'], 
                         check=True, capture_output=True)
            
            # Also set via sysfs for all cores
            for cpu_dir in Path('/sys/devices/system/cpu').glob('cpu[0-9]*'):
                gov_file = cpu_dir / 'cpufreq' / 'scaling_governor'
                if gov_file.exists():
                    gov_file.write_text('performance')
            
            return OptimizationResult(
                action_id='cpu_governor_performance',
                status=OptimizationStatus.SUCCESS,
                message="CPU governor set to performance",
                requires_reboot=False
            )
        except Exception as e:
            return OptimizationResult(
                action_id='cpu_governor_performance',
                status=OptimizationStatus.FAILED,
                message=f"Failed to set governor: {e}"
            )
    
    def _cpu_disable_mitigations(self) -> OptimizationResult:
        """Disable CPU mitigations for performance (security trade-off)."""
        try:
            # Check current cmdline
            cmdline = Path('/proc/cmdline').read_text()
            if 'mitigations=off' not in cmdline:
                # Add to kernel cmdline via grub
                grub_file = Path('/etc/default/grub')
                if grub_file.exists():
                    content = grub_file.read_text()
                    if 'mitigations=off' not in content:
                        content = content.replace(
                            'GRUB_CMDLINE_LINUX_DEFAULT="',
                            'GRUB_CMDLINE_LINUX_DEFAULT="mitigations=off '
                        )
                        grub_file.write_text(content)
                        subprocess.run(['grub-mkconfig', '-o', '/boot/grub/grub.cfg'], check=True)
                        return OptimizationResult(
                            action_id='cpu_disable_mitigations',
                            status=OptimizationStatus.SUCCESS,
                            message="CPU mitigations disabled (requires reboot)",
                            requires_reboot=True
                        )
            
            return OptimizationResult(
                action_id='cpu_disable_mitigations',
                status=OptimizationStatus.SKIPPED,
                message="Already disabled or grub not found"
            )
        except Exception as e:
            return OptimizationResult(
                action_id='cpu_disable_mitigations',
                status=OptimizationStatus.FAILED,
                message=f"Failed: {e}"
            )
    
    def _cpu_enable_pstate(self) -> OptimizationResult:
        """Enable intel_pstate or amd_pstate driver."""
        try:
            cpu = self.profile.cpu
            cmdline = Path('/proc/cmdline').read_text()
            
            if 'Intel' in cpu.model and 'intel_pstate=active' not in cmdline:
                grub_file = Path('/etc/default/grub')
                if grub_file.exists():
                    content = grub_file.read_text()
                    content = content.replace(
                        'GRUB_CMDLINE_LINUX_DEFAULT="',
                        'GRUB_CMDLINE_LINUX_DEFAULT="intel_pstate=active '
                    )
                    grub_file.write_text(content)
                    subprocess.run(['grub-mkconfig', '-o', '/boot/grub/grub.cfg'], check=True)
                    return OptimizationResult(
                        action_id='cpu_enable_pstate',
                        status=OptimizationStatus.SUCCESS,
                        message="intel_pstate=active enabled (requires reboot)",
                        requires_reboot=True
                    )
            elif 'AMD' in cpu.model and 'amd_pstate=active' not in cmdline:
                grub_file = Path('/etc/default/grub')
                if grub_file.exists():
                    content = grub_file.read_text()
                    content = content.replace(
                        'GRUB_CMDLINE_LINUX_DEFAULT="',
                        'GRUB_CMDLINE_LINUX_DEFAULT="amd_pstate=active '
                    )
                    grub_file.write_text(content)
                    subprocess.run(['grub-mkconfig', '-o', '/boot/grub/grub.cfg'], check=True)
                    return OptimizationResult(
                        action_id='cpu_enable_pstate',
                        status=OptimizationStatus.SUCCESS,
                        message="amd_pstate=active enabled (requires reboot)",
                        requires_reboot=True
                    )
            
            return OptimizationResult(
                action_id='cpu_enable_pstate',
                status=OptimizationStatus.SKIPPED,
                message="Already enabled or not applicable"
            )
        except Exception as e:
            return OptimizationResult(
                action_id='cpu_enable_pstate',
                status=OptimizationStatus.FAILED,
                message=f"Failed: {e}"
            )
    
    # ===== Memory Optimizations =====
    
    def _memory_optimize_low_ram(self) -> OptimizationResult:
        """Optimize for low RAM systems (≤16GB)."""
        try:
            actions_taken = []
            
            # 1. Reduce swappiness
            sysctl_file = Path('/etc/sysctl.d/99-cachy-gaming.conf')
            sysctl_content = ""
            if sysctl_file.exists():
                sysctl_content = sysctl_file.read_text()
            
            if 'vm.swappiness' not in sysctl_content:
                sysctl_content += "\n# Gaming optimizations\nvm.swappiness=10\n"
                sysctl_content += "vm.vfs_cache_pressure=50\n"
                sysctl_content += "vm.dirty_ratio=10\n"
                sysctl_content += "vm.dirty_background_ratio=5\n"
                sysctl_file.write_text(sysctl_content)
                subprocess.run(['sysctl', '--system'], check=True)
                actions_taken.append("sysctl tuned")
            
            # 2. Enable zram if not present
            if not Path('/dev/zram0').exists():
                try:
                    subprocess.run(['modprobe', 'zram'], check=True)
                    # Configure zram
                    zram_size = int(self.profile.memory.total_gb * 1024 * 0.5)  # 50% of RAM
                    Path('/sys/block/zram0/disksize').write_text(str(zram_size * 1024 * 1024))
                    subprocess.run(['mkswap', '/dev/zram0'], check=True)
                    subprocess.run(['swapon', '-p', '32767', '/dev/zram0'], check=True)
                    actions_taken.append("zram enabled")
                except Exception:
                    pass
            
            # 3. Install and enable earlyoom
            if shutil.which('earlyoom') is None:
                subprocess.run(['pacman', '-S', '--noconfirm', 'earlyoom'], capture_output=True)
            subprocess.run(['systemctl', 'enable', '--now', 'earlyoom'], capture_output=True)
            actions_taken.append("earlyoom enabled")
            
            return OptimizationResult(
                action_id='memory_optimize_low_ram',
                status=OptimizationStatus.SUCCESS,
                message=f"Low RAM optimizations applied: {', '.join(actions_taken)}",
                details={'actions': actions_taken}
            )
        except Exception as e:
            return OptimizationResult(
                action_id='memory_optimize_low_ram',
                status=OptimizationStatus.FAILED,
                message=f"Failed: {e}"
            )
    
    def _memory_ddr3_optimize(self) -> OptimizationResult:
        """DDR3-specific optimizations."""
        try:
            actions = []
            
            # Enable transparent hugepages for DDR3 (requires root)
            thp_file = Path('/sys/kernel/mm/transparent_hugepage/enabled')
            if thp_file.exists():
                result = self._run_privileged("write_thp_enabled")
                if not result.get("success"):
                    raise Exception(f"THP: {result.get('error')}")
                actions.append("THP=madvise")
            
            # Set hugepage allocation
            sysctl_file = Path('/etc/sysctl.d/99-cachy-gaming.conf')
            sysctl_content = sysctl_file.read_text() if sysctl_file.exists() else ""
            
            if 'vm.nr_hugepages' not in sysctl_content:
                # Calculate hugepages (1GB for 16GB DDR3)
                hugepages = 512  # 512 * 2MB = 1GB
                sysctl_lines = [
                    f"vm.nr_hugepages={hugepages}",
                    "vm.hugetlb_shm_group=0"
                ]
                result = self._run_privileged("write_sysctl", json.dumps(sysctl_lines))
                if not result.get("success"):
                    raise Exception(f"sysctl: {result.get('error')}")
                result = self._run_privileged("run_sysctl_system")
                if not result.get("success"):
                    raise Exception(f"sysctl --system: {result.get('error')}")
                actions.append("hugepages=512")
            
            return OptimizationResult(
                action_id='memory_ddr3_optimize',
                status=OptimizationStatus.SUCCESS,
                message=f"DDR3 optimizations applied: {', '.join(actions)}",
                requires_reboot=False
            )
        except Exception as e:
            return OptimizationResult(
                action_id='memory_ddr3_optimize',
                status=OptimizationStatus.FAILED,
                message=f"Failed: {e}"
            )
    
    def _memory_enable_hugepages(self) -> OptimizationResult:
        """Enable 1GB hugepages for gaming."""
        try:
            # Add to kernel cmdline
            cmdline = Path('/proc/cmdline').read_text()
            if 'default_hugepagesz=1G hugepagesz=1G hugepages=4' not in cmdline:
                grub_file = Path('/etc/default/grub')
                if grub_file.exists():
                    content = grub_file.read_text()
                    content = content.replace(
                        'GRUB_CMDLINE_LINUX_DEFAULT="',
                        'GRUB_CMDLINE_LINUX_DEFAULT="default_hugepagesz=1G hugepagesz=1G hugepages=4 '
                    )
                    grub_file.write_text(content)
                    subprocess.run(['grub-mkconfig', '-o', '/boot/grub/grub.cfg'], check=True)
                    return OptimizationResult(
                        action_id='memory_enable_hugepages',
                        status=OptimizationStatus.SUCCESS,
                        message="1GB hugepages enabled (requires reboot)",
                        requires_reboot=True
                    )
            
            return OptimizationResult(
                action_id='memory_enable_hugepages',
                status=OptimizationStatus.SKIPPED,
                message="Already configured"
            )
        except Exception as e:
            return OptimizationResult(
                action_id='memory_enable_hugepages',
                status=OptimizationStatus.FAILED,
                message=f"Failed: {e}"
            )
    
    def _memory_setup_zram(self) -> OptimizationResult:
        """Setup zram swap."""
        try:
            if Path('/dev/zram0').exists():
                return OptimizationResult(
                    action_id='memory_setup_zram',
                    status=OptimizationStatus.SKIPPED,
                    message="zram already configured"
                )
            
            # Install zram-generator
            subprocess.run(['pacman', '-S', '--noconfirm', 'zram-generator'], capture_output=True)
            
            config = """[zram0]
zram-size = ram / 2
compression-algorithm = zstd
swap-priority = 32767
"""
            Path('/etc/systemd/zram-generator.conf').write_text(config)
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            subprocess.run(['systemctl', 'start', 'systemd-zram-setup@zram0.service'], check=True)
            
            return OptimizationResult(
                action_id='memory_setup_zram',
                status=OptimizationStatus.SUCCESS,
                message="zram configured with zstd compression"
            )
        except Exception as e:
            return OptimizationResult(
                action_id='memory_setup_zram',
                status=OptimizationStatus.FAILED,
                message=f"Failed: {e}"
            )
    
    def _memory_earlyoom(self) -> OptimizationResult:
        """Install and configure earlyoom."""
        try:
            subprocess.run(['pacman', '-S', '--noconfirm', 'earlyoom'], capture_output=True)
            
            # Configure for gaming (prefer killing non-gaming processes)
            config = """EARLYOOM_ARGS="-r 30 -m 5 --avoid '(^|/)(gamemode|steam|heroic|lutris|bottles|wine|proton)' --prefer '(^|/)(chrome|firefox|electron|web)'"
"""
            Path('/etc/default/earlyoom').write_text(config)
            subprocess.run(['systemctl', 'enable', '--now', 'earlyoom'], check=True)
            
            return OptimizationResult(
                action_id='memory_earlyoom',
                status=OptimizationStatus.SUCCESS,
                message="earlyoom installed and configured for gaming"
            )
        except Exception as e:
            return OptimizationResult(
                action_id='memory_earlyoom',
                status=OptimizationStatus.FAILED,
                message=f"Failed: {e}"
            )
    
    # ===== GPU Optimizations =====
    
    def _gpu_amd_optimize(self) -> OptimizationResult:
        """AMD GPU optimizations."""
        try:
            actions = []
            
            # 1. RADV_PERFTEST (requires root for /etc/environment)
            radv_vars = [
                'RADV_PERFTEST=aco,nggc,ngg,gs_draw,rt',
                'AMD_DEBUG=w32ge,w32cs,nofmask',
                'RADV_TEX_ANISO=16',
                'MESA_GLSL_CACHE_DISABLE=false',
                'MESA_SHADER_CACHE_DISABLE=false',
            ]
            
            result = self._run_privileged("write_environment", json.dumps(radv_vars))
            if not result.get("success"):
                raise Exception(f"environment: {result.get('error')}")
            actions.extend([v.split('=')[0] for v in radv_vars])
            
            # 2. Power profile (may need root for hwmon)
            try:
                for hwmon in Path('/sys/class/drm').glob('card*/device/hwmon/hwmon*'):
                    pp_file = hwmon / 'power1_cap'
                    if pp_file.exists():
                        max_file = hwmon / 'power1_cap_max'
                        if max_file.exists():
                            max_val = max_file.read_text().strip()
                            result = self._run_privileged("set_power_limit", max_val, str(pp_file))
                            if result.get("success"):
                                actions.append("power_limit_removed")
            except Exception:
                pass
            
            # 3. AMDGPU PP feature mask (requires root for grub)
            cmdline = Path('/proc/cmdline').read_text()
            if 'amdgpu.ppfeaturemask=0xffffffff' not in cmdline:
                grub_file = Path('/etc/default/grub')
                if grub_file.exists():
                    result = self._run_privileged("update_grub_cmdline", "amdgpu.ppfeaturemask=0xffffffff")
                    if not result.get("success"):
                        raise Exception(f"grub: {result.get('error')}")
                    result = self._run_privileged("run_grub_mkconfig")
                    if not result.get("success"):
                        raise Exception(f"grub-mkconfig: {result.get('error')}")
                    actions.append("ppfeaturemask")
            
            return OptimizationResult(
                action_id='gpu_amd_optimize',
                status=OptimizationStatus.SUCCESS,
                message=f"AMD GPU optimizations: {', '.join(actions)}" + (" (reboot for ppfeaturemask)" if 'ppfeaturemask' in actions else ""),
                requires_reboot='ppfeaturemask' in actions
            )
        except Exception as e:
            return OptimizationResult(
                action_id='gpu_amd_optimize',
                status=OptimizationStatus.FAILED,
                message=f"Failed: {e}"
            )
    
    def _gpu_low_vram(self) -> OptimizationResult:
        """Optimize for low VRAM (≤2GB)."""
        try:
            env_file = Path('/etc/environment')
            env_content = env_file.read_text() if env_file.exists() else ""
            
            low_vram_vars = [
                'AMD_DEBUG=compress',
                'RADV_TEX_ANISO=4',
                'DXVK_HUD=devinfo,fps',
            ]
            
            for var in low_vram_vars:
                if var not in env_content:
                    env_content += f"\n{var}"
            
            env_file.write_text(env_content)
            
            return OptimizationResult(
                action_id='gpu_low_vram',
                status=OptimizationStatus.SUCCESS,
                message="Low VRAM optimizations applied (texture compression, reduced aniso)"
            )
        except Exception as e:
            return OptimizationResult(
                action_id='gpu_low_vram',
                status=OptimizationStatus.FAILED,
                message=f"Failed: {e}"
            )
    
    def _gpu_enable_amdgpu_ppfeature(self) -> OptimizationResult:
        """Enable amdgpu ppfeaturemask for manual OC."""
        return self._gpu_amd_optimize()  # Already covered above
    
    # ===== Kernel Optimizations =====
    
    def _kernel_swappiness(self) -> OptimizationResult:
        """Set swappiness to 10."""
        try:
            sysctl_file = Path('/etc/sysctl.d/99-cachy-gaming.conf')
            sysctl_content = sysctl_file.read_text() if sysctl_file.exists() else ""
            
            if 'vm.swappiness=10' not in sysctl_content:
                sysctl_content += "\nvm.swappiness=10\n"
                sysctl_file.write_text(sysctl_content)
                subprocess.run(['sysctl', '--system'], check=True)
            
            # Also set runtime
            Path('/proc/sys/vm/swappiness').write_text('10')
            
            return OptimizationResult(
                action_id='kernel_swappiness',
                status=OptimizationStatus.SUCCESS,
                message="Swappiness set to 10"
            )
        except Exception as e:
            return OptimizationResult(
                action_id='kernel_swappiness',
                status=OptimizationStatus.FAILED,
                message=f"Failed: {e}"
            )
    
    def _kernel_thp(self) -> OptimizationResult:
        """Set transparent hugepages to madvise."""
        try:
            thp_file = Path('/sys/kernel/mm/transparent_hugepage/enabled')
            if thp_file.exists():
                thp_file.write_text('madvise')
            
            # Also defrag
            defrag_file = Path('/sys/kernel/mm/transparent_hugepage/defrag')
            if defrag_file.exists():
                defrag_file.write_text('madvise')
            
            return OptimizationResult(
                action_id='kernel_thp',
                status=OptimizationStatus.SUCCESS,
                message="Transparent hugepages set to madvise"
            )
        except Exception as e:
            return OptimizationResult(
                action_id='kernel_thp',
                status=OptimizationStatus.FAILED,
                message=f"Failed: {e}"
            )
    
    def _kernel_cachyos(self) -> OptimizationResult:
        """Recommend CachyOS kernel."""
        return OptimizationResult(
            action_id='kernel_cachyos',
            status=OptimizationStatus.SKIPPED,
            message="Install linux-cachyos package: pacman -S linux-cachyos linux-cachyos-headers"
        )
    
    def _kernel_boore_scheduler(self) -> OptimizationResult:
        """Enable BORE scheduler if available."""
        try:
            # Check if BORE is available
            result = subprocess.run(['dmesg'], capture_output=True, text=True)
            if 'BORE' in result.stdout or 'sched_ext' in result.stdout:
                return OptimizationResult(
                    action_id='kernel_boore_scheduler',
                    status=OptimizationStatus.SUCCESS,
                    message="BORE/sched_ext detected in kernel"
                )
            
            return OptimizationResult(
                action_id='kernel_boore_scheduler',
                status=OptimizationStatus.SKIPPED,
                message="Requires CachyOS kernel with BORE scheduler"
            )
        except Exception:
            return OptimizationResult(
                action_id='kernel_boore_scheduler',
                status=OptimizationStatus.SKIPPED,
                message="Unknown kernel"
            )
    
    # ===== Storage Optimizations =====
    
    def _storage_nvme_optimize(self) -> OptimizationResult:
        """NVMe optimizations."""
        try:
            actions = []
            
            # Set I/O scheduler to none for NVMe
            for block in Path('/sys/block').glob('nvme*'):
                sched = block / 'queue' / 'scheduler'
                if sched.exists():
                    sched.write_text('none')
                    actions.append(f"{block.name}: scheduler=none")
                
                # Enable write cache
                wc = block / 'queue' / 'write_cache'
                if wc.exists():
                    wc.write_text('write back')
                    actions.append(f"{block.name}: write_cache=enabled")
            
            # Add to kernel cmdline for persistent
            cmdline = Path('/proc/cmdline').read_text()
            if 'nvme_core.default_ps_max_latency_us=0' not in cmdline:
                grub_file = Path('/etc/default/grub')
                if grub_file.exists():
                    content = grub_file.read_text()
                    content = content.replace(
                        'GRUB_CMDLINE_LINUX_DEFAULT="',
                        'GRUB_CMDLINE_LINUX_DEFAULT="nvme_core.default_ps_max_latency_us=0 '
                    )
                    grub_file.write_text(content)
                    subprocess.run(['grub-mkconfig', '-o', '/boot/grub/grub.cfg'], check=True)
                    actions.append("kernel_cmdline (reboot)")
            
            return OptimizationResult(
                action_id='storage_nvme_optimize',
                status=OptimizationStatus.SUCCESS,
                message=f"NVMe optimizations: {', '.join(actions)}",
                requires_reboot='kernel_cmdline (reboot)' in actions
            )
        except Exception as e:
            return OptimizationResult(
                action_id='storage_nvme_optimize',
                status=OptimizationStatus.FAILED,
                message=f"Failed: {e}"
            )
    
    def _storage_scheduler(self) -> OptimizationResult:
        """Set optimal I/O scheduler."""
        try:
            actions = []
            
            for block in Path('/sys/block').glob('*'):
                if block.name.startswith(('loop', 'ram', 'zram')):
                    continue
                
                sched = block / 'queue' / 'scheduler'
                if sched.exists():
                    current = sched.read_text()
                    if 'nvme' in block.name:
                        target = 'none'
                    elif 'ssd' in block.name.lower() or block.name.startswith('sd'):
                        # Check if rotational
                        rota = block / 'queue' / 'rotational'
                        if rota.exists() and rota.read_text().strip() == '0':
                            target = 'none'
                        else:
                            target = 'bfq'
                    else:
                        target = 'bfq'
                    
                    if f'[{target}]' not in current:
                        sched.write_text(target)
                        actions.append(f"{block.name}: {target}")
            
            return OptimizationResult(
                action_id='storage_scheduler',
                status=OptimizationStatus.SUCCESS,
                message=f"I/O schedulers set: {', '.join(actions) if actions else 'already optimal'}"
            )
        except Exception as e:
            return OptimizationResult(
                action_id='storage_scheduler',
                status=OptimizationStatus.FAILED,
                message=f"Failed: {e}"
            )
    
    # ===== Gaming Optimizations =====
    
    def _gaming_mode_enable(self) -> OptimizationResult:
        """Enable gaming mode optimizations."""
        try:
            actions = []
            
            # Install gamemode
            subprocess.run(['pacman', '-S', '--noconfirm', 'gamemode', 'lib32-gamemode'], capture_output=True)
            subprocess.run(['systemctl', '--user', 'enable', '--now', 'gamemoded'], capture_output=True)
            actions.append("gamemode installed")
            
            # Systemd gaming slice
            gaming_slice = """[Slice]
CPUWeight=1000
IOWeight=1000
MemoryHigh=85%
"""
            Path('/etc/systemd/system/user@.service.d/gaming.conf').parent.mkdir(parents=True, exist_ok=True)
            Path('/etc/systemd/system/user@.service.d/gaming.conf').write_text(gaming_slice)
            actions.append("gaming slice configured")
            
            return OptimizationResult(
                action_id='gaming_mode_enable',
                status=OptimizationStatus.SUCCESS,
                message=f"Gaming mode: {', '.join(actions)}"
            )
        except Exception as e:
            return OptimizationResult(
                action_id='gaming_mode_enable',
                status=OptimizationStatus.FAILED,
                message=f"Failed: {e}"
            )
    
    def _gaming_feral_gamemode(self) -> OptimizationResult:
        """Configure Feral GameMode."""
        return self._gaming_mode_enable()
    
    def _gaming_mangohud(self) -> OptimizationResult:
        """Install MangoHud."""
        try:
            subprocess.run(['pacman', '-S', '--noconfirm', 'mangohud', 'lib32-mangohud'], capture_output=True)
            
            # Configure
            config_dir = Path.home() / '.config' / 'MangoHud'
            config_dir.mkdir(parents=True, exist_ok=True)
            config = """cpu_temp
gpu_temp
vram
ram
fps
frame_timing=1
gpu_color=00FF88
cpu_color=0099CC
background_alpha=0.5
font_size=24
position=top-left
"""
            (config_dir / 'MangoHud.conf').write_text(config)
            
            return OptimizationResult(
                action_id='gaming_mangohud',
                status=OptimizationStatus.SUCCESS,
                message="MangoHud installed and configured"
            )
        except Exception as e:
            return OptimizationResult(
                action_id='gaming_mangohud',
                status=OptimizationStatus.FAILED,
                message=f"Failed: {e}"
            )
    
    def _gaming_vkbasalt(self) -> OptimizationResult:
        """Install vkBasalt for CAS sharpening."""
        try:
            subprocess.run(['pacman', '-S', '--noconfirm', 'vkbasalt', 'lib32-vkbasalt'], capture_output=True)
            
            # Configure CAS sharpening
            config_dir = Path.home() / '.config' / 'vkBasalt'
            config_dir.mkdir(parents=True, exist_ok=True)
            config = """enable = true
cas = true
cas_sharpen = 0.3
fxaa = false
"""
            (config_dir / 'vkBasalt.conf').write_text(config)
            
            return OptimizationResult(
                action_id='gaming_vkbasalt',
                status=OptimizationStatus.SUCCESS,
                message="vkBasalt installed with CAS sharpening"
            )
        except Exception as e:
            return OptimizationResult(
                action_id='gaming_vkbasalt',
                status=OptimizationStatus.FAILED,
                message=f"Failed: {e}"
            )
    
    # ===== Wine/Proton Optimizations =====
    
    def _wine_esync_fsync(self) -> OptimizationResult:
        """Enable esync/fsync for Wine."""
        try:
            env_file = Path('/etc/environment')
            env_content = env_file.read_text() if env_file.exists() else ""
            
            wine_vars = [
                'WINEESYNC=1',
                'WINEFSYNC=1',
                'WINEFSYNC_FUTEX2=1',
            ]
            
            for var in wine_vars:
                if var not in env_content:
                    env_content += f"\n{var}"
            
            env_file.write_text(env_content)
            
            return OptimizationResult(
                action_id='wine_esync_fsync',
                status=OptimizationStatus.SUCCESS,
                message="WINEESYNC/WINEFSYNC enabled (requires re-login)"
            )
        except Exception as e:
            return OptimizationResult(
                action_id='wine_esync_fsync',
                status=OptimizationStatus.FAILED,
                message=f"Failed: {e}"
            )
    
    def _wine_dxvk_cache(self) -> OptimizationResult:
        """Enable DXVK cache."""
        try:
            env_file = Path('/etc/environment')
            env_content = env_file.read_text() if env_file.exists() else ""
            
            dxvk_vars = [
                'DXVK_STATE_CACHE=1',
                'DXVK_STATE_CACHE_PATH=$HOME/.cache/dxvk',
                'DXVK_CONFIG_FILE=$HOME/.config/dxvk.conf',
            ]
            
            for var in dxvk_vars:
                if var not in env_content:
                    env_content += f"\n{var}"
            
            env_file.write_text(env_content)
            
            # Create dxvk config
            config_dir = Path.home() / '.config'
            config_dir.mkdir(exist_ok=True)
            dxvk_config = """[dxvk]
cache = true
hud = devinfo,fps,gpuload
compiler = 1
async = true
"""
            (config_dir / 'dxvk.conf').write_text(dxvk_config)
            
            return OptimizationResult(
                action_id='wine_dxvk_cache',
                status=OptimizationStatus.SUCCESS,
                message="DXVK cache and async compilation enabled"
            )
        except Exception as e:
            return OptimizationResult(
                action_id='wine_dxvk_cache',
                status=OptimizationStatus.FAILED,
                message=f"Failed: {e}"
            )
    
    def _wine_gstreamer(self) -> OptimizationResult:
        """Install gstreamer for Wine media support."""
        try:
            subprocess.run(['pacman', '-S', '--noconfirm', 
                          'gst-plugins-base', 'gst-plugins-good', 'gst-plugins-bad', 'gst-plugins-ugly',
                          'lib32-gst-plugins-base', 'lib32-gst-plugins-good', 'lib32-gst-plugins-bad', 'lib32-gst-plugins-ugly',
                          'gst-libav', 'lib32-gst-libav'], capture_output=True)
            
            return OptimizationResult(
                action_id='wine_gstreamer',
                status=OptimizationStatus.SUCCESS,
                message="GStreamer plugins installed for Wine media support"
            )
        except Exception as e:
            return OptimizationResult(
                action_id='wine_gstreamer',
                status=OptimizationStatus.FAILED,
                message=f"Failed: {e}"
            )


def get_optimizer() -> OptimizationEngine:
    return OptimizationEngine()