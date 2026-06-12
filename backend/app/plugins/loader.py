"""插件加载器 — 从文件系统加载插件"""

import importlib
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type

from .base import Plugin
from .manager import get_plugin_manager

logger = logging.getLogger(__name__)


def _get_plugin_dir() -> Path:
    """K2: 获取插件目录 — 支持 PyInstaller frozen app"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包模式 — 插件打包在 app/plugins/plugins/ 下
        base = Path(sys._MEIPASS)
        return base / "app" / "plugins" / "plugins"
    # 开发模式 — 当前文件所在目录下的 plugins 子目录
    return Path(__file__).parent / "plugins"


class PluginLoader:
    """插件加载器

    支持从以下位置加载插件：
    1. 插件目录（plugins/）
    2. Python包（pip安装的插件）
    3. 单文件插件
    """

    def __init__(self, plugin_dir: Optional[Path] = None):
        """初始化插件加载器

        Args:
            plugin_dir: 插件目录路径（默认为 backend/app/plugins/plugins/）
        """
        self._plugin_dir = plugin_dir or _get_plugin_dir()
        self._loaded_paths: Dict[str, Path] = {}  # plugin_name -> file_path

    @property
    def plugin_dir(self) -> Path:
        """插件目录"""
        return self._plugin_dir

    def discover_plugins(self) -> List[Path]:
        """发现插件目录中的所有插件文件

        Returns:
            插件文件路径列表
        """
        if not self._plugin_dir.exists():
            logger.warning(f"Plugin directory not found: {self._plugin_dir}")
            return []

        plugins = []

        # 扫描目录中的Python文件
        for item in self._plugin_dir.iterdir():
            if item.is_file() and item.suffix == ".py" and not item.name.startswith("_"):
                plugins.append(item)
            elif item.is_dir() and not item.name.startswith("_"):
                # 包形式的插件（有__init__.py）
                init_file = item / "__init__.py"
                if init_file.exists():
                    plugins.append(init_file)

        return plugins

    def load_plugin_from_file(self, file_path: Path) -> List[Type[Plugin]]:
        """从文件加载插件类

        Args:
            file_path: 插件文件路径

        Returns:
            发现的Plugin类列表
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Plugin file not found: {file_path}")

        # 生成模块名
        module_name = f"fugue_plugin_{file_path.stem}"

        try:
            # 动态导入模块
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load module spec from {file_path}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # 查找所有Plugin子类
            plugin_classes = []
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, Plugin)
                    and attr is not Plugin
                ):
                    plugin_classes.append(attr)

            return plugin_classes

        except Exception as e:
            logger.error(f"Failed to load plugin from {file_path}: {e}")
            raise

    def load_plugins_from_directory(self) -> List[Type[Plugin]]:
        """从插件目录加载所有插件

        Returns:
            所有发现的Plugin类列表
        """
        plugin_files = self.discover_plugins()
        all_plugin_classes = []

        for file_path in plugin_files:
            try:
                plugin_classes = self.load_plugin_from_file(file_path)
                all_plugin_classes.extend(plugin_classes)
                logger.info(
                    f"Loaded {len(plugin_classes)} plugin(s) from {file_path.name}"
                )
            except Exception as e:
                logger.error(f"Failed to load plugin from {file_path.name}: {e}")

        return all_plugin_classes

    async def load_and_register_plugins(self):
        """加载并注册所有插件到管理器"""
        manager = get_plugin_manager()

        # 发现插件类
        plugin_classes = self.load_plugins_from_directory()

        # 注册插件类
        for plugin_class in plugin_classes:
            try:
                manager.register_plugin_class(plugin_class)
                self._loaded_paths[plugin_class.name] = self._find_plugin_path(plugin_class)
            except ValueError as e:
                logger.warning(f"Failed to register plugin '{plugin_class.name}': {e}")

        # 加载所有已注册的插件
        await manager.load_all_plugins()

        logger.info(f"Plugin loader: {len(plugin_classes)} plugins discovered and loaded")

    def _find_plugin_path(self, plugin_class: Type[Plugin]) -> Optional[Path]:
        """查找插件类的源文件路径"""
        try:
            module = sys.modules.get(plugin_class.__module__)
            if module and hasattr(module, "__file__"):
                return Path(module.__file__)
        except Exception:
            pass
        return None

    async def reload_plugin(self, plugin_name: str):
        """重新加载插件（开发模式）

        Args:
            plugin_name: 插件名称
        """
        manager = get_plugin_manager()
        plugin = manager.get_plugin(plugin_name)

        if not plugin:
            raise ValueError(f"Plugin '{plugin_name}' not loaded")

        # 找到插件文件路径
        file_path = self._loaded_paths.get(plugin_name)
        if not file_path:
            raise ValueError(f"Cannot find source file for plugin '{plugin_name}'")

        # 卸载旧插件
        await manager.unload_plugin(plugin_name)

        # 重新加载
        plugin_classes = self.load_plugin_from_file(file_path)
        for plugin_class in plugin_classes:
            if plugin_class.name == plugin_name:
                manager.register_plugin_class(plugin_class)
                await manager.load_plugin(plugin_name)
                logger.info(f"Reloaded plugin '{plugin_name}'")
                return

        raise ValueError(f"Plugin class '{plugin_name}' not found in {file_path}")


# 全局插件加载器实例
_plugin_loader: Optional[PluginLoader] = None


def get_plugin_loader() -> PluginLoader:
    """获取全局插件加载器实例"""
    global _plugin_loader
    if _plugin_loader is None:
        _plugin_loader = PluginLoader()
    return _plugin_loader


async def initialize_plugin_system():
    """初始化插件系统（发现并加载所有插件）"""
    loader = get_plugin_loader()
    await loader.load_and_register_plugins()
