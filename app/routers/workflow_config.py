"""
工作流配置管理API路由
提供工作流配置的CRUD操作和验证功能
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from app.routers.auth_db import get_current_user
from app.core.database import get_mongo_db
from tradingagents.graph.workflow_config import WorkflowConfig, NodeConfig, EdgeConfig
from tradingagents.graph.default_config import generate_default_config
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/workflows", tags=["工作流配置"])
logger = logging.getLogger("webapi")


def clean_node_config(node_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    清理节点配置，移除多余的特定类型字段，只保留 agent_type
    
    Args:
        node_config: 节点配置字典
        
    Returns:
        清理后的节点配置字典
    """
    if not isinstance(node_config, dict):
        return node_config
    
    cleaned = node_config.copy()
    config = cleaned.get("config", {})
    
    if isinstance(config, dict):
        # 移除特定类型字段，只保留 agent_type
        config_cleaned = config.copy()
        config_cleaned.pop("analyst_type", None)
        config_cleaned.pop("researcher_type", None)
        config_cleaned.pop("manager_type", None)
        config_cleaned.pop("risk_type", None)
        cleaned["config"] = config_cleaned
    
    return cleaned


def clean_workflow_config(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    清理工作流配置，移除所有节点配置中的特定类型字段
    
    Args:
        config_dict: 工作流配置字典
        
    Returns:
        清理后的工作流配置字典
    """
    if not isinstance(config_dict, dict):
        return config_dict
    
    cleaned = config_dict.copy()
    
    # 清理节点配置
    if "nodes" in cleaned and isinstance(cleaned["nodes"], list):
        cleaned["nodes"] = [clean_node_config(node) for node in cleaned["nodes"]]
    
    return cleaned


# 请求/响应模型
class WorkflowListItem(BaseModel):
    """工作流列表项"""
    id: str
    name: str
    description: Optional[str] = None
    created_at: str
    updated_at: str
    author: Optional[str] = None


class WorkflowCreateRequest(BaseModel):
    """创建工作流请求"""
    name: str
    description: Optional[str] = None
    config: Dict[str, Any]


class WorkflowUpdateRequest(BaseModel):
    """更新工作流请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class WorkflowValidationResult(BaseModel):
    """工作流验证结果"""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []


@router.get("", response_model=List[WorkflowListItem])
async def list_workflows(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    current_user: dict = Depends(get_current_user)
):
    """获取所有工作流配置列表"""
    try:
        db = get_mongo_db()
        collection = db.workflow_configs
        
        # 查询工作流列表
        cursor = collection.find(
            {},
            {"name": 1, "description": 1, "metadata": 1, "created_at": 1, "updated_at": 1}
        ).skip(skip).limit(limit).sort("metadata.updated_at", -1)
        
        workflows = []
        async for doc in cursor:
            workflows.append(WorkflowListItem(
                id=str(doc["_id"]),
                name=doc.get("name", ""),
                description=doc.get("description"),
                created_at=doc.get("metadata", {}).get("created_at", ""),
                updated_at=doc.get("metadata", {}).get("updated_at", ""),
                author=doc.get("metadata", {}).get("author")
            ))
        
        return workflows
    except Exception as e:
        logger.error(f"获取工作流列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工作流列表失败: {str(e)}"
        )


@router.get("/{workflow_id}", response_model=Dict[str, Any])
async def get_workflow(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """获取指定工作流配置"""
    try:
        db = get_mongo_db()
        collection = db.workflow_configs
        
        if not ObjectId.is_valid(workflow_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的工作流ID"
            )
        
        doc = await collection.find_one({"_id": ObjectId(workflow_id)})
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工作流 {workflow_id} 不存在"
            )
        
        # 移除MongoDB的_id字段，使用id替代
        doc["id"] = str(doc.pop("_id"))
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工作流失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工作流失败: {str(e)}"
        )


