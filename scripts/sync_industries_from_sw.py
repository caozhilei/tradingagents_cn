#!/usr/bin/env python3
"""
从申万行业分类同步行业数据
使用AKShare的申万行业分类接口获取行业数据
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne
from app.core.config import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def sync_industries_from_sw():
    """从申万行业分类同步行业数据"""
    try:
        import akshare as ak
        
        logger.info("=" * 80)
        logger.info("🚀 开始从申万行业分类同步行业数据")
        logger.info("=" * 80)
        
        # 连接MongoDB
        logger.info("\n🔌 连接MongoDB...")
        client = AsyncIOMotorClient(settings.MONGO_URI)
        db = client[settings.MONGO_DB]
        collection = db["stock_basic_info"]
        
        # 1. 获取申万行业分类数据
        logger.info("\n📋 步骤1: 获取申万行业分类数据...")
        
        def fetch_sw_industry():
            try:
                # 尝试使用申万行业分类接口
                # 方法1: 获取申万行业分类列表
                return ak.sw_index_cons(index_code="801010")  # 申万一级行业：农林牧渔
            except:
                try:
                    # 方法2: 获取申万行业分类股票列表
                    return ak.sw_index_cons(index_code="801010")
                except:
                    # 方法3: 获取申万行业分类指数列表
                    return ak.sw_index_cons(index_code="801010")
        
        # 先尝试获取申万行业分类指数列表
        logger.info("  尝试获取申万行业分类指数列表...")
        
        def fetch_sw_index_list():
            try:
                # 获取申万一级行业指数列表
                return ak.sw_index_cons(index_code="801010")
            except Exception as e:
                logger.warning(f"  获取申万指数列表失败: {e}")
                return None
        
        # 尝试不同的申万行业分类接口
        sw_data = None
        industry_stock_map: Dict[str, str] = {}  # {code: industry}
        
        # 方法1: 尝试获取申万行业分类股票列表（通过行业代码）
        logger.info("  方法1: 通过申万行业代码获取股票列表...")
        
        # 申万一级行业代码列表（常见行业）
        sw_industry_codes = [
            "801010",  # 农林牧渔
            "801020",  # 采掘
            "801030",  # 化工
            "801040",  # 钢铁
            "801050",  # 有色金属
            "801080",  # 电子
            "801110",  # 家用电器
            "801120",  # 食品饮料
            "801130",  # 纺织服装
            "801140",  # 轻工制造
            "801150",  # 医药生物
            "801160",  # 公用事业
            "801170",  # 交通运输
            "801180",  # 房地产
            "801200",  # 商业贸易
            "801210",  # 休闲服务
            "801230",  # 综合
            "801710",  # 建筑材料
            "801720",  # 建筑装饰
            "801730",  # 电气设备
            "801740",  # 国防军工
            "801750",  # 计算机
            "801760",  # 传媒
            "801770",  # 通信
            "801780",  # 银行
            "801790",  # 非银金融
            "801880",  # 汽车
            "801890",  # 机械设备
        ]
        
        # 申万行业代码到行业名称的映射
        sw_industry_names = {
            "801010": "农林牧渔",
            "801020": "采掘",
            "801030": "化工",
            "801040": "钢铁",
            "801050": "有色金属",
            "801080": "电子",
            "801110": "家用电器",
            "801120": "食品饮料",
            "801130": "纺织服装",
            "801140": "轻工制造",
            "801150": "医药生物",
            "801160": "公用事业",
            "801170": "交通运输",
            "801180": "房地产",
            "801200": "商业贸易",
            "801210": "休闲服务",
            "801230": "综合",
            "801710": "建筑材料",
            "801720": "建筑装饰",
            "801730": "电气设备",
            "801740": "国防军工",
            "801750": "计算机",
            "801760": "传媒",
            "801770": "通信",
            "801780": "银行",
            "801790": "非银金融",
            "801880": "汽车",
            "801890": "机械设备",
        }
        
        success_count = 0
        failed_count = 0
        
        for idx, industry_code in enumerate(sw_industry_codes, 1):
            industry_name = sw_industry_names.get(industry_code, f"行业{industry_code}")
            
            try:
                def fetch_stocks():
                    try:
                        return ak.sw_index_cons(index_code=industry_code)
                    except:
                        return None
                
                stocks_df = await asyncio.to_thread(fetch_stocks)
                
                if stocks_df is not None and not stocks_df.empty:
                    # 提取股票代码
                    stock_count = 0
                    for _, stock_row in stocks_df.iterrows():
                        code = str(stock_row.get('品种代码', '') or stock_row.get('代码', '') or stock_row.get('code', '')).strip()
                        if code:
                            code = code.zfill(6)
                            industry_stock_map[code] = industry_name
                            stock_count += 1
                    
                    success_count += 1
                    logger.info(f"  ✅ [{idx}/{len(sw_industry_codes)}] {industry_name}: {stock_count} 只股票")
                else:
                    failed_count += 1
                    logger.debug(f"  ⚠️  [{idx}/{len(sw_industry_codes)}] {industry_name}: 无数据")
                
                # 添加延迟，避免API限流
                await asyncio.sleep(0.5)
                
            except Exception as e:
                failed_count += 1
                logger.warning(f"  ⚠️  [{idx}/{len(sw_industry_codes)}] {industry_name}: 获取失败 - {e}")
                await asyncio.sleep(0.5)
                continue
        
        logger.info(f"\n✅ 成功获取 {success_count} 个行业的股票数据")
        logger.info(f"⚠️  失败 {failed_count} 个行业")
        logger.info(f"📊 共获取 {len(industry_stock_map)} 只股票的行业信息")
        
        if not industry_stock_map:
            logger.warning("⚠️  没有获取到任何行业数据，尝试备用方法...")
            
            # 备用方法：尝试使用其他AKShare接口
            try:
                logger.info("  尝试使用股票基本信息接口...")
                def fetch_stock_list():
                    return ak.stock_info_a_code_name()
                
                stock_list = await asyncio.to_thread(fetch_stock_list)
                if stock_list is not None and not stock_list.empty:
                    logger.info(f"  成功获取股票列表，共 {len(stock_list)} 只股票")
                    logger.info("  注意：此接口不包含行业信息，需要使用其他方法获取行业数据")
            except Exception as e:
                logger.warning(f"  备用方法也失败: {e}")
            
            return
        
        # 2. 批量更新AKShare数据源
        logger.info("\n💾 步骤2: 批量更新AKShare数据源的行业数据...")
        
        operations = []
        update_count = 0
        batch_size = 100
        
        for code, industry in industry_stock_map.items():
            operations.append(
                UpdateOne(
                    {"code": code, "source": "akshare"},
                    {"$set": {"industry": industry, "updated_at": datetime.utcnow()}},
                    upsert=False
                )
            )
            
            if len(operations) >= batch_size:
                try:
                    result = await collection.bulk_write(operations, ordered=False)
                    update_count += result.modified_count
                    logger.info(f"  已更新 {update_count} 只股票的行业数据...")
                    operations = []
                except Exception as e:
                    logger.warning(f"  批量更新失败: {e}")
                    operations = []
        
        if operations:
            try:
                result = await collection.bulk_write(operations, ordered=False)
                update_count += result.modified_count
            except Exception as e:
                logger.warning(f"  最后一批更新失败: {e}")
        
        logger.info(f"✅ 共更新 {update_count} 只AKShare数据源股票的行业数据")
        
        # 3. 同步到TDX数据源
        logger.info("\n💾 步骤3: 将行业数据同步到TDX数据源...")
        
        tdx_operations = []
        tdx_update_count = 0
        
        for code, industry in industry_stock_map.items():
            # 获取股票名称
            stock_doc = await collection.find_one(
                {"code": code, "source": "akshare"},
                {"name": 1}
            )
            stock_name = stock_doc.get("name", f"股票{code}") if stock_doc else f"股票{code}"
            
            tdx_operations.append(
                UpdateOne(
                    {"code": code, "source": "tdx"},
                    {
                        "$set": {
                            "code": code,
                            "symbol": code,
                            "name": stock_name,
                            "industry": industry,
                            "source": "tdx",
                            "updated_at": datetime.utcnow()
                        }
                    },
                    upsert=True
                )
            )
            
            if len(tdx_operations) >= batch_size:
                try:
                    result = await collection.bulk_write(tdx_operations, ordered=False)
                    tdx_update_count += result.modified_count + result.upserted_count
                    logger.info(f"  已同步 {tdx_update_count} 条TDX记录...")
                    tdx_operations = []
                except Exception as e:
                    logger.warning(f"  批量同步TDX失败: {e}")
                    tdx_operations = []
        
        if tdx_operations:
            try:
                result = await collection.bulk_write(tdx_operations, ordered=False)
                tdx_update_count += result.modified_count + result.upserted_count
            except Exception as e:
                logger.warning(f"  最后一批TDX同步失败: {e}")
        
        logger.info(f"✅ 共同步 {tdx_update_count} 条TDX数据源记录")
        
        # 4. 验证结果
        logger.info("\n📊 步骤4: 验证同步结果...")
        
        for source in ['akshare', 'tdx']:
            total = await collection.count_documents({"source": source})
            with_industry = await collection.count_documents({
                "source": source,
                "industry": {"$ne": None, "$ne": "", "$exists": True}
            })
            logger.info(f"  {source.upper()}数据源:")
            logger.info(f"    股票总数: {total}")
            logger.info(f"    有行业数据: {with_industry}")
            logger.info(f"    覆盖率: {with_industry*100//total if total > 0 else 0}%")
        
        # 统计行业分布
        pipeline = [
            {
                "$match": {
                    "source": {"$in": ["akshare", "tdx"]},
                    "industry": {"$ne": None, "$ne": "", "$exists": True}
                }
            },
            {
                "$group": {
                    "_id": "$industry",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 30}
        ]
        
        industries = []
        async for doc in collection.aggregate(pipeline):
            industries.append({
                "industry": doc.get("_id"),
                "count": doc.get("count", 0)
            })
        
        if industries:
            logger.info(f"\n📊 前30个行业分布:")
            for i, ind in enumerate(industries, 1):
                logger.info(f"  {i}. {ind['industry']}: {ind['count']}只股票")
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 申万行业分类数据同步完成！")
        logger.info("=" * 80)
        
        client.close()
        
    except ImportError:
        logger.error("❌ akshare库未安装，请运行: pip install akshare")
    except Exception as e:
        logger.error(f"❌ 同步失败: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(sync_industries_from_sw())


