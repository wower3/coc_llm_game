import json
import sys
import re
from typing import Dict, Any, List, Optional
import os

# 尝试导入 mysql-connector-python，如果失败则提示安装
try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    print("Error: mysql-connector-python is not installed. Please install it using 'pip install mysql-connector-python'")
    sys.exit(1)

# 定义技能名称到数据库列名的映射
SKILL_MAP = {
    '信用评级': 'skill_001', '会计': 'skill_002', '人类学': 'skill_003', '估价': 'skill_004', '考古学': 'skill_005',
    '攀爬': 'skill_006', '计算机使用': 'skill_007', '乔装': 'skill_008', '闪避': 'skill_009', '汽车驾驶': 'skill_010',
    '电气维修': 'skill_011', '电子学': 'skill_012', '急救': 'skill_013', '历史': 'skill_014', '跳跃': 'skill_015',
    '母语': 'skill_016', '法律': 'skill_017', '图书馆使用': 'skill_018', '聆听': 'skill_019', '锁匠': 'skill_020',
    '机械维修': 'skill_021', '医学': 'skill_022', '博物学': 'skill_023', '导航': 'skill_024', '神秘学': 'skill_025',
    '操作重型机械': 'skill_026', '精神分析': 'skill_027', '心理学': 'skill_028', '骑术': 'skill_029', '妙手': 'skill_030',
    '侦查': 'skill_031', '潜行': 'skill_032', '游泳': 'skill_033', '投掷': 'skill_034', '追踪': 'skill_035',
    '魅惑': 'skill_036', '恐吓': 'skill_037', '话术': 'skill_038', '说服': 'skill_039', '技艺:表演': 'skill_040',
    '技艺:美术': 'skill_041', '技艺:摄影': 'skill_042', '技艺:伪造文书': 'skill_043', '技艺:写作': 'skill_044', '技艺:书法': 'skill_045',
    '技艺:音乐': 'skill_046', '技艺:厨艺': 'skill_047', '技艺:理发': 'skill_048', '技艺:木匠': 'skill_049', '技艺:舞蹈': 'skill_050',
    '技艺:莫里斯舞蹈': 'skill_051', '技艺:歌剧演唱': 'skill_052', '技艺:粉刷/油漆工': 'skill_053', '技艺:制陶': 'skill_054', '技艺:雕塑': 'skill_055',
    '技艺:耕作': 'skill_056', '技艺:制图': 'skill_057', '技艺:打字': 'skill_058', '技艺:速记': 'skill_059', '科学:地质学': 'skill_060',
    '科学:化学': 'skill_061', '科学:生物学': 'skill_062', '科学:数学': 'skill_063', '科学:天文学': 'skill_064', '科学:物理学': 'skill_065',
    '科学:药学': 'skill_066', '科学:植物学': 'skill_067', '科学:动物学': 'skill_068', '科学:密码学': 'skill_069', '科学:工程学': 'skill_070',
    '科学:气象学': 'skill_071', '科学:司法科学': 'skill_072', '科学:鉴证': 'skill_073', '格斗:斗殴': 'skill_074', '格斗:鞭子': 'skill_075',
    '格斗:电锯': 'skill_076', '格斗:斧': 'skill_077', '格斗:剑': 'skill_078', '格斗:绞索': 'skill_079', '格斗:链枷': 'skill_080',
    '格斗:矛': 'skill_081', '射击:步枪/霰弹枪': 'skill_082', '射击:冲锋枪': 'skill_083', '射击:弓': 'skill_084', '射击:火焰喷射器': 'skill_085',
    '射击:机枪': 'skill_086', '射击:手枪': 'skill_087', '射击:重武器': 'skill_088', '英文': 'skill_089', '日语': 'skill_090',
    '韩语': 'skill_091', '俄语': 'skill_092', '西班牙语': 'skill_093', '法语': 'skill_094', '德语': 'skill_095', '意大利语': 'skill_096',
    '葡萄牙语': 'skill_097', '阿拉伯语': 'skill_098', '拉丁语': 'skill_099', '中文': 'skill_100', '爆破': 'skill_101',
    '催眠': 'skill_102', '读唇': 'skill_103', '炮术': 'skill_104', '潜水': 'skill_105', '驯兽': 'skill_106',
    '克苏鲁神话': 'skill_107', '生存': 'skill_108'
}


