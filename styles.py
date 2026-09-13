PREMIUM_STYLE = """
QMainWindow { background-color: #121212; }

/* Боковая панель навигации */
QFrame#SideBar { 
    background-color: #1e1e1e; 
    border-right: 1px solid #333;
}
QPushButton#NavBtn {
    text-align: left;
    padding: 12px 20px;
    background-color: transparent;
    color: #aaa;
    border: none;
    font-size: 14px;
    border-left: 3px solid transparent;
}
QPushButton#NavBtn:hover { background-color: #252525; color: white; }
QPushButton#NavBtn:checked { 
    background-color: #2d2d2d; 
    color: #4cc2ff; 
    border-left: 3px solid #4cc2ff; 
    font-weight: bold;
}

/* Заголовки разделов */
QLabel#Header { font-size: 22px; font-weight: bold; color: white; margin-bottom: 10px; }
QLabel#SubHeader { font-size: 14px; color: #888; margin-bottom: 15px; }

/* Карточки контента */
QFrame#Card { 
    background-color: #1e1e1e; 
    border-radius: 8px; 
    border: 1px solid #333; 
}

/* Списки элементов */
QListWidget {
    background-color: #181818;
    border: 1px solid #333;
    border-radius: 6px;
    color: #ddd;
    outline: none;
}
QListWidget::item { padding: 10px; border-bottom: 1px solid #252525; }
QListWidget::item:selected { background-color: #0063b1; color: white; }

/* Кнопки действий */
QPushButton#ActionBtn {
    background-color: #2d2d2d;
    color: white;
    border: 1px solid #444;
    padding: 8px 16px;
    border-radius: 4px;
}
QPushButton#ActionBtn:hover { background-color: #3d3d3d; border-color: #666; }

/* Кнопки опасных действий (Kill) */
QPushButton#DangerBtn {
    background-color: #4a1010;
    color: #ffcccc;
    border: 1px solid #6e1818;
    padding: 8px 16px;
    border-radius: 4px;
}
QPushButton#DangerBtn:hover { background-color: #7a1515; }

/* Мониторинг CPU и RAM */
QProgressBar {
    background-color: #1e1e1e;
    border: 1px solid #333;
    border-radius: 4px;
    text-align: center;
    color: white;
}
QProgressBar::chunk { background-color: #0078d4; width: 10px; margin: 0.5px; }
"""
