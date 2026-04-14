import sqlite3
import json
import os
import sys
import threading
import traceback
from datetime import datetime


# SQLite 数据库操作封装
class SteamDatabase:
    def __init__(self, db_path=None):
        if db_path is None:
            if getattr(sys, 'frozen', False):
                # 打包后的路径：exe 所在目录/data
                base_dir = os.path.dirname(sys.executable)
            else:
                # 开发环境路径：项目根目录/data (src/data/database.py 向上三级)
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            data_dir = os.path.join(base_dir, 'data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'steam_games.db')
        self.db_path = db_path
        self._lock = threading.Lock()
        self._local = threading.local()
        self._init_db()

    # 获取数据库连接
    def _get_conn(self):
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA busy_timeout=5000")
            self._local.conn = conn
        return self._local.conn

    # 初始化数据库表
    def _init_db(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS games (
                appid INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                release_date TEXT,
                developer TEXT,
                publisher TEXT,
                price_initial INTEGER DEFAULT 0,
                price_final INTEGER DEFAULT 0,
                discount_percent INTEGER DEFAULT 0,
                is_free INTEGER DEFAULT 0,
                genres TEXT DEFAULT '[]',
                tags TEXT DEFAULT '[]',
                categories TEXT DEFAULT '[]',
                platforms TEXT DEFAULT '{}',
                positive_reviews INTEGER DEFAULT 0,
                negative_reviews INTEGER DEFAULT 0,
                review_score_desc TEXT DEFAULT '',
                owners_estimate TEXT DEFAULT '',
                avg_playtime INTEGER DEFAULT 0,
                median_playtime INTEGER DEFAULT 0,
                ccu INTEGER DEFAULT 0,
                header_image TEXT DEFAULT '',
                description TEXT DEFAULT '',
                short_description TEXT DEFAULT '',
                early_access INTEGER DEFAULT 0,
                crawled_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS reviews (
                review_id TEXT PRIMARY KEY,
                appid INTEGER,
                author_playtime INTEGER DEFAULT 0,
                voted_up INTEGER DEFAULT 0,
                review_text TEXT DEFAULT '',
                votes_up INTEGER DEFAULT 0,
                votes_funny INTEGER DEFAULT 0,
                language TEXT DEFAULT '',
                timestamp_created INTEGER DEFAULT 0,
                updated_at TEXT,
                FOREIGN KEY (appid) REFERENCES games(appid)
            );

            CREATE TABLE IF NOT EXISTS crawl_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appid INTEGER,
                status TEXT DEFAULT 'pending',
                error_msg TEXT DEFAULT '',
                crawled_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_games_name ON games(name);
            CREATE INDEX IF NOT EXISTS idx_games_release ON games(release_date);
            CREATE INDEX IF NOT EXISTS idx_games_price ON games(price_final);
            CREATE INDEX IF NOT EXISTS idx_reviews_appid ON reviews(appid);
            CREATE INDEX IF NOT EXISTS idx_crawl_appid ON crawl_log(appid);
        """)
        
        # 数据库自动迁移 (补齐缺失字段)
        # 检查 reviews 表中是否缺少 updated_at
        cursor.execute("PRAGMA table_info(reviews)")
        cols = [info[1] for info in cursor.fetchall()]
        if 'updated_at' not in cols:
            print("[DB MIGRATION] 正在为 reviews 表添加 updated_at 字段...")
            cursor.execute("ALTER TABLE reviews ADD COLUMN updated_at TEXT")
            
        conn.commit()

    # 游戏数据操作
    def upsert_game(self, game_data: dict):
        self.upsert_games_batch([game_data])

    def upsert_games_batch(self, games_list: list):
        if not games_list:
            return
        try:
            now = datetime.now().isoformat()
            processed_list = []
            
            for game_data in games_list:
                item = dict(game_data)
                item['updated_at'] = now
                if 'crawled_at' not in item:
                    item['crawled_at'] = now

                # 序列化 list/dict 字段
                for field in ['genres', 'tags', 'categories', 'platforms']:
                    if field in item and not isinstance(item[field], str):
                        item[field] = json.dumps(item[field], ensure_ascii=False)
                processed_list.append(item)

            # 以第一个元素的键作为列名
            columns = ', '.join(processed_list[0].keys())
            placeholders = ', '.join(['?'] * len(processed_list[0]))
            updates = ', '.join([f'{k}=excluded.{k}' for k in processed_list[0].keys() if k != 'appid'])

            sql = f"""
                INSERT INTO games ({columns}) VALUES ({placeholders})
                ON CONFLICT(appid) DO UPDATE SET {updates}
            """
            
            with self._lock:
                conn = self._get_conn()
                cursor = conn.cursor()
                cursor.executemany(sql, [list(g.values()) for g in processed_list])
                conn.commit()
        except Exception as e:
            print(f"[DB ERROR] upsert_games_batch 失败: {e}")
            traceback.print_exc()

    # 评价数据操作
    def get_all_reviews(self, appid=None, limit=1000):
        try:
            if appid:
                sql = """
                    SELECT r.*, g.name as game_name 
                    FROM reviews r 
                    JOIN games g ON r.appid = g.appid 
                    WHERE r.appid = ?
                    ORDER BY r.timestamp_created DESC 
                    LIMIT ?
                """
                params = (appid, limit)
            else:
                sql = """
                    SELECT r.*, g.name as game_name 
                    FROM reviews r 
                    JOIN games g ON r.appid = g.appid 
                    ORDER BY r.timestamp_created DESC 
                    LIMIT ?
                """
                params = (limit,)
                
            with self._lock:
                conn = self._get_conn()
                cursor = conn.cursor()
                cursor.execute(sql, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[DB ERROR] get_all_reviews 失败: {e}")
            return []

    # 插入或更新评论数据
    def upsert_review(self, review_data: dict):
        try:
            now = datetime.now().isoformat()
            review_data = dict(review_data)
            review_data['updated_at'] = now
            
            columns = ', '.join(review_data.keys())
            placeholders = ', '.join(['?'] * len(review_data))
            updates = ', '.join([f'{k}=excluded.{k}' for k in review_data.keys() if k != 'review_id'])

            sql = f"""
                INSERT INTO reviews ({columns}) VALUES ({placeholders})
                ON CONFLICT(review_id) DO UPDATE SET {updates}
            """
            with self._lock:
                conn = self._get_conn()
                conn.execute(sql, list(review_data.values()))
                conn.commit()
        except Exception as e:
            print(f"[DB ERROR] upsert_review 失败: {e}")

    # 获取所有游戏
    def get_all_games(self, limit=None) -> list:
        try:
            with self._lock:
                conn = self._get_conn()
                sql = "SELECT * FROM games ORDER BY positive_reviews + negative_reviews DESC"
                if limit:
                    sql += f" LIMIT {int(limit)}"
                rows = conn.execute(sql).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"[DB ERROR] get_all_games: {e}")
            return []

    # 获取游戏总数
    def get_game_count(self) -> int:
        try:
            with self._lock:
                conn = self._get_conn()
                row = conn.execute("SELECT COUNT(*) as cnt FROM games").fetchone()
            return row['cnt'] if row else 0
        except Exception as e:
            print(f"[DB ERROR] get_game_count: {e}")
            return 0

    # 获取数据库统计信息
    def get_stats(self) -> dict:
        stats = {
            'total_games': 0, 'avg_price': 0,
            'avg_positive_rate': 0, 'total_reviews': 0,
            'total_review_texts': 0
        }
        try:
            with self._lock:
                conn = self._get_conn()
                
                row = conn.execute("SELECT COUNT(*) as cnt FROM games").fetchone()
                stats['total_games'] = row['cnt']

                row = conn.execute(
                    "SELECT AVG(price_final) as avg_price FROM games WHERE is_free=0 AND price_final > 0"
                ).fetchone()
                stats['avg_price'] = round(row['avg_price'] / 100, 2) if row and row['avg_price'] else 0

                row = conn.execute("""
                    SELECT AVG(CAST(positive_reviews AS REAL) / 
                           CASE WHEN positive_reviews + negative_reviews > 0 
                                THEN positive_reviews + negative_reviews 
                                ELSE 1 END) as avg_rating
                    FROM games WHERE positive_reviews + negative_reviews > 10
                """).fetchone()
                stats['avg_positive_rate'] = round(row['avg_rating'] * 100, 1) if row and row['avg_rating'] else 0

                row = conn.execute(
                    "SELECT SUM(positive_reviews + negative_reviews) as total FROM games"
                ).fetchone()
                stats['total_reviews'] = row['total'] or 0

                row = conn.execute("SELECT COUNT(*) as cnt FROM reviews").fetchone()
                stats['total_review_texts'] = row['cnt']
        except Exception as e:
            print(f"[DB ERROR] get_stats: {e}")
            traceback.print_exc()
        return stats

    # 获取价格分布数据
    def get_price_distribution(self) -> list:
        try:
            with self._lock:
                conn = self._get_conn()
                rows = conn.execute("""
                    SELECT price_final / 100 as price_dollar, COUNT(*) as count
                    FROM games WHERE is_free=0 AND price_final > 0
                    GROUP BY price_final / 100
                    ORDER BY price_dollar
                """).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"[DB ERROR] get_price_distribution: {e}")
            return []

    # 按年份统计发行数量
    def get_release_by_year(self) -> list:
        try:
            with self._lock:
                conn = self._get_conn()
                rows = conn.execute("""
                    SELECT substr(release_date, 1, 4) as year, COUNT(*) as count
                    FROM games 
                    WHERE release_date IS NOT NULL AND release_date != '' 
                          AND length(release_date) >= 4
                    GROUP BY year
                    HAVING year >= '2000' AND year <= '2030'
                    ORDER BY year
                """).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"[DB ERROR] get_release_by_year: {e}")
            return []

    # 获取类型分布
    def get_genre_distribution(self) -> list:
        try:
            with self._lock:
                conn = self._get_conn()
                rows = conn.execute("SELECT genres FROM games WHERE genres != '[]'").fetchall()
            genre_count = {}
            for row in rows:
                try:
                    genres = json.loads(row['genres'])
                    for g in genres:
                        name = g if isinstance(g, str) else g.get('description', '')
                        if name:
                            genre_count[name] = genre_count.get(name, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    pass
            sorted_genres = sorted(genre_count.items(), key=lambda x: x[1], reverse=True)
            return [{'name': k, 'count': v} for k, v in sorted_genres[:20]]
        except Exception as e:
            print(f"[DB ERROR] get_genre_distribution: {e}")
            return []

    # 获取评分分布
    def get_rating_distribution(self) -> list:
        try:
            with self._lock:
                conn = self._get_conn()
                rows = conn.execute("""
                    SELECT 
                        CASE 
                            WHEN CAST(positive_reviews AS REAL) / (positive_reviews + negative_reviews) >= 0.95 THEN '好评如潮'
                            WHEN CAST(positive_reviews AS REAL) / (positive_reviews + negative_reviews) >= 0.80 THEN '特别好评'
                            WHEN CAST(positive_reviews AS REAL) / (positive_reviews + negative_reviews) >= 0.70 THEN '多半好评'
                            WHEN CAST(positive_reviews AS REAL) / (positive_reviews + negative_reviews) >= 0.40 THEN '褒贬不一'
                            WHEN CAST(positive_reviews AS REAL) / (positive_reviews + negative_reviews) >= 0.20 THEN '多半差评'
                            ELSE '差评如潮'
                        END as rating_level,
                        COUNT(*) as count
                    FROM games
                    WHERE positive_reviews + negative_reviews >= 10
                    GROUP BY rating_level
                    ORDER BY count DESC
                """).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"[DB ERROR] get_rating_distribution: {e}")
            return []

    # 删除一个游戏的所有相关数据（游戏、评论、日志）
    def delete_game_full(self, appid: int):
        try:
            with self._lock:
                conn = self._get_conn()
                cursor = conn.cursor()
                # 开启事务
                cursor.execute("BEGIN TRANSACTION")
                cursor.execute("DELETE FROM games WHERE appid = ?", (appid,))
                cursor.execute("DELETE FROM reviews WHERE appid = ?", (appid,))
                cursor.execute("DELETE FROM crawl_log WHERE appid = ?", (appid,))
                conn.commit()
                return True
        except Exception as e:
            print(f"[DB ERROR] delete_game_full 失败 appid={appid}: {e}")
            return False

    # 爬虫日志
    def log_crawl(self, appid: int, status: str, error_msg: str = ''):
        try:
            now = datetime.now().isoformat()
            with self._lock:
                conn = self._get_conn()
                conn.execute(
                    "INSERT INTO crawl_log (appid, status, error_msg, crawled_at) VALUES (?, ?, ?, ?)",
                    (appid, status, error_msg, now)
                )
                conn.commit()
        except Exception as e:
            print(f"[DB ERROR] log_crawl: {e}")

    # 获取已爬取的 appid 集合
    def get_crawled_appids(self) -> set:
        try:
            with self._lock:
                conn = self._get_conn()
                rows = conn.execute(
                    "SELECT DISTINCT appid FROM crawl_log WHERE status='success'"
                ).fetchall()
            return {row['appid'] for row in rows}
        except Exception as e:
            print(f"[DB ERROR] get_crawled_appids: {e}")
            return set()

    # 关闭当前线程的连接
    def close(self):
        try:
            if hasattr(self._local, 'conn') and self._local.conn:
                self._local.conn.close()
                self._local.conn = None
        except Exception:
            pass
