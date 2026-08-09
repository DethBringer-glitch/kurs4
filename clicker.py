import sys
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
import os


class ClickerApp(QWidget):
  def __init__(self):
    super().__init__()
    if os.path.exists('counter.txt'):
      with open('counter.txt', 'r', encoding='utf-8') as f:
        self.counter = int(f.read(), 2)
    else:
      self.counter = 0
    self.initUI()

  def initUI(self):
    self.setWindowTitle('кликер')
    self.resize(300, 200)
    layout = QVBoxLayout()

    self.label = QLabel(f'{self.counter}', self)
    self.label.setStyleSheet('font-size: 100px; text-align: center;')
    self.label.setAlignment(Qt.AlignCenter)
    layout.addWidget(self.label)

    self.button = QPushButton('', self)
    self.button.setStyleSheet('font-size: 20px; padding: 10px;')
    self.button.clicked.connect(self.add_click)
    layout.addWidget(self.button)

    self.setLayout(layout)

  def add_click(self):
    self.counter += 1
    with open('counter.txt', 'w', encoding='utf-8') as f:
      f.write(bin(self.counter)[2::])
    self.label.setText(f'{self.counter}')


if __name__ == '__main__':
  app = QApplication(sys.argv)
  ex = ClickerApp()
  ex.show()
  sys.exit(app.exec_())
