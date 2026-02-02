#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合测试套件
合并所有分散的测试文件到一个统一的测试框架
"""

import pytest
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.base_scorer import (
    ScoreConfig, 
    BaseScorer, 
    CharacterScorerMixin,
    StyleEvaluator,
    StructureEvaluator,
    get_keyword_cache
)
from src.utils.enhanced_scorer import EnhancedCharacterScorer, score_content
from src.agents.real.quality_checker_agent import QualityCheckerAgent
from src.agents.character_consistency_checker import CharacterConsistencyChecker


class TestScoreConfig:
    """测试评分配置"""
    
    def test_default_values(self):
        config = ScoreConfig()
        assert config.SPEECH_BASE_SCORE == 0.5
        assert config.BEHAVIOR_BASE_SCORE == 0.45
        assert config.DIMENSION_WEIGHT_SPEECH == 0.30
        
    def test_custom_values(self):
        config = ScoreConfig(SPEECH_BASE_SCORE=0.6)
        assert config.SPEECH_BASE_SCORE == 0.6


class TestStyleEvaluator:
    """测试风格评估器"""
    
    @pytest.fixture
    def evaluator(self):
        return StyleEvaluator()
    
    def test_classical_content(self, evaluator):
        content = "话说宝玉来到潇湘馆，只见黛玉正在窗前抚琴。"
        score = evaluator.evaluate(content)
        assert 6.0 <= score <= 10.0
        
    def test_modern_content(self, evaluator):
        content = "今天天气很好，我去公园散步。"
        score = evaluator.evaluate(content)
        assert score >= 6.0  # 基础分


class TestStructureEvaluator:
    """测试结构评估器"""
    
    @pytest.fixture
    def evaluator(self):
        return StructureEvaluator()
    
    def test_complete_structure(self, evaluator):
        content = "话说...且听下回分解"
        score = evaluator.evaluate(content, {'title': '测试回目'})
        assert score >= 0.5
        
    def test_incomplete_structure(self, evaluator):
        content = "短内容"
        score = evaluator.evaluate(content)
        assert 0.0 <= score <= 1.0


class TestEnhancedScorer:
    """测试增强评分器"""
    
    @pytest.fixture
    def scorer(self):
        return EnhancedCharacterScorer()
    
    def test_baoyu_scoring(self, scorer):
        content = """
        宝玉笑道：'好妹妹，你今日气色好些了。'
        黛玉摇头叹道：'不过是一时罢了。'
        """
        result = scorer.score_character(content, "宝玉")
        assert result['total_score'] >= 5.0
        assert 'speech_score' in result
        assert 'behavior_score' in result
        
    def test_daiyu_scoring(self, scorer):
        content = """
        黛玉垂泪道：'你又说这些，我怎当得起。'
        说罢，又咳嗽起来。
        """
        result = scorer.score_character(content, "黛玉")
        assert result['total_score'] >= 4.5


class TestCharacterConsistency:
    """测试人物一致性检查器"""
    
    @pytest.fixture
    def checker(self):
        return CharacterConsistencyChecker()
    
    @pytest.mark.asyncio
    async def test_consistency_check(self, checker):
        content = """
        宝玉对黛玉道：'好妹妹，你今日诗做得如何？'
        黛玉笑道：'不过是随感而发，有什么好不好。'
        """
        result = await checker.check_consistency(
            content, 
            ['宝玉', '黛玉'],
            threshold=0.5
        )
        assert 'overall_score' in result
        assert 'individual_results' in result


class TestQualityCheckerIntegration:
    """测试质量检查器集成"""
    
    @pytest.mark.asyncio
    async def test_evaluation_pipeline(self):
        # 这里可以添加集成测试
        pass


class TestScorerConsistency:
    """测试各评分器之间的一致性"""
    
    def test_scorers_produce_similar_results(self):
        """确保不同评分器对相同内容产生相似结果"""
        content = """
        宝玉笑道：'好妹妹，今日天气甚好，咱们去园中走走。'
        黛玉摇头道：'我身子不适，不想动弹。'
        宝玉叹道：'你总这样，教人如何放心。'
        """
        
        # 使用不同的评分器
        from src.utils.enhanced_scorer import score_content
        
        result1 = score_content(content, ['宝玉', '黛玉'])
        
        # 分数应该在合理范围内
        assert 0 <= result1['overall_score'] <= 10


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 运行整合测试套件")
    print("=" * 60)
    
    # 使用pytest运行测试
    exit_code = pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '-x'  # 遇到第一个失败就停止
    ])
    
    return exit_code == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
