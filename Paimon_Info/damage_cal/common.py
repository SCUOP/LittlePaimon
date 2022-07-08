from pathlib import Path
from typing import Tuple, Dict, Optional, List, Union
from ...utils.enka_util import get_artifact_suit
from PIL import Image, ImageDraw
from littlepaimon_utils.files import load_image, load_json
from littlepaimon_utils.images import get_font, draw_center_text

text_font = str(Path() / 'resources' / 'LittlePaimon' / 'hywh.ttf')
number_font = str(Path() / 'resources' / 'LittlePaimon' / 'number.ttf')


def udc(dm: float,
        crit: Tuple[float, float],
        db: float,
        sl: int,
        rcb: Optional[float] = 0.1,
        rcd: Optional[float] = 0,
        el: Optional[int] = 90,
        dcr: Optional[float] = 0,
        dci: Optional[float] = 0,
        r: Optional[float] = 1,
        ) -> List[str]:
    """
    计算伤害
    :param dm: 倍率区
    :param crit: 暴击区
    :param db: 增伤区
    :param sl: 角色等级
    :param rcb: 怪物基础抗性
    :param rcd: 抗性减少
    :param el: 怪物等级
    :param dcr: 抗性系数减少
    :param dci: 无视防御系数
    :param r: 反应最终系数
    :return: 伤害
    """
    if crit[0] > 1:
        damage = dm * (1 + crit[1]) * (1 + db) * resistance_coefficient(rcb, rcd) * defense_coefficient(sl, el, dcr, dci) * r
        return [str(int(damage)), str(int(damage))]
    else:
        damage = dm * (1 + crit[0] * crit[1]) * (1 + db) * resistance_coefficient(rcb, rcd) * defense_coefficient(sl, el, dcr, dci) * r
        return [str(int(damage)), str(int(damage / (1 + crit[0] * crit[1]) * (1 + crit[1])))]


def resistance_coefficient(base_resistance: float = 0.1, reduction_rate: float = 0):
    """
    计算抗性系数
    :param base_resistance: 怪物基础抗性
    :param reduction_rate: 减抗系数
    :return: 抗性系数
    """
    resistance = base_resistance - reduction_rate
    if resistance > 0.75:
        return 1 / (1 + 4 * resistance)
    elif 0 <= resistance < 0.75:
        return 1 - resistance
    else:
        return 1 - (resistance / 2)


def defense_coefficient(self_level: int = 90, enemy_level: int = 90, reduction_rate: float = 0, ignore: float = 0):
    """
    计算防御力系数
    :param self_level: 角色自身等级
    :param enemy_level: 怪物等级
    :param reduction_rate: 减防系数
    :param ignore: 无视防御系数
    :return: 防御力系数
    """
    return (self_level + 100) / ((self_level + 100) + (enemy_level + 100) * (1 - reduction_rate) * (1 - ignore))


def growth_reaction(mastery: int = 0, base_coefficient: float = 1.5, extra_coefficient: float = 0):
    """
    计算增幅反应的系数
    :param mastery: 元素精通
    :param base_coefficient: 基础系数，如蒸发为1.5， 融化为2
    :param extra_coefficient: 反应系数提高，如魔女4件套效果
    :return: 增幅系数
    """
    mastery_increase = (2.78 * mastery) / (mastery + 1400)
    return base_coefficient * (1 + mastery_increase + extra_coefficient)


def upheaval_reaction(level: int, type: str, mastery: int = 0, extra_coefficient: float = 0, resistance: float = 0.9):
    """
    计算剧变反应的伤害
    :param level: 等级
    :param type: 反应类型
    :param mastery: 元素精通
    :param extra_coefficient: 反应系数提高，如如雷4件套效果
    :param resistance: 怪物抗性系数
    :return: 剧变伤害
    """
    if type == '超导':
        base_ratio = 1
    elif type == '扩散':
        base_ratio = 1.2
    elif type == '碎冰':
        base_ratio = 3
    elif type == '超载':
        base_ratio = 4
    else:
        base_ratio = 4.8
    base_coefficient = 723  # 暂缺全等级剧变反应的系数，先写90级的
    mastery_increase = (16 * mastery) / (mastery + 2000)
    return base_coefficient * base_ratio * (1 + mastery_increase + extra_coefficient) * resistance


