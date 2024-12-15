import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QLineEdit, QComboBox, QTabWidget, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from simulator import Simulator

class SimulatorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.simulator = Simulator()
        self.setWindowTitle("Симулятор измерительного прибора")
        self.setGeometry(100, 100, 800, 600)
        self.initUI()

    def initUI(self):
        main_widget = QWidget()
        layout = QVBoxLayout()

        # Вкладки
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Вкладка с графиком
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.tab_widget.addTab(self.canvas, "График")

        # Вкладка с журналом событий
        self.event_log = QTableWidget()
        self.event_log.setColumnCount(3)
        self.event_log.setHorizontalHeaderLabels(["Время", "Значение", "Статус"])
        self.tab_widget.addTab(self.event_log, "Журнал событий")

        # Управление
        control_widget = QWidget()
        control_layout = QVBoxLayout()

        self.start_button = QPushButton("Начать симуляцию")
        self.start_button.clicked.connect(self.start_simulation)
        control_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Остановить симуляцию")
        self.stop_button.clicked.connect(self.stop_simulation)
        control_layout.addWidget(self.stop_button)

        # Статус
        self.status_label = QLabel("Статус: OK")
        control_layout.addWidget(self.status_label)

        # Режим работы
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Normal", "Interference", "Emergency"])
        control_layout.addWidget(self.mode_combo)

        # Эталонное значение
        self.reference_value_input = QLineEdit()
        self.reference_value_input.setPlaceholderText("Эталонное значение")
        control_layout.addWidget(self.reference_value_input)

        control_widget.setLayout(control_layout)
        layout.addWidget(control_widget)

        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)

    def start_simulation(self):
        reference_value = float(self.reference_value_input.text())
        self.simulator.run_simulation(reference_value)
        self.timer.start(1000)  # Обновление каждую секунду

    def stop_simulation(self):
        self.simulator.stop_simulation()
        self.timer.stop()

    def update_plot(self):
        """Обновление графика."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        values = [m["value"] for m in self.simulator.measurements]
        timestamps = [m["timestamp"] for m in self.simulator.measurements]
        ax.plot(timestamps, values, label="Измерения")
        ax.legend()
        self.canvas.draw()

        # Обновление журнала событий
        self.event_log.setRowCount(len(self.simulator.measurements))
        for row, measurement in enumerate(self.simulator.measurements):
            self.event_log.setItem(row, 0, QTableWidgetItem(measurement["timestamp"]))
            self.event_log.setItem(row, 1, QTableWidgetItem(str(measurement["value"])))
            self.event_log.setItem(row, 2, QTableWidgetItem(measurement["status"]))

        # Обработка очереди данных
        self.simulator.process_queue()

    def closeEvent(self, event):
        self.simulator.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimulatorGUI()
    window.show()
    sys.exit(app.exec_())
