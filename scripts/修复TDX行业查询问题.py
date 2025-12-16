#!/usr/bin/env python3
"""
修复TDX行业查询相关问题的脚本

功能：
1. 修复.env文件的编码问题（确保为UTF-8）
2. 检查网络代理设置（AKShare需要访问外部API）
3. 确保TDX服务器可以正常连接

使用方法：
    python scripts/修复TDX行业查询问题.py
"""

import sys
import os
from pathlib import Path
import logging

# 尝试导入chardet，如果不存在则使用其他方法
try:
    import chardet
    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def fix_env_file_encoding():
    """修复.env文件的编码问题，确保为UTF-8"""
    logger.info("=" * 80)
    logger.info("🔧 修复 .env 文件编码问题")
    logger.info("=" * 80)
    
    env_file = project_root / ".env"
    
    if not env_file.exists():
        logger.warning(f"⚠️  .env 文件不存在: {env_file}")
        logger.info("💡 提示: 如果.env文件在其他位置，请手动检查编码")
        return False
    
    try:
        # 1. 检测当前编码
        logger.info(f"📂 检查文件: {env_file}")
        
        with open(env_file, 'rb') as f:
            raw_data = f.read()
        
        # 使用chardet检测编码（如果可用）
        if HAS_CHARDET:
            detected = chardet.detect(raw_data)
            current_encoding = detected.get('encoding', 'unknown')
            confidence = detected.get('confidence', 0)
            logger.info(f"   检测到的编码: {current_encoding} (置信度: {confidence:.2%})")
        else:
            current_encoding = None
            confidence = 0
            logger.info("   编码检测库(chardet)未安装，将尝试常见编码")
        
        # 2. 尝试读取文件
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info("✅ 文件可以UTF-8方式读取")
            return True
        except UnicodeDecodeError as e:
            logger.warning(f"⚠️  UTF-8读取失败: {e}")
            
            # 3. 尝试使用检测到的编码读取
            if HAS_CHARDET and current_encoding and current_encoding != 'utf-8' and confidence > 0.5:
                try:
                    logger.info(f"🔄 尝试使用 {current_encoding} 编码读取...")
                    with open(env_file, 'r', encoding=current_encoding) as f:
                        content = f.read()
                    
                    # 4. 转换为UTF-8并保存
                    logger.info("💾 转换为UTF-8编码并保存...")
                    backup_file = env_file.with_suffix('.env.backup')
                    env_file.rename(backup_file)
                    logger.info(f"📋 备份原文件到: {backup_file}")
                    
                    with open(env_file, 'w', encoding='utf-8', newline='\n') as f:
                        f.write(content)
                    
                    logger.info("✅ .env文件已成功转换为UTF-8编码")
                    logger.info(f"📋 原文件已备份到: {backup_file}")
                    return True
                    
                except Exception as e2:
                    logger.error(f"❌ 转换失败: {e2}")
                    return False
            else:
                # 尝试常见编码
                encodings = ['gbk', 'gb2312', 'latin-1', 'cp1252']
                for enc in encodings:
                    try:
                        logger.info(f"🔄 尝试使用 {enc} 编码读取...")
                        with open(env_file, 'r', encoding=enc) as f:
                            content = f.read()
                        
                        # 转换为UTF-8
                        logger.info("💾 转换为UTF-8编码并保存...")
                        backup_file = env_file.with_suffix('.env.backup')
                        env_file.rename(backup_file)
                        logger.info(f"📋 备份原文件到: {backup_file}")
                        
                        with open(env_file, 'w', encoding='utf-8', newline='\n') as f:
                            f.write(content)
                        
                        logger.info("✅ .env文件已成功转换为UTF-8编码")
                        logger.info(f"📋 原文件已备份到: {backup_file}")
                        return True
                    except Exception:
                        continue
                
                logger.error("❌ 无法识别文件编码，请手动检查")
                return False
                
    except Exception as e:
        logger.error(f"❌ 处理.env文件失败: {e}")
        return False