def weapon_common_fix(data: dict):
    """
    对武器的通用面板属性修正
    :param data: 角色数据
    :return: 角色数据
    """
    attr = data['属性']
    weapon = data['武器']
    # 针对q的额外属性
    extra_q = {
        '暴击率': 0,
        '增伤':  0
    }
    # 针对e的额外属性
    extra_e = {
        '暴击率':  0,
        '增伤':   0,
        '额外倍率': 0
    }
    # 针对a的额外属性
    extra_a = {
        '普攻暴击率':    0,
        '普攻增伤':     0,
        '普攻额外倍率':   0,
        '重击暴击率':    0,
        '重击增伤':     0,
        '重击额外倍率':   0,
        '下落攻击暴击率':  0,
        '下落攻击增伤':   0,
        '下落攻击额外倍率': 0
    }
    # 单手剑
    if weapon['名称'] == '波乱月白经津':
        for i, k in enumerate(attr['伤害加成']):
            attr['伤害加成'][i] = k + (0.09 + 0.03 * weapon['精炼等级'])
        extra_a['普攻增伤'] += 2 * (0.15 + 0.05 * weapon['精炼等级'])
        data['伤害描述'].append('波乱满层')
    elif weapon['名称'] == '辰砂之纺锤':
        extra_e['额外倍率'] += (attr['基础防御'] + attr['额外防御']) * (0.3 + 0.1 * weapon['精炼等级'])
    elif weapon['名称'] == '腐殖之剑':
        extra_e['增伤'] += 0.12 + 0.04 * weapon['精炼等级']
        extra_e['暴击率'] += 0.045 + 0.015 * weapon['精炼等级']
    elif weapon['名称'] == '苍古自由之誓':
        for i, k in enumerate(attr['伤害加成']):
            attr['伤害加成'][i] = k + (0.075 + 0.025 * weapon['精炼等级'])
        data['额外攻击'] += data['基础攻击'] * (0.15 + 0.05 * weapon['精炼等级'])
        extra_a['普攻增伤'] += 0.12 + 0.04 * weapon['精炼等级']
        extra_a['重击增伤'] += 0.12 + 0.04 * weapon['精炼等级']
        extra_a['下落攻击增伤'] += 0.12 + 0.04 * weapon['精炼等级']
        data['伤害描述'].append('苍古触发')
    elif weapon['名称'] == '雾切之回光':
        # TODO 吃不满3层的角色
        for i, k in enumerate(attr['伤害加成']):
            attr['伤害加成'][i] = k + (0.3 + 0.1 * weapon['精炼等级'])
        data['伤害描述'].append('雾切满层')
    elif weapon['名称'] == '铁蜂刺':
        for i, k in enumerate(attr['伤害加成']):
            attr['伤害加成'][i] = k + 2 * (0.045 + 0.015 * weapon['精炼等级'])
        data['伤害描述'].append('铁蜂刺满层')
    elif weapon['名称'] == '黑岩长剑':
        attr['额外攻击'] += attr['基础攻击'] * (0.09 + 0.03 * weapon['精炼等级'])
        data['伤害描述'].append('黑岩1层')
    elif weapon['名称'] in ['暗巷闪光', '冷刃']:
        for i, k in enumerate(attr['伤害加成']):
            attr['伤害加成'][i] = k + (0.09 + 0.03 * weapon['精炼等级'])
    elif weapon['名称'] == '飞天大御剑':
        attr['额外攻击'] += attr['基础攻击'] * (0.09 + 0.03 * weapon['精炼等级'])
    elif weapon['名称'] == '黎明神剑':
        attr['暴击率'] += 0.115 + 0.025 * weapon['精炼等级']
    elif weapon['名称'] == '暗铁剑':
        attr['额外攻击'] += attr['基础攻击'] * (0.15 + 0.05 * weapon['精炼等级'])
    elif weapon['名称'] == '黑剑':
        extra_a['普攻增伤'] += 0.15 + 0.05 * weapon['精炼等级']
        extra_a['重击增伤'] += 0.15 + 0.05 * weapon['精炼等级']
    elif weapon['名称'] == '铁影阔剑':
        extra_a['重击增伤'] += 0.25 + 0.05 * weapon['精炼等级']

    # 双手剑
    elif weapon['名称'] == '赤角石溃杵':
        extra_a['普攻额外倍率'] += (attr['基础防御'] + attr['额外防御']) * (0.3 + 0.1 * weapon['精炼等级'])
    elif weapon['名称'] == '松籁响起之时':
        attr['额外攻击'] += attr['基础攻击'] * (0.09 + 0.03 * weapon['精炼等级'])
        data['伤害描述'].append('松籁触发')
    elif weapon['名称'] == '狼的末路':
        attr['额外攻击'] += attr['基础攻击'] * (0.3 + 0.1 * weapon['精炼等级'])
        data['伤害描述'].append('狼末触发')
    elif weapon['名称'] == '天空之傲':
        for i, k in enumerate(attr['伤害加成']):
            attr['伤害加成'][i] = k + (0.06 + 0.02 * weapon['精炼等级'])
    elif weapon['名称'] == '钟剑':
        for i, k in enumerate(attr['伤害加成']):
            attr['伤害加成'][i] = k + (0.09 + 0.03 * weapon['精炼等级'])
        data['伤害描述'].append('钟剑触发')
    elif weapon['名称'] == '白影剑':
        attr['额外攻击'] += attr['基础攻击'] * 4 * (0.045 + 0.015 * weapon['精炼等级'])
        attr['额外防御'] += attr['基础防御'] * 4 * (0.045 + 0.015 * weapon['精炼等级'])
        data['伤害描述'].append('白影剑满层')
    elif weapon['名称'] == '螭骨剑':
        for i, k in enumerate(attr['伤害加成']):
            attr['伤害加成'][i] = k + 5 * (0.05 + 0.01 * weapon['精炼等级'])
        data['伤害描述'].append('螭骨满层')
    elif weapon['名称'] in ['沐浴龙血的剑', '鸦羽弓', '魔导绪论']:
        for i, k in enumerate(attr['伤害加成']):
            attr['伤害加成'][i] = k + (0.09 + 0.03 * weapon['精炼等级'])
    elif weapon['名称'] == '飞天大御剑':
        attr['额外攻击'] += attr['基础攻击'] * 4 * (0.05 + 0.01 * weapon['精炼等级'])
        data['伤害描述'].append('白影剑满层')
    elif weapon['名称'] == '衔珠海皇':
        extra_q['增伤'] += 0.09 + 0.03 * weapon['精炼等级']
    elif weapon['名称'] == '桂木斩长正':
        extra_e['增伤'] += 0.045 + 0.015 * weapon['精炼等级']
    # 弓
    elif weapon['名称'] == '落霞':
        for i, k in enumerate(attr['伤害加成']):
            attr['伤害加成'][i] = k + (0.115 + 0.025 * weapon['精炼等级'])
        data['伤害描述'].append('落霞最高层')
    elif weapon['名称'] == '若水':
        for i, k in enumerate(attr['伤害加成']):
            attr['伤害加成'][i] = k + (0.15 + 0.05 * weapon['精炼等级'])
    elif weapon['名称'] == '终末嗟叹之诗':
        attr['额外攻击'] += attr['基础攻击'] * (0.15 + 0.05 * weapon['精炼等级'])
        attr['元素精通'] += 75 + 25 * weapon['精炼等级']
        data['伤害描述'].append('终末触发')
    elif weapon['名称'] == '冬极白星':
        attr['额外攻击'] += attr['基础攻击'] * (0.36 + 0.12 * weapon['精炼等级'])
        extra_q['增伤'] += 0.09 + 0.03 * weapon['精炼等级']
        extra_e['增伤'] += 0.09 + 0.03 * weapon['精炼等级']
        data['伤害描述'].append('冬极满层')
    elif weapon['名称'] == '试作澹月':
        attr['额外攻击'] += attr['基础攻击'] * (0.27 + 0.09 * weapon['精炼等级'])
        data['伤害描述'].append('试作触发')
    elif weapon['名称'] == '钢轮弓':
        attr['额外攻击'] += attr['基础攻击'] * 4 * (0.03 + 0.01 * weapon['精炼等级'])
        data['伤害描述'].append('钢轮弓满层')
    elif weapon['名称'] == '暗巷猎手':
        for i, k in enumerate(attr['伤害加成']):
            attr['伤害加成'][i] = k + 5 * (0.015 + 0.005 * weapon['精炼等级'])
        data['伤害描述'].append('暗巷猎手5层')
    elif weapon['名称'] == '风花之颂':
        attr['额外攻击'] += attr['基础攻击'] * (0.12 + 0.04 * weapon['精炼等级'])
        data['伤害描述'].append('风花触发')
    elif weapon['名称'] == '绝弦':
        extra_q['增伤'] += 0.18 + 0.06 * weapon['精炼等级']
        extra_e['增伤'] += 0.18 + 0.06 * weapon['精炼等级']
    elif weapon['名称'] == '幽夜华尔兹':
        extra_e['增伤'] += 0.15 + 0.05 * weapon['精炼等级']
        extra_a['普攻增伤'] += 0.15 + 0.05 * weapon['精炼等级']
    elif weapon['名称'] == '掠食者':
        extra_a['普攻增伤'] += 0.1
        extra_a['重击增伤'] += 0.1
    elif weapon['名称'] == '飞雷之弦振':
        extra_a['普攻增伤'] += 0.3 + 0.1 * weapon['精炼等级']
        data['伤害描述'].append('飞雷满层')
    elif weapon['名称'] == '破魔之弓':
        extra_a['普攻增伤'] += 0.24 + 0.08 * weapon['精炼等级']
        extra_a['重击增伤'] += 0.18 + 0.06 * weapon['精炼等级']
        data['伤害描述'].append('破魔满能量')
    elif weapon['名称'] == '阿莫斯之弓':
        extra_a['普攻增伤'] += 0.39 + 0.13 * weapon['精炼等级']
        extra_a['重击增伤'] += 0.39 + 0.13 * weapon['精炼等级']
        data['伤害描述'].append('阿莫斯满层')
    elif weapon['名称'] == '弓藏':
        extra_a['普攻增伤'] += 0.3 + 0.1 * weapon['精炼等级']
        extra_a['重击增伤'] -= 0.1
    elif weapon['名称'] == '弹弓':
        extra_a['普攻增伤'] += 0.3 + 0.06 * weapon['精炼等级']
        extra_a['重击增伤'] += 0.3 + 0.06 * weapon['精炼等级']

    # 长柄武器
    elif weapon['名称'] == '白缨枪':
        extra_a['普攻增伤'] += 0.18 + 0.06 * weapon['精炼等级']
    elif weapon['名称'] == '护摩之杖':
        attr['额外攻击'] += (attr['基础生命'] + attr['额外生命']) * (0.008 + 0.002 * weapon['精炼等级'])
        if '半血以下' not in data['伤害描述']:
            data['伤害描述'].append('半血以下')
    elif weapon['名称'] == '和璞鸢':
        attr['额外攻击'] += attr['基础攻击'] * 7 * (0.025 + 0.007 * weapon['精炼等级'])
        for i, k in enumerate(attr['伤害加成']):
            attr['伤害加成'][i] = k + (0.09 + 0.03 * weapon['精炼等级'])
        data['伤害描述'].append('和璞鸢满层')
    elif weapon['名称'] == '决斗之枪':
        attr['额外攻击'] += attr['基础攻击'] * 0.18 + 0.06 * weapon['精炼等级']
        data['伤害描述'].append('决斗单怪')
    elif weapon['名称'] == '息灾':
        for i, k in enumerate(attr['伤害加成']):
            attr['伤害加成'][i] = k + (0.09 + 0.03 * weapon['精炼等级'])
        attr['额外攻击'] += attr['基础攻击'] * 6 * (0.024 + 0.006 * weapon['精炼等级'])
        data['伤害描述'].append('息灾前台满层')
    elif weapon['名称'] == '薙草之稻光':
        attr['额外攻击'] += attr['基础攻击'] * (attr['元素充能效率'] - 1) * (0.21 + 0.07 * weapon['精炼等级'])
        attr['元素充能效率'] += 0.25 + 0.05 * weapon['精炼等级']
    elif weapon['名称'] == '「渔获」':
        extra_q['增伤'] += 0.12 + 0.04 * weapon['精炼等级']
        extra_q['暴击率'] += 0.045 + 0.015 * weapon['精炼等级']
    # 法器
    elif weapon['名称'] == '证誓之明瞳':
        attr['元素充能效率'] += 0.18 + 0.06 * weapon['精炼等级']
    elif weapon['名称'] == '神乐之真意':
        for i, k in enumerate(attr['伤害加成']):
            attr['伤害加成'][i] = k + (0.09 + 0.03 * weapon['精炼等级'])
        extra_e['增伤'] += 3 * (0.09 + 0.03 * weapon['精炼等级'])
        data['伤害描述'].append('神乐满层')
    elif weapon['名称'] == '白辰之环':
        for i, k in enumerate(attr['伤害加成']):
            attr['伤害加成'][i] = k + (0.075 + 0.025 * weapon['精炼等级'])
        data['伤害描述'].append('白辰触发')
    elif weapon['名称'] == '天空之卷':
        for i, k in enumerate(attr['伤害加成']):
            attr['伤害加成'][i] = k + (0.09 + 0.03 * weapon['精炼等级'])
    elif weapon['名称'] == '四风原典':
        for i, k in enumerate(attr['伤害加成']):
            attr['伤害加成'][i] = k + 4 * (0.06 + 0.02 * weapon['精炼等级'])
        data['伤害描述'].append('四风满层')
    elif weapon['名称'] == '流浪乐章':
        for i, k in enumerate(attr['伤害加成']):
            attr['伤害加成'][i] = k + (0.36 + 0.12 * weapon['精炼等级'])
        data['伤害描述'].append('流浪触发增伤')
    elif weapon['名称'] == '万国诸海图谱':
        for i, k in enumerate(attr['伤害加成']):
            attr['伤害加成'][i] = k + 2 * (0.06 + 0.02 * weapon['精炼等级'])
        data['伤害描述'].append('万国满层')
    elif weapon['名称'] == '暗巷的酒与诗':
        attr['额外攻击'] += attr['基础攻击'] * (0.15 + 0.05 * weapon['精炼等级'])
        data['伤害描述'].append('暗巷触发')
    elif weapon['名称'] == '嘟嘟可故事集':
        attr['额外攻击'] += attr['基础攻击'] * (0.06 + 0.02 * weapon['精炼等级'])
        extra_a['重击增伤'] += 0.12 + 0.04 * weapon['精炼等级']
    elif weapon['名称'] == '翡玉法球':
        attr['额外攻击'] += attr['基础攻击'] * (0.15 + 0.05 * weapon['精炼等级'])
        data['伤害描述'].append('翡玉触发')
    elif weapon['名称'] == '匣里日月':
        extra_q['增伤'] += 0.15 + 0.05 * weapon['精炼等级']
        extra_e['增伤'] += 0.15 + 0.05 * weapon['精炼等级']
        extra_a['普攻增伤'] += 0.15 + 0.05 * weapon['精炼等级']

    # 系列武器
    elif weapon['名称'].startswith('千岩'):
        attr['暴击率'] += (0.02 + 0.01 * weapon['精炼等级'])
        attr['额外攻击'] += attr['基础攻击'] * (0.06 + 0.01 * weapon['精炼等级'])
        data['伤害描述'].append('璃月人1层')
    elif weapon['名称'] in ['匣里灭辰', '匣里龙吟', '雨裁']:
        for i, k in enumerate(attr['伤害加成']):
            attr['伤害加成'][i] = k + (0.16 + 0.04 * weapon['精炼等级'])
        data['伤害描述'].append(f'{weapon["名称"][:2]}触发')
    elif weapon['名称'].startswith('黑岩'):
        attr['额外攻击'] += attr['基础攻击'] * (0.09 + 0.03 * weapon['精炼等级'])
        data['伤害描述'].append('黑岩1层')
    elif weapon['名称'] in ['贯虹之槊', '斫峰之刃', '尘世之锁', '无工之剑']:
        attr['额外攻击'] += attr['基础攻击'] * 2 * 5 * (0.003 + 0.001 * weapon['精炼等级'])
        attr['护盾强效'] += 0.15 + 0.05 * weapon['精炼等级']
        data['伤害描述'].append('武器带盾满层')
    elif weapon['名称'] in ['断浪长鳍', '恶王丸', '朦云之月']:
        extra_q['增伤'] += (0.0009 + 0.0003 * weapon['精炼等级']) * 240
        data['伤害描述'].append('武器被动算240能量')

    data['属性'] = attr
    return data, extra_q, extra_e, extra_a