def normalize_skill_name(name: str) -> str:
    """标准化技能名称，移除括号内的额外信息"""
    return name.split('(')[0].strip()


def escape_sql_string(value: str) -> str:
    """转义SQL字符串中的特殊字符"""
    if value is None:
        return 'NULL'
    # 使用mysql.connector的转义方法更为安全，但这里为了保持原逻辑，先手动实现
    # 在实际执行时，参数化查询是更好的选择
    escaped_value = value.replace("'", "''")
    return f"'{escaped_value}'"

def to_sql_value(value: Any) -> str:
    """将Python值转换为SQL值"""
    if value is None:
        return 'NULL'
    if isinstance(value, str):
        return escape_sql_string(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (dict, list)):
        return escape_sql_string(json.dumps(value, ensure_ascii=False))
    return str(value)


def flatten_json_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """将嵌套的JSON数据扁平化为一层字典"""
    flat_data = {}

    flat_data['id'] = data.get('id')

    if 'info' in data:
        info = data['info']
        flat_data['year'] = 2023 if info.get('year') == 'modern' else info.get('year')
        flat_data['max_skill'] = info.get('maxSkill')
        flat_data['max_hobby_skill'] = info.get('maxHobbySkill')
        flat_data['name'] = f"{info.get('last_name', '')}{info.get('first_name', '')}"
        flat_data['age'] = info.get('age')
        flat_data['sex'] = info.get('sex')
        flat_data['language'] = info.get('lang')
        flat_data['birth_place'] = info.get('birth_place')
        flat_data['live_place'] = info.get('live_place')

    if 'attr' in data:
        attr = data['attr']
        flat_data['strength'] = attr.get('str')
        flat_data['constitution'] = attr.get('con')
        flat_data['size'] = attr.get('siz')
        flat_data['dexterity'] = attr.get('dex')
        flat_data['appearance'] = attr.get('app')
        flat_data['education'] = attr.get('edu')
        flat_data['intelligence'] = attr.get('int')
        flat_data['willpower'] = attr.get('pow')
        flat_data['luck'] = attr.get('luck')
        damage = attr.get('damage', '0')
        if isinstance(damage, str):
            match = re.search(r'\\d+', damage)
            flat_data['damage_bonus'] = int(match.group(0)) if match else 0
        else:
            flat_data['damage_bonus'] = damage
        flat_data['build'] = attr.get('build')
        flat_data['movement'] = attr.get('mov')
        flat_data['hit_points'] = attr.get('hp')
        flat_data['magic_points'] = attr.get('mp')
        flat_data['sanity'] = attr.get('san')

    if 'occ' in data:
        flat_data['occupation_id'] = data['occ'].get('value')

    if 'credit' in data:
        flat_data['cash_amount'] = data['credit'].get('cashNum')
        flat_data['assets_amount'] = data['credit'].get('AssetsNum')
        flat_data['credit_rating_spend'] = data['credit'].get('crSpend')

    flat_data['skills'] = data.get('skills')
    weapons = data.get('weapons')
    # 定义武器名称到weapon_XXX ID的映射
    weapon_map = {
        "徒手格斗": "weapon_000", "弓箭": "weapon_001", "指虎": "weapon_002", "长鞭": "weapon_003",
        "燃烧的火炬": "weapon_004", "电锯": "weapon_005", "包皮铁棍": "weapon_006", "大型棍状物": "weapon_007",
        "十字弩": "weapon_008", "绞具": "weapon_010", "斧头": "weapon_011", "大型刀具": "weapon_012",
        "中型刀具": "weapon_013", "小型刀": "weapon_014", "220v通电导线": "weapon_015", "催泪瓦斯": "weapon_016",
        "抛出的石块": "weapon_018", "苦无": "weapon_019", "矛": "weapon_020", "掷矛": "weapon_021",
        "大型剑": "weapon_022", "中型剑": "weapon_023", "轻剑": "weapon_024", "电棍": "weapon_025",
        "泰瑟枪": "weapon_026", "伐木斧": "weapon_027", "燧发枪": "weapon_029", ".22短口自动手枪": "weapon_030",
        ".25短口手枪(单管)": "weapon_031", ".32自动手枪": "weapon_032", ".32or7.65mm自动手枪": "weapon_033",
        ".357Magnum左轮手枪": "weapon_034", ".38or9mm左轮手枪": "weapon_035", "贝雷塔M9": "weapon_037",
        "格洛克179mm自动手枪": "weapon_038", ".41左轮手枪": "weapon_040", ".44马格南左轮手枪": "weapon_041",
        ".45左轮手枪": "weapon_042", ".45自动手枪": "weapon_043", ".58斯普林菲尔德步枪": "weapon_045",
        ".22杠杆式步枪": "weapon_046", ".30卡宾枪": "weapon_047", ".45马提尼·亨利步枪": "weapon_048",
        "加兰德M1、M2步枪": "weapon_050", "SKS半自动步枪": "weapon_051", ".303(7.7mm)李恩菲尔德": "weapon_052",
        ".30-06(7.62mm)栓式枪机步枪": "weapon_053", ".30-06(7.62mm)半自动步枪": "weapon_054",
        ".444(莫兰上校气动步枪)": "weapon_055", "猎象枪(双管)": "weapon_056", "16号霰弹枪(双管)": "weapon_058",
        "12号霰弹枪": "weapon_059", "12号泵动霰弹枪": "weapon_060", "12号半自动霰弹枪": "weapon_061",
        "削短12号双管霰弹枪": "weapon_062", "10号霰弹枪(双管)": "weapon_063", "12号贝里尼M3(折叠式枪托)": "weapon_064",
        "12号SPAS(折叠式)": "weapon_065", "AK-47orAKM": "weapon_066", "AK-74": "weapon_067", "巴雷特M82": "weapon_068",
        "FNFALLightAutomatic": "weapon_069", "GalilAssale": "weapon_070", "M16A2": "weapon_071", "M4": "weapon_072",
        "SteyrAUG": "weapon_073", "巴雷特M70/90": "weapon_074", "贝格曼MP181/MP2811": "weapon_075",
        "Heckler & Koch MP5": "weapon_076", "蝎式冲锋枪": "weapon_078", "汤普森冲锋枪": "weapon_079",
        "乌兹微型": "weapon_080", "M1882加特林机枪": "weapon_081", "M1918式勃朗宁自动步枪": "weapon_082",
        "M1917A1式勃朗宁重机枪": "weapon_083", "布伦式轻机枪": "weapon_084", "刘易斯式轻机枪": "weapon_085",
        "Minigun": "weapon_086", "FNMinimi5.56mm轻机枪": "weapon_087", "维克斯MK1式机枪": "weapon_088",
        "燃烧瓶": "weapon_089", "信号枪": "weapon_090", "M79榴弹发射器": "weapon_091", "土制炸药": "weapon_092",
        "冲锋枪": "weapon_093", "管状炸弹": "weapon_094", "塑胶炸弹(C4)": "weapon_095", "手榴弹": "weapon_096",
        "81mm迫击炮": "weapon_097", "75mm野战炮": "weapon_098", "120mm坦克炮(稳定)": "weapon_099",
        "5英寸舰载炮(稳定)": "weapon_100", "反步兵地雷": "weapon_101", "阔剑地雷": "weapon_102",
        "火焰喷射器": "weapon_103", "轻型反坦克武器": "weapon_104"
    }

    weapons = data.get('weapons')
    if weapons and isinstance(weapons, list):
        weapon_ids = []
        for weapon in weapons:
            name = weapon.get('name', '')
            if name in weapon_map:
                weapon_ids.append(weapon_map[name])
        flat_data['weapons'] = json.dumps(weapon_ids) if weapon_ids else None
    else:
        flat_data['weapons'] = None
    flat_data['equipments'] = data.get('equips')
    flat_data['notes'] = data.get('note')

    if 'background' in data:
        background = data['background']
        flat_data['personal_description'] = background.get('personalDescription')
        flat_data['beliefs'] = background.get('beliefs')
        flat_data['traits'] = background.get('traits')
        flat_data['significant_people'] = background.get('significantPeople')
        flat_data['meaningful_locations'] = background.get('meaningfulLocations')
        flat_data['treasured_possessions'] = background.get('treasuredPossessions')
        flat_data['injuries'] = background.get('injuries')
        flat_data['phobias'] = background.get('phobias')
        flat_data['encounters'] = background.get('encounters')
        flat_data['mythos'] = background.get('mythos')
        flat_data['relationships'] = background.get('relationShip')

    flat_data['face_image_path'] = data.get('face')

    return flat_data


