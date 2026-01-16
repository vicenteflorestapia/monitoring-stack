#!/usr/bin/env python3
import os, time, random, argparse, threading
from concurrent.futures import ThreadPoolExecutor
import psycopg2
from psycopg2 import pool

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'user': os.getenv('POSTGRES_USER', 'monitor_admin'),
    'password': os.getenv('POSTGRES_PASSWORD', 'monitor_pass_2024'),
    'database': os.getenv('POSTGRES_DB', 'production_db')
}

CLIENTS = ['acme_corp', 'tech_solutions', 'global_services', 'innovatech',
           'dataflow_inc', 'cloud_systems', 'netwise', 'securepay',
           'fasttrack_logistics', 'greentech_energy']

class LoadGenerator:
    def __init__(self, mode='light'):
        self.mode = mode
        self.running = True
        self.stats = {'inserts': 0, 'updates': 0, 'selects': 0}
        self.pool = psycopg2.pool.ThreadedConnectionPool(5, 20, **DB_CONFIG)
        self.configs = {
            'light': {'workers': 2, 'delay': 1.0, 'batch': 10},
            'medium': {'workers': 5, 'delay': 0.5, 'batch': 50},
            'heavy': {'workers': 10, 'delay': 0.1, 'batch': 100},
        }

    def insert(self, client):
        conn = self.pool.getconn()
        try:
            batch = self.configs[self.mode]['batch']
            with conn.cursor() as cur:
                cur.execute(f"""
                    INSERT INTO clients.{client} (amount, status, category)
                    SELECT (random()*10000)::numeric(12,2),
                           (ARRAY['pending','completed','failed'])[1+floor(random()*3)::int],
                           (ARRAY['sales','refund','subscription'])[1+floor(random()*3)::int]
                    FROM generate_series(1, {batch})
                """)
                conn.commit()
                self.stats['inserts'] += batch
        except Exception as e:
            conn.rollback()
            print(f"[ERROR] Insert: {e}")
        finally:
            self.pool.putconn(conn)

    def update(self, client):
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                new_status = random.choice(['pending', 'completed', 'failed'])
                cur.execute(f"""
                    UPDATE clients.{client} 
                    SET status = %s
                    WHERE id IN (
                        SELECT id FROM clients.{client} 
                        WHERE status = 'pending' 
                        LIMIT 20
                    )
                """, (new_status,))
                self.stats['updates'] += cur.rowcount
                conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"[ERROR] Update: {e}")
        finally:
            self.pool.putconn(conn)

    def select(self, client):
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT category, COUNT(*), SUM(amount) 
                    FROM clients.{client} 
                    GROUP BY category
                """)
                cur.fetchall()
                self.stats['selects'] += 1
        except Exception as e:
            print(f"[ERROR] Select: {e}")
        finally:
            self.pool.putconn(conn)

    def worker(self, wid):
        while self.running:
            client = random.choice(CLIENTS)
            op = random.choices(['insert','update','select'], weights=[50,30,20])[0]
            getattr(self, op)(client)
            time.sleep(self.configs[self.mode]['delay'])

    def run(self):
        cfg = self.configs[self.mode]
        print(f"{'='*60}")
        print(f"  Load Generator - Mode: {self.mode.upper()}")
        print(f"  Workers: {cfg['workers']} | Delay: {cfg['delay']}s | Batch: {cfg['batch']}")
        print(f"  Target DB: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        print(f"  Press Ctrl+C to stop")
        print(f"{'='*60}")
        
        def stats_printer():
            while self.running:
                time.sleep(10)
                print(f"\n[STATS] Inserts: {self.stats['inserts']} | Updates: {self.stats['updates']} | Selects: {self.stats['selects']}")
        
        threading.Thread(target=stats_printer, daemon=True).start()
        
        with ThreadPoolExecutor(max_workers=cfg['workers']) as ex:
            try:
                [ex.submit(self.worker, i) for i in range(cfg['workers'])]
                while True: time.sleep(1)
            except KeyboardInterrupt:
                print("\n\nStopping...")
                self.running = False
        
        print(f"\n{'='*60}")
        print(f"  FINAL: Inserts: {self.stats['inserts']} | Updates: {self.stats['updates']} | Selects: {self.stats['selects']}")
        print(f"{'='*60}")
        self.pool.closeall()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', '-m', choices=['light','medium','heavy'], default='light')
    LoadGenerator(parser.parse_args().mode).run()