def common_fix(data: dict):
    """
    对武器、圣遗物的通用面板属性修正
    :param data: 角色数据
    :return: 角色数据
    """
    if '伤害描述' not in data:
        data['伤害描述'] = []
    if '护盾强效' not in data['属性']:
        data['属性']['护盾强效'] = 0
    data, extra_q, extra_e, extra_a = weapon_common_fix(data)
    artifacts = data['圣遗物']
    attr = data['属性']
    weapon = data['武器']
    suit = get_artifact_suit(artifacts)
    # 两件套的情况
    if '逆飞的流星' in suit:
        attr['护盾强效'] += 0.35
    if '昔日宗室之仪' in suit:
        extra_q['增伤'] += 0.2
    if '赌徒' in suit:
        extra_e['增伤'] += 0.2
    if '武人' in suit:
        extra_a['普攻增伤'] += 0.15
        extra_a['重击增伤'] += 0.15
    if len(suit) == 2:
        # 四件套的情况
        if suit[0][0] == suit[1][0]:
            if suit[0][0] == '绝缘之旗印':
                extra_q['增伤'] += 0.25 * attr['元素充能效率']
            if suit[0][0] == '苍白之火':
                attr['额外攻击'] += attr['基础攻击'] * 0.18
                attr['伤害加成'][0] += 0.25
                data['伤害描述'].append('苍白满层')
            elif suit[0][0] == '华馆梦醒形骸记':
                attr['伤害加成'][6] += 0.24
                attr['额外防御'] += attr['基础防御'] * 0.24
                data['伤害描述'].append('华馆满层')
            elif suit[0][0] == '千岩牢固':
                attr['护盾强效'] += 0.3
                attr['额外攻击'] += attr['基础攻击'] * 0.2
                data['伤害描述'].append('千岩触发')
            elif suit[0][0] == '昔日宗室之仪':
                attr['额外攻击'] += attr['基础攻击'] * 0.2
                data['伤害描述'].append('宗室触发')
            elif suit[0][0] == '冰风迷途的勇士':
                attr['暴击率'] += 0.2
                data['伤害描述'].append('冰套暴击20%')
            elif suit[0][0] == '勇士之心':
                for i, k in enumerate(attr['伤害加成']):
                    attr['伤害加成'][i] = k + 0.3
                data['伤害描述'].append('勇士触发')
            elif suit[0][0] == '教官':
                attr['元素精通'] += 120
                data['伤害描述'].append('教官触发')
            elif suit[0][0] == '炽烈的炎之魔女':
                if data['名称'] in ['胡桃', '宵宫']:
                    attr['伤害加成'][1] += 0.075
                    data['伤害描述'].append('魔女1层')
                else:
                    attr['伤害加成'][1] += 0.225
                    data['伤害描述'].append('魔女满层')
                attr['蒸发系数'] = 0.15
            elif suit[0][0] == '渡过烈火的贤人':
                for i, k in enumerate(attr['伤害加成']):
                    attr['伤害加成'][i] = k + 0.5
                data['伤害描述'].append('渡火触发')
            elif suit[0][0] == '平息鸣雷的尊者':
                for i, k in enumerate(attr['伤害加成']):
                    attr['伤害加成'][i] = k + 0.5
                data['伤害描述'].append('平雷触发')
            elif suit[0][0] == '战狂':
                attr['暴击率'] += 0.24
                data['伤害描述'].append('战狂触发')
            elif suit[0][0] == '辰砂往生录':
                attr['额外攻击'] += attr['基础攻击'] * 0.48
                data['伤害描述'].append('辰砂满层')
            elif suit[0][0] == '被怜爱的少女':
                attr['受治疗加成'] += 0.2
            elif suit[0][0] == '追忆之注连':
                extra_a['普攻增伤'] += 0.5
                extra_a['重击增伤'] += 0.5
                extra_a['下落攻击增伤'] += 0.5
                data['伤害描述'].append('追忆触发')
            elif suit[0][0] == '流浪大地的乐团':
                if weapon['类型'] in ['法器', '弓箭']:
                    extra_a['重击增伤'] += 0.35
            elif suit[0][0] == '角斗士的终幕礼':
                if weapon['类型'] in ['单手剑', '双手剑', '长柄武器']:
                    extra_a['普攻增伤'] += 0.35
            elif suit[0][0] == '染血的骑士道':
                extra_a['重击增伤'] += 0.5
                data['伤害描述'].append('染血触发')
            elif suit[0][0] == '沉沦之心':
                extra_a['普攻增伤'] += 0.3
                extra_a['重击增伤'] += 0.3
                data['伤害描述'].append('沉沦触发')
            elif suit[0][0] == '逆飞的流星':
                extra_a['普攻增伤'] += 0.4
                extra_a['重击增伤'] += 0.4
                data['伤害描述'].append('流星触发')
            elif suit[0][0] == '武人':
                extra_a['普攻增伤'] += 0.25
                extra_a['重击增伤'] += 0.25
                data['伤害描述'].append('武人触发')
            elif suit[0][0] == '行者之心':
                extra_a['重击暴击率'] += 0.3
    data['属性'] = attr
    return data, extra_q, extra_e, extra_a


