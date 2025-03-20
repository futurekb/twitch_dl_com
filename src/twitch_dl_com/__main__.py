import sys
import os
from PyQt6.QtWidgets import QApplication
from .ui.main_window import MainWindow

def main():
    # プラットフォームプラグインの問題を回避
    os.environ['QT_QPA_PLATFORM'] = 'xcb'
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
