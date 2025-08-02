"""
配置驅動的服務註冊器

根據配置文件動態註冊服務，支持靈活的服務配置和依賴注入。
"""

import importlib
import logging
from typing import Dict, Any, Type, Callable, List
from .service_container import ServiceContainer, ServiceLifecycle
from .service_config import (
    ContainerConfiguration,
    ServiceConfiguration,
    ServiceScope,
    ServiceType,
    get_config_manager,
)


class ConfigDrivenServiceRegistrar:
    """配置驅動的服務註冊器"""

    def __init__(self, container: ServiceContainer):
        self.container = container
        self.logger = logging.getLogger(__name__)
        self._registered_services: Dict[str, Type] = {}
        self._service_instances: Dict[str, Any] = {}

    def register_from_configuration(self, config: ContainerConfiguration):
        """
        根據配置註冊所有服務

        Args:
            config: 容器配置
        """
        self.logger.info("Starting configuration-driven service registration")

        # 按優先級排序服務
        services = sorted(config.services, key=lambda s: s.priority, reverse=True)

        # 分階段註冊
        self._register_services_by_phase(services)

        self.logger.info(f"Registered {len(services)} services from configuration")

    def _register_services_by_phase(self, services: List[ServiceConfiguration]):
        """分階段註冊服務"""

        # 階段1：註冊無依賴的服務
        no_dependency_services = [s for s in services if not s.dependencies]
        self._register_service_batch(no_dependency_services, "Phase 1: No Dependencies")

        # 階段2：註冊有依賴的服務
        dependency_services = [s for s in services if s.dependencies]
        self._register_service_batch(dependency_services, "Phase 2: With Dependencies")

    def _register_service_batch(
        self, services: List[ServiceConfiguration], phase_name: str
    ):
        """批量註冊服務"""
        self.logger.debug(f"Starting {phase_name}")

        for service_config in services:
            try:
                self._register_single_service(service_config)
            except Exception as e:
                self.logger.error(
                    f"Failed to register service '{service_config.name}': {e}"
                )
                raise

        self.logger.debug(f"Completed {phase_name}")

    def _register_single_service(self, service_config: ServiceConfiguration):
        """註冊單個服務"""
        self.logger.debug(f"Registering service: {service_config.name}")

        # 解析服務類型
        service_type = self._resolve_service_type(service_config.implementation)
        self._registered_services[service_config.name] = service_type

        # 創建服務工廠
        factory = self._create_service_factory(service_config, service_type)

        # 根據作用域註冊服務
        lifecycle = self._convert_scope_to_lifecycle(service_config.scope)

        if lifecycle == ServiceLifecycle.SINGLETON:
            self.container.register_singleton(service_type, factory)
        elif lifecycle == ServiceLifecycle.TRANSIENT:
            self.container.register_transient(service_type, factory)
        else:
            # 對於實例類型，立即創建並註冊
            instance = factory()
            self.container.register_instance(service_type, instance)
            self._service_instances[service_config.name] = instance

        self.logger.debug(
            f"Successfully registered service: {service_config.name} as {lifecycle.value}"
        )

    def _resolve_service_type(self, implementation: str) -> Type:
        """解析服務類型"""
        try:
            # 分割模塊和類名
            if "." in implementation:
                module_path, class_name = implementation.rsplit(".", 1)
            else:
                raise ValueError(f"Invalid implementation format: {implementation}")

            # 動態導入模塊
            module = importlib.import_module(module_path)

            # 獲取類
            service_class = getattr(module, class_name)

            if not isinstance(service_class, type):
                raise ValueError(f"'{implementation}' is not a class")

            return service_class

        except ImportError as e:
            raise ValueError(f"Cannot import module for '{implementation}': {e}")
        except AttributeError as e:
            raise ValueError(f"Class not found in module for '{implementation}': {e}")

    def _create_service_factory(
        self, service_config: ServiceConfiguration, service_type: Type
    ) -> Callable:
        """創建服務工廠函數"""

        if service_config.service_type == ServiceType.FACTORY:
            return self._create_factory_service_factory(service_config, service_type)
        elif service_config.service_type == ServiceType.INSTANCE:
            return self._create_instance_service_factory(service_config, service_type)
        else:
            return self._create_class_service_factory(service_config, service_type)

    def _create_class_service_factory(
        self, service_config: ServiceConfiguration, service_type: Type
    ) -> Callable:
        """創建類服務工廠"""

        def factory():
            # 解析依賴
            kwargs = {}

            for dependency in service_config.dependencies:
                try:
                    # 嘗試從容器解析依賴
                    dep_type = self._resolve_service_type(dependency.type)
                    dep_instance = self.container.resolve(dep_type)
                    kwargs[dependency.name] = dep_instance
                except Exception as e:
                    if dependency.optional:
                        if dependency.default_value is not None:
                            kwargs[dependency.name] = dependency.default_value
                        # 如果是可選依賴且沒有默認值，則跳過
                    else:
                        raise ValueError(
                            f"Cannot resolve required dependency '{dependency.name}' for service '{service_config.name}': {e}"
                        )

            # 創建服務實例
            try:
                instance = service_type(**kwargs)
            except TypeError as e:
                # 如果構造函數不接受參數，嘗試不帶參數創建
                if "unexpected keyword argument" in str(e):
                    instance = service_type()
                else:
                    raise

            # 在創建後設置配置參數
            for param_name, param_value in service_config.parameters.items():
                if hasattr(instance, param_name):
                    setattr(instance, param_name, param_value)
                    self.logger.debug(
                        f"Set parameter {param_name}={param_value} for service {service_config.name}"
                    )
                else:
                    self.logger.warning(
                        f"Service {service_config.name} does not have attribute '{param_name}'"
                    )

            return instance

        return factory

    def _create_factory_service_factory(
        self, service_config: ServiceConfiguration, service_type: Type
    ) -> Callable:
        """創建工廠服務工廠"""

        def factory():
            # 對於工廠類型，service_type應該是一個工廠函數
            factory_func = service_type

            # 準備參數
            kwargs = service_config.parameters.copy()

            # 解析依賴並添加到參數中
            for dependency in service_config.dependencies:
                try:
                    dep_type = self._resolve_service_type(dependency.type)
                    dep_instance = self.container.resolve(dep_type)
                    kwargs[dependency.name] = dep_instance
                except Exception as e:
                    if not dependency.optional:
                        raise ValueError(
                            f"Cannot resolve dependency '{dependency.name}': {e}"
                        )

            return factory_func(**kwargs)

        return factory

    def _create_instance_service_factory(
        self, service_config: ServiceConfiguration, service_type: Type
    ) -> Callable:
        """創建實例服務工廠"""

        def factory():
            # 對於實例類型，直接返回預創建的實例
            if service_config.name in self._service_instances:
                return self._service_instances[service_config.name]

            # 如果沒有預創建，則創建新實例
            kwargs = service_config.parameters.copy()
            return service_type(**kwargs)

        return factory

    def _convert_scope_to_lifecycle(self, scope: ServiceScope) -> ServiceLifecycle:
        """轉換作用域到生命週期"""
        if scope == ServiceScope.SINGLETON:
            return ServiceLifecycle.SINGLETON
        elif scope == ServiceScope.TRANSIENT:
            return ServiceLifecycle.TRANSIENT
        elif scope == ServiceScope.SCOPED:
            # 對於作用域服務，在這個實現中視為單例
            return ServiceLifecycle.SINGLETON
        else:
            return ServiceLifecycle.SINGLETON

    def get_registered_service_types(self) -> Dict[str, Type]:
        """獲取已註冊的服務類型"""
        return self._registered_services.copy()

    def get_service_instances(self) -> Dict[str, Any]:
        """獲取服務實例"""
        return self._service_instances.copy()


