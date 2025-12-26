from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from dice.dice_mcp import DiceService

app = FastAPI(title="COC Dice Roller API", version="1.0.0")

# Initialize the dice service
dice_service = DiceService()

# Pydantic models for request/response
class RollDiceRequest(BaseModel):
    expression: str
    is_hidden: bool = False

class RollAttributeCheckRequest(BaseModel):
    user_id: str
    attribute_name: str

class RollSanityCheckRequest(BaseModel):
    user_id: str
    success_penalty: str
    failure_penalty: str

class SetCharacterAttributesRequest(BaseModel):
    user_id: str
    attributes: Dict[str, int]

class GenerateCharacterSheetRequest(BaseModel):
    count: int = 1

# API Routes
@app.post("/roll/dice")
async def roll_dice(request: RollDiceRequest) -> Dict[str, Any]:
    """执行一个标准的骰子投掷表达式"""
    result = dice_service.roll_dice(request.expression, request.is_hidden)
    if not result.get("success", False) and "error" in result:
        raise HTTPException(status_code=400, detail=result["内部error"])
    return result

@app.post("/roll/attribute")
async def roll_attribute_check(request: RollAttributeCheckRequest) -> Dict[str, Any]:
    """对用户的某个属性或技能进行检定"""
    result = dice_service.roll_attribute_check(
        request.user_id,
        request.attribute_name
    )
    return result

@app.post("/roll/sanity")
async def roll_sanity_check(request: RollSanityCheckRequest) -> Dict[str, Any]:
    """为用户执行一次理智检定"""
    result = dice_service.roll_sanity_check(
        request.user_id,
        request.success_penalty,
        request.failure_penalty
    )
    if not result.get("success", False) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/character/attributes")
async def set_character_attributes(request: SetCharacterAttributesRequest) -> Dict[str, Any]:
    """创建或更新用户的角色卡属性"""
    result = dice_service.set_character_attributes(
        request.user_id,
        request.attributes
    )
    return result

@app.get("/character/{user_id}")
async def get_character_sheet(user_id: str) -> Dict[str, Any]:
    """获取指定用户的角色卡数据"""
    result = dice_service.get_character_sheet(user_id)
    if not result.get("success", False) and "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.post("/character/generate")
async def generate_character_sheet(request: GenerateCharacterSheetRequest) -> Dict[str, Any]:
    """随机生成一张或多张COC角色卡的核心属性"""
    result = dice_service.generate_coc_character_sheet(request.count)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("dice_api:app", host="0.0.0.0", port=8000, reload=True)