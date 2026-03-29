from __future__ import annotations
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Dict, List, Optional


CANONICAL_CHARACTER_PROFILES: Dict[str, Dict[str, object]] = {
    "贾宝玉": {
        "aliases": ["宝玉"],
        "性格": "纯真敏感，厌恶仕途经济，重情而多思",
        "现状": "身在贾府繁华之中，却渐觉家道与人情皆有衰飒之意",
        "发展方向": "由情入悟，在家族崩解与人生幻灭中走向精神脱身",
        "description": "贾府公子，通灵宝玉主人公，情感与命运的核心人物。",
    },
    "林黛玉": {
        "aliases": ["黛玉", "颦儿", "林姑娘"],
        "性格": "聪慧敏感，孤高真挚，才情出众而多愁",
        "现状": "寄居贾府，体弱多病，与宝玉情深而处境脆弱",
        "发展方向": "在爱情与身世压力中坚守真性情，命运愈发凄婉",
        "description": "林如海与贾敏之女，诗心最盛，与宝玉感情最深。",
    },
    "薛宝钗": {
        "aliases": ["宝钗", "宝姐姐"],
        "性格": "端庄稳重，通达世情，温厚含蓄",
        "现状": "随母居于贾府，深得长辈赏识，与宝玉婚姻线若隐若现",
        "发展方向": "在礼法与情感夹缝中维持体面，也承受命运反噬",
        "description": "薛家小姐，处事圆融，是贾府婚配格局中的关键人物。",
    },
    "王熙凤": {
        "aliases": ["凤姐", "熙凤", "凤丫头"],
        "性格": "精明强干，泼辣机变，权术与手腕兼具",
        "现状": "掌理荣府事务，表面风光，实则内外交困",
        "发展方向": "在家族财政与权力旋涡中由盛转衰",
        "description": "贾琏之妻，荣府实际管家者，才干与悲剧性并存。",
    },
    "贾母": {
        "aliases": ["老太太", "老祖宗"],
        "性格": "慈威并重，老成练达，重亲情与体统",
        "现状": "为贾府精神核心，维系诸房人情与秩序",
        "发展方向": "随着家族衰败加深，其庇护之力日益有限",
        "description": "贾府最高长辈，众人依归所在。",
    },
    "贾探春": {
        "aliases": ["探春", "三姑娘"],
        "性格": "精明爽利，志气高远，颇有治家之才",
        "现状": "才识出众，却受庶出身份掣肘",
        "发展方向": "在家族倾颓中显示担当，终不免远嫁离散",
        "description": "贾府三小姐，才干与见识最强的年轻一辈之一。",
    },
    "史湘云": {
        "aliases": ["湘云", "云丫头"],
        "性格": "豪爽烂漫，旷达真诚，才思敏捷",
        "现状": "与贾府往来亲密，虽明朗却亦有寄人篱下之感",
        "发展方向": "以爽朗之姿映照群芳薄命，后运亦多波折",
        "description": "史家小姐，性情明快，与宝玉黛玉都极亲近。",
    },
    "袭人": {
        "aliases": ["花袭人"],
        "性格": "温柔周全，谨慎体贴，深谙规矩",
        "现状": "为宝玉房中大丫鬟，日常最亲近宝玉起居",
        "发展方向": "在情分与本分之间求存，最终难免随命运流转",
        "description": "宝玉身边最稳妥得力的丫鬟之一。",
    },
    "紫鹃": {
        "aliases": [],
        "性格": "忠心伶俐，细致体察，偏向黛玉",
        "现状": "随侍黛玉，最知其心事病情",
        "发展方向": "作为黛玉知己与照应者，承受其命运余波",
        "description": "黛玉贴身丫鬟，常为其情绪与处境周旋。",
    },
    "贾政": {
        "aliases": [],
        "性格": "严正守礼，重名教，望子成器",
        "现状": "身为家长，力图维持门第体统，对宝玉多不满",
        "发展方向": "在家运败落中愈加显出礼法无力",
        "description": "宝玉之父，封建父权与名教期待的代表。",
    },
    "王夫人": {
        "aliases": [],
        "性格": "持重严肃，信奉礼法，内里偏护己出",
        "现状": "在贾府内宅拥有极强影响力",
        "发展方向": "在危局中愈加收缩保守，也推动若干悲剧结果",
        "description": "宝玉之母，荣府核心长辈之一。",
    },
    "贾琏": {
        "aliases": ["琏二爷"],
        "性格": "风流世故，处事圆滑，担当不足",
        "现状": "周旋内外事务，婚姻与家务多生波澜",
        "发展方向": "随家族败势显露轻薄与无力",
        "description": "荣府二爷，王熙凤之夫。",
    },
    "平儿": {
        "aliases": [],
        "性格": "温和干练，通情达理，善于调停",
        "现状": "夹在凤姐与贾琏之间，操持大量琐务",
        "发展方向": "在纷乱人事中维持难得的清明与善意",
        "description": "凤姐心腹丫鬟，处事公道，深得众人好感。",
    },
    "鸳鸯": {
        "aliases": [],
        "性格": "刚直自守，忠诚果决，不肯苟从",
        "现状": "服侍贾母，地位特殊，常见识贾府深层矛盾",
        "发展方向": "在权势逼迫中守住人格与选择",
        "description": "贾母的大丫鬟，性情坚贞。",
    },
    "贾迎春": {
        "aliases": ["迎春", "二姑娘"],
        "性格": "懦弱温吞，逆来顺受",
        "现状": "在府中存在感较弱，缺乏自保之力",
        "发展方向": "在婚姻与家运安排中沦为牺牲品",
        "description": "贾府二小姐，命运最显柔弱受制。",
    },
    "贾惜春": {
        "aliases": ["惜春", "四姑娘"],
        "性格": "冷淡孤僻，清峭早熟，带出世之思",
        "现状": "年纪尚幼，却已对繁华与人情生出疏离感",
        "发展方向": "由冷眼旁观转向遁世离俗",
        "description": "贾府四小姐，性情最接近清冷出尘。",
    },
}


