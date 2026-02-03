#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IntentLoader - 用户意图配置加载器
"""

import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class IntentLoader:
    """
    用户意图配置加载器
    
    功能：
    1. 加载用户意图配置文件
    2. 验证配置格式
    3. 提供默认配置
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        初始化加载器
        
        Args:
            config_dir: 配置目录路径，默认使用 config/user_intents/
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / "config" / "user_intents"
        
        self.config_dir = config_dir
        self.schema_path = Path(__file__).parent.parent.parent / "config" / "user_intent_schema.yml"
    
    def load_user_intent(self, intent_name: str = "default") -> Optional[Dict[str, Any]]:
        """
        加载用户意图配置
        
        Args:
            intent_name: 意图配置文件名（不含扩展名）
            
        Returns:
            意图配置字典，加载失败返回 None
        """
        config_path = self.config_dir / f"{intent_name}.yml"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 验证配置
            if self.validate_intent(config):
                return config
            else:
                print(f"配置验证失败: {intent_name}")
                return None
                
        except Exception as e:
            print(f"加载意图配置失败: {e}")
            return None
    
    def validate_intent(self, config: Dict[str, Any]) -> bool:
        """
        验证意图配置格式
        
        Args:
            config: 配置字典
            
        Returns:
            是否有效
        """
        # 基础检查
        if not isinstance(config, dict):
            return False
        
        # 检查必需的顶层键
        required_keys = ['宏观结局', '中观路线', '微观控制']
        for key in required_keys:
            if key not in config:
                print(f"缺少必需配置项: {key}")
                return False
        
        # 检查宏观结局
        macro = config.get('宏观结局', {})
        if 'type' not in macro or 'description' not in macro:
            print("宏观结局缺少 type 或 description")
            return False
        
        # 检查中观路线
        meso = config.get('中观路线', {})
        if '宝黛爱情线' not in meso:
            print("中观路线缺少宝黛爱情线")
            return False
        
        # 检查微观控制
        micro = config.get('微观控制', {})
        if '人物性格强化' not in micro:
            print("微观控制缺少人物性格强化")
            return False
        
        return True
    
    def get_default_intent(self) -> Dict[str, Any]:
        """获取默认用户意图配置"""
        return self.load_user_intent("default") or {}
    
    def list_available_intents(self) -> list:
        """列出所有可用的意图配置"""
        intents = []
        try:
            for config_file in self.config_dir.glob("*.yml"):
                intents.append(config_file.stem)
        except Exception as e:
            print(f"列出意图配置失败: {e}")
        
        return intents
    
    def get_macro_ending(self, config: Dict[str, Any]) -> str:
        """获取宏观结局类型"""
        return config.get('宏观结局', {}).get('type', '未知')
    
    def get_character_traits(
        self,
        config: Dict[str, Any],
        character: str
    ) -> Dict[str, str]:
        """获取人物性格强化配置"""
        traits = config.get('微观控制', {}).get('人物性格强化', {})
        return traits.get(character, {})
    
    def get_style_preference(self, config: Dict[str, Any]) -> Dict[str, str]:
        """获取风格偏好配置"""
        return config.get('微观控制', {}).get('风格偏好', {})


# 便捷函数
def create_intent_loader() -> IntentLoader:
    """创建默认的意图加载器"""
    return IntentLoader()


def load_default_intent() -> Dict[str, Any]:
    """加载默认意图配置"""
    loader = create_intent_loader()
    return loader.get_default_intent()


if __name__ == "__main__":
    # 测试
    print("=" * 60)
    print("📋 IntentLoader 测试")
    print("=" * 60)
    
    loader = create_intent_loader()
    
    # 列出可用配置
    intents = loader.list_available_intents()
    print(f"\n📁 可用意图配置: {intents}")
    
    # 加载默认配置
    config = loader.get_default_intent()
    if config:
        print("✅ 默认配置加载成功")
        
        # 获取宏观结局
        ending = loader.get_macro_ending(config)
        print(f"📌 宏观结局: {ending}")
        
        # 获取黛玉性格配置
        daiyu_traits = loader.get_character_traits(config, "林黛玉")
        print(f"\n👤 林黛玉性格强化:")
        print(f"   突出: {daiyu_traits.get('突出特质', '')}")
        print(f"   避免: {daiyu_traits.get('避免特质', '')}")
        
        # 获取风格偏好
        style = loader.get_style_preference(config)
        print(f"\n🎨 风格偏好:")
        print(f"   诗词: {style.get('诗词数量', '')}")
        print(f"   基调: {style.get('情感基调', '')}")
    
    print("\n" + "=" * 60)
    print("✅ IntentLoader 测试完成")
    print("=" * 60)
