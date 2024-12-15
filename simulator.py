import random
import time
from datetime import datetime
import sqlite3
import threading
import queue

class Simulator:
    def __init__(self, range_min=0, range_max=100, frequency=1, error_rate=0.05):
        self.range_min = range_min
        self.range_max = range_max
        self.frequency = frequency  # Частота измерений в Гц
        self.error_rate = error_rate  # Погрешность
        self.status = "OK"
        self.environment = {"temperature": 25, "humidity": 50, "pressure": 101.3}
        self.measurements = []
        self.db_conn = sqlite3.connect('measurements.db', check_same_thread=False)
        self.create_table()
        self.running = False
        self.simulation_thread = None
        self.data_queue = queue.Queue()

    def create_table(self):
        cursor = self.db_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                value REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT
            )
        ''')
        self.db_conn.commit()

    def generate_measurement(self, reference_value):
        """Генерация измерений с учетом погрешности."""
        error = random.uniform(-self.error_rate, self.error_rate)
        value = reference_value * (1 + error)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.measurements.append({"value": value, "timestamp": timestamp, "status": self.status})
        self.data_queue.put((value, timestamp, self.status))
        return value, timestamp

    def save_to_db(self, value, timestamp, status):
        cursor = self.db_conn.cursor()
        cursor.execute('INSERT INTO measurements (value, timestamp, status) VALUES (?, ?, ?)', (value, timestamp, status))
        self.db_conn.commit()

    def simulate_noise(self):
        """Имитация шумов и помех."""
        noise = random.uniform(-0.5, 0.5)
        return noise

    def simulate_error(self):
        """Имитация аварийного состояния."""
        self.status = random.choice(["OK", "ERROR", "WARNING"])

    def run_simulation(self, reference_value):
        """Основной цикл симуляции."""
        self.running = True
        self.simulation_thread = threading.Thread(target=self._simulation_loop, args=(reference_value,))
        self.simulation_thread.start()

    def _simulation_loop(self, reference_value):
        while self.running:
            value, timestamp = self.generate_measurement(reference_value)
            print(f"[{timestamp}] Измерение: {value:.2f}, Статус: {self.status}")
            self.simulate_error()
            time.sleep(2 / self.frequency)

    def stop_simulation(self):
        self.running = False
        if self.simulation_thread:
            self.simulation_thread.join()

    def process_queue(self):
        while not self.data_queue.empty():
            value, timestamp, status = self.data_queue.get()
            self.save_to_db(value, timestamp, status)

    def close(self):
        self.db_conn.close()