all_skill_data = load_json(path=Path(__file__).parent.parent.parent / 'utils' / 'json_data' / 'roles_data.json')


def get_damage_multipiler(data: dict) -> dict:
    skill_data = all_skill_data[data['名称']]['skill']
    level_q = data['天赋'][2]['等级'] - 1
    level_e = data['天赋'][1]['等级'] - 1
    level_a = data['天赋'][0]['等级'] - 1
    if data['名称'] == '钟离':
        return {
            '玉璋护盾': (float(skill_data['元素战技·地心']['数值']['护盾附加吸收量'][level_e].replace('%最大生命值', '')) / 100.0,
                     int(skill_data['元素战技·地心']['数值']['护盾基础吸收量'][level_e].replace(',', ''))),
            '原岩共鸣': float(skill_data['元素战技·地心']['数值']['岩脊伤害/共鸣伤害'][level_e].split('/')[1].replace('%', '')) / 100.0,
            '天星':   float(skill_data['元素爆发·天星']['数值']['技能伤害'][level_q].replace('%', '')) / 100.0,
            '踢枪':   float(skill_data['普通攻击·岩雨']['数值']['五段伤害'][level_a].replace('%×4', '')) / 100.0
        }
    if data['名称'] == '胡桃':
        return {
            '攻击力提高': float(skill_data['蝶引来生']['数值']['攻击力提高'][level_e].replace('%生命值上限', '')) / 100.0,
            '重击':    float(skill_data['普通攻击·往生秘传枪法']['数值']['重击伤害'][level_a].replace('%', '')) / 100.0,
            '雪梅香': float(skill_data['蝶引来生']['数值']['血梅香伤害'][level_e].replace('%', '')) / 100.0,
            '大招':  float(skill_data['安神秘法']['数值']['低血量时技能伤害'][level_q].replace('%', '')) / 100.0
        }
    if data['名称'] == '雷电将军':
        qa = skill_data['奥义·梦想真说']['数值']['重击伤害'][level_q].split('+')
        return {
            '协同攻击':     float(skill_data['神变·恶曜开眼']['数值']['协同攻击伤害'][level_e].replace('%', '')) / 100.0,
            'e增伤':      float(
                skill_data['神变·恶曜开眼']['数值']['元素爆发伤害提高'][level_e].replace('每点元素能量', '').replace('%', '')) / 100.0 * 90,
            '梦想一刀基础':   float(skill_data['奥义·梦想真说']['数值']['梦想一刀基础伤害'][level_q].replace('%', '')) / 100.0,
            '梦想一刀愿力':   float(
                skill_data['奥义·梦想真说']['数值']['愿力加成'][level_q].split('%/')[0].replace('每层', '')) / 100.0 * 60,
            '梦想一心重击基础': (float(qa[0].replace('%', '')) / 100.0, float(qa[1].replace('%', '')) / 100.0),
            '梦想一心愿力':   float(
                skill_data['奥义·梦想真说']['数值']['愿力加成'][level_q].split('%/')[1].replace('%攻击力', '')) / 100.0 * 60,
            '梦想一心能量': float(skill_data['奥义·梦想真说']['数值']['梦想一心能量恢复'][level_q])
        }
    if data['名称'] == '魈':
        a = skill_data['普通攻击·卷积微尘']['数值']['低空/高空坠地冲击伤害'][level_a].split('/')
        return {
            'AX:低空下落首戳': float(a[0].replace('%', '')) / 100,
            'AX:高空下落首戳': float(a[1].replace('%', '')) / 100,
            'E:风轮两立': float(skill_data['风轮两立']['数值']['技能伤害'][level_e].replace('%', '')) / 100.0,
            'B:靖妖傩舞': float(skill_data['靖妖傩舞']['数值']['普通攻击/重击/下落攻击伤害提升'][level_q].replace('%', '')) / 100
        }
    if data['名称'] == '香菱':
        return {
            '锅巴喷火': float(skill_data['锅巴出击']['数值']['喷火伤害'][level_e].replace('%', '')) / 100.0,
            '旋火轮':  float(skill_data['旋火轮']['数值']['旋火轮伤害'][level_q].replace('%', '')) / 100.0
        }
    if data['名称'] == '申鹤':
        return {
            '冰翎': float(skill_data['仰灵威召将役咒']['数值']['伤害值提升'][level_e].replace('%', '')) / 100.0,
            '大招减抗': float(skill_data['神女遣灵真诀']['数值']['抗性降低'][level_q].replace('%', '')) / 100.0,
            'e长按':  float(skill_data['仰灵威召将役咒']['数值']['长按技能伤害'][level_e].replace('%', '')) / 100.0,
            '大招持续': float(skill_data['神女遣灵真诀']['数值']['持续伤害'][level_q].replace('%', '')) / 100.0
        }
    if data['名称'] == '刻晴':
        az = skill_data['普通攻击·云来剑法']['数值']['重击伤害'][level_a].split('+')
        return {
            'AZ:重击': (float(az[0].replace('%', '')) / 100.0, float(az[1].replace('%', '')) / 100.0),
            'E:战技斩击': float(skill_data['星斗归位']['数值']['斩击伤害'][level_e].replace('%', '')) / 100.0,
            'Q:大招尾刀': float(skill_data['天街巡游']['数值']['最后一击伤害'][level_q].replace('%', '')) / 100.0
        }
    if data['名称'] == '可莉':
        return {
            '重击': float(skill_data['普通攻击·砰砰']['数值']['重击伤害'][level_a].replace('%', '')) / 100.0,
            '蹦蹦炸弹': float(skill_data['蹦蹦炸弹']['数值']['蹦蹦炸弹伤害'][level_q].replace('%', '')) / 100.0,
            '轰轰火花': float(skill_data['轰轰火花']['数值']['轰轰火花伤害'][level_q].replace('%', '')) / 100.0,
        }
    if data['名称'] == '八重神子':
        e = '杀生樱伤害·肆阶' if len(data['命座']) >= 2 else '杀生樱伤害·叁阶'
        return {
            '重击': float(skill_data['普通攻击·狐灵食罪式']['数值']['重击伤害'][level_a].replace('%', '')) / 100.0,
            '杀生樱': float(skill_data['野干役咒·杀生樱']['数值'][e][level_e].replace('%', '')) / 100.0,
            '天狐霆雷': float(skill_data['大密法·天狐显真']['数值']['天狐霆雷伤害'][level_q].replace('%', '')) / 100.0,
        }
    if data['名称'] == '阿贝多':
        return {
            '阳华绽放': float(skill_data['创生法·拟造阳华']['数值']['刹那之花伤害'][level_e].replace('%防御力', '')) / 100.0,
            '大招首段': float(skill_data['诞生式·大地之潮']['数值']['爆发伤害'][level_q].replace('%', '')) / 100.0
        }
    if data['名称'] == '神里绫华':
        return {
            '重击': float(skill_data['普通攻击·神里流·倾']['数值']['重击伤害'][level_a].replace('%*3', '')) / 100.0,
            '冰华伤害': float(skill_data['神里流·冰华']['数值']['技能伤害'][level_e].replace('%', '')) / 100.0,
            '霜灭每段': float(skill_data['神里流·霜灭']['数值']['切割伤害'][level_q].replace('%', '')) / 100.0,
        }
    if data['名称'] == '行秋':
        e = skill_data['古华剑·画雨笼山']['数值']['技能伤害'][level_e].split('+')
        return {
            '画雨笼山': (float(e[0].replace('%', '')) / 100.0, float(e[1].replace('%', '')) / 100.0),
            '裁雨留虹每段': float(skill_data['古华剑·裁雨留虹']['数值']['剑雨伤害'][level_e].replace('%', '')) / 100.0
        }
    if data['名称'] == '夜兰':
        return {
            '破局矢':   float(skill_data['普通攻击·潜形隐曜弓']['数值']['破局矢伤害'][level_a].replace('%生命值上限', '')) / 100.0,
            '元素战技': float(skill_data['萦络纵命索']['数值']['技能伤害'][level_e].replace('%生命值上限', '')) / 100.0,
            '大招每段': float(skill_data['渊图玲珑骰']['数值']['玄掷玲珑伤害'][level_q].replace('%生命值上限*3', '')) / 100.0,
        }
    if data['名称'] == '甘雨':
        return {
            '霜华矢': (float(skill_data['普通攻击·流天射术']['数值']['霜华矢命中伤害'][level_a].replace('%', '')) / 100.0, float(skill_data['普通攻击·流天射术']['数值']['霜华矢·霜华绽发伤害'][level_a].replace('%', '')) / 100.0),
            '元素战技': float(skill_data['山泽麟迹']['数值']['技能伤害'][level_e].replace('%', '')) / 100.0,
            '冰棱伤害': float(skill_data['降众天华']['数值']['冰棱伤害'][level_q].replace('%', '')) / 100.0,
        }


