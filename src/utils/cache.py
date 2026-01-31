#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存工具类
用于缓存API调用结果和其他昂贵的计算操作
"""

import json
import hashlib
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Dict
from functools import wraps


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_dir: str = "output/cache", default_ttl: int = 3600):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录
            default_ttl: 默认生存时间（秒）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl
        
        # 内存缓存（短期缓存）
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
    
    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """生成缓存键"""
        # 创建包含函数名、参数的字符串
        cache_input = {
            'func_name': func_name,
            'args': args,
            'kwargs': {k: v for k, v in sorted(kwargs.items())}  # 排序确保一致性
        }
        
        # 使用JSON序列化并哈希
        serialized = json.dumps(cache_input, sort_keys=True, default=str)
        return hashlib.md5(serialized.encode()).hexdigest()
    
    def _is_expired(self, timestamp: datetime, ttl: int) -> bool:
        """检查缓存是否过期"""
        return datetime.now() > timestamp + timedelta(seconds=ttl)
    
    def get(self, key: str, ttl: Optional[int] = None) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            ttl: 生存时间（秒），None表示使用默认值
            
        Returns:
            缓存的值，如果不存在或已过期则返回None
        """
        ttl = ttl or self.default_ttl
        
        # 首先检查内存缓存
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if not self._is_expired(entry['timestamp'], entry['ttl']):
                return entry['value']
            else:
                del self.memory_cache[key]  # 删除过期项
        
        # 检查文件缓存
        cache_file = self.cache_dir / f"{key}.pickle"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    entry = pickle.load(f)
                
                if not self._is_expired(entry['timestamp'], entry['ttl']):
                    # 存入内存缓存
                    self.memory_cache[key] = entry
                    return entry['value']
                else:
                    cache_file.unlink()  # 删除过期文件
            except Exception:
                cache_file.unlink(missing_ok=True)  # 删除损坏的文件
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒），None表示使用默认值
        """
        ttl = ttl or self.default_ttl
        timestamp = datetime.now()
        
        # 存入内存缓存
        self.memory_cache[key] = {
            'value': value,
            'timestamp': timestamp,
            'ttl': ttl
        }
        
        # 存入文件缓存
        cache_file = self.cache_dir / f"{key}.pickle"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump({
                    'value': value,
                    'timestamp': timestamp,
                    'ttl': ttl
                }, f)
        except Exception as e:
            print(f"⚠️  缓存写入失败: {e}")
    
    def clear_expired(self) -> int:
        """清除过期的文件缓存，返回删除的文件数"""
        deleted_count = 0
        
        # 清除内存中的过期项
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if self._is_expired(entry['timestamp'], entry['ttl'])
        ]
        for key in expired_keys:
            del self.memory_cache[key]
        
        # 清除文件中的过期项
        for cache_file in self.cache_dir.glob("*.pickle"):
            try:
                with open(cache_file, 'rb') as f:
                    entry = pickle.load(f)
                
                if self._is_expired(entry['timestamp'], entry['ttl']):
                    cache_file.unlink()
                    deleted_count += 1
            except Exception:
                cache_file.unlink(missing_ok=True)
        
        return deleted_count
    
    def clear_all(self) -> None:
        """清除所有缓存"""
        self.memory_cache.clear()
        
        for cache_file in self.cache_dir.glob("*.pickle"):
            cache_file.unlink()


# 全局缓存实例
_cache_manager = CacheManager()


def cached(ttl: Optional[int] = None, cache_params: bool = True):
    """
    缓存装饰器
    
    Args:
        ttl: 生存时间（秒），None表示使用默认值
        cache_params: 是否根据参数区分缓存
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not cache_params:
                key = f"{func.__module__}.{func.__name__}_default"
            else:
                key = _cache_manager._generate_cache_key(
                    f"{func.__module__}.{func.__name__}", args[1:], kwargs  # 排除self参数
                )
            
            # 尝试获取缓存
            cached_result = _cache_manager.get(key, ttl)
            if cached_result is not None:
                print(f"🎯 [CACHE] 命中缓存: {func.__name__}")
                return cached_result
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            _cache_manager.set(key, result, ttl)
            print(f"💾 [CACHE] 缓存结果: {func.__name__}")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not cache_params:
                key = f"{func.__module__}.{func.__name__}_default"
            else:
                key = _cache_manager._generate_cache_key(
                    f"{func.__module__}.{func.__name__}", args[1:], kwargs  # 排除self参数
                )
            
            # 尝试获取缓存
            cached_result = _cache_manager.get(key, ttl)
            if cached_result is not None:
                print(f"🎯 [CACHE] 命中缓存: {func.__name__}")
                return cached_result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            _cache_manager.set(key, result, ttl)
            print(f"💾 [CACHE] 缓存结果: {func.__name__}")
            
            return result
        
        # 根据函数是否异步返回相应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 为了使用asyncio.iscoroutinefunction，我们需要导入它
import asyncio