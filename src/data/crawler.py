import requests
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger('SteamCrawler')

# Steam 数据获取
class SteamCrawler:
    STORE_API = "https://store.steampowered.com/api/appdetails"
    STORE_SEARCH_API = "https://store.steampowered.com/api/storesearch/"
    REVIEW_API = "https://store.steampowered.com/appreviews/{appid}?json=1&language=all&purchase_type=all&num_per_page=0"
    REVIEW_DETAIL_API = "https://store.steampowered.com/appreviews/{appid}?json=1&language=schinese&purchase_type=all&num_per_page=10&filter=updated&day_range=365"
    STEAMSPY_API = "https://steamspy.com/api.php"

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                       '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }

    def __init__(self, request_delay=0.2, is_running_func=None):
        self.request_delay = request_delay
        self.is_running_func = is_running_func or (lambda: True)
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.session.cookies.set('birthtime', '568022401', domain='store.steampowered.com')
        self.session.cookies.set('wants_mature_content', '1', domain='store.steampowered.com')

    # 可中断的休眠
    def _sleep(self, duration):
        steps = int(duration / 0.1)
        for _ in range(steps):
            if not self.is_running_func():
                return False
            time.sleep(0.1)
        remain = duration - steps * 0.1
        if remain > 0 and self.is_running_func():
            time.sleep(remain)
        return self.is_running_func()

    # 带指数退避的网络请求封装
    def _request_with_retry(self, url, params=None, timeout=15, max_retries=3):
        for attempt in range(max_retries):
            if not self.is_running_func():
                return None
            try:
                resp = self.session.get(url, params=params, timeout=timeout)
                if resp.status_code == 429:
                    # 对于官方 API，429 需要更长的冷却时间
                    is_store_api = "steampowered.com" in url
                    base_wait = 30 if is_store_api else 5
                    wait_time = (2 ** attempt) * base_wait 
                    
                    logger.warning(f"[429 Rate Limit] 触发限流，等待 {wait_time} 秒重试 [{url}]")
                    # 尝试通知外部限流状态（如果提供了回调）
                    if hasattr(self, 'rate_limit_callback') and self.rate_limit_callback:
                        self.rate_limit_callback(wait_time)
                        
                    if not self._sleep(wait_time):
                        return None
                    continue
                resp.raise_for_status()
                return resp
            except requests.exceptions.RequestException as e:
                logger.warning(f"网络异常 (尝试 {attempt+1}/{max_retries}): {e} | URL: {url}")
                if attempt < max_retries - 1:
                    if not self._sleep(2 ** attempt):
                        return None
                else:
                    logger.error(f"网络请求最终失败: {url}")
                    return None
        return None

    # 根据游戏名搜索应用
    def fetch_apps_by_search(self, term: str) -> list:
        params = {'term': term, 'l': 'zh-cn', 'cc': 'CN'}
        resp = self._request_with_retry(self.STORE_SEARCH_API, params=params)
        if resp:
            try:
                data = resp.json()
                if data.get('total') > 0:
                    return data.get('items', [])
            except Exception as e:
                logger.error(f"解析搜索结果失败: {e}")
        return []

    # 从 SteamSpy 批量获取游戏核心指标 (每页 1000 款)
    def fetch_bulk_from_steamspy(self, page=0) -> list:
        params = {'request': 'all', 'page': str(page)}
        resp = self._request_with_retry(self.STEAMSPY_API, params=params)
        if not resp:
            return []
        
        # 检查响应内容是否为有效的 JSON
        content_type = resp.headers.get('Content-Type', '')
        if 'application/json' not in content_type and resp.text.strip() and not resp.text.strip().startswith('{'):
            logger.error(f"SteamSpy API 返回非 JSON 内容: {resp.text[:200]}")
            return []
        
        try:
            data = resp.json()
            if not isinstance(data, dict):
                logger.error(f"SteamSpy API 返回格式异常，期望 dict 得到 {type(data)}")
                return []
            
            games = []
            for appid, info in data.items():
                # 转换 SteamSpy 格式为我们的数据库格式
                games.append({
                    'appid': int(appid),
                    'name': info.get('name', ''),
                    'developer': info.get('developer', ''),
                    'publisher': info.get('publisher', ''),
                    'price_final': int(info.get('price', 0)),
                    'price_initial': int(info.get('initialprice', 0)),
                    'discount_percent': int(info.get('discount', 0)),
                    'is_free': 1 if int(info.get('price', 0)) == 0 else 0,
                    'positive_reviews': int(info.get('positive', 0)),
                    'negative_reviews': int(info.get('negative', 0)),
                    'owners_estimate': info.get('owners', '0 .. 0'),
                    'avg_playtime': int(info.get('average_forever', 0)),
                    'median_playtime': int(info.get('median_forever', 0)),
                    'ccu': int(info.get('ccu', 0)),
                })
            return games
        except Exception as e:
            logger.error(f"解析 SteamSpy 批量数据失败: {e}")
            return []

    # 获取单个游戏详情
    def fetch_app_details(self, appid: int, cc='cn') -> dict:
        params = {'appids': str(appid), 'cc': cc, 'l': 'schinese'}
        resp = self._request_with_retry(self.STORE_API, params=params)
        if not resp:
            return None

        try:
            data = resp.json()
            app_data = data.get(str(appid), {})
            if not app_data.get('success'):
                return None

            detail = app_data.get('data', {})
            if detail.get('type') != 'game':
                return None  # 跳过非游戏

            price_info = detail.get('price_overview', {})
            is_free = detail.get('is_free', False)
            release_date = detail.get('release_date', {}).get('date', '')
            genres = [g.get('description', '') for g in detail.get('genres', [])]
            categories = [c.get('description', '') for c in detail.get('categories', [])]

            return {
                'appid': appid,
                'name': detail.get('name', ''),
                'release_date': release_date,
                'developer': ', '.join(detail.get('developers', [])),
                'publisher': ', '.join(detail.get('publishers', [])),
                'price_initial': price_info.get('initial', 0),
                'price_final': price_info.get('final', 0),
                'discount_percent': price_info.get('discount_percent', 0),
                'is_free': 1 if is_free else 0,
                'genres': genres,
                'tags': [],
                'categories': categories,
                'platforms': detail.get('platforms', {}),
                'header_image': detail.get('header_image', ''),
                'short_description': detail.get('short_description', ''),
                'description': detail.get('detailed_description', '')[:2000],
                'early_access': 0,
            }
        except Exception as e:
            logger.error(f"解析游戏 {appid} 详情时出错: {e}")
            return None

    # 获取游戏评论摘要
    def fetch_reviews_summary(self, appid: int) -> dict:
        url = self.REVIEW_API.format(appid=appid)
        resp = self._request_with_retry(url)
        if not resp:
            return {}
        try:
            summary = resp.json().get('query_summary', {})
            return {
                'positive_reviews': summary.get('total_positive', 0),
                'negative_reviews': summary.get('total_negative', 0),
                'review_score_desc': summary.get('review_score_desc', ''),
            }
        except Exception as e:
            logger.error(f"解析游戏 {appid} 评论摘要异常: {e}")
            return {}

    # 获取游戏评论详情
    def fetch_reviews_detail(self, appid: int, count=10) -> list:
        url = self.REVIEW_DETAIL_API.format(appid=appid)
        resp = self._request_with_retry(url)
        if not resp:
            return []
        try:
            reviews = []
            for r in resp.json().get('reviews', []):
                author = r.get('author', {})
                review = {
                    'review_id': r.get('recommendationid', ''),
                    'appid': appid,
                    'author_playtime': author.get('playtime_forever', 0),
                    'voted_up': 1 if r.get('voted_up') else 0,
                    'review_text': (r.get('review', '') or '')[:2000],
                    'votes_up': r.get('votes_up', 0),
                    'votes_funny': r.get('votes_funny', 0),
                    'language': r.get('language', ''),
                    'timestamp_created': r.get('timestamp_created', 0),
                }
                if review['review_id']:
                    reviews.append(review)
            return reviews
        except Exception as e:
            logger.error(f"解析游戏 {appid} 评论详情异常: {e}")
            return []

    # 获取 SteamSpy 数据
    def fetch_steamspy(self, appid: int) -> dict:
        params = {'request': 'appdetails', 'appid': appid}
        resp = self._request_with_retry(self.STEAMSPY_API, params=params)
        if not resp:
            return {}
        try:
            data = resp.json()
            tags = list(data.get('tags', {}).keys()) if isinstance(data.get('tags'), dict) else []
            return {
                'owners_estimate': data.get('owners', ''),
                'avg_playtime': data.get('average_forever', 0),
                'median_playtime': data.get('median_forever', 0),
                'ccu': data.get('ccu', 0),
                'tags': tags,
            }
        except Exception as e:
            logger.error(f"解析 SteamSpy {appid} 失败: {e}")
            return {}


