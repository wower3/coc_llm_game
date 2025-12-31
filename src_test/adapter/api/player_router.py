"""
COC 玩家数据路由
提供角色信息、技能数据的查询接口
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api", tags=["玩家数据"])

# 延迟加载数据库连接
_db = None


def get_db():
    global _db
    if _db is None:
        from src_test.infrastructure.database import get_repository
        _db = get_repository()
    return _db


def get_all_chinese_names():
    """获取所有技能的中文名映射"""
    db = get_db()
    sql = "SELECT id, name FROM chinese_name"
    results = db.db.execute_query(sql)
    return {row['id']: row['name'] for row in results}


@router.get('/player/{player_id}')
def get_player(player_id: str):
    """获取玩家基本信息"""
    try:
        player = get_db().get_user_card(player_id)
        if not player or not player.id:
            raise HTTPException(status_code=404, detail='未找到该调查员')

        data = player.model_dump()
        con = data.get('constitution', 0) or 0
        siz = data.get('size', 0) or 0
        pow_val = data.get('willpower', 0) or 0

        return {
            'success': True,
            'data': {
                'id': data.get('id'),
                'name': data.get('name'),
                'age': data.get('age'),
                'sex': data.get('sex', 'Male'),
                'strength': data.get('strength'),
                'constitution': con,
                'size': siz,
                'dexterity': data.get('dexterity'),
                'appearance': data.get('appearance'),
                'education': data.get('education'),
                'intelligence': data.get('intelligence'),
                'willpower': pow_val,
                'luck': data.get('luck'),
                'hit_points': data.get('hit_points'),
                'magic_points': data.get('magic_points'),
                'sanity': data.get('sanity'),
                'max_hp': (con + siz) // 10 if (con and siz) else 0,
                'max_mp': pow_val // 5 if pow_val else 0,
                'max_san': 99,
                'damage_bonus': data.get('damage_bonus', 0),
                'build': data.get('build', 0),
                'movement': data.get('movement', 0),
                'occupation_id': data.get('occupation_id')
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
        skills_data = get_db().get_skill_card(player_id)
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
        name = get_db().get_id(skill_id)
        return {'success': True, 'data': {'id': skill_id, 'name': name}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/health')
def health_check():
    """健康检查接口"""
    return {'status': 'ok', 'message': 'Player API 服务运行中'}
