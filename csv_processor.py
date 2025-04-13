import csv
from typing import List, Dict, Optional
import os


class CSVProcessor:
    """Класс для обработки CSV файлов с данными измерений."""
    
    @staticmethod
    def read_csv(file_path: str) -> List[Dict[str, float]]:
        """
        Чтение данных из CSV файла.
        
        Args:
            file_path: Путь к CSV файлу
            
        Returns:
            List[Dict[str, float]]: Список словарей с данными измерений
            
        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если формат файла некорректный
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл {file_path} не найден")
            
        measurements = []
        try:
            with open(file_path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        measurement = {
                            'value': float(row['value']),
                            'timestamp': row.get('timestamp', ''),
                            'status': row.get('status', 'OK')
                        }
                        measurements.append(measurement)
                    except (KeyError, ValueError) as e:
                        raise ValueError(f"Некорректный формат данных в CSV файле: {e}")
        except Exception as e:
            raise ValueError(f"Ошибка при чтении CSV файла: {e}")
            
        return measurements

    @staticmethod
    def write_csv(file_path: str, measurements: List[Dict[str, float]]) -> None:
        """
        Запись данных в CSV файл.
        
        Args:
            file_path: Путь к CSV файлу
            measurements: Список словарей с данными измерений
        """
        fieldnames = ['value', 'timestamp', 'status']
        try:
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(measurements)
        except Exception as e:
            raise ValueError(f"Ошибка при записи в CSV файл: {e}") 
        
#value,timestamp,status пример формата данных для csv файла
# 50.0,2024-03-20 10:00:00,OK
# 51.2,2024-03-20 10:00:01,OK
# 49.8,2024-03-20 10:00:02,WARNING
# 52.5,2024-03-20 10:00:03,ERROR