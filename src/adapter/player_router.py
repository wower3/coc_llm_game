"""
COC 玩家数据路由
提供角色信息、技能数据的查询接口
"""

from fastapi import APIRouter, HTTPException
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.dice.model import DataContainer

router = APIRouter(prefix="/api", tags=["玩家数据"])

# 数据库连接实例
db = DataContainer()


def get_all_chinese_names():
    """获取所有技能的中文名映射"""
    sql = "SELECT id, name FROM chinese_name"
    results = db._execute_query(sql)
    return {row['id']: row['name'] for row in results}


@router.get('/player/{player_id}')
def get_player(player_id: str):
    """获取玩家基本信息"""
    try:
        sql = f"SELECT * FROM players WHERE id = '{player_id}'"
        results = db._execute_query(sql)

        if not results:
            raise HTTPException(status_code=404, detail='未找到该调查员')

        player = results[0]
        con = player.get('constitution', 0) or 0
        siz = player.get('size', 0) or 0
        pow_val = player.get('willpower', 0) or 0

        return {
            'success': True,
            'data': {
                'id': player.get('id'),
                'name': player.get('name'),
                'age': player.get('age'),
                'sex': player.get('sex', 'Male'),
                'strength': player.get('strength'),
                'constitution': con,
                'size': siz,
                'dexterity': player.get('dexterity'),
                'appearance': player.get('appearance'),
                'education': player.get('education'),
                'intelligence': player.get('intelligence'),
                'willpower': pow_val,
                'luck': player.get('luck'),
                'hit_points': player.get('hit_points'),
                'magic_points': player.get('magic_points'),
                'sanity': player.get('sanity'),
                'max_hp': (con + siz) // 10 if (con and siz) else 0,
                'max_mp': pow_val // 5 if pow_val else 0,
                'max_san': 99,
                'damage_bonus': player.get('damage_bonus', 0),
                'build': player.get('build', 0),
                'movement': player.get('movement', 0),
                'occupation_id': player.get('occupation_id')
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/skills/{player_id}')
def get_skills(player_id: str):
    """获取玩家技能信息（数值大于10的技能）"""
    try:
        skills_data = db.get_skill_card(player_id)
        skills_dict = skills_data.model_dump()
        chinese_names = get_all_chinese_names()

        filtered_skills = []
        for key, value in skills_dict.items():
            if key.startswith('skill_') and value is not None and value > 10:
                skill_id = key
                skill_name = chinese_names.get(skill_id, skill_id)
                filtered_skills.append({
                    'id': skill_id,
                    'name': skill_name,
                    'value': value
                })

        filtered_skills.sort(key=lambda x: x['value'], reverse=True)
        return {'success': True, 'data': filtered_skills}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/chinese_name/{skill_id}')
def get_chinese_name(skill_id: str):
    """获取单个技能的中文名"""
    try:
        name = db.get_id(skill_id)
        return {'success': True, 'data': {'id': skill_id, 'name': name}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/health')
def health_check():
    """健康检查接口"""
    return {'status': 'ok', 'message': 'Player API 服务运行中'}
