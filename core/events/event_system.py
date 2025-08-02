"""
事件系統 - 實現發布/訂閱模式
用於解耦UI和業務邏輯之間的直接依賴
"""

import logging
from typing import Dict, List, Callable
from abc import ABC, abstractmethod


class Event(ABC):
    """事件基類"""

    def __init__(self, source: str = None):
        self.source = source or "unknown"

    @property
    @abstractmethod
    def event_type(self) -> str:
        """事件類型標識"""
        pass


class EventSystem:
    """事件發布/訂閱系統"""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        self._logger = logging.getLogger(__name__)

    def subscribe(self, event_type: str, handler: Callable[[Event], None]):
        """訂閱事件"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(handler)
        self._logger.debug(f"Subscribed to event '{event_type}': {handler.__name__}")

    def unsubscribe(self, event_type: str, handler: Callable[[Event], None]):
        """取消訂閱事件"""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                self._logger.debug(
                    f"Unsubscribed from event '{event_type}': {handler.__name__}"
                )
            except ValueError:
                self._logger.warning(
                    f"Handler {handler.__name__} not found for event '{event_type}'"
                )

    def publish(self, event: Event):
        """發布事件"""
        event_type = event.event_type

        if event_type not in self._subscribers:
            self._logger.debug(f"No subscribers for event '{event_type}'")
            return

        self._logger.debug(f"Publishing event '{event_type}' from {event.source}")

        for handler in self._subscribers[event_type]:
            try:
                handler(event)
            except Exception as e:
                self._logger.error(
                    f"Error in event handler {handler.__name__} for event '{event_type}': {e}"
                )

    def get_subscriber_count(self, event_type: str) -> int:
        """獲取指定事件類型的訂閱者數量"""
        return len(self._subscribers.get(event_type, []))

    def clear_subscribers(self, event_type: str = None):
        """清除訂閱者"""
        if event_type:
            self._subscribers.pop(event_type, None)
            self._logger.debug(f"Cleared subscribers for event '{event_type}'")
        else:
            self._subscribers.clear()
            self._logger.debug("Cleared all subscribers")


# 全局事件系統實例
_global_event_system = None


def get_event_system() -> EventSystem:
    """獲取全局事件系統實例"""
    global _global_event_system
    if _global_event_system is None:
        _global_event_system = EventSystem()
    return _global_event_system