@dataclass
class CharacterProfile:
    name: str
    aliases: List[str] = field(default_factory=list)
    personality: str = ""
    current_state: str = ""
    development_direction: str = ""
    description: str = ""
    mention_count: int = 0

    def to_dict(self) -> Dict[str, object]:
        return {
            "aliases": self.aliases,
            "性格": self.personality,
            "现状": self.current_state,
            "发展方向": self.development_direction,
            "description": self.description,
            "mention_count": self.mention_count,
        }


class CharacterKnowledgeBase:
    """轻量人物知识库，提供稳定的人物画像与别名解析。"""

    def __init__(self, persist_path: str = "data/knowledge_base/characters/canonical.json"):
        self.persist_path = Path(persist_path)
        self._profiles: Dict[str, Dict[str, object]] = {}
        self._alias_to_name: Dict[str, str] = {}
        if self.persist_path.exists():
            self.load()

    def build_from_text(self, text: str) -> Dict[str, Dict[str, object]]:
        profiles: Dict[str, Dict[str, object]] = {}
        for name, seed in CANONICAL_CHARACTER_PROFILES.items():
            aliases = list(seed.get("aliases", []))
            mention_count = text.count(name) + sum(text.count(alias) for alias in aliases)
            if mention_count == 0:
                continue
            profile = CharacterProfile(
                name=name,
                aliases=aliases,
                personality=str(seed.get("性格", "")),
                current_state=str(seed.get("现状", "")),
                development_direction=str(seed.get("发展方向", "")),
                description=str(seed.get("description", "")),
                mention_count=mention_count,
            )
            profiles[name] = profile.to_dict()
        self._profiles = profiles
        self._rebuild_alias_index()
        return profiles

    def save(self) -> None:
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        self.persist_path.write_text(
            json.dumps(self._profiles, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load(self) -> Dict[str, Dict[str, object]]:
        self._profiles = json.loads(self.persist_path.read_text(encoding="utf-8"))
        self._rebuild_alias_index()
        return self._profiles

    def all(self) -> Dict[str, Dict[str, object]]:
        return dict(self._profiles)

    def get(self, name: str) -> Optional[Dict[str, object]]:
        canonical_name = self.resolve_name(name)
        if not canonical_name:
            return None
        return self._profiles.get(canonical_name)

    def resolve_name(self, name: str) -> Optional[str]:
        if name in self._profiles:
            return name
        return self._alias_to_name.get(name)

    def count(self) -> int:
        return len(self._profiles)

    def _rebuild_alias_index(self) -> None:
        alias_to_name: Dict[str, str] = {}
        for name, profile in self._profiles.items():
            for alias in profile.get("aliases", []):
                alias_to_name[str(alias)] = name
        self._alias_to_name = alias_to_name


def build_character_kb(
    source: str = "data/raw/hongloumeng_80.md",
    persist_path: str = "data/knowledge_base/characters/canonical.json",
) -> CharacterKnowledgeBase:
    text = Path(source).read_text(encoding="utf-8")
    kb = CharacterKnowledgeBase(persist_path=persist_path)
    kb.build_from_text(text)
    kb.save()
    return kb