# 后台爬虫线程
class CrawlerThread(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(int, int)
    error = pyqtSignal(str)
    game_crawled = pyqtSignal(dict)

    def __init__(self, db, target_count=500, search_keyword=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.target_count = target_count
        self.search_keyword = search_keyword
        self._is_running = True
        self.crawler = SteamCrawler(request_delay=2.0, is_running_func=self.is_running)
        self.crawler.rate_limit_callback = self.on_rate_limit

    def is_running(self):
        return self._is_running

    # 数据获取触发 429 时的回调
    def on_rate_limit(self, seconds):
        self.progress.emit(0, 0, f"触发 Steam 接口限流，预计冷却 {seconds} 秒...")

    def stop(self):
        self._is_running = False

    def run(self):
        success = 0
        batch_size = 100
        
        try:
            if self.search_keyword:
                logger.info(f"数据获取线程启动，搜索关键词: {self.search_keyword}")
                self.progress.emit(0, 0, f"正在搜索: {self.search_keyword}...")
                
                search_results = self.crawler.fetch_apps_by_search(self.search_keyword)
                if not search_results:
                    self.progress.emit(0, 0, f"未找到匹配 '{self.search_keyword}' 的游戏")
                    self.finished.emit(0, 0)
                    return
                
                pending_games = []
                for item in search_results:
                    appid = item.get('id')
                    if appid:
                        pending_games.append({'appid': int(appid), 'name': item.get('name', '')})
                
                total = len(pending_games)
                self.progress.emit(0, total, f"找到 {total} 款匹配项，正在同步数据...")
            else:
                logger.info(f"数据获取线程启动，目标数量: {self.target_count}")
                self.progress.emit(0, self.target_count, "正在从 SteamSpy 获取游戏候选列表...")

                # 获取已完整同步的 appid 集合 (避免重复同步详情)
                crawled_appids = self.db.get_crawled_appids()

                # 1. 获取候选数据 (翻页直到凑齐足够的“新”游戏)
                all_bulk_games = []
                page = 0
                while len(all_bulk_games) < self.target_count and page < 10: # 最多翻 10 页
                    if not self._is_running: break
                    
                    self.progress.emit(0, self.target_count, f"正在从 SteamSpy 获取游戏池 (第 {page+1} 页)...")
                    bulk_data = self.crawler.fetch_bulk_from_steamspy(page)
                    if not bulk_data:
                        break
                    
                    # 过滤掉已经完整同步过的游戏
                    new_games = [g for g in bulk_data if g['appid'] not in crawled_appids]
                    all_bulk_games.extend(new_games)
                    
                    page += 1
                    self.crawler._sleep(1.5)

                if not self._is_running:
                    self.finished.emit(success, 0)
                    return

                # 限制到目标数量
                pending_games = all_bulk_games[:self.target_count]
                total = len(pending_games)

                if total == 0:
                    if page == 0:
                        # 第一页就没有数据，可能是 SteamSpy 服务问题
                        self.progress.emit(0, 0, "SteamSpy 服务暂时不可用 (连接数过多)，请稍后重试或使用搜索功能")
                    else:
                        self.progress.emit(0, 0, "本地数据库已是最新，没有发现新游戏")
                    self.finished.emit(0, 0)
                    return

                self.progress.emit(0, total, f"发现 {total} 款新游戏，正在快速同步基础指标...")
                for i in range(0, total, batch_size):
                    if not self._is_running: break
                    batch = pending_games[i : i + batch_size]
                    self.db.upsert_games_batch(batch)
                    for g in batch:
                        self.game_crawled.emit(g)
                        self.db.log_crawl(g['appid'], 'success', '核心指标已同步')
                    success += len(batch)
                    self.progress.emit(min(i + batch_size, total), total, f"已同步 {min(i + batch_size, total)} 款基础数据")

            if not self._is_running:
                self.finished.emit(success, 0)
                return

            # 2. 多线程并发补充详情 (搜索模式也需要补充详情和 SteamSpy 数据)
            detail_limit = total
            self.progress.emit(0, detail_limit, "正在补充详细数据 (详情、评价、SteamSpy指标等)...")
            
            def fetch_and_update(game_base):
                if not self._is_running: return None
                appid = game_base['appid']
                try:
                    import random
                    time.sleep(random.uniform(0.5, 1.5))
                    
                    # 1. 抓取官方详情 (类型、描述等)
                    detail = self.crawler.fetch_app_details(appid)
                    if detail:
                        game_base.update(detail)
                    
                    # 2. 抓取官方评分摘要 (解决搜索模式下 N/A 问题)
                    reviews_summary = self.crawler.fetch_reviews_summary(appid)
                    if reviews_summary:
                        game_base.update(reviews_summary)
                    
                    # 3. 抓取 SteamSpy 补充数据 (如果是搜索出来的，之前可能没有 SteamSpy 基础指标)
                    spy_data = self.crawler.fetch_steamspy(appid)
                    if spy_data:
                        game_base.update(spy_data)
                    
                    # 3. 抓取精选评论 (填充 reviews 表)
                    reviews = self.crawler.fetch_reviews_detail(appid, count=10)
                    if reviews:
                        for r in reviews:
                            self.db.upsert_review(r)
                    
                    # 4. 更新数据库并记录成功日志
                    self.db.upsert_game(game_base)
                    self.db.log_crawl(appid, 'success', f'详情及 {len(reviews)} 条评论同步完成')
                    return game_base
                    
                except Exception as e:
                    logger.error(f"同步 appid={appid} 失败: {e}")
                    self.db.log_crawl(appid, 'failed', str(e))
                return None

            # 使用线程池并发补充
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = {executor.submit(fetch_and_update, pending_games[i]): i for i in range(detail_limit)}
                
                completed_count = 0
                for future in as_completed(futures):
                    if not self._is_running:
                        executor.shutdown(wait=False)
                        break
                        
                    completed_count += 1
                    game_result = future.result()
                    if game_result:
                        self.game_crawled.emit(game_result)
                        if self.search_keyword:
                            success += 1
                    
                    self.progress.emit(completed_count, detail_limit, 
                                     f"同步进度 [{completed_count}/{detail_limit}]")
                    
                    self.crawler._sleep(0.5)

        except Exception as e:
            logger.error(f"数据获取线程运行时捕获异常: {e}")
            self.error.emit(str(e))

        logger.info(f"数据获取线程结束. 成功处理: {success}")
        self.finished.emit(success, 0)
