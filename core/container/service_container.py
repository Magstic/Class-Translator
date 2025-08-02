"""
服務容器 - 依賴注入容器實現

提供服務註冊、解析和生命週期管理功能。
"""

from typing import Dict, Any, Type, TypeVar, Callable, Optional, List
from abc import ABC, abstractmethod
import logging
from enum import Enum
from .service_lifecycle import get_lifecycle_manager, ServiceLifecycleManager

T = TypeVar("T")


class ServiceLifecycle(Enum):
    """服務生命週期枚舉"""

    SINGLETON = "Singleton"
    TRANSIENT = "Transient"
    INSTANCE = "Instance"


class ServiceRegistration:
    """服務註冊信息"""

    def __init__(self, factory: Callable, lifecycle: ServiceLifecycle):
        self.factory = factory
        self.lifecycle = lifecycle


class IServiceContainer(ABC):
    """服務容器接口"""

    @abstractmethod
    def register_singleton(
        self, service_type: Type[T], factory: Callable[[], T]
    ) -> None:
        """註冊單例服務"""
        pass

    @abstractmethod
    def register_transient(
        self, service_type: Type[T], factory: Callable[[], T]
    ) -> None:
        """註冊瞬態服務"""
        pass

    @abstractmethod
    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """註冊服務實例"""
        pass

    @abstractmethod
    def resolve(self, service_type: Type[T]) -> T:
        """解析服務實例"""
        pass

    @abstractmethod
    def is_registered(self, service_type: Type[T]) -> bool:
        """檢查服務是否已註冊"""
        pass


class ServiceContainer(IServiceContainer):
    """依賴注入服務容器實現"""

    def __init__(self):
        self._services: Dict[Type, ServiceRegistration] = {}
        self._instances: Dict[Type, Any] = {}
        self.logger = logging.getLogger(__name__)
        self._lifecycle_manager = get_lifecycle_manager()
        self._dependency_resolver = None  # 延遲初始化避免循環導入

        self.logger.info("ServiceContainer initialized")

    def register_singleton(
        self, service_type: Type[T], factory: Callable[[], T]
    ) -> None:
        """
        註冊單例服務

        Args:
            service_type: 服務類型
            factory: 創建服務的工廠函數
        """
        self._services[service_type] = ServiceRegistration(
            factory, ServiceLifecycle.SINGLETON
        )
        self.logger.debug(f"Registered singleton: {service_type.__name__}")

    def register_transient(
        self, service_type: Type[T], factory: Callable[[], T]
    ) -> None:
        """
        註冊瞬態服務（每次解析都創建新實例）

        Args:
            service_type: 服務類型
            factory: 創建服務的工廠函數
        """
        self._services[service_type] = ServiceRegistration(
            factory, ServiceLifecycle.TRANSIENT
        )
        self.logger.debug(f"Registered transient: {service_type.__name__}")

    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """
        註冊服務實例

        Args:
            service_type: 服務類型
            instance: 服務實例
        """
        self._services[service_type] = ServiceRegistration(
            lambda: instance, ServiceLifecycle.INSTANCE
        )
        self.logger.debug(f"Registered instance: {service_type.__name__}")

    def resolve(self, service_type: Type[T]) -> T:
        """
        解析服務實例

        Args:
            service_type: 服務類型

        Returns:
            服務實例

        Raises:
            ValueError: 如果服務未註冊
        """
        if service_type not in self._services:
            # 嘗試自動解析
            if self._dependency_resolver:
                return self._dependency_resolver.auto_resolve(service_type)
            else:
                raise ValueError(f"Service {service_type.__name__} is not registered")

        registration = self._services[service_type]

        if registration.lifecycle == ServiceLifecycle.SINGLETON:
            # 單例模式：如果已存在實例，直接返回
            if service_type in self._instances:
                return self._instances[service_type]

            # 創建新實例
            instance = registration.factory()
            self._instances[service_type] = instance

            # 註冊到生命週期管理器
            self._lifecycle_manager.register_service_created(instance)
            self._lifecycle_manager.initialize_service(instance)

            self.logger.debug(f"Created singleton instance of {service_type.__name__}")
            return instance

        elif registration.lifecycle == ServiceLifecycle.TRANSIENT:
            # 瞬態模式：每次都創建新實例
            instance = registration.factory()

            # 註冊到生命週期管理器
            self._lifecycle_manager.register_service_created(instance)
            self._lifecycle_manager.initialize_service(instance)

            self.logger.debug(f"Created transient instance of {service_type.__name__}")
            return instance

        elif registration.lifecycle == ServiceLifecycle.INSTANCE:
            # 實例模式：直接返回預註冊的實例
            instance = registration.factory()

            # 註冊到生命週期管理器（如果還沒註冊）
            if service_type not in self._instances:
                self._lifecycle_manager.register_service_created(instance)
                self._lifecycle_manager.initialize_service(instance)
                self._instances[service_type] = instance

            self.logger.debug(
                f"Returned registered instance of {service_type.__name__}"
            )
            return instance

        else:
            raise ValueError(f"Unknown service lifecycle: {registration.lifecycle}")

    def is_registered(self, service_type: Type[T]) -> bool:
        """
        檢查服務是否已註冊

        Args:
            service_type: 服務類型

        Returns:
            True如果已註冊
        """
        return service_type in self._services

    def get_registered_services(self) -> Dict[str, str]:
        """
        獲取已註冊的服務列表

        Returns:
            服務名稱到生命週期的映射
        """
        return {
            service_type.__name__: registration.lifecycle.value
            for service_type, registration in self._services.items()
        }

    def enable_auto_resolution(self):
        """
        啟用自動依賴解析功能
        """
        if self._dependency_resolver is None:
            from .dependency_resolver import DependencyResolver

            self._dependency_resolver = DependencyResolver(self)
            self.logger.info("Auto dependency resolution enabled")

    def get_dependency_graph(self, service_type: Type) -> Dict[str, List[str]]:
        """
        獲取服務依賴圖

        Args:
            service_type: 服務類型

        Returns:
            依賴圖
        """
        if self._dependency_resolver:
            return self._dependency_resolver.get_dependency_graph(service_type)
        else:
            return {}

    def validate_dependencies(self, service_types: List[Type]) -> List[str]:
        """
        驗證服務依賴

        Args:
            service_types: 服務類型列表

        Returns:
            錯誤信息列表
        """
        if self._dependency_resolver:
            return self._dependency_resolver.validate_dependencies(service_types)
        else:
            return []

    def get_lifecycle_manager(self) -> ServiceLifecycleManager:
        """
        獲取生命週期管理器

        Returns:
            生命週期管理器實例
        """
        return self._lifecycle_manager

    def dispose_all(self):
        """
        銷毀所有服務
        """
        self._lifecycle_manager.dispose_all_services()
        self._instances.clear()
        self.logger.info("All services disposed")

    def clear(self):
        """清空容器中的所有服務"""
        self.dispose_all()
        self._services.clear()
        self.logger.info("ServiceContainer cleared")


# 全局服務容器實例
_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """獲取全局服務容器實例"""
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container


def set_container(container: ServiceContainer):
    """設置全局服務容器實例"""
    global _container
    _container = container