class ConfigurationBasedContainerBuilder:
    """基於配置的容器構建器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def build_container_from_config(
        self, config: ContainerConfiguration
    ) -> ServiceContainer:
        """
        根據配置構建容器

        Args:
            config: 容器配置

        Returns:
            配置好的服務容器
        """
        self.logger.info("Building container from configuration")

        # 創建容器
        container = ServiceContainer()

        # 根據配置設置容器選項
        if config.auto_registration:
            container.enable_auto_resolution()

        # 設置日誌級別
        logging.getLogger().setLevel(getattr(logging, config.logging_level.upper()))

        # 創建註冊器並註冊服務
        registrar = ConfigDrivenServiceRegistrar(container)
        registrar.register_from_configuration(config)

        self.logger.info("Container built successfully from configuration")
        return container

    def build_container_from_file(self, config_file: str) -> ServiceContainer:
        """
        從配置文件構建容器

        Args:
            config_file: 配置文件路径

        Returns:
            配置好的服務容器
        """
        config_manager = get_config_manager()
        config = config_manager.load_configuration("default", config_file)
        return self.build_container_from_config(config)


def create_container_from_config(config: ContainerConfiguration) -> ServiceContainer:
    """
    便捷函數：根據配置創建容器

    Args:
        config: 容器配置

    Returns:
        配置好的服務容器
    """
    builder = ConfigurationBasedContainerBuilder()
    return builder.build_container_from_config(config)


def create_container_from_file(config_file: str) -> ServiceContainer:
    """
    便捷函數：從配置文件創建容器

    Args:
        config_file: 配置文件路径

    Returns:
        配置好的服務容器
    """
    builder = ConfigurationBasedContainerBuilder()
    return builder.build_container_from_file(config_file)
