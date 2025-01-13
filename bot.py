# depined_bot.py

import asyncio
import aiohttp
from fake_useragent import UserAgent
import logging
import json
import os
import signal
from datetime import datetime
from colorama import Fore, Style, init
import sys

# 初始化 colorama
init(autoreset=True)

# =========================
# 日志记录模块
# =========================

class Logger:
    def __init__(self):
        self.logger = logging.getLogger("DepinedBot")
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log(self, level, message, value=''):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level = level.lower()
        colors = {
            'info': Fore.CYAN + Style.BRIGHT,
            'warn': Fore.YELLOW + Style.BRIGHT,
            'error': Fore.RED + Style.BRIGHT,
            'success': Fore.GREEN + Style.BRIGHT,
            'debug': Fore.MAGENTA + Style.BRIGHT
        }
        color = colors.get(level, Fore.WHITE)
        level_tag = f"[ {level.upper()} ]"
        timestamp = f"[ {now} ]"
        formatted_message = f"{Fore.CYAN + Style.BRIGHT}[ DepinedBot ]{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}{timestamp}{Style.RESET_ALL} {color}{level_tag}{Style.RESET_ALL} {message}"
        
        if value:
            if isinstance(value, dict) or isinstance(value, list):
                try:
                    serialized = json.dumps(value, ensure_ascii=False)
                    formatted_value = f" {Fore.GREEN}{serialized}{Style.RESET_ALL}" if level != 'error' else f" {Fore.RED}{serialized}{Style.RESET_ALL}"
                except Exception as e:
                    self.error("序列化日志值时出错:", str(e))
                    formatted_value = f" {Fore.RED}无法序列化的值{Style.RESET_ALL}"
            else:
                if level == 'error':
                    formatted_value = f" {Fore.RED}{value}{Style.RESET_ALL}"
                elif level == 'warn':
                    formatted_value = f" {Fore.YELLOW}{value}{Style.RESET_ALL}"
                else:
                    formatted_value = f" {Fore.GREEN}{value}{Style.RESET_ALL}"
            formatted_message += formatted_value

        self.logger.log(getattr(logging, level.upper(), logging.INFO), formatted_message)

    def info(self, message, value=''):
        self.log('info', message, value)

    def warn(self, message, value=''):
        self.log('warn', message, value)

    def error(self, message, value=''):
        self.log('error', message, value)

    def success(self, message, value=''):
        self.log('success', message, value)

    def debug(self, message, value=''):
        self.log('debug', message, value)

logger = Logger()

# =========================
# 辅助函数模块
# =========================

async def delay(seconds):
    """延迟执行"""
    await asyncio.sleep(seconds)

async def save_to_file(filename, data):
    """将数据保存到文件，每条数据占一行"""
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            if isinstance(data, (dict, list)):
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
            else:
                f.write(str(data) + '\n')
        logger.info(f"数据已保存到 {filename}")
    except Exception as e:
        logger.error(f"保存数据到 {filename} 时失败:", str(e))