@router.post("", response_model=Dict[str, Any])
async def create_workflow(
    request: WorkflowCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """创建新的工作流配置"""
    try:
        db = get_mongo_db()
        collection = db.workflow_configs
        
        # 验证配置
        try:
            config = WorkflowConfig(**request.config)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"配置格式错误: {str(e)}"
            )
        
        # 检查名称是否已存在
        existing = await collection.find_one({"name": request.name})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"工作流名称 '{request.name}' 已存在"
            )
        
        # 设置元数据
        config.name = request.name
        config.description = request.description
        config.metadata["author"] = current_user.get("username", "unknown")
        config.metadata["created_at"] = datetime.now().isoformat()
        config.metadata["updated_at"] = datetime.now().isoformat()
        
        # 保存到数据库
        doc = config.model_dump()
        # 清理多余的特定类型字段
        doc = clean_workflow_config(doc)
        result = await collection.insert_one(doc)
        
        # 返回创建的工作流
        doc["id"] = str(result.inserted_id)
        doc.pop("_id", None)
        
        logger.info(f"✅ 创建工作流成功: {request.name} (id: {result.inserted_id})")
        
        return {
            "success": True,
            "data": doc,
            "message": "工作流创建成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建工作流失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建工作流失败: {str(e)}"
        )


