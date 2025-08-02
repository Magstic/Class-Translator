"""
依賴注入容器模塊

提供服務容器、依賴解析和生命週期管理功能的統一入口。
"""

from .service_container import (
    ServiceContainer,
    IServiceContainer,
    ServiceLifecycle,
    ServiceRegistration,
)
from .service_registration import register_default_services
from .dependency_resolver import DependencyResolver
from .service_lifecycle import ServiceLifecycleManager, get_lifecycle_manager
from .service_config import (
    ContainerConfiguration,
    ServiceConfiguration,
    ServiceScope,
    ServiceType,
    ServiceDependency,
    ServiceConfigurationManager,
    get_config_manager,
)
from .config_driven_registrar import (
    ConfigDrivenServiceRegistrar,
    ConfigurationBasedContainerBuilder,
    create_container_from_config,
    create_container_from_file,
)

# 全局服務容器實例
_global_container = None


def get_container() -> ServiceContainer:
    """獲取全局服務容器實例"""
    global _global_container
    if _global_container is None:
        _global_container = ServiceContainer()
        # 啟用自動依賴解析
        _global_container.enable_auto_resolution()
    return _global_container


def set_container(container: ServiceContainer):
    """設置全局服務容器實例"""
    global _global_container
    _global_container = container


def create_enhanced_container() -> ServiceContainer:
    """創建增強的服務容器"""
    container = ServiceContainer()
    container.enable_auto_resolution()
    return container


# 導出主要類和函數
__all__ = [
    # 核心容器
    "ServiceContainer",
    "IServiceContainer",
    "ServiceLifecycle",
    "ServiceRegistration",
    "register_default_services",
    # 依賴管理
    "DependencyResolver",
    "ServiceLifecycleManager",
    "get_lifecycle_manager",
    # 配置驅動
    "ContainerConfiguration",
    "ServiceConfiguration",
    "ServiceScope",
    "ServiceType",
    "ServiceDependency",
    "ServiceConfigurationManager",
    "get_config_manager",
    "ConfigDrivenServiceRegistrar",
    "ConfigurationBasedContainerBuilder",
    "create_container_from_config",
    "create_container_from_file",
    # 容器管理
    "get_container",
    "set_container",
    "create_enhanced_container",
]