def generate_players_insert(flat_data: Dict[str, Any]) -> str:
    """生成players表的INSERT语句"""
    columns = [
        'id', 'year', 'max_skill', 'max_hobby_skill', 'name', 'age', 'sex', 'language',
        'birth_place', 'live_place', 'strength', 'constitution', 'size', 'dexterity',
        'appearance', 'education', 'intelligence', 'willpower', 'luck', 'damage_bonus',
        'build', 'movement', 'hit_points', 'magic_points', 'sanity', 'occupation_id',
        'cash_amount', 'assets_amount', 'credit_rating_spend', 'weapons',
        'equipments', 'personal_description', 'beliefs', 'traits', 'significant_people',
        'meaningful_locations', 'treasured_possessions', 'injuries', 'phobias', 'encounters',
        'mythos', 'relationships', 'face_image_path', 'notes'
    ]

    # 确保 'skills' 键不包含在 players 表的插入数据中
    player_data = {k: v for k, v in flat_data.items() if k != 'skills'}

    values = [to_sql_value(player_data.get(col)) for col in columns]

    return f"INSERT INTO `players` (`{ '`, `'.join(columns) }`) VALUES ({ ', '.join(values) });"


def generate_skills_insert(flat_data: Dict[str, Any]) -> str:
    """生成skills表的INSERT语句"""
    skill_values = {col: 'NULL' for col in SKILL_MAP.values()}

    if 'skills' in flat_data and flat_data['skills']:
        for skill_group in flat_data['skills']:
            for skill in skill_group:
                norm_name = normalize_skill_name(skill.get('name', ''))
                if norm_name in SKILL_MAP:
                    col_name = SKILL_MAP[norm_name]
                    skill_values[col_name] = to_sql_value(skill.get('pts'))

    columns = ['id'] + sorted(skill_values.keys())
    values = [to_sql_value(flat_data.get('id'))] + [skill_values[key] for key in sorted(skill_values.keys())]

    return f"INSERT INTO `skills` (`{ '`, `'.join(columns) }`) VALUES ({ ', '.join(values) });"


