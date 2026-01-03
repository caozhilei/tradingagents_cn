"""
MCP选股服务 - 使用LLM调用MCP工具进行智能选股
"""
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.data_sources.tdx_adapter import TDXAdapter
from app.services.data_sources.mcp_transformer import parse_wenda_response
from app.core.unified_config import UnifiedConfigManager

logger = logging.getLogger(__name__)


class MCPScreeningService:
    """MCP选股服务"""
    
    def __init__(self):
        self.tdx_adapter = TDXAdapter()
        self.config_manager = UnifiedConfigManager()
    
    async def query_stocks_with_llm(
        self,
        user_query: str,
        market: str = "AG",
        max_results: int = 50
    ) -> Dict[str, Any]:
        """
        使用LLM理解用户查询，然后调用MCP工具查找股票
        
        Args:
            user_query: 用户的自然语言查询
            market: 市场类型 (AG=A股, JJ=基金, ZS=指数)
            max_results: 最大返回结果数
            
        Returns:
            包含股票列表和查询信息的字典
        """
        try:
            # 获取LLM配置列表
            llm_configs = self.config_manager.get_llm_configs()
            if not llm_configs:
                return {
                    "success": False,
                    "message": "未配置LLM，无法进行智能查询",
                    "stocks": [],
                    "query": user_query,
                    "original_query": user_query,
                    "total": 0,
                    "columns": []
                }
            
            # 使用第一个启用的LLM配置，或默认模型
            default_model_name = self.config_manager.get_default_model()
            llm_config = None
            
            # 查找匹配的配置
            for config in llm_configs:
                if config.model_name == default_model_name or (not llm_config and config.enabled):
                    llm_config = config
                    break
            
            # 如果没找到，使用第一个启用的配置
            if not llm_config:
                llm_config = next((c for c in llm_configs if c.enabled), llm_configs[0] if llm_configs else None)
            
            if not llm_config:
                return {
                    "success": False,
                    "message": "未找到可用的LLM配置",
                    "stocks": [],
                    "query": user_query,
                    "original_query": user_query,
                    "total": 0,
                    "columns": []
                }
            
            # 转换为字典格式
            config_dict = {
                "provider": llm_config.provider.value if hasattr(llm_config.provider, 'value') else str(llm_config.provider),
                "model_name": llm_config.model_name,
                "backend_url": getattr(llm_config, 'backend_url', None) or getattr(llm_config, 'api_base', None) or "",
                "temperature": getattr(llm_config, 'temperature', 0.1),
                "max_tokens": getattr(llm_config, 'max_tokens', 2000),
                "timeout": getattr(llm_config, 'timeout', 60),
                "api_key": getattr(llm_config, 'api_key', None) or ""
            }
            
            # 创建LLM实例
            llm = await self._create_llm(config_dict)
            
            # 使用LLM将用户查询转换为MCP查询格式
            mcp_query = await self._convert_query_with_llm(llm, user_query, market)
            
            logger.info(f"🔄 [MCP选股] LLM转换后的查询: {mcp_query}")
            
            # 调用MCP工具（使用异步版本）
            result = await self.tdx_adapter.query_wenda_via_mcp_async(
                question=mcp_query,
                market=market,
                page=1,
                size=max_results,
                structured=True,
                store=False
            )
            
            if not result:
                return {
                    "success": False,
                    "message": "MCP查询失败，请检查MCP配置",
                    "stocks": [],
                    "query": mcp_query,
                    "original_query": user_query,
                    "total": 0,
                    "columns": []
                }
            
            # 解析结果
            parsed_result = result if isinstance(result, dict) else parse_wenda_response(result)
            
            # 转换为股票列表格式
            stocks = self._convert_to_stock_list(parsed_result)
            
            return {
                "success": True,
                "message": f"找到 {len(stocks)} 只股票",
                "stocks": stocks,
                "query": mcp_query,
                "original_query": user_query,
                "total": parsed_result.get("total", len(stocks)),
                "columns": parsed_result.get("columns", [])
            }
            
        except Exception as e:
            logger.error(f"❌ [MCP选股] 查询失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"查询失败: {str(e)}",
                "stocks": [],
                "query": user_query,
                "original_query": user_query,
                "total": 0,
                "columns": []
            }
    
    async def _create_llm(self, config: Dict[str, Any]):
        """创建LLM实例"""
        from tradingagents.graph.trading_graph import create_llm_by_provider
        
        # 从配置中提取参数
        provider = config.get("provider", "dashscope")
        model = config.get("model_name") or config.get("model", "qwen-plus")
        backend_url = config.get("backend_url", "")
        temperature = config.get("temperature", 0.1)
        max_tokens = config.get("max_tokens", 2000)
        timeout = config.get("timeout", 60)
        
        # 获取API Key（优先从环境变量，然后从配置）
        api_key = config.get("api_key") or os.getenv("DASHSCOPE_API_KEY", "")
        
        return create_llm_by_provider(
            provider=provider,
            model=model,
            backend_url=backend_url,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            api_key=api_key
        )
    
    async def _convert_query_with_llm(self, llm, user_query: str, market: str) -> str:
        """
        使用LLM将用户的自然语言查询转换为MCP查询格式
        
        MCP查询规则：
        1. 单只个股：{股票名称/代码}+{查询内容}
        2. 多只个股对比：拆分为独立查询
        3. 行业/板块：{行业名称}+{指标}
        4. 复杂条件：使用逻辑运算符(且/或)
        """
        from langchain_core.messages import HumanMessage, SystemMessage
        
        system_prompt = f"""你是一位专业的股票查询助手，负责将用户的自然语言查询转换为MCP（通达信问小达）查询格式。

MCP查询规则：
1. **单只个股查询**：格式为 `[股票名称/代码]+[查询内容]`
   - 示例：`贵州茅台600519市盈率<20且ROE>15%`
   - 支持多条件组合，使用逻辑运算符(且/或)

2. **多只个股对比**：必须拆分为独立查询
   - 示例：`比较茅台和五粮液` → 拆分为 `贵州茅台财务数据` 和 `五粮液财务数据`

3. **行业/板块查询**：格式为 `[行业名称]+[指标]`
   - 示例：`半导体行业PE中位数`

4. **条件筛选查询**：
   - 示例：`PE<20且ROE>15%的股票` → `PE<20且ROE>15%`
   - 示例：`涨停的股票` → `涨停`
   - 示例：`涨幅超过5%的股票` → `涨幅>5%`
   - 示例：`成交量放大的股票` → `量比>1.5`

5. **技术指标查询**：
   - 示例：`MACD金叉的股票` → `MACD金叉`
   - 示例：`突破20日均线的股票` → `突破MA20`

6. **资金流向查询**：
   - 示例：`主力资金净流入的股票` → `主力净流入`
   - 示例：`北向资金流入的股票` → `北向资金流入`

7. **财务指标查询**：
   - 示例：`ROE>20%的股票` → `ROE>20%`
   - 示例：`净利润增长的股票` → `净利润增长`

重要提示：
- 只返回转换后的MCP查询语句，不要添加任何解释
- 保持查询简洁明了，符合MCP查询规范
- 如果用户查询不明确，返回最可能的查询格式
- 市场类型：{market}（AG=A股，JJ=基金，ZS=指数）

用户查询：{user_query}

请直接返回转换后的MCP查询语句："""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query)
        ]
        
        try:
            response = llm.invoke(messages)
            mcp_query = response.content.strip()
            
            # 清理可能的引号或多余格式
            if mcp_query.startswith('"') and mcp_query.endswith('"'):
                mcp_query = mcp_query[1:-1]
            if mcp_query.startswith("'") and mcp_query.endswith("'"):
                mcp_query = mcp_query[1:-1]
            
            return mcp_query
        except Exception as e:
            logger.error(f"❌ [MCP选股] LLM转换失败: {e}")
            # 如果LLM转换失败，直接返回用户查询
            return user_query
    
    def _convert_to_stock_list(self, parsed_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """将MCP解析结果转换为股票列表格式"""
        stocks = []
        
        records = parsed_result.get("records", [])
        columns = parsed_result.get("columns", [])
        
        # 查找股票代码和名称字段
        code_field = None
        name_field = None
        
        for col in columns:
            col_lower = col.lower()
            if "code" in col_lower or "代码" in col or "sec_code" in col_lower:
                code_field = col
            if "name" in col_lower or "名称" in col or "sec_name" in col_lower:
                name_field = col
        
        for record in records:
            stock = {}
            
            # 提取代码和名称
            if code_field and code_field in record:
                stock["code"] = str(record[code_field]).zfill(6)
            elif "code" in record:
                stock["code"] = str(record["code"]).zfill(6)
            else:
                # 尝试从其他字段推断
                for key, value in record.items():
                    if isinstance(value, str) and value.isdigit() and len(value) == 6:
                        stock["code"] = value
                        break
            
            if name_field and name_field in record:
                stock["name"] = str(record[name_field])
            elif "name" in record:
                stock["name"] = str(record["name"])
            
            # 添加其他字段
            for key, value in record.items():
                if key not in ["code", "name", code_field, name_field]:
                    stock[key] = value
            
            if stock.get("code"):
                stocks.append(stock)
        
        return stocks