async def read_file(path_file):
    """读取文件并返回非空行的列表"""
    try:
        if not os.path.exists(path_file):
            logger.warn(f"文件 {path_file} 不存在。")
            return []
        with open(path_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return [line.strip() for line in lines if line.strip()]
    except Exception as e:
        logger.error(f"读取文件 {path_file} 时出错:", str(e))
        return []

def new_agent(proxy=None):
    """根据代理类型创建代理字典"""
    if proxy:
        if proxy.startswith('http://') or proxy.startswith('https://'):
            return {
                'http': proxy,
                'https': proxy
            }
        elif proxy.startswith('socks4://') or proxy.startswith('socks5://'):
            return {
                'http': proxy,
                'https': proxy
            }
        else:
            logger.warn(f"不支持的代理类型: {proxy}")
            return None
    return None

# =========================
# API 模块
# =========================

ua = UserAgent()
headers = {
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": ua.random
}

def make_headers(token=None):
    """生成请求头"""
    hdr = headers.copy()
    hdr['Content-Type'] = 'application/json'
    if token:
        hdr['Authorization'] = f'Bearer {token}'
    return hdr

async def register_user(session, email, password):
    """注册用户"""
    url = 'https://api.depined.org/api/user/register'
    payload = {
        'email': email,
        'password': password
    }
    try:
        async with session.post(url, json=payload, headers=make_headers()) as response:
            if response.status == 200:
                data = await response.json()
                logger.success('用户注册成功:', data.get('message', ''))
                return data
            else:
                error_data = await response.json()
                logger.error('注册用户时出错:', error_data)
                return None
    except aiohttp.ClientError as e:
        logger.error('注册用户时出错:', str(e))
        return None

async def login_user(session, email, password):
    """用户登录"""
    url = 'https://api.depined.org/api/user/login'
    payload = {
        'email': email,
        'password': password
    }
    try:
        async with session.post(url, json=payload, headers=make_headers()) as response:
            if response.status == 200:
                data = await response.json()
                logger.success('用户登录成功:', data.get('message', ''))
                return data
            else:
                error_data = await response.json()
                logger.error('用户登录时出错:', error_data)
                return None
    except aiohttp.ClientError as e:
        logger.error('用户登录时出错:', str(e))
        return None

async def create_user_profile(session, token, payload):
    """创建用户资料"""
    url = 'https://api.depined.org/api/user/profile-creation'
    try:
        async with session.post(url, json=payload, headers=make_headers(token)) as response:
            if response.status == 200:
                data = await response.json()
                logger.success('用户资料创建成功:', data.get('message', ''))
                return data
            else:
                error_data = await response.json()
                logger.error('创建用户资料时出错:', error_data)
                return None
    except aiohttp.ClientError as e:
        logger.error('创建用户资料时出错:', str(e))
        return None

async def confirm_user_reff(session, token, referral_code):
    """确认用户推荐码"""
    url = 'https://api.depined.org/api/access-code/referal'
    payload = {
        'referral_code': referral_code
    }
    try:
        async with session.post(url, json=payload, headers=make_headers(token)) as response:
            if response.status == 200:
                data = await response.json()
                logger.success('确认用户推荐码成功:', data.get('message', ''))
                return data
            else:
                error_data = await response.json()
                logger.error('确认用户推荐码时出错:', error_data)
                return None
    except aiohttp.ClientError as e:
        logger.error('确认用户推荐码时出错:', str(e))
        return None

async def get_user_info(session, token, proxy=None):
    """获取用户信息"""
    url = 'https://api.depined.org/api/user/details'
    try:
        proxies = new_agent(proxy)
        async with session.get(url, headers=make_headers(token), proxy=proxies.get('http') if proxies else None) as response:
            if response.status == 200:
                data = await response.json()
                logger.info('获取用户信息成功')
                return data
            else:
                error_data = await response.json()
                logger.error('获取用户信息时出错:', error_data)
                return None
    except aiohttp.ClientError as e:
        logger.error('获取用户信息时出错:', str(e))
        return None

async def get_earnings(session, token, proxy=None):
    """获取收益信息"""
    url = 'https://api.depined.org/api/stats/epoch-earnings'
    try:
        proxies = new_agent(proxy)
        async with session.get(url, headers=make_headers(token), proxy=proxies.get('http') if proxies else None) as response:
            if response.status == 200:
                data = await response.json()
                logger.info('获取收益信息成功')
                return data
            else:
                error_data = await response.json()
                logger.error('获取收益信息时出错:', error_data)
                return None
    except aiohttp.ClientError as e:
        logger.error('获取收益信息时出错:', str(e))
        return None

async def connect(session, token, proxy=None):
    """连接用户"""
    url = 'https://api.depined.org/api/user/widget-connect'
    payload = {
        'connected': True
    }
    try:
        proxies = new_agent(proxy)
        async with session.post(url, json=payload, headers=make_headers(token), proxy=proxies.get('http') if proxies else None) as response:
            if response.status == 200:
                data = await response.json()
                logger.success('连接用户成功:', data.get('message', ''))
                return data
            else:
                error_data = await response.json()
                logger.error('连接用户时出错:', error_data)
                return None
    except aiohttp.ClientError as e:
        logger.error('连接用户时出错:', str(e))
        return None

# =========================
# 主程序逻辑
# =========================

async def process_account(session, token, proxy, index):
    """处理单个账户，包括获取用户信息和设置定时任务"""
    try:
        user_data = await get_user_info(session, token, proxy)
        if user_data and 'data' in user_data:
            email = user_data['data'].get('email', '')
            verified = user_data['data'].get('verified', False)
            current_tier = user_data['data'].get('current_tier', '')
            points_balance = user_data['data'].get('points_balance', 0)
            logger.info(f"账户 {index + 1} 信息:", {
                'email': email,
                'verified': verified,
                'current_tier': current_tier,
                'points_balance': points_balance
            })
        
        # 设置每30秒执行一次的定时任务
        async def periodic_task():
            while True:
                connect_res = await connect(session, token, proxy)
                logger.info(f"账户 {index + 1} Ping 结果:", connect_res or {'message': '未知错误'})
                
                earnings_res = await get_earnings(session, token, proxy)
                if earnings_res and 'data' in earnings_res:
                    logger.info(f"账户 {index + 1} 收益结果:", earnings_res['data'])
                else:
                    logger.info(f"账户 {index + 1} 收益结果:", {'message': '未知错误'})
                
                await asyncio.sleep(30)

        asyncio.create_task(periodic_task())

    except Exception as e:
        logger.error(f"处理账户 {index + 1} 时出错:", str(e))

async def main():
    """主函数"""
    # 显示横幅
    banner = """
    =========================
    === 欢迎使用 DepinedBot ===
    =========================
    """
    logger.info(banner)
    
    # 延迟3秒
    await delay(3)
    
    # 读取 tokens 和 proxies
    tokens = await read_file("tokens.txt")
    if not tokens:
        logger.error('在 tokens.txt 中未找到任何令牌。')
        return
    
    proxies = await read_file("proxy.txt")
    if not proxies:
        logger.warn('未配置代理，程序将不使用代理。')
    
    logger.info(f"开始处理所有账户: {len(tokens)} 个账户")
    
    # 创建 aiohttp ClientSession
    timeout = aiohttp.ClientTimeout(total=60)
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        # 处理每个账户
        tasks = []
        for index, token in enumerate(tokens):
            proxy = proxies[index % len(proxies)] if proxies else None
            task = asyncio.create_task(process_account(session, token, proxy, index))
            tasks.append(task)
        
        await asyncio.gather(*tasks)

        # 保持程序运行，等待所有定时任务执行
        await asyncio.Event().wait()

# =========================
# 进程信号处理
# =========================

def shutdown():
    """优雅地关闭程序"""
    logger.warn("接收到终止信号，正在清理并退出程序...")
    sys.exit(0)

def setup_signal_handlers():
    """设置信号处理器"""
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, shutdown)
        except NotImplementedError:
            # 例如在 Windows 上，某些信号可能不被支持
            signal.signal(sig, lambda s, f: shutdown())

# =========================
# 运行主程序
# =========================

if __name__ == "__main__":
    try:
        setup_signal_handlers()
        asyncio.run(main())
    except Exception as e:
        logger.error("程序运行时出错:", str(e))
