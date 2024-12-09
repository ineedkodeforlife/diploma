import random
import time
from datetime import datetime

class Simulator:
    def __init__(self, range_min=0, range_max=100, frequency=1, error_rate=0.05):
        self.range_min = range_min
        self.range_max = range_max
        self.frequency = frequency  # Частота измерений в Гц
        self.error_rate = error_rate  # Погрешность
        self.status = "OK"
        self.environment = {"temperature": 25, "humidity": 50, "pressure": 101.3}
        self.measurements = []

    def generate_measurement(self, reference_value):
        """Генерация измерений с учетом погрешности."""
        error = random.uniform(-self.error_rate, self.error_rate)
        value = reference_value * (1 + error)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.measurements.append({"value": value, "timestamp": timestamp, "status": self.status})
        return value, timestamp

    def simulate_noise(self):
        """Имитация шумов и помех."""
        noise = random.uniform(-0.5, 0.5)
        return noise

    def simulate_error(self):
        """Имитация аварийного состояния."""
        self.status = random.choice(["OK", "ERROR", "WARNING"])

    def run_simulation(self, reference_value):
        """Основной цикл симуляции."""
        while True:
            value, timestamp = self.generate_measurement(reference_value)
            print(f"[{timestamp}] Измерение: {value:.2f}, Статус: {self.status}")
            self.simulate_error()
            time.sleep(2 / self.frequency)
