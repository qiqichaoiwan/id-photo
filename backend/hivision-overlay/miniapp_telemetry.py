"""Best-effort, anonymous API counters, stored separately from membership data."""
import os
import queue
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

from miniapp_membership import DATA_DIR

TELEMETRY_PATH = DATA_DIR / 'service_metrics.sqlite3'
RETENTION_DAYS = 30
ROUTES = frozenset({
    '/idphoto', '/idphoto_crop', '/human_matting', '/convert_image',
    '/add_background', '/generate_layout_photos', '/watermark', '/set_kb',
    '/auth/wechat', '/membership/status', '/membership/plans',
})


class MetricsWriter:
    """A bounded queue makes monitoring independent of the request path."""

    def __init__(self, path=TELEMETRY_PATH):
        self.path = Path(path)
        self.queue = queue.Queue(maxsize=4096)
        self.lock = threading.Lock()
        self.worker = None

    def record(self, route, status, elapsed_ms):
        if route not in ROUTES:
            return
        try:
            bucket = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:00:00Z')
            self.queue.put_nowait((bucket, route, int(status) // 100, max(0, int(elapsed_ms))))
            with self.lock:
                if self.worker is None or not self.worker.is_alive():
                    self.worker = threading.Thread(target=self._run, daemon=True, name='service-metrics')
                    self.worker.start()
        except Exception:
            # Metrics must never cause an image or payment request to fail.
            return

    def _run(self):
        while True:
            first = self.queue.get()
            batch = [first]
            while len(batch) < 128:
                try:
                    batch.append(self.queue.get_nowait())
                except queue.Empty:
                    break
            try:
                self._write(batch)
            except (OSError, sqlite3.Error):
                pass
            finally:
                for _ in batch:
                    self.queue.task_done()

    def _write(self, batch):
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with sqlite3.connect(str(self.path), timeout=0.3) as db:
            os.chmod(self.path, 0o600)
            db.execute('''CREATE TABLE IF NOT EXISTS metrics (
                hour TEXT NOT NULL, route TEXT NOT NULL, status_class INTEGER NOT NULL,
                count INTEGER NOT NULL, duration_ms INTEGER NOT NULL, max_ms INTEGER NOT NULL,
                PRIMARY KEY (hour, route, status_class))''')
            db.executemany('''INSERT INTO metrics VALUES (?, ?, ?, 1, ?, ?)
                ON CONFLICT(hour, route, status_class) DO UPDATE SET
                count=count+1, duration_ms=duration_ms+excluded.duration_ms,
                max_ms=MAX(max_ms, excluded.max_ms)''',
                [(hour, route, cls, duration, duration) for hour, route, cls, duration in batch])
            cutoff = (datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)).strftime('%Y-%m-%dT%H:00:00Z')
            db.execute('DELETE FROM metrics WHERE hour < ?', (cutoff,))


writer = MetricsWriter()


def read_metrics(days=7):
    """Never create a database on reads; absence means no observations yet."""
    if not TELEMETRY_PATH.is_file():
        return {'available': True, 'first_observed_at': None, 'rows': [], 'retention_days': RETENTION_DAYS}
    try:
        uri = 'file:' + quote(str(TELEMETRY_PATH)) + '?mode=ro'
        with sqlite3.connect(uri, uri=True, timeout=0.5) as db:
            db.row_factory = sqlite3.Row
            first = db.execute('SELECT MIN(hour) FROM metrics').fetchone()[0]
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%dT%H:00:00Z')
            rows = db.execute('''SELECT route, status_class, SUM(count) AS count,
                SUM(duration_ms) AS duration_ms, MAX(max_ms) AS max_ms
                FROM metrics WHERE hour >= ? GROUP BY route, status_class
                ORDER BY route, status_class''', (cutoff,)).fetchall()
        return {'available': True, 'first_observed_at': first, 'rows': [dict(row) for row in rows],
                'retention_days': RETENTION_DAYS}
    except (OSError, sqlite3.Error):
        return {'available': False, 'first_observed_at': None, 'rows': [], 'retention_days': RETENTION_DAYS}
