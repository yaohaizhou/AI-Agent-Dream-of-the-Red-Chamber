#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IntentParser - 意图解析器
将自然语言转换为结构化意图配置
"""

import re
from typing import Dict, Any, Optional
from dataclasses import dataclass

from ..agents.gpt5_client import GPT5Client
from ..config.settings import Settings


@dataclass
class UserIntent:
    """用户意图数据结构"""
    raw_input: str
    macro_ending: str
    meso_routes: Dict[str, Any]
    micro_controls: Dict[str, Any]
    confidence: float


class IntentParser:
    """
    意图解析器
    
    功能：
    1. 解析用户自然语言输入
    2. 提取三层意图（宏观/中观/微观）
    3. 输出结构化配置
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.gpt5_client = GPT5Client(self.settings)
    
    def parse(self, user_input: str) -> UserIntent:
        """
        解析用户意图
        
        Args:
            user_input: 用户自然语言输入
            
        Returns:
            UserIntent 结构化意图
        """
        # 预处理
        cleaned_input = self._preprocess(user_input)
        
        # 提取宏观结局
        macro = self._extract_macro(cleaned_input)
        
        # 提取中观路线
        meso = self._extract_meso(cleaned_input)
        
        # 提取微观控制
        micro = self._extract_micro(cleaned_input)
        
        # 计算置信度
        confidence = self._calculate_confidence(macro, meso, micro)
        
        return UserIntent(
            raw_input=user_input,
            macro_ending=macro,
            meso_routes=meso,
            micro_controls=micro,
            confidence=confidence
        )
    
    def _preprocess(self, text: str) -> str:
        """预处理用户输入"""
        # 去除多余空格
        text = re.sub(r'\s+', ' ', text)
        # 去除特殊字符
        text = re.sub(r'[^\w\s，。！？、：""''（）]', '', text)
        return text.strip()
    
    def _extract_macro(self, text: str) -> str:
        """提取宏观结局意图"""
        # 关键词匹配
        if any(kw in text for kw in ['宝黛', '宝玉黛玉', '黛玉宝玉', '在一起', '终成眷属', '结婚']):
            return '宝黛终成眷属'
        elif any(kw in text for kw in ['黛玉死', '泪尽', '病逝']):
            return '黛玉泪尽而亡'
        elif any(kw in text for kw in ['出家', '和尚', '空门']):
            return '宝玉出家'
        else:
            return '自定义'
    
    def _extract_meso(self, text: str) -> Dict[str, Any]:
        """提取中观路线意图"""
        routes = {}
        
        # 提取过程要求
        if any(kw in text for kw in ['波折', '曲折', '坎坷', '磨难']):
            routes['过程要求'] = '需要有波折，不能太顺利'
        elif any(kw in text for kw in ['顺利', '平淡']):
            routes['过程要求'] = '过程相对顺利'
        
        # 提取情感要求
        if any(kw in text for kw in ['坚强', '勇敢', '抗争']):
            routes['人物要求'] = '人物要坚强勇敢'
        elif any(kw in text for kw in ['温柔', '顺从']):
            routes['人物要求'] = '人物性格温柔顺从'
        
        return routes
    
    def _extract_micro(self, text: str) -> Dict[str, Any]:
        """提取微观控制意图"""
        controls = {}
        
        # 诗词要求
        if any(kw in text for kw in ['诗词', '诗', '词', '诗句']):
            if any(kw in text for kw in ['多', '多首', '大量']):
                controls['诗词数量'] = '每回多首'
            else:
                controls['诗词数量'] = '每回1-2首'
        
        # 性格强化
        character_traits = {}
        if '黛玉' in text or '林黛玉' in text:
            if any(kw in text for kw in ['坚强', '勇敢', '不悲观']):
                character_traits['林黛玉'] = {
                    '突出特质': '坚强勇敢',
                    '避免特质': '悲观自怜'
                }
        
        if character_traits:
            controls['人物性格强化'] = character_traits
        
        # 情感基调
        if any(kw in text for kw in ['哀而不伤', '悲中有望']):
            controls['情感基调'] = '哀而不伤'
        elif any(kw in text for kw in ['悲伤', '凄惨']):
            controls['情感基调'] = '悲伤'
        elif any(kw in text for kw in ['欢乐', '喜剧']):
            controls['情感基调'] = '欢乐'
        
        return controls
    
    def _calculate_confidence(
        self,
        macro: str,
        meso: Dict,
        micro: Dict
    ) -> float:
        """计算解析置信度"""
        score = 0.0
        
        # 宏观必须有
        if macro != '自定义':
            score += 0.4
        
        # 中观有加分
        if meso:
            score += 0.3
        
        # 微观有加分
        if micro:
            score += 0.3
        
        return score
    
    def to_yaml(self, intent: UserIntent) -> str:
        """将意图转换为YAML格式"""
        import yaml
        
        config = {
            'raw_input': intent.raw_input,
            '宏观结局': {
                'type': intent.macro_ending
            },
            '中观路线': intent.meso_routes,
            '微观控制': intent.micro_controls,
            'confidence': intent.confidence
        }
        
        return yaml.dump(config, allow_unicode=True, sort_keys=False)


def parse_user_intent(text: str) -> UserIntent:
    """便捷函数：解析用户意图"""
    parser = IntentParser()
    return parser.parse(text)


if __name__ == "__main__":
    # 测试
    print("=" * 60)
    print("🎯 IntentParser 测试")
    print("=" * 60)
    
    test_inputs = [
        "我希望宝玉黛玉最后在一起，但过程要有波折",
        "希望黛玉更坚强，不要太悲观，每回都要有诗词",
        "宝黛终成眷属，贾府中兴，风格要哀而不伤"
    ]
    
    for i, input_text in enumerate(test_inputs, 1):
        print(f"\n📝 测试 {i}: {input_text}")
        intent = parse_user_intent(input_text)
        print(f"   宏观: {intent.macro_ending}")
        print(f"   中观: {intent.meso_routes}")
        print(f"   微观: {intent.micro_controls}")
        print(f"   置信度: {intent.confidence:.2f}")
    
    print("\n" + "=" * 60)
    print("✅ IntentParser 测试完成")
    print("=" * 60)
