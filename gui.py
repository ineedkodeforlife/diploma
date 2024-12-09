import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QLineEdit
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

        # График
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Управление
        self.start_button = QPushButton("Начать симуляцию")
        self.start_button.clicked.connect(self.start_simulation)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Остановить симуляцию")
        layout.addWidget(self.stop_button)

        # Статус
        self.status_label = QLabel("Статус: OK")
        layout.addWidget(self.status_label)

        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

    def start_simulation(self):
        reference_value = 50  # Пример эталонного значения
        self.simulator.run_simulation(reference_value)

    def update_plot(self):
        """Обновление графика."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        values = [m["value"] for m in self.simulator.measurements]
        timestamps = [m["timestamp"] for m in self.simulator.measurements]
        ax.plot(timestamps, values, label="Измерения")
        ax.legend()
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimulatorGUI()
    window.show()
    sys.exit(app.exec_())
