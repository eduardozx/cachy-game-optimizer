"""
CachyOS Game Optimizer - Intelligent Error Analyzer & Auto-Fixer
Analyzes game launch logs and applies targeted winetricks fixes.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from enum import Enum
from pathlib import Path
import subprocess


class FixPriority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ErrorPattern:
    """Defines a log pattern and its corresponding fix."""
    name: str
    patterns: List[str]  # Regex patterns to match in logs
    winetricks: List[str]  # winetricks commands to run
    priority: FixPriority = FixPriority.MEDIUM
    description: str = ""
    requires_restart: bool = False


@dataclass
class FixResult:
    """Result of applying a fix."""
    pattern_name: str
    winetricks_applied: List[str]
    success: bool
    message: str


# ============================================================
# ERROR PATTERN DATABASE
# Maps common Wine/Proton log patterns to winetricks fixes
# ============================================================

ERROR_PATTERNS: List[ErrorPattern] = [
    # --- Visual C++ Runtime ---
    ErrorPattern(
        name="missing_vcrun2019",
        patterns=[
            r"msvcp140\.dll",
            r"vcruntime140\.dll",
            r"MSVCP140",
            r"VCRUNTIME140",
            r"ucrtbase\.dll",
        ],
        winetricks=["vcrun2019", "vcrun2022"],
        priority=FixPriority.HIGH,
        description="Missing Visual C++ 2019/2022 runtime",
    ),
    ErrorPattern(
        name="missing_vcrun2015",
        patterns=[
            r"msvcp120\.dll",
            r"msvcr120\.dll",
        ],
        winetricks=["vcrun2015"],
        priority=FixPriority.HIGH,
        description="Missing Visual C++ 2015 runtime",
    ),
    ErrorPattern(
        name="missing_vcrun2013",
        patterns=[
            r"msvcp110\.dll",
            r"msvcr110\.dll",
        ],
        winetricks=["vcrun2013"],
        priority=FixPriority.MEDIUM,
        description="Missing Visual C++ 2013 runtime",
    ),

    # --- DirectX / DXVK / VKD3D ---
    ErrorPattern(
        name="dxvk_missing",
        patterns=[
            r"dxgi\.dll",
            r"d3d11\.dll",
            r"d3d10core\.dll",
            r"DXGI",
            r"D3D11",
            r"vkd3d",
            r"VKD3D",
        ],
        winetricks=["dxvk", "vkd3d"],
        priority=FixPriority.HIGH,
        description="DirectX/Vulkan translation layer missing",
    ),
    ErrorPattern(
        name="d3dx9_missing",
        patterns=[
            r"d3dx9_\d+\.dll",
            r"D3DX9",
        ],
        winetricks=["d3dx9"],
        priority=FixPriority.MEDIUM,
        description="DirectX 9 extensions missing",
    ),
    ErrorPattern(
        name="d3dx10_11_missing",
        patterns=[
            r"d3dx10_\d+\.dll",
            r"d3dx11_\d+\.dll",
            r"D3DX10",
            r"D3DX11",
        ],
        winetricks=["d3dx10", "d3dx11"],
        priority=FixPriority.MEDIUM,
        description="DirectX 10/11 extensions missing",
    ),
    ErrorPattern(
        name="xinput_missing",
        patterns=[
            r"xinput1_\d+\.dll",
            r"XInput",
        ],
        winetricks=["xinput"],
        priority=FixPriority.LOW,
        description="XInput (controller) support missing",
    ),
    ErrorPattern(
        name="xact_missing",
        patterns=[
            r"xactengine\d+_\d+\.dll",
            r"XACT",
        ],
        winetricks=["xact"],
        priority=FixPriority.LOW,
        description="XACT audio engine missing",
    ),

    # --- .NET Framework ---
    ErrorPattern(
        name="dotnet_missing",
        patterns=[
            r"mscoree\.dll",
            r"clr\.dll",
            r"System\.",
            r"mscorlib",
            r"PresentationFramework",
            r"WindowsBase",
        ],
        winetricks=["dotnet48", "dotnet40"],
        priority=FixPriority.MEDIUM,
        description=".NET Framework missing",
    ),

    # --- Windows Components ---
    ErrorPattern(
        name="wbemprox_missing",
        patterns=[
            r"wbemprox",
            r"wbem_services",
            r"WMI",
            r"enum_class_object",
        ],
        winetricks=["wbemprox"],
        priority=FixPriority.HIGH,
        description="WMI/WBEM proxy missing",
    ),
    ErrorPattern(
        name="ntdll_missing",
        patterns=[
            r"ntdll\.dll",
            r"NtQuerySystemInformation",
            r"NtCreateFile",
        ],
        winetricks=["ntdll"],
        priority=FixPriority.HIGH,
        description="ntdll.dll issues",
    ),
    ErrorPattern(
        name="msvcrt_missing",
        patterns=[
            r"msvcrt\.dll",
            r"MSVCRT",
        ],
        winetricks=["msvcrt"],
        priority=FixPriority.MEDIUM,
        description="MSVCRT runtime missing",
    ),

    # --- Audio ---
    ErrorPattern(
        name="xaudio2_missing",
        patterns=[
            r"xaudio2_\d+\.dll",
            r"XAudio2",
        ],
        winetricks=["xaudio2"],
        priority=FixPriority.LOW,
        description="XAudio2 missing",
    ),
    ErrorPattern(
        name="dsound_missing",
        patterns=[
            r"dsound\.dll",
            r"DirectSound",
        ],
        winetricks=["dsound"],
        priority=FixPriority.LOW,
        description="DirectSound missing",
    ),

    # --- Media Foundation ---
    ErrorPattern(
        name="mf_missing",
        patterns=[
            r"mfplat\.dll",
            r"mfreadwrite\.dll",
            r"MediaFoundation",
            r"MFCreate",
        ],
        winetricks=["mf", "mfplat"],
        priority=FixPriority.LOW,
        description="Media Foundation missing",
    ),

    # --- Crash / Page Fault ---
    ErrorPattern(
        name="page_fault_null",
        patterns=[
            r"Unhandled page fault on write access to 00000000",
            r"page fault on read access to 00000000",
            r"NULL pointer",
        ],
        winetricks=["vcrun2019", "vcrun2022", "dxvk"],
        priority=FixPriority.HIGH,
        description="Null pointer dereference - likely missing runtime or DXVK",
    ),
    ErrorPattern(
        name="stack_overflow",
        patterns=[
            r"stack overflow",
            r"Stack overflow",
            r"guard page",
        ],
        winetricks=[],
        priority=FixPriority.HIGH,
        description="Stack overflow - may need PROTON_NO_ESYNC=1",
    ),

    # --- WineDBG / Debugger ---
    ErrorPattern(
        name="debugger_invoked",
        patterns=[
            r"starting debugger",
            r"winedbg",
            r"DbgHelp",
            r"elf_search_auxv",
        ],
        winetricks=[],
        priority=FixPriority.HIGH,
        description="Crash triggered debugger - check above errors",
    ),

    # --- DLL Hell ---
    ErrorPattern(
        name="dll_not_found",
        patterns=[
            r"not found.*\.dll",
            r"failed to load.*\.dll",
            r"LoadLibrary.*failed",
        ],
        winetricks=[],
        priority=FixPriority.MEDIUM,
        description="Generic DLL loading failure - check specific DLL above",
    ),

    # --- Graphics Driver / Vulkan ---
    ErrorPattern(
        name="vulkan_missing",
        patterns=[
            r"vulkan.*not found",
            r"VK_ERROR_INCOMPATIBLE_DRIVER",
            r"vkCreateInstance",
            r"amdgpu",
            r"radv",
        ],
        winetricks=[],
        priority=FixPriority.HIGH,
        description="Vulkan driver issue - update GPU drivers",
    ),

    # --- Sync / ESYNC / FSYNC ---
    ErrorPattern(
        name="esync_fsync_issue",
        patterns=[
            r"esync",
            r"fsync",
            r"eventfd",
            r"futex",
        ],
        winetricks=[],
        priority=FixPriority.MEDIUM,
        description="ESYNC/FSYNC issue - try PROTON_NO_ESYNC=1 PROTON_NO_FSYNC=1",
    ),
]


# ============================================================
# ANALYZER CLASS
# ============================================================

class GameErrorAnalyzer:
    """Analyzes game logs and recommends/applies fixes."""

    def __init__(self, prefix_path: str):
        self.prefix_path = Path(prefix_path)
        self.detected_issues: List[ErrorPattern] = []
        self.applied_fixes: List[FixResult] = []

    def analyze_logs(self, log_lines: List[str]) -> List[ErrorPattern]:
        """Analyze log lines and return matched error patterns."""
        log_text = "\n".join(log_lines)
        matched = []

        for pattern in ERROR_PATTERNS:
            for regex in pattern.patterns:
                if re.search(regex, log_text, re.IGNORECASE):
                    matched.append(pattern)
                    break  # One match per pattern is enough

        # Sort by priority
        priority_order = {FixPriority.HIGH: 0, FixPriority.MEDIUM: 1, FixPriority.LOW: 2}
        matched.sort(key=lambda p: priority_order[p.priority])

        self.detected_issues = matched
        return matched

    def get_recommended_fixes(self) -> List[ErrorPattern]:
        """Get unique winetricks fixes from detected issues."""
        seen = set()
        unique = []
        for issue in self.detected_issues:
            for wt in issue.winetricks:
                if wt not in seen:
                    seen.add(wt)
                    # Find the pattern that has this winetrick as primary
                    for p in ERROR_PATTERNS:
                        if wt in p.winetricks:
                            unique.append(p)
                            break
        return unique

    def apply_fixes(self, prefix_path: Optional[str] = None, dry_run: bool = False) -> List[FixResult]:
        """Apply all recommended winetricks fixes to the prefix."""
        prefix = Path(prefix_path) if prefix_path else self.prefix_path
        results = []

        # Get unique winetricks to apply
        winetricks_set: Set[str] = set()
        for issue in self.detected_issues:
            for wt in issue.winetricks:
                winetricks_set.add(wt)

        if not winetricks_set:
            return [FixResult("none", [], True, "No fixes needed")]

        winetricks_list = sorted(winetricks_set)

        for wt in winetricks_list:
            result = self._run_winetricks(prefix, [wt], dry_run)
            results.append(result)
            self.applied_fixes.append(result)

        return results

    def _run_winetricks(self, prefix: Path, winetricks_list: List[str], dry_run: bool) -> FixResult:
        """Run winetricks for a specific prefix."""
        env = os.environ.copy()
        env["WINEPREFIX"] = str(prefix)
        env["WINETRICKS_OPT_SHARE"] = "1"  # Avoid GUI prompts

        cmd = ["winetricks", "-q"] + winetricks_list  # -q = quiet/unattended

        if dry_run:
            return FixResult(
                pattern_name="dry_run",
                winetricks_applied=winetricks_list,
                success=True,
                message=f"DRY RUN: Would run: {' '.join(cmd)} with WINEPREFIX={prefix}"
            )

        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300,  # 5 min timeout per winetricks
            )

            if result.returncode == 0:
                return FixResult(
                    pattern_name="winetricks",
                    winetricks_applied=winetricks_list,
                    success=True,
                    message=f"Applied: {', '.join(winetricks_list)}"
                )
            else:
                return FixResult(
                    pattern_name="winetricks",
                    winetricks_applied=winetricks_list,
                    success=False,
                    message=f"Failed: {result.stderr[-500:] if result.stderr else 'Unknown error'}"
                )
        except subprocess.TimeoutExpired:
            return FixResult(
                pattern_name="winetricks",
                winetricks_applied=winetricks_list,
                success=False,
                message="Timeout (5 min) - winetricks may be waiting for input"
            )
        except Exception as e:
            return FixResult(
                pattern_name="winetricks",
                winetricks_applied=winetricks_list,
                success=False,
                message=f"Exception: {e}"
            )

    def generate_report(self) -> str:
        """Generate human-readable report of analysis and fixes."""
        lines = ["=" * 60]
        lines.append("GAME ERROR ANALYSIS REPORT")
        lines.append("=" * 60)

        if not self.detected_issues:
            lines.append("✅ No known error patterns detected in logs.")
            return "\n".join(lines)

        lines.append(f"\n🔍 Detected {len(self.detected_issues)} issue(s):\n")

        for issue in self.detected_issues:
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[issue.priority.value]
            lines.append(f"{priority_icon} {issue.name}")
            lines.append(f"   Description: {issue.description}")
            lines.append(f"   Fixes: {', '.join(issue.winetricks) if issue.winetricks else 'Manual intervention needed'}")
            lines.append("")

        if self.applied_fixes:
            lines.append("\n🔧 Fixes Applied:\n")
            for fix in self.applied_fixes:
                status = "✅" if fix.success else "❌"
                lines.append(f"{status} {', '.join(fix.winetricks_applied)}: {fix.message}")

        return "\n".join(lines)


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def analyze_game_logs(log_lines: List[str], prefix_path: str) -> GameErrorAnalyzer:
    """Quick analysis of game logs."""
    analyzer = GameErrorAnalyzer(prefix_path)
    analyzer.analyze_logs(log_lines)
    return analyzer


def auto_fix_game_errors(log_lines: List[str], prefix_path: str, dry_run: bool = False) -> List[FixResult]:
    """Analyze and auto-fix game errors in one call."""
    analyzer = GameErrorAnalyzer(prefix_path)
    analyzer.analyze_logs(log_lines)
    return analyzer.apply_fixes(prefix_path, dry_run)


import os