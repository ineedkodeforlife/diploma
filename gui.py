import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                            QTextEdit, QFileDialog, QMessageBox, QTabWidget,
                            QGroupBox, QComboBox, QSpinBox, QDoubleSpinBox,
                            QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from datetime import datetime

from simulator import Simulator, OperationMode, SimulationMode
from csv_processor import CSVProcessor


class SimulationThread(QThread):
    """Поток для выполнения симуляции."""
    measurement_signal = pyqtSignal(str)
    data_signal = pyqtSignal(float, str, str)  # value, timestamp, status
    statistics_signal = pyqtSignal(dict)
    finished_signal = pyqtSignal()

    def __init__(self, simulator, reference_value):
        super().__init__()
        self.simulator = simulator
        self.reference_value = reference_value
        self.running = True

    def run(self):
        """Запуск симуляции."""
        try:
            self.simulator.run_simulation(self.reference_value)
            while self.running:
                if not self.simulator.data_queue.empty():
                    value, timestamp, status = self.simulator.data_queue.get()
                    self.measurement_signal.emit(
                        f"[{timestamp}] Измерение: {value:.2f}, Статус: {status}"
                    )
                    self.data_signal.emit(value, timestamp, status)
                    self.statistics_signal.emit(self.simulator.get_statistics())
        except Exception as e:
            self.measurement_signal.emit(f"Ошибка: {str(e)}")
        finally:
            self.finished_signal.emit()

    def stop(self):
        """Остановка симуляции."""
        self.running = False
        self.simulator.stop_simulation()


