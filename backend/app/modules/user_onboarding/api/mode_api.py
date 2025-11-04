"""
Mode Management API Endpoints
"""

from fastapi import APIRouter, Query
from typing import Dict

from app.modules.common.schemas.response import APIResponse, success_response
from app.modules.user_onboarding.models.user_mode import UserPreferences, UserMode
from app.modules.user_onboarding.schemas.mode_schemas import (
    ModeUpdateRequest,
    ModeResponse,
    PreferencesUpdateRequest,
    PreferencesResponse
)
from app.modules.user_onboarding.services.mode_service import ModeService

router = APIRouter()
mode_service = ModeService()

# 简单的内存存储（生产环境应使用数据库）
_user_preferences: Dict[str, UserPreferences] = {}


@router.get("/mode", response_model=APIResponse[ModeResponse])
async def get_current_mode(user_id: str = Query(..., description="User ID")):
    """获取当前用户模式"""
    # 如果用户不存在，创建默认偏好设置
    if user_id not in _user_preferences:
        _user_preferences[user_id] = mode_service.create_default_preferences(user_id)
    
    prefs = _user_preferences[user_id]
    mode_response = ModeResponse(
        user_id=prefs.user_id,
        mode=prefs.mode,
        updated_at=prefs.updated_at
    )
    
    return success_response(mode_response)


@router.post("/mode", response_model=APIResponse[ModeResponse])
async def update_mode(
    request: ModeUpdateRequest,
    user_id: str = Query(..., description="User ID")
):
    """更新用户模式"""
    # 如果用户不存在，创建默认偏好设置
    if user_id not in _user_preferences:
        _user_preferences[user_id] = mode_service.create_default_preferences(user_id)
    
    current_prefs = _user_preferences[user_id]
    
    # 切换模式
    mode_response = mode_service.switch_mode(
        user_id=user_id,
        current_mode=current_prefs.mode,
        new_mode=request.mode
    )
    
    # 更新存储的偏好设置
    current_prefs.mode = request.mode
    current_prefs.updated_at = mode_response.updated_at
    
    return success_response(mode_response)


@router.get("/preferences", response_model=APIResponse[PreferencesResponse])
async def get_preferences(user_id: str = Query(..., description="User ID")):
    """获取用户偏好设置"""
    # 如果用户不存在，创建默认偏好设置
    if user_id not in _user_preferences:
        _user_preferences[user_id] = mode_service.create_default_preferences(user_id)
    
    prefs = _user_preferences[user_id]
    prefs_response = PreferencesResponse(
        user_id=prefs.user_id,
        mode=prefs.mode,
        completed_guides=prefs.completed_guides,
        show_tooltips=prefs.show_tooltips,
        language=prefs.language,
        created_at=prefs.created_at,
        updated_at=prefs.updated_at
    )
    
    return success_response(prefs_response)


@router.put("/preferences", response_model=APIResponse[PreferencesResponse])
async def update_preferences(
    request: PreferencesUpdateRequest,
    user_id: str = Query(..., description="User ID")
):
    """更新用户偏好设置（支持部分更新）"""
    # 如果用户不存在，创建默认偏好设置
    if user_id not in _user_preferences:
        _user_preferences[user_id] = mode_service.create_default_preferences(user_id)
    
    current_prefs = _user_preferences[user_id]
    
    # 更新偏好设置
    updated_prefs = mode_service.update_preferences(
        current_prefs=current_prefs,
        show_tooltips=request.show_tooltips,
        language=request.language,
        completed_guides=request.completed_guides
    )
    
    # 保存更新后的偏好设置
    _user_preferences[user_id] = updated_prefs
    
    prefs_response = PreferencesResponse(
        user_id=updated_prefs.user_id,
        mode=updated_prefs.mode,
        completed_guides=updated_prefs.completed_guides,
        show_tooltips=updated_prefs.show_tooltips,
        language=updated_prefs.language,
        created_at=updated_prefs.created_at,
        updated_at=updated_prefs.updated_at
    )
    
    return success_response(prefs_response)