def check_proxy_settings():
    """检查网络代理设置"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("🌐 检查网络代理设置")
    logger.info("=" * 80)
    
    # 检查环境变量中的代理设置
    http_proxy = os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
    https_proxy = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')
    no_proxy = os.getenv('NO_PROXY') or os.getenv('no_proxy')
    
    logger.info("📋 当前代理设置:")
    logger.info(f"   HTTP_PROXY: {http_proxy or '(未设置)'}")
    logger.info(f"   HTTPS_PROXY: {https_proxy or '(未设置)'}")
    logger.info(f"   NO_PROXY: {no_proxy or '(未设置)'}")
    
    # 检查.env文件中的代理配置
    env_file = project_root / ".env"
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            has_http_proxy = 'HTTP_PROXY=' in content or 'http_proxy=' in content
            has_https_proxy = 'HTTPS_PROXY=' in content or 'https_proxy=' in content
            has_no_proxy = 'NO_PROXY=' in content or 'no_proxy=' in content
            
            logger.info("")
            logger.info("📋 .env文件中的代理配置:")
            logger.info(f"   HTTP_PROXY: {'✅ 已配置' if has_http_proxy else '❌ 未配置'}")
            logger.info(f"   HTTPS_PROXY: {'✅ 已配置' if has_https_proxy else '❌ 未配置'}")
            logger.info(f"   NO_PROXY: {'✅ 已配置' if has_no_proxy else '❌ 未配置'}")
            
            # 检查NO_PROXY是否包含必要的域名
            if has_no_proxy:
                no_proxy_lower = content.lower()
                required_domains = [
                    'eastmoney.com',
                    'push2.eastmoney.com',
                    'gtimg.cn',
                    'sinaimg.cn',
                    'tushare.pro',
                    'baostock.com'
                ]
                
                missing_domains = []
                for domain in required_domains:
                    if domain not in no_proxy_lower:
                        missing_domains.append(domain)
                
                if missing_domains:
                    logger.warning("⚠️  NO_PROXY缺少以下域名:")
                    for domain in missing_domains:
                        logger.warning(f"     - {domain}")
                    logger.info("")
                    logger.info("💡 建议在.env文件中添加以下配置:")
                    logger.info("   NO_PROXY=localhost,127.0.0.1,eastmoney.com,push2.eastmoney.com,82.push2.eastmoney.com,gtimg.cn,sinaimg.cn,api.tushare.pro,baostock.com")
                else:
                    logger.info("✅ NO_PROXY配置完整")
            
        except Exception as e:
            logger.warning(f"⚠️  读取.env文件失败: {e}")
    
    # 测试AKShare连接
    logger.info("")
    logger.info("🧪 测试AKShare连接...")
    try:
        import akshare as ak
        import requests
        
        # 尝试获取少量数据
        try:
            df = ak.stock_zh_a_spot_em()
            logger.info(f"✅ AKShare连接成功，获取到 {len(df)} 条股票数据")
            
            # 测试关键域名
            test_urls = [
                'https://82.push2.eastmoney.com',
                'https://push2.eastmoney.com'
            ]
            
            for url in test_urls:
                try:
                    response = requests.get(url, timeout=5)
                    logger.info(f"✅ {url} 连接成功 (状态码: {response.status_code})")
                except Exception as e:
                    logger.warning(f"⚠️  {url} 连接失败: {e}")
            
            return True
        except Exception as e:
            logger.error(f"❌ AKShare连接失败: {e}")
            logger.info("")
            logger.info("💡 可能的解决方案:")
            logger.info("   1. 检查NO_PROXY配置是否包含eastmoney.com等域名")
            logger.info("   2. 如果使用代理，确保NO_PROXY配置正确")
            logger.info("   3. 检查网络连接是否正常")
            return False
    except ImportError:
        logger.warning("⚠️  akshare库未安装，跳过连接测试")
        return False


def check_tdx_connection():
    """检查TDX服务器连接"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("📡 检查TDX服务器连接")
    logger.info("=" * 80)
    
    try:
        from data.tdx_utils import get_tdx_provider
        
        logger.info("🔄 尝试连接TDX服务器...")
        provider = get_tdx_provider()
        
        if not provider:
            logger.error("❌ 无法获取TDX提供器")
            return False
        
        if provider.connected:
            logger.info("✅ TDX已连接")
        else:
            logger.info("🔌 尝试连接TDX服务器...")
            if provider.connect():
                logger.info("✅ TDX服务器连接成功")
            else:
                logger.error("❌ TDX服务器连接失败")
                logger.info("")
                logger.info("💡 可能的原因:")
                logger.info("   1. TDX服务器不可用或网络问题")
                logger.info("   2. 防火墙阻止连接")
                logger.info("   3. 服务器列表配置错误")
                return False
        
        # 测试获取股票信息
        logger.info("")
        logger.info("🧪 测试获取股票信息...")
        try:
            test_code = "000001"
            realtime_data = provider.get_real_time_data(test_code)
            if realtime_data:
                logger.info(f"✅ 成功获取股票 {test_code} 的实时数据")
                logger.info(f"   股票名称: {realtime_data.get('name', 'N/A')}")
                logger.info(f"   当前价格: {realtime_data.get('price', 'N/A')}")
                return True
            else:
                logger.warning("⚠️  未获取到股票数据")
                return False
        except Exception as e:
            logger.error(f"❌ 获取股票数据失败: {e}")
            return False
            
    except ImportError as e:
        logger.error(f"❌ 导入TDX工具失败: {e}")
        logger.info("💡 提示: 确保已安装pytdx库: pip install pytdx")
        return False
    except Exception as e:
        logger.error(f"❌ TDX连接测试失败: {e}")
        return False


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("🚀 开始修复TDX行业查询问题")
    logger.info("=" * 80)
    logger.info("")
    
    results = {
        'env_file': False,
        'proxy': False,
        'tdx': False
    }
    
    # 1. 修复.env文件编码
    results['env_file'] = fix_env_file_encoding()
    
    # 2. 检查代理设置
    results['proxy'] = check_proxy_settings()
    
    # 3. 检查TDX连接
    results['tdx'] = check_tdx_connection()
    
    # 输出总结
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 修复结果总结")
    logger.info("=" * 80)
    logger.info(f"   .env文件编码: {'✅ 正常' if results['env_file'] else '❌ 需要修复'}")
    logger.info(f"   代理设置: {'✅ 正常' if results['proxy'] else '❌ 需要检查'}")
    logger.info(f"   TDX连接: {'✅ 正常' if results['tdx'] else '❌ 需要修复'}")
    logger.info("=" * 80)
    
    if all(results.values()):
        logger.info("")
        logger.info("🎉 所有检查通过！可以正常使用TDX查询行业信息了。")
    else:
        logger.info("")
        logger.info("⚠️  部分检查未通过，请根据上述提示进行修复。")
    
    return all(results.values())


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ 发生错误: {e}", exc_info=True)
        sys.exit(1)

