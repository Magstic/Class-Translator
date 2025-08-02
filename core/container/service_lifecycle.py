"""
服務生命週期管理器

管理服務的創建、初始化、銷毀等生命週期事件。
"""

import logging
import weakref
from typing import Dict, List, Type, Any, Callable, Protocol
from enum import Enum


class ServiceState(Enum):
    """服務狀態枚舉"""

    CREATED = "created"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    DISPOSING = "disposing"
    DISPOSED = "disposed"


class IDisposable(Protocol):
    """可釋放資源的接口"""

    def dispose(self) -> None:
        """釋放資源"""
        pass


class IInitializable(Protocol):
    """可初始化的接口"""

    def initialize(self) -> None:
        """初始化服務"""
        pass


class ServiceLifecycleManager:
    """服務生命週期管理器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 服務狀態跟蹤
        self._service_states: Dict[int, ServiceState] = {}
        self._service_refs: Dict[int, weakref.ref] = {}

        # 生命週期事件處理器
        self._creation_handlers: List[Callable[[Any], None]] = []
        self._initialization_handlers: List[Callable[[Any], None]] = []
        self._disposal_handlers: List[Callable[[Any], None]] = []

        # 初始化順序管理
        self._initialization_order: List[Type] = []
        self._disposal_order: List[Type] = []

    def register_service_created(self, service: Any):
        """
        註冊服務已創建

        Args:
            service: 服務實例
        """
        service_id = id(service)
        self._service_states[service_id] = ServiceState.CREATED
        self._service_refs[service_id] = weakref.ref(
            service, self._on_service_garbage_collected
        )

        self.logger.debug(f"Service created: {type(service).__name__}")

        # 觸發創建事件
        for handler in self._creation_handlers:
            try:
                handler(service)
            except Exception as e:
                self.logger.error(
                    f"Error in creation handler for {type(service).__name__}: {e}"
                )

    def initialize_service(self, service: Any):
        """
        初始化服務

        Args:
            service: 服務實例
        """
        service_id = id(service)

        if service_id not in self._service_states:
            self.register_service_created(service)

        current_state = self._service_states.get(service_id)
        if current_state in [ServiceState.INITIALIZED, ServiceState.INITIALIZING]:
            return  # 已經初始化或正在初始化

        self._service_states[service_id] = ServiceState.INITIALIZING

        try:
            # 如果服務實現了IInitializable接口，調用initialize方法
            if hasattr(service, "initialize") and callable(
                getattr(service, "initialize")
            ):
                service.initialize()

            self._service_states[service_id] = ServiceState.INITIALIZED
            self.logger.debug(f"Service initialized: {type(service).__name__}")

            # 觸發初始化事件
            for handler in self._initialization_handlers:
                try:
                    handler(service)
                except Exception as e:
                    self.logger.error(
                        f"Error in initialization handler for {type(service).__name__}: {e}"
                    )

        except Exception as e:
            self.logger.error(
                f"Failed to initialize service {type(service).__name__}: {e}"
            )
            self._service_states[service_id] = ServiceState.CREATED
            raise

    def dispose_service(self, service: Any):
        """
        銷毀服務

        Args:
            service: 服務實例
        """
        service_id = id(service)

        current_state = self._service_states.get(service_id)
        if current_state in [ServiceState.DISPOSED, ServiceState.DISPOSING]:
            return  # 已經銷毀或正在銷毀

        self._service_states[service_id] = ServiceState.DISPOSING

        try:
            # 觸發銷毀事件
            for handler in self._disposal_handlers:
                try:
                    handler(service)
                except Exception as e:
                    self.logger.error(
                        f"Error in disposal handler for {type(service).__name__}: {e}"
                    )

            # 如果服務實現了IDisposable接口，調用dispose方法
            if hasattr(service, "dispose") and callable(getattr(service, "dispose")):
                service.dispose()

            self._service_states[service_id] = ServiceState.DISPOSED
            self.logger.debug(f"Service disposed: {type(service).__name__}")

        except Exception as e:
            self.logger.error(
                f"Failed to dispose service {type(service).__name__}: {e}"
            )
            raise

    def dispose_all_services(self):
        """銷毀所有服務"""
        # 按照相反的初始化順序銷毀服務
        services_to_dispose = []

        for service_ref in self._service_refs.values():
            service = service_ref()
            if service is not None:
                services_to_dispose.append(service)

        # 按照類型的相反順序銷毀
        services_to_dispose.sort(
            key=lambda s: self._get_disposal_priority(type(s)), reverse=True
        )

        for service in services_to_dispose:
            try:
                self.dispose_service(service)
            except Exception as e:
                self.logger.error(
                    f"Error disposing service {type(service).__name__}: {e}"
                )

    def get_service_state(self, service: Any) -> ServiceState:
        """
        獲取服務狀態

        Args:
            service: 服務實例

        Returns:
            服務狀態
        """
        service_id = id(service)
        return self._service_states.get(service_id, ServiceState.CREATED)

    def get_service_statistics(self) -> Dict[str, int]:
        """
        獲取服務統計信息

        Returns:
            服務統計字典
        """
        stats = {}
        for state in ServiceState:
            stats[state.value] = sum(
                1 for s in self._service_states.values() if s == state
            )

        stats["total"] = len(self._service_states)
        stats["active"] = len(
            [ref for ref in self._service_refs.values() if ref() is not None]
        )

        return stats

    def add_creation_handler(self, handler: Callable[[Any], None]):
        """添加服務創建事件處理器"""
        self._creation_handlers.append(handler)

    def add_initialization_handler(self, handler: Callable[[Any], None]):
        """添加服務初始化事件處理器"""
        self._initialization_handlers.append(handler)

    def add_disposal_handler(self, handler: Callable[[Any], None]):
        """添加服務銷毀事件處理器"""
        self._disposal_handlers.append(handler)

    def set_initialization_order(self, service_types: List[Type]):
        """設置服務初始化順序"""
        self._initialization_order = service_types.copy()

    def set_disposal_order(self, service_types: List[Type]):
        """設置服務銷毀順序"""
        self._disposal_order = service_types.copy()

    def _get_disposal_priority(self, service_type: Type) -> int:
        """獲取服務銷毀優先級"""
        try:
            return self._disposal_order.index(service_type)
        except ValueError:
            return len(self._disposal_order)  # 未指定順序的服務最後銷毀

    def _on_service_garbage_collected(self, weak_ref):
        """服務被垃圾回收時的回調"""
        # 清理相關記錄
        service_id = None
        for sid, ref in self._service_refs.items():
            if ref is weak_ref:
                service_id = sid
                break

        if service_id:
            self._service_states.pop(service_id, None)
            self._service_refs.pop(service_id, None)
            self.logger.debug(f"Service garbage collected: {service_id}")


# 全局生命週期管理器實例
_lifecycle_manager = None


def get_lifecycle_manager() -> ServiceLifecycleManager:
    """獲取全局生命週期管理器實例"""
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = ServiceLifecycleManager()
    return _lifecycle_manager
