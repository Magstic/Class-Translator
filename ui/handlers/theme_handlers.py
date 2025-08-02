"""
主题相关的处理器
"""

import logging
from .base_handler import BaseHandler
from core.services.theme_service import ThemeService, ThemeChangedEvent


class ThemeHandlers(BaseHandler):
    """处理所有主题相关的功能"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.theme_service = None
        self._setup_theme_service()
    
    def _setup_theme_service(self):
        """设置主题服务"""
        try:
            # 尝试从容器获取主题服务
            # 注意：这里需要延迟获取，因为在初始化时容器可能还没完全设置好
            pass
        except Exception as e:
            self.logger.error(f"Failed to setup theme service: {e}")
    
    def register_commands(self, command_invoker):
        """注册主题相关的命令"""
        # 主題對話框已移除，改用菜單欄快速切換
        pass
    
    # 主題對話框相關方法已移除，改用MainWindow中的快速切換
    
    def _get_theme_service(self) -> ThemeService:
        """获取主题服务实例"""
        try:
            # 尝试多种方式获取主题服务
            
            # 方式1: 通过全局应用实例获取
            # 在main.py中，App实例被存储在根窗口中
            if hasattr(self.root, '_app_instance'):
                return self.root._app_instance.container.resolve(ThemeService)
            
            # 方式2: 通过根窗口的属性获取
            # 在某些情况下，app实例可能被存储为其他属性
            for attr_name in ['app', 'application', '_application']:
                if hasattr(self.root, attr_name):
                    app = getattr(self.root, attr_name)
                    if hasattr(app, 'container'):
                        return app.container.resolve(ThemeService)
            
            # 方式3: 创建新的主题服务实例（备用方案）
            self.logger.warning("无法从容器获取主题服务，创建新实例")
            return ThemeService(self.root)
            
        except Exception as e:
            self.logger.error(f"获取主题服务失败: {e}")
            # 如果所有方法都失败，尝试创建一个新实例
            try:
                return ThemeService(self.root)
            except Exception as create_error:
                self.logger.error(f"创建主题服务实例失败: {create_error}")
                return None
    
    def on_theme_changed(self, event: ThemeChangedEvent):
        """处理主题变更事件"""
        try:
            self.logger.info(f"主题已变更为: {event.theme_name}")
            
            # 这里可以添加主题变更后的额外处理逻辑
            # 比如更新特定UI组件的样式等
            
        except Exception as e:
            self.logger.error(f"处理主题变更事件失败: {e}")
    
    def get_current_theme(self) -> str:
        """获取当前主题名称"""
        if not self.theme_service:
            self.theme_service = self._get_theme_service()
        
        if self.theme_service:
            return self.theme_service.get_current_theme()
        
        return "light"  # 默认主题
    
    def apply_theme(self, theme_name: str) -> bool:
        """应用指定主题"""
        if not self.theme_service:
            self.theme_service = self._get_theme_service()
        
        if self.theme_service:
            return self.theme_service.apply_theme(theme_name)
        
        return False
