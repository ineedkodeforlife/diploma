import random
import time
from datetime import datetime
import sqlite3
import threading
import queue
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum


class OperationMode(Enum):
    """Режимы работы симулятора."""
    NORMAL = "normal"          # Нормальный режим
    INTERFERENCE = "interference"  # Режим с помехами
    EMERGENCY = "emergency"    # Аварийный режим
    CALIBRATION = "calibration"  # Режим калибровки


class SimulationMode(Enum):
    """Режимы симуляции."""
    REAL_TIME = "real_time"    # Режим реального времени
    ACCELERATED = "accelerated"  # Ускоренная симуляция
    STEP_BY_STEP = "step_by_step"  # Пошаговый режим


class Simulator:
    """
    Класс для симуляции измерений с учетом погрешности и сохранения результатов в базу данных.
    
    Attributes:
        range_min (float): Минимальное значение диапазона измерений
        range_max (float): Максимальное значение диапазона измерений
        frequency (float): Частота измерений в Гц
        error_rate (float): Погрешность измерений (от 0 до 1)
    """
    
    def __init__(self, range_min: float = 0, range_max: float = 100, 
                 frequency: float = 1, error_rate: float = 0.05) -> None:
        """
        Инициализация симулятора.
        
        Args:
            range_min: Минимальное значение диапазона измерений
            range_max: Максимальное значение диапазона измерений
            frequency: Частота измерений в Гц
            error_rate: Погрешность измерений (от 0 до 1)
        """
        if not 0 <= error_rate <= 1:
            raise ValueError("error_rate должен быть в диапазоне от 0 до 1")
        if frequency <= 0:
            raise ValueError("frequency должна быть положительным числом")
        if range_min >= range_max:
            raise ValueError("range_min должен быть меньше range_max")
            
        self.range_min = range_min
        self.range_max = range_max
        self.frequency = frequency
        self.error_rate = error_rate
        self.status = "OK"
        self.environment = {"temperature": 25, "humidity": 50, "pressure": 101.3}
        self._measurements_lock = threading.Lock()
        self.measurements = []
        self.running = False
        self.simulation_thread = None
        self.data_queue = queue.Queue(maxsize=1000)
        self._db_lock = threading.Lock()
        
        # Режимы работы
        self.operation_mode = OperationMode.NORMAL
        self.simulation_mode = SimulationMode.REAL_TIME
        self.simulation_speed = 1.0  # Множитель скорости симуляции
        
        # Статистика
        self.statistics = {
            "total_measurements": 0,
            "errors": 0,
            "warnings": 0,
            "min_value": float('inf'),
            "max_value": float('-inf'),
            "avg_value": 0
        }
        
        try:
            self.db_conn = sqlite3.connect('measurements.db', check_same_thread=False)
            self.create_table()
        except sqlite3.Error as e:
            raise RuntimeError(f"Ошибка при подключении к базе данных: {e}")

    def __enter__(self):
        """Поддержка контекстного менеджера."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Закрытие ресурсов при выходе из контекста."""
        self.close()

    def create_table(self) -> None:
        """Создает таблицу измерений в базе данных."""
        try:
            with self._db_lock:
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
        except sqlite3.Error as e:
            raise RuntimeError(f"Ошибка при создании таблицы: {e}")

    def set_operation_mode(self, mode: OperationMode) -> None:
        """Установка режима работы."""
        self.operation_mode = mode

    def set_simulation_mode(self, mode: SimulationMode, speed: float = 1.0) -> None:
        """Установка режима симуляции."""
        self.simulation_mode = mode
        self.simulation_speed = speed

    def set_environment(self, temperature: float, humidity: float, pressure: float) -> None:
        """Установка параметров окружающей среды."""
        self.environment = {
            "temperature": temperature,
            "humidity": humidity,
            "pressure": pressure
        }

    def generate_measurement(self, reference_value: float) -> Tuple[float, str]:
        """
        Генерация измерений с учетом погрешности и режима работы.
        
        Args:
            reference_value: Опорное значение для измерения
            
        Returns:
            Tuple[float, str]: Значение измерения и временная метка
        """
        # Базовая погрешность
        error = random.uniform(-self.error_rate, self.error_rate)
        
        # Дополнительные помехи в зависимости от режима
        if self.operation_mode == OperationMode.INTERFERENCE:
            error += random.uniform(-0.1, 0.1)  # Увеличенные помехи
        elif self.operation_mode == OperationMode.EMERGENCY:
            error += random.uniform(-0.3, 0.3)  # Сильные помехи
            
        # Влияние окружающей среды
        env_factor = 1.0
        if self.environment["temperature"] > 30:
            env_factor += 0.05
        if self.environment["humidity"] > 70:
            env_factor += 0.05
        if self.environment["pressure"] < 100:
            env_factor += 0.05
            
        value = reference_value * (1 + error) * env_factor
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Обновление статистики
        with self._measurements_lock:
            self.measurements.append({"value": value, "timestamp": timestamp, "status": self.status})
            self.update_statistics(value)
        
        try:
            self.data_queue.put((value, timestamp, self.status), timeout=1)
        except queue.Full:
            print("Предупреждение: очередь данных переполнена")
            
        return value, timestamp

    def update_statistics(self, value: float) -> None:
        """Обновление статистики измерений."""
        self.statistics["total_measurements"] += 1
        if self.status == "ERROR":
            self.statistics["errors"] += 1
        elif self.status == "WARNING":
            self.statistics["warnings"] += 1
            
        self.statistics["min_value"] = min(self.statistics["min_value"], value)
        self.statistics["max_value"] = max(self.statistics["max_value"], value)
        
        # Обновление среднего значения
        total = self.statistics["total_measurements"]
        self.statistics["avg_value"] = (
            (self.statistics["avg_value"] * (total - 1) + value) / total
        )

    def simulate_error(self):
        """Имитация аварийного состояния с учетом режима работы."""
        if self.operation_mode == OperationMode.NORMAL:
            self.status = "OK"
        elif self.operation_mode == OperationMode.INTERFERENCE:
            self.status = random.choice(["OK", "WARNING"])
        elif self.operation_mode == OperationMode.EMERGENCY:
            self.status = random.choice(["OK", "ERROR", "WARNING"])
        elif self.operation_mode == OperationMode.CALIBRATION:
            self.status = "CALIBRATION"

    def run_simulation(self, reference_value: float) -> None:
        """
        Запуск симуляции в отдельном потоке.
        
        Args:
            reference_value: Опорное значение для измерения
        """
        if self.running:
            raise RuntimeError("Симуляция уже запущена")
            
        self.running = True
        self.simulation_thread = threading.Thread(
            target=self._simulation_loop,
            args=(reference_value,),
            daemon=True
        )
        self.simulation_thread.start()

    def _simulation_loop(self, reference_value):
        """Основной цикл симуляции."""
        while self.running:
            value, timestamp = self.generate_measurement(reference_value)
            self.simulate_error()
            
            # Управление скоростью симуляции
            if self.simulation_mode == SimulationMode.REAL_TIME:
                time.sleep(1.0 / (self.frequency * self.simulation_speed))
            elif self.simulation_mode == SimulationMode.STEP_BY_STEP:
                time.sleep(1.0)  # Пауза между шагами
            else:  # ACCELERATED
                time.sleep(0.1 / self.simulation_speed)

    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики измерений."""
        return self.statistics.copy()

    def get_measurements(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Получение последних измерений."""
        with self._measurements_lock:
            return self.measurements[-limit:]

    def clear_statistics(self) -> None:
        """Очистка статистики."""
        self.statistics = {
            "total_measurements": 0,
            "errors": 0,
            "warnings": 0,
            "min_value": float('inf'),
            "max_value": float('-inf'),
            "avg_value": 0
        }

    def save_to_db(self, value: float, timestamp: str, status: str) -> None:
        """Сохраняет измерение в базу данных."""
        try:
            with self._db_lock:
                cursor = self.db_conn.cursor()
                cursor.execute(
                    'INSERT INTO measurements (value, timestamp, status) VALUES (?, ?, ?)',
                    (value, timestamp, status)
                )
                self.db_conn.commit()
        except sqlite3.Error as e:
            print(f"Ошибка при сохранении в базу данных: {e}")

    def process_queue(self):
        while not self.data_queue.empty():
            value, timestamp, status = self.data_queue.get()
            self.save_to_db(value, timestamp, status)

    def close(self) -> None:
        """Закрытие всех ресурсов."""
        self.stop_simulation()
        if hasattr(self, 'db_conn'):
            try:
                self.db_conn.close()
            except sqlite3.Error as e:
                print(f"Ошибка при закрытии соединения с базой данных: {e}")

    def stop_simulation(self) -> None:
        """Остановка симуляции."""
        self.running = False
        if self.simulation_thread:
            self.simulation_thread.join(timeout=5)
            if self.simulation_thread.is_alive():
                print("Предупреждение: поток симуляции не завершился корректно")