def draw_dmg_pic(dmg: Dict[str, Union[tuple, list]]):
    """
    绘制伤害图片
    :param dmg: 伤害字典
    :return: 伤害图片
    """
    # 读取图片资源
    mask_top = load_image(path=Path() / 'resources' / 'LittlePaimon' / 'player_card2' / '遮罩top.png')
    mask_body = load_image(path=Path() / 'resources' / 'LittlePaimon' / 'player_card2' / '遮罩body.png')
    mask_bottom = load_image(path=Path() / 'resources' / 'LittlePaimon' / 'player_card2' / '遮罩bottom.png')
    height = 60 * len(dmg) - 20
    # 创建画布
    bg = Image.new('RGBA', (948, height + 80), (0, 0, 0, 0))
    bg.alpha_composite(mask_top, (0, 0))
    bg.alpha_composite(mask_body.resize((948, height)), (0, 60))
    bg.alpha_composite(mask_bottom, (0, height + 60))
    bg_draw = ImageDraw.Draw(bg)
    # 绘制顶栏
    bg_draw.line((250, 0, 250, 948), (255, 255, 255, 75), 2)
    bg_draw.line((599, 0, 599, 60), (255, 255, 255, 75), 2)
    bg_draw.line((0, 60, 948, 60), (255, 255, 255, 75), 2)
    draw_center_text(bg_draw, '伤害计算', 0, 250, 11, 'white', get_font(30, text_font))
    draw_center_text(bg_draw, '期望伤害', 250, 599, 11, 'white', get_font(30, text_font))
    draw_center_text(bg_draw, '暴击伤害', 599, 948, 11, 'white', get_font(30, text_font))
    i = 1
    for describe, dmg_list in dmg.items():
        bg_draw.line((0, 60 * i, 948, 60 * i), (255, 255, 255, 75), 2)
        draw_center_text(bg_draw, describe, 0, 250, 60 * i + 13, 'white', get_font(30, text_font))
        if len(dmg_list) == 1:
            if describe == '额外说明':
                draw_center_text(bg_draw, dmg_list[0], 250, 948, 60 * i + 13, 'white', get_font(30, text_font))
            else:
                draw_center_text(bg_draw, dmg_list[0], 250, 948, 60 * i + 16, 'white', get_font(30, number_font))
        else:
            bg_draw.line((599, 60 * i, 599, 60 * (i + 1)), (255, 255, 255, 75), 2)
            draw_center_text(bg_draw, dmg_list[0], 250, 599, 60 * i + 16, 'white', get_font(30, number_font))
            draw_center_text(bg_draw, dmg_list[1], 599, 948, 60 * i + 16, 'white', get_font(30, number_font))
        i += 1

    return bg
