"""
服務配置模塊

定義服務配置的結構和驗證邏輯，支持從配置文件動態註冊服務。
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ServiceScope(Enum):
    """服務作用域"""

    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


class ServiceType(Enum):
    """服務類型"""

    CLASS = "class"
    FACTORY = "factory"
    INSTANCE = "instance"
    INTERFACE = "interface"


@dataclass
class ServiceDependency:
    """服務依賴配置"""

    name: str
    type: str
    optional: bool = False
    default_value: Any = None


@dataclass
class ServiceConfiguration:
    """單個服務配置"""

    name: str
    implementation: str
    scope: ServiceScope = ServiceScope.SINGLETON
    service_type: ServiceType = ServiceType.CLASS
    dependencies: List[ServiceDependency] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    interfaces: List[str] = field(default_factory=list)
    enabled: bool = True
    priority: int = 0
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        """後處理，確保枚舉類型正確"""
        if isinstance(self.scope, str):
            self.scope = ServiceScope(self.scope)
        if isinstance(self.service_type, str):
            self.service_type = ServiceType(self.service_type)


@dataclass
class ContainerConfiguration:
    """容器配置"""

    services: List[ServiceConfiguration] = field(default_factory=list)
    auto_registration: bool = True
    circular_dependency_detection: bool = True
    lifecycle_management: bool = True
    logging_level: str = "INFO"
    validation_enabled: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContainerConfiguration":
        """從字典創建配置"""
        services = []
        for service_data in data.get("services", []):
            # 處理依賴
            dependencies = []
            for dep_data in service_data.get("dependencies", []):
                if isinstance(dep_data, str):
                    dependencies.append(ServiceDependency(name=dep_data, type=dep_data))
                else:
                    dependencies.append(ServiceDependency(**dep_data))

            service_config = ServiceConfiguration(
                name=service_data["name"],
                implementation=service_data["implementation"],
                scope=ServiceScope(service_data.get("scope", "singleton")),
                service_type=ServiceType(service_data.get("service_type", "class")),
                dependencies=dependencies,
                parameters=service_data.get("parameters", {}),
                interfaces=service_data.get("interfaces", []),
                enabled=service_data.get("enabled", True),
                priority=service_data.get("priority", 0),
                tags=service_data.get("tags", []),
            )
            services.append(service_config)

        return cls(
            services=services,
            auto_registration=data.get("auto_registration", True),
            circular_dependency_detection=data.get(
                "circular_dependency_detection", True
            ),
            lifecycle_management=data.get("lifecycle_management", True),
            logging_level=data.get("logging_level", "INFO"),
            validation_enabled=data.get("validation_enabled", True),
        )

    @classmethod
    def from_json_file(cls, file_path: Union[str, Path]) -> "ContainerConfiguration":
        """從JSON文件加載配置"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading configuration: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "services": [
                {
                    "name": service.name,
                    "implementation": service.implementation,
                    "scope": service.scope.value,
                    "service_type": service.service_type.value,
                    "dependencies": [
                        {
                            "name": dep.name,
                            "type": dep.type,
                            "optional": dep.optional,
                            "default_value": dep.default_value,
                        }
                        for dep in service.dependencies
                    ],
                    "parameters": service.parameters,
                    "interfaces": service.interfaces,
                    "enabled": service.enabled,
                    "priority": service.priority,
                    "tags": service.tags,
                }
                for service in self.services
                if service.enabled
            ],
            "auto_registration": self.auto_registration,
            "circular_dependency_detection": self.circular_dependency_detection,
            "lifecycle_management": self.lifecycle_management,
            "logging_level": self.logging_level,
            "validation_enabled": self.validation_enabled,
        }

    def save_to_json_file(self, file_path: Union[str, Path]):
        """保存到JSON文件"""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    def get_services_by_tag(self, tag: str) -> List[ServiceConfiguration]:
        """根據標籤獲取服務"""
        return [
            service
            for service in self.services
            if tag in service.tags and service.enabled
        ]

    def get_service_by_name(self, name: str) -> Optional[ServiceConfiguration]:
        """根據名稱獲取服務"""
        for service in self.services:
            if service.name == name and service.enabled:
                return service
        return None

    def validate(self) -> List[str]:
        """驗證配置"""
        errors = []

        # 檢查服務名稱唯一性
        names = [service.name for service in self.services if service.enabled]
        duplicates = set([name for name in names if names.count(name) > 1])
        if duplicates:
            errors.append(f"Duplicate service names: {', '.join(duplicates)}")

        # 檢查依賴是否存在
        service_names = set(names)
        # 添加常見的外部依賴（不需要在配置中定義）
        external_dependencies = {
            "root",  # tkinter.Tk 實例
            "ui",  # 可能是別名
            "state_manager",  # 可能是別名
            "file_service",  # 可能是別名
            "translation_service",  # 可能是別名
            "highlighting_service",  # 可能是別名
            "project_service",  # 可能是別名
        }

        # 建立服務名稱到類型的映射
        service_type_mapping = {}
        for service in self.services:
            if service.enabled:
                # 使用類名作為可能的依賴名稱
                class_name = service.implementation.split(".")[-1]
                service_type_mapping[class_name] = service.name
                service_type_mapping[service.name.lower()] = service.name

        for service in self.services:
            if not service.enabled:
                continue

            for dependency in service.dependencies:
                dep_name = dependency.name

                # 跳過可選依賴
                if dependency.optional:
                    continue

                # 跳過外部依賴
                if dep_name in external_dependencies:
                    continue

                # 檢查直接名稱匹配
                if dep_name in service_names:
                    continue

                # 檢查類型映射
                if dep_name in service_type_mapping:
                    continue

                # 檢查是否是類型名稱
                dep_type = (
                    dependency.type.split(".")[-1]
                    if "." in dependency.type
                    else dependency.type
                )
                if dep_type in [
                    s.implementation.split(".")[-1] for s in self.services if s.enabled
                ]:
                    continue

                # 如果都不匹配，則記錄錯誤
                errors.append(
                    f"Service '{service.name}' has unresolved dependency: '{dependency.name}' (type: {dependency.type})"
                )

        # 檢查循環依賴
        if self.circular_dependency_detection:
            circular_deps = self._detect_circular_dependencies()
            if circular_deps:
                errors.extend(
                    [
                        f"Circular dependency detected: {' -> '.join(cycle)}"
                        for cycle in circular_deps
                    ]
                )

        return errors

    def _detect_circular_dependencies(self) -> List[List[str]]:
        """檢測循環依賴"""
        # 構建依賴圖
        graph = {}
        for service in self.services:
            if service.enabled:
                graph[service.name] = [
                    dep.name for dep in service.dependencies if not dep.optional
                ]

        # 使用DFS檢測循環
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: List[str]):
            if node in rec_stack:
                # 找到循環
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])

            rec_stack.remove(node)

        for service_name in graph:
            if service_name not in visited:
                dfs(service_name, [])

        return cycles


