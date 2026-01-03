
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.routers.auth_db import get_current_user

from app.services.screening_service import ScreeningService, ScreeningParams
from app.services.enhanced_screening_service import get_enhanced_screening_service
from app.services.mcp_screening_service import MCPScreeningService
from app.models.screening import (
    ScreeningCondition, ScreeningRequest as NewScreeningRequest,
    ScreeningResponse as NewScreeningResponse, FieldInfo, BASIC_FIELDS_INFO
)
from app.core.response import ok

router = APIRouter(tags=["screening"])
logger = logging.getLogger("webapi")

# 筛选字段配置响应模型
class FieldConfigResponse(BaseModel):
    """筛选字段配置响应"""
    fields: Dict[str, FieldInfo]
    categories: Dict[str, List[str]]

# 传统的请求/响应模型（保持向后兼容）
class OrderByItem(BaseModel):
    field: str
    direction: str = Field("desc", pattern=r"^(?i)(asc|desc)$")

class ScreeningRequest(BaseModel):
    market: str = Field("CN", description="市场：CN")
    date: Optional[str] = Field(None, description="交易日YYYY-MM-DD，缺省为最新")
    adj: str = Field("qfq", description="复权口径：qfq/hfq/none（P0占位）")
    conditions: Dict[str, Any] = Field(default_factory=dict)
    order_by: Optional[List[OrderByItem]] = None
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)

class ScreeningResponse(BaseModel):
    total: int
    items: List[dict]

# 服务实例
svc = ScreeningService()
enhanced_svc = get_enhanced_screening_service()
mcp_screening_svc = MCPScreeningService()