class SimulatorGUI(QMainWindow):
    """Графический интерфейс симулятора."""
    
    def __init__(self):
        super().__init__()
        self.simulator = Simulator()
        self.simulation_thread = None
        self.init_ui()
        
        # Данные для графика
        self.timestamps = []
        self.values = []
        self.statuses = []
        
        # Таймер для обновления графика и статистики
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start(1000)  # Обновление каждую секунду

    def init_ui(self):
        """Инициализация интерфейса."""
        self.setWindowTitle('Симулятор измерительного прибора')
        self.setGeometry(100, 100, 1200, 800)

        # Основной виджет и компоновка
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Левая панель с настройками
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        main_layout.addWidget(left_panel, stretch=1)

        # Группа настроек прибора
        settings_group = QGroupBox("Настройки прибора")
        settings_layout = QVBoxLayout()
        
        # Диапазон измерений
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("Диапазон:"))
        self.range_min_input = QDoubleSpinBox()
        self.range_min_input.setRange(-1000, 1000)
        self.range_min_input.setValue(0)
        self.range_max_input = QDoubleSpinBox()
        self.range_max_input.setRange(-1000, 1000)
        self.range_max_input.setValue(100)
        range_layout.addWidget(self.range_min_input)
        range_layout.addWidget(QLabel("до"))
        range_layout.addWidget(self.range_max_input)
        settings_layout.addLayout(range_layout)
        
        # Частота измерений
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("Частота (Гц):"))
        self.frequency_input = QDoubleSpinBox()
        self.frequency_input.setRange(0.1, 100)
        self.frequency_input.setValue(1)
        freq_layout.addWidget(self.frequency_input)
        settings_layout.addLayout(freq_layout)
        
        # Погрешность
        error_layout = QHBoxLayout()
        error_layout.addWidget(QLabel("Погрешность (%):"))
        self.error_rate_input = QDoubleSpinBox()
        self.error_rate_input.setRange(0, 100)
        self.error_rate_input.setValue(5)
        error_layout.addWidget(self.error_rate_input)
        settings_layout.addLayout(error_layout)
        
        settings_group.setLayout(settings_layout)
        left_layout.addWidget(settings_group)

        # Группа режимов работы
        modes_group = QGroupBox("Режимы работы")
        modes_layout = QVBoxLayout()
        
        # Режим работы
        operation_mode_layout = QHBoxLayout()
        operation_mode_layout.addWidget(QLabel("Режим работы:"))
        self.operation_mode_combo = QComboBox()
        self.operation_mode_combo.addItems([mode.value for mode in OperationMode])
        operation_mode_layout.addWidget(self.operation_mode_combo)
        modes_layout.addLayout(operation_mode_layout)
        
        # Режим симуляции
        simulation_mode_layout = QHBoxLayout()
        simulation_mode_layout.addWidget(QLabel("Режим симуляции:"))
        self.simulation_mode_combo = QComboBox()
        self.simulation_mode_combo.addItems([mode.value for mode in SimulationMode])
        simulation_mode_layout.addWidget(self.simulation_mode_combo)
        modes_layout.addLayout(simulation_mode_layout)
        
        # Скорость симуляции
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Скорость:"))
        self.speed_input = QDoubleSpinBox()
        self.speed_input.setRange(0.1, 10)
        self.speed_input.setValue(1)
        speed_layout.addWidget(self.speed_input)
        modes_layout.addLayout(speed_layout)
        
        modes_group.setLayout(modes_layout)
        left_layout.addWidget(modes_group)

        # Группа параметров окружающей среды
        environment_group = QGroupBox("Параметры окружающей среды")
        environment_layout = QVBoxLayout()
        
        # Температура
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Температура (°C):"))
        self.temperature_input = QDoubleSpinBox()
        self.temperature_input.setRange(-50, 50)
        self.temperature_input.setValue(25)
        temp_layout.addWidget(self.temperature_input)
        environment_layout.addLayout(temp_layout)
        
        # Влажность
        humidity_layout = QHBoxLayout()
        humidity_layout.addWidget(QLabel("Влажность (%):"))
        self.humidity_input = QDoubleSpinBox()
        self.humidity_input.setRange(0, 100)
        self.humidity_input.setValue(50)
        humidity_layout.addWidget(self.humidity_input)
        environment_layout.addLayout(humidity_layout)
        
        # Давление
        pressure_layout = QHBoxLayout()
        pressure_layout.addWidget(QLabel("Давление (кПа):"))
        self.pressure_input = QDoubleSpinBox()
        self.pressure_input.setRange(0, 200)
        self.pressure_input.setValue(101.3)
        pressure_layout.addWidget(self.pressure_input)
        environment_layout.addLayout(pressure_layout)
        
        environment_group.setLayout(environment_layout)
        left_layout.addWidget(environment_group)

        # Группа управления
        control_group = QGroupBox("Управление")
        control_layout = QVBoxLayout()
        
        # Ввод эталонного значения
        reference_layout = QHBoxLayout()
        reference_layout.addWidget(QLabel("Эталонное значение:"))
        self.reference_input = QDoubleSpinBox()
        self.reference_input.setRange(-1000, 1000)
        self.reference_input.setValue(50)
        reference_layout.addWidget(self.reference_input)
        control_layout.addLayout(reference_layout)
        
        # Загрузка CSV файла
        csv_layout = QHBoxLayout()
        self.csv_path_label = QLabel("CSV файл не выбран")
        self.browse_button = QPushButton("Обзор...")
        self.browse_button.clicked.connect(self.browse_csv)
        csv_layout.addWidget(self.csv_path_label)
        csv_layout.addWidget(self.browse_button)
        control_layout.addLayout(csv_layout)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        self.start_button = QPushButton('Запустить симуляцию')
        self.start_button.clicked.connect(self.start_simulation)
        self.stop_button = QPushButton('Остановить симуляцию')
        self.stop_button.clicked.connect(self.stop_simulation)
        self.stop_button.setEnabled(False)
        self.export_button = QPushButton('Экспорт в CSV')
        self.export_button.clicked.connect(self.export_to_csv)
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addWidget(self.export_button)
        control_layout.addLayout(buttons_layout)
        
        control_group.setLayout(control_layout)
        left_layout.addWidget(control_group)

        # Правая панель с графиком и статистикой
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        main_layout.addWidget(right_panel, stretch=2)

        # Вкладки
        self.tabs = QTabWidget()
        right_layout.addWidget(self.tabs)

        # Вкладка с графиком
        plot_tab = QWidget()
        plot_layout = QVBoxLayout(plot_tab)
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        plot_layout.addWidget(self.canvas)
        self.tabs.addTab(plot_tab, "График")

        # Вкладка с логом
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        log_layout.addWidget(self.log_area)
        self.tabs.addTab(log_tab, "Лог измерений")

        # Вкладка со статистикой
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Параметр", "Значение"])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        stats_layout.addWidget(self.stats_table)
        self.tabs.addTab(stats_tab, "Статистика")

    def update_plot(self):
        """Обновление графика."""
        if not self.timestamps:
            return
            
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Преобразуем временные метки в datetime
        times = [datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in self.timestamps]
        
        # Создаем график
        ax.plot(times, self.values, 'b-', label='Измерения')
        
        # Добавляем точки с разными цветами в зависимости от статуса
        for i, status in enumerate(self.statuses):
            color = 'g' if status == 'OK' else 'r' if status == 'ERROR' else 'y'
            ax.plot(times[i], self.values[i], f'{color}o')
        
        # Настраиваем график
        ax.set_xlabel('Время')
        ax.set_ylabel('Значение')
        ax.set_title('График измерений')
        ax.grid(True)
        ax.legend()
        
        # Форматируем оси времени
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        self.figure.tight_layout()
        
        # Обновляем холст
        self.canvas.draw()

    def update_statistics(self, stats):
        """Обновление таблицы статистики."""
        self.stats_table.setRowCount(len(stats))
        for i, (key, value) in enumerate(stats.items()):
            self.stats_table.setItem(i, 0, QTableWidgetItem(str(key)))
            self.stats_table.setItem(i, 1, QTableWidgetItem(str(value)))

    def browse_csv(self):
        """Открытие диалога выбора CSV файла."""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Выберите CSV файл", "", "CSV Files (*.csv)"
        )
        if file_name:
            self.csv_path_label.setText(file_name)
            try:
                # Читаем CSV файл и устанавливаем первое значение как эталонное
                measurements = CSVProcessor.read_csv(file_name)
                if measurements:
                    self.reference_input.setValue(measurements[0]['value'])
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось прочитать CSV файл: {str(e)}")

    def start_simulation(self):
        """Запуск симуляции."""
        try:
            # Обновляем настройки прибора
            self.simulator.range_min = self.range_min_input.value()
            self.simulator.range_max = self.range_max_input.value()
            self.simulator.frequency = self.frequency_input.value()
            self.simulator.error_rate = self.error_rate_input.value() / 100
            
            # Устанавливаем режимы работы
            operation_mode = OperationMode(self.operation_mode_combo.currentText())
            simulation_mode = SimulationMode(self.simulation_mode_combo.currentText())
            self.simulator.set_operation_mode(operation_mode)
            self.simulator.set_simulation_mode(simulation_mode, self.speed_input.value())
            
            # Устанавливаем параметры окружающей среды
            self.simulator.set_environment(
                self.temperature_input.value(),
                self.humidity_input.value(),
                self.pressure_input.value()
            )
            
            # Очищаем предыдущие данные
            self.timestamps = []
            self.values = []
            self.statuses = []
            self.log_area.clear()
            self.simulator.clear_statistics()
            
            # Запускаем симуляцию
            reference_value = self.reference_input.value()
            
            # Если выбран CSV файл, загружаем данные из него
            if self.csv_path_label.text() != "CSV файл не выбран":
                try:
                    measurements = CSVProcessor.read_csv(self.csv_path_label.text())
                    if measurements:
                        self.simulator.measurements = measurements
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить данные из CSV: {str(e)}")
            
            self.simulation_thread = SimulationThread(self.simulator, reference_value)
            self.simulation_thread.measurement_signal.connect(self.update_output)
            self.simulation_thread.data_signal.connect(self.process_measurement)
            self.simulation_thread.statistics_signal.connect(self.update_statistics)
            self.simulation_thread.finished_signal.connect(self.simulation_finished)
            self.simulation_thread.start()
            
            # Обновляем состояние кнопок
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.export_button.setEnabled(False)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def stop_simulation(self):
        """Остановка симуляции."""
        if self.simulation_thread:
            self.simulation_thread.stop()
            self.simulation_thread.wait()
            self.simulation_thread = None
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.export_button.setEnabled(True)

    def simulation_finished(self):
        """Обработка завершения симуляции."""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.export_button.setEnabled(True)

    def process_measurement(self, value, timestamp, status):
        """Обработка нового измерения."""
        self.timestamps.append(timestamp)
        self.values.append(value)
        self.statuses.append(status)
        
        # Ограничиваем количество точек на графике
        max_points = 100
        if len(self.timestamps) > max_points:
            self.timestamps = self.timestamps[-max_points:]
            self.values = self.values[-max_points:]
            self.statuses = self.statuses[-max_points:]

    def update_output(self, message):
        """Обновление области вывода."""
        self.log_area.append(message)

    def export_to_csv(self):
        """Экспорт данных в CSV."""
        if not self.simulator.measurements:
            QMessageBox.warning(self, "Ошибка", "Нет данных для экспорта")
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self, "Сохранить CSV файл", "", "CSV Files (*.csv)"
        )
        if file_name:
            try:
                CSVProcessor.write_csv(file_name, self.simulator.measurements)
                QMessageBox.information(self, "Успех", "Данные успешно экспортированы")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при экспорте: {str(e)}")

    def closeEvent(self, event):
        """Обработка закрытия окна."""
        if self.simulation_thread:
            self.simulation_thread.stop()
            self.simulation_thread.wait()
        self.simulator.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimulatorGUI()
    window.show()
    sys.exit(app.exec_())