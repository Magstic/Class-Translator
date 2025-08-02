"""
依賴解析器 - 自動依賴注入和循環檢測

提供自動構造函數注入、依賴循環檢測和生命週期管理功能。
"""

import inspect
import logging
from typing import Dict, Type, TypeVar, Set, List, get_type_hints
from .service_container import ServiceContainer

T = TypeVar("T")


class DependencyResolver:
    """依賴解析器 - 提供自動依賴注入功能"""

    def __init__(self, container: ServiceContainer):
        self.container = container
        self.logger = logging.getLogger(__name__)
        self._resolving_stack: Set[Type] = set()  # 用於檢測循環依賴

    def auto_resolve(self, service_type: Type[T]) -> T:
        """
        自動解析服務及其依賴

        Args:
            service_type: 要解析的服務類型

        Returns:
            服務實例

        Raises:
            ValueError: 如果發現循環依賴或無法解析依賴
        """
        # 檢查循環依賴
        if service_type in self._resolving_stack:
            cycle_path = (
                " -> ".join([t.__name__ for t in self._resolving_stack])
                + f" -> {service_type.__name__}"
            )
            raise ValueError(f"Circular dependency detected: {cycle_path}")

        # 如果服務已經註冊，直接解析
        if self.container.is_registered(service_type):
            return self.container.resolve(service_type)

        # 自動註冊和解析
        self._resolving_stack.add(service_type)
        try:
            instance = self._create_instance_with_dependencies(service_type)
            self.container.register_instance(service_type, instance)
            return instance
        finally:
            self._resolving_stack.remove(service_type)

    def _create_instance_with_dependencies(self, service_type: Type[T]) -> T:
        """
        創建帶有依賴注入的服務實例

        Args:
            service_type: 服務類型

        Returns:
            服務實例
        """
        # 獲取構造函數簽名
        constructor = service_type.__init__
        signature = inspect.signature(constructor)

        # 獲取類型提示
        type_hints = get_type_hints(constructor)

        # 準備構造函數參數
        kwargs = {}

        for param_name, param in signature.parameters.items():
            if param_name == "self":
                continue

            # 獲取參數類型
            param_type = type_hints.get(param_name)

            if param_type is None:
                # 如果沒有類型提示，嘗試從默認值推斷
                if param.default != inspect.Parameter.empty:
                    continue  # 使用默認值
                else:
                    raise ValueError(
                        f"Cannot resolve parameter '{param_name}' for {service_type.__name__}: no type hint provided"
                    )

            # 解析依賴
            try:
                dependency = self.auto_resolve(param_type)
                kwargs[param_name] = dependency
                self.logger.debug(
                    f"Resolved dependency {param_name}: {param_type.__name__} for {service_type.__name__}"
                )
            except Exception as e:
                if param.default != inspect.Parameter.empty:
                    # 如果有默認值，使用默認值
                    continue
                else:
                    raise ValueError(
                        f"Cannot resolve dependency '{param_name}' of type {param_type.__name__} for {service_type.__name__}: {e}"
                    )

        # 創建實例
        try:
            instance = service_type(**kwargs)
            self.logger.debug(
                f"Created instance of {service_type.__name__} with dependencies: {list(kwargs.keys())}"
            )
            return instance
        except Exception as e:
            raise ValueError(
                f"Failed to create instance of {service_type.__name__}: {e}"
            )

    def get_dependency_graph(self, service_type: Type) -> Dict[str, List[str]]:
        """
        獲取服務的依賴圖

        Args:
            service_type: 服務類型

        Returns:
            依賴圖字典
        """
        graph = {}
        visited = set()

        def build_graph(current_type: Type):
            if current_type in visited:
                return

            visited.add(current_type)
            dependencies = []

            # 獲取構造函數依賴
            constructor = current_type.__init__
            signature = inspect.signature(constructor)
            type_hints = get_type_hints(constructor)

            for param_name, param in signature.parameters.items():
                if param_name == "self":
                    continue

                param_type = type_hints.get(param_name)
                if param_type and param.default == inspect.Parameter.empty:
                    dependencies.append(param_type.__name__)
                    build_graph(param_type)

            graph[current_type.__name__] = dependencies

        build_graph(service_type)
        return graph

    def validate_dependencies(self, service_types: List[Type]) -> List[str]:
        """
        驗證服務依賴是否可以解析

        Args:
            service_types: 要驗證的服務類型列表

        Returns:
            錯誤信息列表
        """
        errors = []

        for service_type in service_types:
            try:
                # 嘗試獲取依賴圖
                graph = self.get_dependency_graph(service_type)

                # 檢查循環依賴
                if self._has_circular_dependency(graph):
                    errors.append(
                        f"Circular dependency detected in {service_type.__name__}"
                    )

            except Exception as e:
                errors.append(f"Cannot validate {service_type.__name__}: {e}")

        return errors

    def _has_circular_dependency(self, graph: Dict[str, List[str]]) -> bool:
        """
        檢查依賴圖中是否存在循環依賴

        Args:
            graph: 依賴圖

        Returns:
            True如果存在循環依賴
        """
        # 使用深度優先搜索檢測循環
        visited = set()
        rec_stack = set()

        def dfs(node: str) -> bool:
            if node in rec_stack:
                return True  # 發現循環

            if node in visited:
                return False

            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if dfs(neighbor):
                    return True

            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                if dfs(node):
                    return True

        return False