class ServiceConfigurationManager:
    """服務配置管理器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._configurations: Dict[str, ContainerConfiguration] = {}
        self._active_config: Optional[str] = None

    def load_configuration(
        self, name: str, file_path: Union[str, Path]
    ) -> ContainerConfiguration:
        """加載配置"""
        try:
            config = ContainerConfiguration.from_json_file(file_path)

            # 驗證配置
            if config.validation_enabled:
                errors = config.validate()
                if errors:
                    raise ValueError(
                        f"Configuration validation failed: {'; '.join(errors)}"
                    )

            self._configurations[name] = config
            self.logger.info(f"Loaded configuration '{name}' from {file_path}")
            return config

        except Exception as e:
            self.logger.error(f"Failed to load configuration '{name}': {e}")
            raise

    def get_configuration(self, name: str) -> Optional[ContainerConfiguration]:
        """獲取配置"""
        return self._configurations.get(name)

    def set_active_configuration(self, name: str):
        """設置活動配置"""
        if name not in self._configurations:
            raise ValueError(f"Configuration '{name}' not found")
        self._active_config = name
        self.logger.info(f"Set active configuration to '{name}'")

    def get_active_configuration(self) -> Optional[ContainerConfiguration]:
        """獲取活動配置"""
        if self._active_config:
            return self._configurations.get(self._active_config)
        return None

    def create_default_configuration(self) -> ContainerConfiguration:
        """創建默認配置"""
        return ContainerConfiguration(
            services=[
                ServiceConfiguration(
                    name="FileService",
                    implementation="core.services.file_service.FileService",
                    scope=ServiceScope.SINGLETON,
                    tags=["core", "service"],
                ),
                ServiceConfiguration(
                    name="TranslationService",
                    implementation="core.services.translation_service.TranslationService",
                    scope=ServiceScope.SINGLETON,
                    parameters={"max_concurrent_requests": 3},
                    tags=["core", "service"],
                ),
                ServiceConfiguration(
                    name="HighlightingService",
                    implementation="core.services.highlighting_service.HighlightingService",
                    scope=ServiceScope.SINGLETON,
                    parameters={"enabled": True},
                    tags=["core", "service"],
                ),
                ServiceConfiguration(
                    name="ProjectService",
                    implementation="core.services.project_service.ProjectService",
                    scope=ServiceScope.SINGLETON,
                    tags=["core", "service"],
                ),
                ServiceConfiguration(
                    name="AppStateManager",
                    implementation="core.state.app_state_manager.AppStateManager",
                    scope=ServiceScope.SINGLETON,
                    tags=["core", "state"],
                ),
                ServiceConfiguration(
                    name="MainWindow",
                    implementation="ui.main_window.MainWindow",
                    scope=ServiceScope.SINGLETON,
                    dependencies=[ServiceDependency(name="root", type="tkinter.Tk")],
                    tags=["ui", "window"],
                ),
                ServiceConfiguration(
                    name="EventHandlers",
                    implementation="ui.event_handlers.EventHandlers",
                    scope=ServiceScope.SINGLETON,
                    dependencies=[
                        ServiceDependency(name="root", type="tkinter.Tk"),
                        ServiceDependency(name="ui", type="ui.main_window.MainWindow"),
                        ServiceDependency(
                            name="state_manager",
                            type="core.state.app_state_manager.AppStateManager",
                        ),
                        ServiceDependency(
                            name="file_service",
                            type="core.services.file_service.FileService",
                        ),
                        ServiceDependency(
                            name="translation_service",
                            type="core.services.translation_service.TranslationService",
                        ),
                        ServiceDependency(
                            name="highlighting_service",
                            type="core.services.highlighting_service.HighlightingService",
                        ),
                        ServiceDependency(
                            name="project_service",
                            type="core.services.project_service.ProjectService",
                        ),
                    ],
                    tags=["ui", "handlers"],
                ),
            ]
        )


# 全局配置管理器實例
_config_manager = None


def get_config_manager() -> ServiceConfigurationManager:
    """獲取全局配置管理器實例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ServiceConfigurationManager()
    return _config_manager
