#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理类
负责读取和解析settings.yaml配置文件
"""

import os
from pathlib import Path
from typing import Dict, Any
import yaml
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv


@dataclass
class AgentConfig:
    """Agent配置"""
    name: str
    model: str
    temperature: float
    max_tokens: int


@dataclass
class QualityConfig:
    """质量评估配置"""
    style_weight: float
    character_weight: float
    plot_weight: float
    literary_weight: float
    min_score_threshold: float


@dataclass
class Settings:
    """主配置类"""
    # 项目基本信息
    project_name: str = "AI续写红楼梦"
    project_version: str = "1.0.0"

    # ADK配置
    adk_enabled: bool = True
    model_provider: str = "openai"
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    context_window: int = 100000

    # Agent配置
    agents: Dict[str, AgentConfig] = field(default_factory=dict)

    # 数据配置
    source_file: str = "data/raw/hongloumeng_80.md"
    processed_dir: str = "data/processed"
    knowledge_base: str = "data/knowledge_base.db"

    # 模型配置
    model_name: str = "gpt-5-chat-0807-global"
    temperature: float = 0.8
    max_length: int = 100000

    # 生成配置
    chapters_to_generate: int = 40
    words_per_chapter: int = 2500
    literary_requirements: str = "古风文学风格、文辞优雅、人物性格一致"

    # 质量配置
    quality: QualityConfig = None

    # 系统配置
    debug_mode: bool = False
    log_level: str = "INFO"
    max_retries: int = 3
    timeout_seconds: int = 300

    def __post_init__(self):
        """初始化后处理"""
        self.load_environment_variables()
        self.load_from_file()

    def load_environment_variables(self):
        """从环境变量和.env文件加载配置"""
        try:
            # 尝试加载.env文件
            project_root = Path(__file__).parent.parent.parent
            env_path = project_root / "config" / ".env"
            if env_path.exists():
                load_dotenv(env_path)
                print(f"✅ 已加载配置文件: {env_path}")
            else:
                print(f"⚠️ 配置文件不存在: {env_path}")
                print("请创建 config/.env 文件并配置 OPENAI_API_KEY 和 OPENAI_BASE_URL")
        except Exception as e:
            print(f"加载环境变量失败: {e}")

        # 从环境变量读取OpenAI配置
        api_key = os.getenv('OPENAI_API_KEY')
        base_url = os.getenv('OPENAI_BASE_URL')

        if api_key:
            self.api_key = api_key
            print("✅ 已读取 OPENAI_API_KEY")
        else:
            print("⚠️ 未找到 OPENAI_API_KEY 环境变量")

        if base_url:
            self.base_url = base_url
            print("✅ 已读取 OPENAI_BASE_URL")
        else:
            print("⚠️ 未找到 OPENAI_BASE_URL 环境变量")

        # 从环境变量读取其他配置
        debug_mode_str = os.getenv('DEBUG_MODE', str(self.debug_mode))
        self.debug_mode = debug_mode_str.lower() == 'true'

        log_level = os.getenv('LOG_LEVEL')
        if log_level:
            self.log_level = log_level

    def load_from_file(self, config_path: Optional[str] = None):
        """从YAML文件加载配置"""
        if config_path is None:
            # 默认配置文件路径
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "settings.yaml"

        if not Path(config_path).exists():
            # 如果配置文件不存在，使用默认配置
            self._set_defaults()
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            # 解析项目信息
            if 'project' in config_data:
                self.project_name = config_data['project'].get('name', self.project_name)
                self.project_version = config_data['project'].get('version', self.project_version)

            # 解析ADK配置
            if 'adk' in config_data:
                adk_config = config_data['adk']
                self.adk_enabled = adk_config.get('enabled', self.adk_enabled)
                self.model_provider = adk_config.get('model_provider', self.model_provider)
                self.base_url = adk_config.get('base_url', self.base_url)
                self.api_key = adk_config.get('api_key', self.api_key)
                self.context_window = adk_config.get('context_window', self.context_window)

            # 解析Agent配置
            if 'agents' in config_data:
                for agent_key, agent_data in config_data['agents'].items():
                    agent_config = AgentConfig(
                        name=agent_data.get('name', agent_key),
                        model=agent_data.get('model', 'gpt-5-chat-0807-global'),
                        temperature=agent_data.get('temperature', 0.7),
                        max_tokens=agent_data.get('max_tokens', 2000)
                    )
                    self.agents[agent_key] = agent_config

            # 解析数据配置
            if 'data' in config_data:
                data_config = config_data['data']
                self.source_file = data_config.get('source_file', self.source_file)
                self.processed_dir = data_config.get('processed_dir', self.processed_dir)
                self.knowledge_base = data_config.get('knowledge_base', self.knowledge_base)

            # 解析模型配置
            if 'model' in config_data:
                model_config = config_data['model']
                self.model_name = model_config.get('model_name', self.model_name)
                self.temperature = model_config.get('temperature', self.temperature)
                self.max_length = model_config.get('max_length', self.max_length)

            # 解析生成配置
            if 'generation' in config_data:
                gen_config = config_data['generation']
                self.chapters_to_generate = gen_config.get('chapters_to_generate', self.chapters_to_generate)
                self.words_per_chapter = gen_config.get('words_per_chapter', self.words_per_chapter)
                self.literary_requirements = gen_config.get('literary_requirements', self.literary_requirements)

            # 解析质量配置
            if 'quality' in config_data:
                quality_config = config_data['quality']
                self.quality = QualityConfig(
                    style_weight=quality_config.get('style_weight', 0.3),
                    character_weight=quality_config.get('character_weight', 0.3),
                    plot_weight=quality_config.get('plot_weight', 0.25),
                    literary_weight=quality_config.get('literary_weight', 0.15),
                    min_score_threshold=quality_config.get('min_score_threshold', 7.0)
                )
            else:
                self.quality = QualityConfig(0.3, 0.3, 0.25, 0.15, 7.0)

            # 解析系统配置
            if 'system' in config_data:
                sys_config = config_data['system']
                self.debug_mode = sys_config.get('debug_mode', self.debug_mode)
                self.log_level = sys_config.get('log_level', self.log_level)
                self.max_retries = sys_config.get('max_retries', self.max_retries)
                self.timeout_seconds = sys_config.get('timeout_seconds', self.timeout_seconds)

        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self._set_defaults()

    def _set_defaults(self):
        """设置默认配置"""
        # 默认Agent配置
        self.agents = {
            'data_processor': AgentConfig('数据预处理Agent', 'gpt-5-chat-0807-global', 0.3, 2000),
            'strategy_planner': AgentConfig('续写策略Agent', 'gpt-5-chat-0807-global', 0.7, 4000),
            'content_generator': AgentConfig('内容生成Agent', 'gpt-5-chat-0807-global', 0.8, 8000),
            'quality_checker': AgentConfig('质量校验Agent', 'gpt-5-chat-0807-global', 0.4, 3000),
            'user_interface': AgentConfig('用户交互Agent', 'gpt-5-chat-0807-global', 0.6, 2000)
        }

        # 默认质量配置
        self.quality = QualityConfig(0.3, 0.3, 0.25, 0.15, 7.0)

    def save_to_file(self, config_path: Optional[str] = None):
        """保存配置到文件"""
        if config_path is None:
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "settings.yaml"

        # 将配置对象转换为字典
        config_dict = {
            'project': {
                'name': self.project_name,
                'version': self.project_version
            },
            'adk': {
                'enabled': self.adk_enabled,
                'model_provider': self.model_provider,
                'base_url': self.base_url,
                'api_key': self.api_key,
                'context_window': self.context_window
            },
            'agents': {
                key: {
                    'name': agent.name,
                    'model': agent.model,
                    'temperature': agent.temperature,
                    'max_tokens': agent.max_tokens
                }
                for key, agent in self.agents.items()
            },
            'data': {
                'source_file': self.source_file,
                'processed_dir': self.processed_dir,
                'knowledge_base': self.knowledge_base
            },
            'model': {
                'model_name': self.model_name,
                'temperature': self.temperature,
                'max_length': self.max_length
            },
            'generation': {
                'chapters_to_generate': self.chapters_to_generate,
                'words_per_chapter': self.words_per_chapter,
                'literary_requirements': self.literary_requirements
            },
            'quality': {
                'style_weight': self.quality.style_weight,
                'character_weight': self.quality.character_weight,
                'plot_weight': self.quality.plot_weight,
                'literary_weight': self.quality.literary_weight,
                'min_score_threshold': self.quality.min_score_threshold
            },
            'system': {
                'debug_mode': self.debug_mode,
                'log_level': self.log_level,
                'max_retries': self.max_retries,
                'timeout_seconds': self.timeout_seconds
            }
        }

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def get_agent_config(self, agent_key: str) -> Optional[AgentConfig]:
        """获取指定Agent的配置"""
        return self.agents.get(agent_key)

    def validate_config(self) -> list[str]:
        """验证配置的完整性"""
        errors = []

        # 检查必需的配置项
        if not self.adk_enabled:
            errors.append("ADK必须启用")

        if not self.api_key:
            errors.append("API密钥未配置")

        if not self.agents:
            errors.append("Agent配置缺失")

        if not self.quality:
            errors.append("质量配置缺失")

        return errors