@router.get("/fields", response_model=FieldConfigResponse)
async def get_screening_fields(user: dict = Depends(get_current_user)):
    """
    获取筛选字段配置
    返回所有可用的筛选字段及其配置信息
    """
    try:
        # 字段分类
        categories = {
            "basic": ["code", "name", "industry", "area", "market"],
            "market_value": ["total_mv", "circ_mv"],
            "financial": ["pe", "pb", "pe_ttm", "pb_mrq", "roe"],
            "trading": ["turnover_rate", "volume_ratio"],
            "price": ["close", "pct_chg", "amount"],
            "technical": ["ma20", "rsi14", "kdj_k", "kdj_d", "kdj_j", "dif", "dea", "macd_hist"]
        }

        return FieldConfigResponse(
            fields=BASIC_FIELDS_INFO,
            categories=categories
        )

    except Exception as e:
        logger.error(f"[get_screening_fields] 获取字段配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _convert_legacy_conditions_to_new_format(legacy_conditions: Dict[str, Any]) -> List[ScreeningCondition]:
    """
    将传统格式的筛选条件转换为新格式

    传统格式示例:
    {
        "logic": "AND",
        "children": [
            {"field": "market_cap", "op": "between", "value": [5000000, 9007199254740991]}
        ]
    }

    新格式:
    [
        ScreeningCondition(field="total_mv", operator="between", value=[50, 90071992547])
    ]
    """
    conditions = []

    # 字段名映射（前端可能使用的旧字段名 -> 统一的后端字段名）
    field_mapping = {
        "market_cap": "total_mv",      # 市值（兼容旧字段名）
        "pe_ratio": "pe",              # 市盈率（兼容旧字段名）
        "pb_ratio": "pb",              # 市净率（兼容旧字段名）
        "turnover": "turnover_rate",   # 换手率（兼容旧字段名）
        "change_percent": "pct_chg",   # 涨跌幅（兼容旧字段名）
        "price": "close",              # 价格（兼容旧字段名）
    }

    # 操作符映射
    operator_mapping = {
        "between": "between",
        "gt": ">",
        "lt": "<",
        "gte": ">=",
        "lte": "<=",
        "eq": "==",
        "ne": "!=",
        "in": "in",
        "contains": "contains"
    }

    if isinstance(legacy_conditions, dict):
        children = legacy_conditions.get("children", [])

        for child in children:
            if isinstance(child, dict):
                field = child.get("field")
                op = child.get("op")
                value = child.get("value")

                if field and op and value is not None:
                    # 映射字段名
                    mapped_field = field_mapping.get(field, field)

                    # 映射操作符
                    mapped_op = operator_mapping.get(op, op)

                    # 处理市值单位转换（前端传入的是万元，数据库存储的是亿元）
                    if mapped_field == "total_mv" and isinstance(value, list):
                        # 将万元转换为亿元
                        converted_value = [v / 10000 for v in value if isinstance(v, (int, float))]
                        logger.info(f"[screening] 市值单位转换: {value} 万元 -> {converted_value} 亿元")
                        value = converted_value
                    elif mapped_field == "total_mv" and isinstance(value, (int, float)):
                        value = value / 10000
                        logger.info(f"[screening] 市值单位转换: {child.get('value')} 万元 -> {value} 亿元")

                    # 创建筛选条件
                    condition = ScreeningCondition(
                        field=mapped_field,
                        operator=mapped_op,
                        value=value
                    )
                    conditions.append(condition)

                    logger.info(f"[screening] 转换条件: {field}({op}) -> {mapped_field}({mapped_op}), 值: {value}")

    return conditions


# 传统筛选接口（保持向后兼容，但使用增强服务）
@router.post("/run", response_model=ScreeningResponse)
async def run_screening(req: ScreeningRequest, user: dict = Depends(get_current_user)):
    try:
        logger.info(f"[screening] 请求条件: {req.conditions}")
        logger.info(f"[screening] 排序与分页: order_by={req.order_by}, limit={req.limit}, offset={req.offset}")

        # 转换传统格式的条件为新格式
        conditions = _convert_legacy_conditions_to_new_format(req.conditions)
        logger.info(f"[screening] 转换后的条件: {conditions}")

        # 使用增强筛选服务
        result = await enhanced_svc.screen_stocks(
            conditions=conditions,
            market=req.market,
            date=req.date,
            adj=req.adj,
            limit=req.limit,
            offset=req.offset,
            order_by=[{"field": o.field, "direction": o.direction} for o in (req.order_by or [])],
            use_database_optimization=True
        )

        logger.info(f"[screening] 筛选完成: total={result.get('total')}, "
                   f"took={result.get('took_ms')}ms, optimization={result.get('optimization_used')}")

        if result.get('items'):
            sample = result['items'][:3]
            logger.info(f"[screening] 返回样例(前3条): {sample}")

        return ScreeningResponse(total=result["total"], items=result["items"])

    except Exception as e:
        logger.error(f"[screening] 处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# 新的优化筛选接口
@router.post("/enhanced", response_model=NewScreeningResponse)
async def enhanced_screening(req: NewScreeningRequest, user: dict = Depends(get_current_user)):
    """
    增强的股票筛选接口
    - 支持更丰富的筛选条件格式
    - 自动选择最优的筛选策略（数据库优化 vs 传统方法）
    - 提供详细的性能统计信息
    """
    try:
        logger.info(f"[enhanced_screening] 筛选条件: {len(req.conditions)}个")
        logger.info(f"[enhanced_screening] 排序与分页: order_by={req.order_by}, limit={req.limit}, offset={req.offset}")

        # 执行增强筛选
        result = await enhanced_svc.screen_stocks(
            conditions=req.conditions,
            market=req.market,
            date=req.date,
            adj=req.adj,
            limit=req.limit,
            offset=req.offset,
            order_by=req.order_by,
            use_database_optimization=req.use_database_optimization
        )

        logger.info(f"[enhanced_screening] 筛选完成: total={result.get('total')}, "
                   f"took={result.get('took_ms')}ms, optimization={result.get('optimization_used')}")

        return NewScreeningResponse(
            total=result["total"],
            items=result["items"],
            took_ms=result.get("took_ms"),
            optimization_used=result.get("optimization_used"),
            source=result.get("source")
        )

    except Exception as e:
        logger.error(f"[enhanced_screening] 筛选失败: {e}")
        raise HTTPException(status_code=500, detail=f"增强筛选失败: {str(e)}")


# 获取支持的字段信息
@router.get("/fields", response_model=List[Dict[str, Any]])
async def get_supported_fields(user: dict = Depends(get_current_user)):
    """获取所有支持的筛选字段信息"""
    try:
        fields = await enhanced_svc.get_all_supported_fields()
        return fields
    except Exception as e:
        logger.error(f"[screening] 获取字段信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取字段信息失败: {str(e)}")


# 获取单个字段的详细信息
@router.get("/fields/{field_name}", response_model=Dict[str, Any])
async def get_field_info(field_name: str, user: dict = Depends(get_current_user)):
    """获取指定字段的详细信息"""
    try:
        field_info = await enhanced_svc.get_field_info(field_name)
        if not field_info:
            raise HTTPException(status_code=404, detail=f"字段 '{field_name}' 不存在")
        return field_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[screening] 获取字段信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取字段信息失败: {str(e)}")


# 验证筛选条件
@router.post("/validate", response_model=Dict[str, Any])
async def validate_conditions(conditions: List[ScreeningCondition], user: dict = Depends(get_current_user)):
    """验证筛选条件的有效性"""
    try:
        validation_result = await enhanced_svc.validate_conditions(conditions)
        return validation_result
    except Exception as e:
        logger.error(f"[screening] 验证条件失败: {e}")
        raise HTTPException(status_code=500, detail=f"验证条件失败: {str(e)}")

# 重复定义的旧端点移除（保留带日志的版本）


@router.get("/industries")
async def get_industries(user: dict = Depends(get_current_user)):
    """
    获取数据库中所有可用的行业列表
    根据系统配置的数据源优先级，从所有启用的数据源获取行业分类数据（包括TDX）
    如果数据库中的行业数据不足，从AKShare实时获取行业列表作为补充
    返回按股票数量排序的行业列表
    """
    try:
        from app.core.database import get_mongo_db
        from app.core.unified_config import UnifiedConfigManager
        import asyncio

        db = get_mongo_db()
        collection = db["stock_basic_info"]

        # 🔥 获取数据源优先级配置（使用统一配置管理器的异步方法）
        config = UnifiedConfigManager()
        data_source_configs = await config.get_data_source_configs_async()

        # 提取启用的数据源，按优先级排序（包括TDX）
        enabled_sources = []
        for ds in data_source_configs:
            if not ds.enabled:
                continue
            # 处理枚举类型：如果type是枚举，获取value；否则直接使用
            ds_type = ds.type.value if hasattr(ds.type, 'value') else str(ds.type)
            ds_type_lower = ds_type.lower()
            if ds_type_lower in ['tushare', 'akshare', 'baostock', 'tdx']:
                enabled_sources.append(ds_type_lower)

        if not enabled_sources:
            # 如果没有配置，使用默认顺序
            enabled_sources = ['tushare', 'akshare', 'baostock', 'tdx']

        logger.info(f"[get_industries] 数据源优先级: {enabled_sources}")

        # 🔥 从所有启用的数据源查询行业（合并结果）
        # 首先尝试从数据库查询所有启用数据源的行业数据
        pipeline = [
            {
                "$match": {
                    "source": {"$in": enabled_sources},  # 🔥 查询所有启用的数据源（包括TDX）
                    "industry": {"$ne": None, "$ne": "", "$exists": True}  # 过滤空行业
                }
            },
            {
                "$group": {
                    "_id": "$industry",
                    "count": {"$sum": 1},
                    "sources": {"$addToSet": "$source"}  # 记录该行业来自哪些数据源
                }
            },
            {"$sort": {"count": -1}},  # 按股票数量降序排序
            {
                "$project": {
                    "industry": "$_id",
                    "count": 1,
                    "sources": 1,
                    "_id": 0
                }
            }
        ]

        industries = []
        industry_dict = {}  # 用于去重和合并
        async for doc in collection.aggregate(pipeline):
            # 清洗字段，避免 NaN/Inf 导致 JSON 序列化失败
            raw_industry = doc.get("industry")
            safe_industry = ""
            try:
                if raw_industry is None:
                    safe_industry = ""
                elif isinstance(raw_industry, float):
                    if raw_industry != raw_industry or raw_industry in (float("inf"), float("-inf")):
                        safe_industry = ""
                    else:
                        safe_industry = str(raw_industry)
                else:
                    safe_industry = str(raw_industry).strip()
            except Exception:
                safe_industry = ""

            if not safe_industry:  # 跳过空行业
                continue

            raw_count = doc.get("count", 0)
            safe_count = 0
            try:
                if isinstance(raw_count, float):
                    if raw_count != raw_count or raw_count in (float("inf"), float("-inf")):
                        safe_count = 0
                    else:
                        safe_count = int(raw_count)
                else:
                    safe_count = int(raw_count)
            except Exception:
                safe_count = 0

            # 如果行业已存在，合并计数（取最大值）
            if safe_industry in industry_dict:
                industry_dict[safe_industry]["count"] = max(industry_dict[safe_industry]["count"], safe_count)
            else:
                industry_dict[safe_industry] = {
                    "value": safe_industry,
                    "label": safe_industry,
                    "count": safe_count,
                }

        industries = list(industry_dict.values())
        industries.sort(key=lambda x: x["count"], reverse=True)  # 按股票数量降序排序

        logger.info(f"[get_industries] 从数据库返回 {len(industries)} 个行业（数据源: {enabled_sources}）")

        # 🔥 如果行业数据不足（少于10个），尝试从AKShare实时获取补充（限制数量避免超时）
        if len(industries) < 10:
            logger.info(f"[get_industries] 数据库行业数据不足（{len(industries)}个），尝试从AKShare实时获取补充（采样50只股票）...")
            try:
                from app.services.data_sources.akshare_adapter import AKShareAdapter
                import akshare as ak

                akshare_adapter = AKShareAdapter()
                if akshare_adapter.is_available():
                    # 从AKShare获取股票列表并提取行业信息（采样方式）
                    def fetch_stock_list():
                        try:
                            # 使用AKShare获取A股股票列表
                            return ak.stock_info_a_code_name()
                        except Exception as e:
                            logger.warning(f"[get_industries] AKShare获取股票列表失败: {e}")
                            return None

                    stock_list_df = await asyncio.to_thread(fetch_stock_list)
                    if stock_list_df is not None and not stock_list_df.empty:
                        # 提取股票代码（6位），采样50只股票（每20只取1只，覆盖不同市场）
                        stock_codes_all = stock_list_df['code'].apply(lambda x: str(x).zfill(6)).tolist()
                        # 采样策略：取前50只，覆盖不同代码段
                        sample_size = min(50, len(stock_codes_all))
                        step = max(1, len(stock_codes_all) // sample_size)
                        stock_codes = stock_codes_all[::step][:sample_size]
                        
                        # 批量获取行业信息
                        akshare_industries = {}
                        success_count = 0
                        for code in stock_codes:
                            try:
                                def fetch_stock_info():
                                    try:
                                        return ak.stock_individual_info_em(symbol=code)
                                    except:
                                        return None
                                
                                stock_info = await asyncio.to_thread(fetch_stock_info)
                                if stock_info is not None and not stock_info.empty:
                                    # 提取行业信息
                                    industry_row = stock_info[stock_info['item'] == '所属行业']
                                    if not industry_row.empty:
                                        industry_name = str(industry_row['value'].iloc[0]).strip()
                                        if industry_name and industry_name not in ['-', '--', '未知', '']:
                                            if industry_name not in akshare_industries:
                                                akshare_industries[industry_name] = 0
                                            akshare_industries[industry_name] += 1
                                            success_count += 1
                                
                                # 添加延迟，避免API限流
                                if success_count % 10 == 0:  # 每10个请求后延迟稍长
                                    await asyncio.sleep(0.2)
                                else:
                                    await asyncio.sleep(0.05)
                            except Exception as e:
                                logger.debug(f"[get_industries] 获取{code}行业信息失败: {e}")
                                continue

                        # 合并AKShare的行业数据
                        if akshare_industries:
                            for industry_name, count in akshare_industries.items():
                                if industry_name in industry_dict:
                                    # 如果已存在，更新计数（取较大值）
                                    industry_dict[industry_name]["count"] = max(industry_dict[industry_name]["count"], count)
                                else:
                                    # 新增行业
                                    industry_dict[industry_name] = {
                                        "value": industry_name,
                                        "label": industry_name,
                                        "count": count,
                                    }

                            industries = list(industry_dict.values())
                            industries.sort(key=lambda x: x["count"], reverse=True)
                            logger.info(f"[get_industries] 从AKShare补充了 {len(akshare_industries)} 个行业，共 {len(industries)} 个行业")
            except Exception as e:
                logger.warning(f"[get_industries] 从AKShare获取行业数据失败: {e}")

        # 确定实际使用的数据源
        used_sources = []
        if industries:
            used_sources = list(set(enabled_sources))
        if len(industries) > 0 and any('akshare' in str(ind).lower() for ind in industries[:10]):
            if 'akshare' not in used_sources:
                used_sources.append('akshare')

        return {
            "industries": industries,
            "total": len(industries),
            "source": "+".join(used_sources) if used_sources else "database"  # 🔥 返回数据来源
        }

    except Exception as e:
        logger.error(f"[get_industries] 获取行业列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# MCP智能选股查询
class MCPQueryRequest(BaseModel):
    """MCP查询请求"""
    query: str = Field(..., description="用户的自然语言查询，例如：'PE<20且ROE>15%的股票'、'涨停的股票'等")
    market: str = Field("AG", description="市场类型：AG=A股，JJ=基金，ZS=指数")
    max_results: int = Field(50, ge=1, le=200, description="最大返回结果数")


class MCPQueryResponse(BaseModel):
    """MCP查询响应"""
    success: bool
    message: str
    stocks: List[Dict[str, Any]]
    query: str
    original_query: str
    total: int
    columns: List[str]


@router.post("/mcp-query")
async def mcp_query_stocks(
    request: MCPQueryRequest,
    user: dict = Depends(get_current_user)
):
    """
    使用MCP工具进行智能选股查询
    
    支持的自然语言查询示例：
    - "PE<20且ROE>15%的股票"
    - "涨停的股票"
    - "涨幅超过5%的股票"
    - "MACD金叉的股票"
    - "主力资金净流入的股票"
    - "半导体行业PE中位数"
    - "突破20日均线的股票"
    """
    try:
        result = await mcp_screening_svc.query_stocks_with_llm(
            user_query=request.query,
            market=request.market,
            max_results=request.max_results
        )
        # 验证结果格式（确保所有字段都存在）
        try:
            response_data = MCPQueryResponse(**result)
            return ok(data=response_data.dict())
        except Exception as validation_error:
            logger.error(f"[MCP选股] 响应验证失败: {validation_error}")
            # 如果验证失败，直接返回结果（确保包含所有必需字段）
            return ok(data=result)
    except Exception as e:
        logger.error(f"[MCP选股] 查询失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"MCP查询失败: {str(e)}")