def execute_sql(db_config: Dict[str, Any], sql_statements: List[str]):
    """连接到数据库并执行SQL语句"""
    conn = None
    try:
        conn = mysql.connector.connect(
            host=db_config['db_host'],
            user=db_config['db_user'],
            password=db_config['db_password'],
            database=db_config['db_name'],
            port=db_config['db_port']
        )
        cursor = conn.cursor()

        for statement in sql_statements:
            if statement.strip():
                cursor.execute(statement)

        conn.commit()
        print("SQL statements executed successfully.")

    except Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            print("Database connection closed.")


def main():
    if len(sys.argv) < 2:
        print("Usage: python trans.py <json_file>")
        sys.exit(1)

    json_file = sys.argv[1]

    # 获取脚本所在的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_config_path = os.path.join(script_dir, 'database.json')

    try:
        with open(db_config_path, 'r', encoding='utf-8') as f:
            db_config = json.load(f)
    except Exception as e:
        print(f"Error reading database config file '{db_config_path}': {e}")
        sys.exit(1)

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file '{json_file}': {e}")
        sys.exit(1)

    flat_data = flatten_json_data(data)

    sql_statements = [
        generate_players_insert(flat_data),
        generate_skills_insert(flat_data)
    ]

    execute_sql(db_config, sql_statements)


if __name__ == '__main__':
    main()