@router.put("/{workflow_id}", response_model=Dict[str, Any])
async def update_workflow(
    workflow_id: str,
    request: WorkflowUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """更新工作流配置"""
    try:
        db = get_mongo_db()
        collection = db.workflow_configs
        
        if not ObjectId.is_valid(workflow_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的工作流ID"
            )
        
        # 查找现有工作流
        existing = await collection.find_one({"_id": ObjectId(workflow_id)})
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工作流 {workflow_id} 不存在"
            )
        
        # 更新字段
        update_data = {}
        if request.name is not None:
            # 检查新名称是否已被其他工作流使用
            name_existing = await collection.find_one({
                "name": request.name,
                "_id": {"$ne": ObjectId(workflow_id)}
            })
            if name_existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"工作流名称 '{request.name}' 已被使用"
                )
            update_data["name"] = request.name
        
        if request.description is not None:
            update_data["description"] = request.description
        
        if request.config is not None:
            # 验证配置
            try:
                config = WorkflowConfig(**request.config)
                config_dict = config.model_dump()
                # 清理多余的特定类型字段
                config_dict = clean_workflow_config(config_dict)
                # 将配置的各个字段添加到更新数据中，排除 metadata（单独处理）
                for key, value in config_dict.items():
                    if key not in ['name', 'description', 'metadata']:  # 这些字段单独处理
                        update_data[key] = value
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"配置格式错误: {str(e)}"
                )
        
        # 更新元数据（确保不与其他字段冲突）
        # 先获取现有的 metadata
        existing_metadata = existing.get("metadata", {})
        if not isinstance(existing_metadata, dict):
            existing_metadata = {}
        
        # 更新 updated_at，保留其他 metadata 字段
        existing_metadata["updated_at"] = datetime.now().isoformat()
        update_data["metadata"] = existing_metadata
        
        # 执行更新
        result = await collection.update_one(
            {"_id": ObjectId(workflow_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有需要更新的内容"
            )
        
        # 返回更新后的工作流
        updated = await collection.find_one({"_id": ObjectId(workflow_id)})
        updated["id"] = str(updated.pop("_id"))
        
        logger.info(f"✅ 更新工作流成功: {workflow_id}")
        
        return {
            "success": True,
            "data": updated,
            "message": "工作流更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新工作流失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新工作流失败: {str(e)}"
        )


@router.delete("/{workflow_id}", response_model=Dict[str, Any])
async def delete_workflow(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """删除工作流配置"""
    try:
        db = get_mongo_db()
        collection = db.workflow_configs
        
        if not ObjectId.is_valid(workflow_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的工作流ID"
            )
        
        # 检查工作流是否存在
        existing = await collection.find_one({"_id": ObjectId(workflow_id)})
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工作流 {workflow_id} 不存在"
            )
        
        # 检查是否为默认工作流
        if existing.get("metadata", {}).get("is_default", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除默认工作流"
            )
        
        # 删除工作流
        result = await collection.delete_one({"_id": ObjectId(workflow_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除工作流失败"
            )
        
        logger.info(f"✅ 删除工作流成功: {workflow_id}")
        
        return {
            "success": True,
            "message": "工作流删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除工作流失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除工作流失败: {str(e)}"
        )


@router.post("/{workflow_id}/validate", response_model=WorkflowValidationResult)
async def validate_workflow(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """验证工作流配置的有效性"""
    try:
        db = get_mongo_db()
        collection = db.workflow_configs
        
        if not ObjectId.is_valid(workflow_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的工作流ID"
            )
        
        # 获取工作流配置
        doc = await collection.find_one({"_id": ObjectId(workflow_id)})
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工作流 {workflow_id} 不存在"
            )
        
        errors = []
        warnings = []
        
        try:
            # 验证配置格式
            config = WorkflowConfig(**doc)
            
            # 验证节点ID唯一性
            node_ids = [node.id for node in config.nodes]
            if len(node_ids) != len(set(node_ids)):
                errors.append("节点ID不唯一")
            
            # 验证边的源和目标节点是否存在
            valid_node_ids = set(node_ids) | {"START", "END"}
            for edge in config.edges:
                if edge.source not in valid_node_ids:
                    errors.append(f"边的源节点不存在: {edge.source}")
                if edge.target not in valid_node_ids:
                    errors.append(f"边的目标节点不存在: {edge.target}")
            
            # 验证至少有一个START边和一个END边
            has_start = any(edge.source == "START" for edge in config.edges)
            has_end = any(edge.target == "END" for edge in config.edges)
            if not has_start:
                errors.append("工作流缺少START入口")
            if not has_end:
                errors.append("工作流缺少END出口")
            
            # 验证条件边的condition配置
            for edge in config.edges:
                if edge.type.value == "conditional" and not edge.condition:
                    errors.append(f"条件边 {edge.id} 缺少condition配置")
            
        except Exception as e:
            errors.append(f"配置格式错误: {str(e)}")
        
        valid = len(errors) == 0
        
        return WorkflowValidationResult(
            valid=valid,
            errors=errors,
            warnings=warnings
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证工作流失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证工作流失败: {str(e)}"
        )


async def get_default_workflow_config() -> Optional[WorkflowConfig]:
    """从数据库加载默认工作流配置（异步版本，服务函数，不依赖认证）"""
    try:
        db = get_mongo_db()
        collection = db["workflow_configs"]
        
        # 查询默认工作流
        doc = await collection.find_one({"metadata.is_default": True})
        
        if doc:
            # 移除MongoDB的_id字段
            doc.pop("_id", None)
            return WorkflowConfig(**doc)
        
        return None
    except Exception as e:
        logger.warning(f"加载默认工作流配置失败: {e}")
        return None


def get_default_workflow_config_sync() -> Optional[WorkflowConfig]:
    """从数据库加载默认工作流配置（同步版本，用于同步上下文）"""
    try:
        from app.core.database import get_mongo_db_sync
        db = get_mongo_db_sync()
        collection = db["workflow_configs"]
        
        # 查询默认工作流
        doc = collection.find_one({"metadata.is_default": True})
        
        if doc:
            # 移除MongoDB的_id字段
            doc.pop("_id", None)
            return WorkflowConfig(**doc)
        
        return None
    except Exception as e:
        logger.warning(f"加载默认工作流配置失败: {e}")
        return None


@router.get("/default/config", response_model=Dict[str, Any])
async def get_default_workflow(
    selected_analysts: Optional[str] = Query(None, description="选中的分析师，逗号分隔"),
    current_user: dict = Depends(get_current_user)
):
    """获取默认工作流配置"""
    try:
        # 首先尝试从数据库加载
        config = await get_default_workflow_config()
        
        # 如果数据库中没有，使用生成函数（向后兼容）
        if not config:
            # 解析selected_analysts参数
            analyst_list = None
            if selected_analysts:
                analyst_list = [a.strip() for a in selected_analysts.split(",") if a.strip()]
            
            # 生成默认配置
            config = generate_default_config(selected_analysts=analyst_list)
        
        return {
            "success": True,
            "data": config.model_dump(),
            "message": "默认工作流配置"
        }
    except Exception as e:
        logger.error(f"获取默认工作流失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取默认工作流失败: {str(e)}"
        )

