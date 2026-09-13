import sys
import os
import winreg
import psutil
import ctypes
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QListWidget,
                             QMessageBox, QStackedWidget, QFrame, QProgressBar,
                             QListWidgetItem, QFileDialog)
from PyQt5.QtCore import Qt, QTimer
from styles import PREMIUM_STYLE


class UltimateUnlocker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SimpleUnlocker ULTIMATE")
        self.resize(900, 600)
        self.setStyleSheet(PREMIUM_STYLE)
        self.target_file = ""
        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(2000)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Боковое меню навигации
        sidebar = QFrame()
        sidebar.setObjectName("SideBar")
        sidebar.setFixedWidth(220)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(0, 20, 0, 20)
        side_layout.setSpacing(5)

        lbl_logo = QLabel("  🛡️ UNLOCKER\n  ULTIMATE")
        lbl_logo.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: white; padding-left: 10px; margin-bottom: 20px;")
        side_layout.addWidget(lbl_logo)

        self.nav_group = []
        self.add_nav_btn("📊 Дашборд", 0, side_layout)
        self.add_nav_btn("🔓 Файл Анлокер", 1, side_layout)
        self.add_nav_btn("🚀 Автозагрузка", 2, side_layout)
        self.add_nav_btn("🌐 Сеть и DNS", 3, side_layout)
        self.add_nav_btn("🧹 Очистка", 4, side_layout)

        side_layout.addStretch()
        lbl_ver = QLabel("  v2.0 Premium")
        lbl_ver.setStyleSheet("color: #444; padding: 10px;")
        side_layout.addWidget(lbl_ver)
        main_layout.addWidget(sidebar)

        # Главная область с вкладками
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("padding: 10px;")
        self.stack.addWidget(self.page_dashboard())
        self.stack.addWidget(self.page_file_unlock())
        self.stack.addWidget(self.page_autorun())
        self.stack.addWidget(self.page_network())
        self.stack.addWidget(self.page_cleaner())
        main_layout.addWidget(self.stack)

        # ИСПРАВЛЕНО: Активируем именно первую кнопку из списка
        self.nav_group[0].setChecked(True)

    def add_nav_btn(self, text, index, layout):
        btn = QPushButton(text)
        btn.setObjectName("NavBtn")
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self.switch_page(index, btn))
        layout.addWidget(btn)
        self.nav_group.append(btn)

    def switch_page(self, index, btn_sender):
        self.stack.setCurrentIndex(index)
        for btn in self.nav_group:
            btn.setChecked(False)
        btn_sender.setChecked(True)
        if index == 2: self.refresh_autoruns()

    def create_header(self, title, sub):
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 10)
        l1 = QLabel(title)
        l1.setObjectName("Header")
        l2 = QLabel(sub)
        l2.setObjectName("SubHeader")
        vl.addWidget(l1)
        vl.addWidget(l2)
        return w

    # --- СТРАНИЦА: ДАШБОРД ---
    def page_dashboard(self):
        p = QWidget();
        l = QVBoxLayout(p)
        l.addWidget(self.create_header("Состояние системы", "Мониторинг ресурсов и быстрые фиксы"))

        stats_frame = QFrame();
        stats_frame.setObjectName("Card");
        sl = QVBoxLayout(stats_frame)
        sl.addWidget(QLabel("Загрузка CPU:"))
        self.cpu_bar = QProgressBar();
        sl.addWidget(self.cpu_bar)
        sl.addWidget(QLabel("Использование RAM:"))
        self.ram_bar = QProgressBar();
        sl.addWidget(self.ram_bar)
        l.addWidget(stats_frame)

        l.addWidget(QLabel("Быстрое исправление блокировок:"))
        grid_frame = QFrame();
        grid_frame.setObjectName("Card");
        gl = QVBoxLayout(grid_frame)

        fixes = [("Вернуть Диспетчер задач", self.fix_taskmgr),
                 ("Вернуть Редактор реестра", self.fix_regedit),
                 ("Вернуть Командную строку", self.fix_cmd)]
        for txt, func in fixes:
            h = QHBoxLayout();
            h.addWidget(QLabel(txt))
            b = QPushButton("Исправить");
            b.setObjectName("ActionBtn");
            b.clicked.connect(func)
            h.addWidget(b);
            gl.addLayout(h)

        l.addWidget(grid_frame);
        l.addStretch()
        return p

    def update_stats(self):
        self.cpu_bar.setValue(int(psutil.cpu_percent()))
        self.ram_bar.setValue(int(psutil.virtual_memory().percent))

    # --- СТРАНИЦА: ФАЙЛ АНЛОКЕР ---
    def page_file_unlock(self):
        p = QWidget();
        l = QVBoxLayout(p)
        l.addWidget(self.create_header("File Unlocker", "Если файл занят процессом, выберите его через Обзор"))

        file_frame = QFrame();
        file_frame.setObjectName("Card");
        fl = QVBoxLayout(file_frame)
        h = QHBoxLayout()
        self.path_edit = QLabel("Файл не выбран...")
        self.path_edit.setStyleSheet("color: #aaa; border: 1px dashed #444; padding: 10px; border-radius: 4px;")
        btn = QPushButton("Выбрать файл");
        btn.setObjectName("ActionBtn");
        btn.clicked.connect(self.browse_file)
        h.addWidget(self.path_edit, 1);
        h.addWidget(btn);
        fl.addLayout(h)

        fl.addWidget(QLabel("Процессы-блокировщики:"))
        self.lock_list = QListWidget();
        fl.addWidget(self.lock_list)

        unlock_btn = QPushButton("☠️ Убить процессы и разблокировать")
        unlock_btn.setObjectName("DangerBtn");
        unlock_btn.clicked.connect(self.kill_lockers)
        fl.addWidget(unlock_btn)

        l.addWidget(file_frame);
        l.addStretch()
        return p

    def browse_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Выберите заблокированный файл")
        if f:
            self.target_file = os.path.abspath(f).lower()
            self.path_edit.setText(f)
            self.path_edit.setStyleSheet("color: #4cc2ff; border: 1px solid #4cc2ff; padding: 10px;")
            self.check_locks()

    def check_locks(self):
        self.lock_list.clear()
        found = False
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                for item in proc.open_files():
                    if item.path.lower() == self.target_file:
                        w_item = QListWidgetItem(f"{proc.info['name']} (PID: {proc.info['pid']})")
                        w_item.setData(Qt.UserRole, proc.info['pid'])
                        self.lock_list.addItem(w_item)
                        found = True
            except:
                pass
        if not found: self.lock_list.addItem("Файл свободен (или блокировка системная)")

    def kill_lockers(self):
        if self.lock_list.count() == 0: return
        killed = 0
        for i in range(self.lock_list.count()):
            pid = self.lock_list.item(i).data(Qt.UserRole)
            if pid:
                try:
                    psutil.Process(pid).kill()
                    killed += 1
                except:
                    pass
        QMessageBox.information(self, "Готово", f"Завершено процессов: {killed}")
        self.check_locks()

    # --- СТРАНИЦА: АВТОЗАГРУЗКА ---
    def page_autorun(self):
        p = QWidget();
        l = QVBoxLayout(p)
        l.addWidget(self.create_header("Менеджер автозагрузки", "Удалите лишнее, чтобы ПК загружался быстрее"))
        self.autorun_list = QListWidget();
        l.addWidget(self.autorun_list)

        btn_layout = QHBoxLayout()
        btn_del = QPushButton("Удалить из автозагрузки");
        btn_del.setObjectName("DangerBtn");
        btn_del.clicked.connect(self.delete_autorun)
        btn_ref = QPushButton("Обновить список");
        btn_ref.setObjectName("ActionBtn");
        btn_ref.clicked.connect(self.refresh_autoruns)
        btn_layout.addWidget(btn_del);
        btn_layout.addWidget(btn_ref);
        l.addLayout(btn_layout)
        return p

    def refresh_autoruns(self):
        self.autorun_list.clear()
        paths = [(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                 (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run")]
        for root, key_path in paths:
            try:
                key = winreg.OpenKey(root, key_path, 0, winreg.KEY_READ)
                i = 0
                while True:
                    try:
                        name, val, _ = winreg.EnumValue(key, i)
                        item = QListWidgetItem(f"{name}  ➜  {val}")
                        item.setData(Qt.UserRole, (root, key_path, name))
                        self.autorun_list.addItem(item);
                        i += 1
                    except OSError:
                        break
            except:
                pass

    def delete_autorun(self):
        item = self.autorun_list.currentItem()
        if not item: return
        root, key_path, name = item.data(Qt.UserRole)
        reply = QMessageBox.question(self, "Подтверждение", f"Удалить '{name}' из автозагрузки?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                key = winreg.OpenKey(root, key_path, 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key, name);
                winreg.CloseKey(key)
                self.refresh_autoruns()
                QMessageBox.information(self, "Успех", "Запись удалена.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить: {e}")

    # --- СТРАНИЦА: СЕТЬ И ОЧИСТКА ---
    def page_network(self):
        p = QWidget();
        l = QVBoxLayout(p)
        l.addWidget(self.create_header("Сетевая аптечка", "Инструменты для восстановления интернета"))

        card = QFrame();
        card.setObjectName("Card");
        cl = QVBoxLayout(card)
        info = QLabel("Используйте эти кнопки, если браузер не открывает сайты после удаления вирусов.")
        info.setWordWrap(True);
        info.setStyleSheet("color: #888; margin-bottom: 20px;");
        cl.addWidget(info)

        btns = [("Сброс Winsock (netsh winsock reset)", self.net_winsock),
                ("Очистка кэша DNS (ipconfig /flushdns)", self.net_dns),
                ("Сброс TCP/IP стека", self.net_ip)]
        for title, func in btns:
            b = QPushButton(title);
            b.setObjectName("ActionBtn");
            b.setMinimumHeight(40);
            b.clicked.connect(func);
            cl.addWidget(b)
        l.addWidget(card);
        l.addStretch()
        return p

    def run_cmd(self, cmd, success_msg):
        try:
            subprocess.run(cmd, shell=True, check=True)
            QMessageBox.information(self, "Успешно", success_msg)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Сбой команды: {e}")

    def net_winsock(self):
        self.run_cmd("netsh winsock reset", "Каталог Winsock сброшен.\nПерезагрузите ПК!")

    def net_dns(self):
        self.run_cmd("ipconfig /flushdns", "Кэш DNS успешно очищен.")

    def net_ip(self):
        self.run_cmd("netsh int ip reset", "TCP/IP сброшен.\nПерезагрузите ПК!")

    def page_cleaner(self):
        p = QWidget();
        l = QVBoxLayout(p)
        l.addWidget(self.create_header("Очистка мусора", "Освободите место, удалив временные файлы"))

        card = QFrame();
        card.setObjectName("Card");
        cl = QVBoxLayout(card)
        lbl = QLabel("Нажмите кнопку для сканирования и очистки папки Temp.")
        lbl.setStyleSheet("color: #aaa; margin-bottom: 10px;");
        cl.addWidget(lbl)

        btn = QPushButton("🧹 Очистить системный TEMP");
        btn.setObjectName("ActionBtn")
        btn.setMinimumHeight(50);
        btn.setStyleSheet("font-size: 14px; font-weight: bold;");
        btn.clicked.connect(self.clean_temp)
        cl.addWidget(btn);
        l.addWidget(card);
        l.addStretch()
        return p

    def clean_temp(self):
        temp_dir = os.environ.get('TEMP')
        if not temp_dir: return
        deleted, errors = 0, 0
        for root, dirs, files in os.walk(temp_dir):
            for f in files:
                try:
                    os.remove(os.path.join(root, f));
                    deleted += 1
                except:
                    errors += 1
        QMessageBox.information(self, "Очистка завершена",
                                f"Удалено файлов: {deleted}\nНе удалось удалить (заняты): {errors}")

    # --- СИСТЕМНЫЕ ТВИТЫ ---
    def set_reg_val(self, path, name, val):
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, path)
            winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, val);
            winreg.CloseKey(key)
            QMessageBox.information(self, "Успех", "Настройка применена!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def fix_taskmgr(self):
        self.set_reg_val(r"Software\Microsoft\Windows\CurrentVersion\Policies\System", "DisableTaskMgr", 0)

    def fix_regedit(self):
        self.set_reg_val(r"Software\Microsoft\Windows\CurrentVersion\Policies\System", "DisableRegistryTools", 0)

    def fix_cmd(self):
        self.set_reg_val(r"Software\Policies\Microsoft\Windows\System", "DisableCMD", 0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UltimateUnlocker()
    window.show()
    sys.exit(app.exec_())

