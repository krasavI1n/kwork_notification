import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Kwork Monitor")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
