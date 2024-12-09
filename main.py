from gui import SimulatorGUI
from PyQt5.QtWidgets import QApplication
import sys

def main():
    """Точка входа в приложение."""
    app = QApplication(sys.argv)  # Создание приложения PyQt
    window = SimulatorGUI()       # Инициализация графического интерфейса
    window.show()                 # Отображение главного окна
    sys.exit(app.exec_())         # Запуск главного цикла приложения

if __name__ == "__main__":
    main()
