import sqlite3
import os

class HistoryManager:
    def __init__(self, db_path=None):
        if db_path is None:
            # 기본 경로는 스크립트 위치 기준으로 자동 계산 (c:/.../automation/news_history.db)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(base_dir, "news_history.db")
        else:
            self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """DB 및 테이블 초기화 및 마이그레이션"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                title TEXT,
                local_url TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # [V2.9.9] local_url 컬럼이 없는 기존 DB를 위해 마이그레이션 시도
        try:
            cur.execute("ALTER TABLE history ADD COLUMN local_url TEXT")
        except: pass 
        conn.commit()
        conn.close()

    def is_already_processed(self, url):
        """이미 처리된 URL인지 확인"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT id FROM history WHERE url = ?", (url,))
        result = cur.fetchone()
        conn.close()
        return result is not None

    def add_to_history(self, url, title, local_url=None):
        """처리된 URL과 로컬 주소 추가"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("INSERT OR REPLACE INTO history (url, title, local_url) VALUES (?, ?, ?)", (url, title, local_url))
            conn.commit()
            conn.close()
            return True
        except: return False

    def get_recent_posts(self, limit=10):
        """로컬 주소가 포함된 최근 기사 목록 반환"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("SELECT title, local_url FROM history WHERE local_url IS NOT NULL ORDER BY processed_at DESC LIMIT ?", (limit,))
            rows = cur.fetchall()
            conn.close()
            return [{"title": row[0], "url": row[1]} for row in rows]
        except: return []

    def is_similar_title_exists(self, title, threshold=0.5):
        """최근 100건의 제목과 비교하여 유사도가 높은 것이 있는지 확인 (Jaccard Similarity)"""
        if not title: return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            # 최근 100건의 기사 제목을 가져옴
            cur.execute("SELECT title FROM history ORDER BY processed_at DESC LIMIT 100")
            recent_titles = [row[0] for row in cur.fetchall() if row[0]]
            conn.close()
            
            # 검색어 정규화 (공백 기준 단어 화이트리스트)
            new_words = set(title.split())
            if not new_words: return False
            
            for old_title in recent_titles:
                old_words = set(old_title.split())
                if not old_words: continue
                
                # 단어 교집합 / 합집합 비율 계산 (Jaccard Similarity)
                intersection = new_words.intersection(old_words)
                union = new_words.union(old_words)
                similarity = len(intersection) / len(union)
                
                if similarity >= threshold:
                    return True
            return False
        except:
            return False
