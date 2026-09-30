"""
CachyOS Game Optimizer - Futuristic Gaming Performance Suite
Maximize gaming performance on CachyOS with hardware-specific optimizations.
"""

__version__ = "1.0.0"
__author__ = "CachyOS Game Optimizer"
__license__ = "MIT"

from .hardware import get_detector, HardwareDetector, SystemProfile
from .optimizer import get_optimizer, OptimizationEngine, OptimizationResult
from .games import get_game_manager, GameManager, Game, GameSource, GameConfig
from .main import CachyGameOptimizerApp, main

__all__ = [
    "get_detector",
    "HardwareDetector",
    "SystemProfile",
    "get_optimizer",
    "OptimizationEngine",
    "OptimizationResult",
    "get_game_manager",
    "GameManager",
    "Game",
    "GameSource",
    "GameConfig",
    "CachyGameOptimizerApp",
    "main",
]