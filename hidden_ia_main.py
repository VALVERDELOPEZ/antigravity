import sys
import os
import ctypes
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QHBoxLayout, QFileDialog
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from rag_engine import RAGEngine

# Windows API constants
WDA_EXCLUDEFROMCAPTURE = 0x00000011

class AIWorker(QThread):
    response_ready = pyqtSignal(str)
    
    def __init__(self, engine, prompt, system_prompt):
        super().__init__()
        self.engine = engine
        self.prompt = prompt
        self.system_prompt = system_prompt

    def run(self):
        try:
            response = self.engine.get_response(self.prompt, self.system_prompt)
            self.response_ready.emit(response)
        except Exception as e:
            self.response_ready.emit(f"Error: {str(e)}")

class HiddenIA(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visible") # Innocent title
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Load System Prompt
        try:
            with open(r"C:\Users\TRENDINGPC\.gemini\antigravity\brain\995bd58f-01d9-43ae-8895-94360b8f72c7\system_prompt.txt", "r", encoding="utf-8") as f:
                self.system_prompt = f.read()
        except:
            self.system_prompt = "You are an expert assistant."

        # Initialize RAG Engine
        self.engine = RAGEngine()
        
        self.resize(380, 550)
        self.move(100, 100)
        
        self.main_widget = QWidget()
        self.main_widget.setObjectName("MainWidget")
        self.main_widget.setStyleSheet("""
            #MainWidget {
                background-color: rgba(25, 25, 25, 245);
                border-radius: 12px;
                border: 1px solid #444;
            }
            QTextEdit {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 8px;
                color: #dcdcdc;
                font-family: 'Consolas', 'Segoe UI';
                font-size: 11pt;
                padding: 10px;
            }
            QLineEdit {
                background-color: #333;
                border: 1px solid #555;
                border-radius: 5px;
                color: #fff;
                padding: 10px;
                font-size: 10pt;
            }
            QPushButton {
                background-color: #3e3e3e;
                color: #ccc;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton#AskBtn {
                background-color: #005a9e;
                color: white;
            }
            QPushButton:hover { background-color: #555; }
            QPushButton#AskBtn:hover { background-color: #0078d4; }
        """)
        
        layout = QVBoxLayout(self.main_widget)
        
        # Header / Drag handle
        header = QHBoxLayout()
        self.title_label = QPushButton("HIDDEN IA")
        self.title_label.setStyleSheet("background: transparent; color: #666; font-size: 8pt; border: none;")
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self.close)
        self.upload_btn = QPushButton("📁")
        self.upload_btn.setFixedSize(30, 30)
        self.upload_btn.clicked.connect(self.upload_document)
        
        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.upload_btn)
        header.addWidget(self.close_btn)
        layout.addLayout(header)
        
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        layout.addWidget(self.chat_history)
        
        input_container = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Comandos...")
        self.input_field.returnPressed.connect(self.handle_send)
        self.send_btn = QPushButton("ASK")
        self.send_btn.setObjectName("AskBtn")
        self.send_btn.clicked.connect(self.handle_send)
        
        input_container.addWidget(self.input_field)
        input_container.addWidget(self.send_btn)
        layout.addLayout(input_container)
        
        self.setCentralWidget(self.main_widget)
        self.apply_stealth_mode()
        self._old_pos = None

    def apply_stealth_mode(self):
        try:
            hwnd = int(self.winId())
            ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
        except: pass

    def upload_document(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Seleccionar Documentos", "", "Text Files (*.txt);;All Files (*.*)")
        for file in files:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                name = os.path.basename(file)
                self.engine.add_document(name, content)
            self.chat_history.append(f"<b>[SISTEMA]</b> Documento cargado: {name}")

    def handle_send(self):
        text = self.input_field.text().strip()
        if not text: return
        
        self.chat_history.append(f"<br><b style='color:#0078d4;'>Usted:</b> {text}")
        self.input_field.clear()
        self.chat_history.append("<i style='color:#777;'>Pensando...</i>")
        
        self.worker = AIWorker(self.engine, text, self.system_prompt)
        self.worker.response_ready.connect(self.display_response)
        self.worker.start()

    def display_response(self, response):
        # Remove "Thinking..."
        cursor = self.chat_history.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.select(cursor.SelectionType.LineUnderCursor)
        cursor.removeSelectedText()
        
        self.chat_history.append(f"<b style='color:#50fa7b;'>IA:</b><br>{response}<br>")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self._old_pos:
            delta = event.globalPosition().toPoint() - self._old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self._old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event): self._old_pos = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HiddenIA()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HiddenIA()
    window.show()
    sys.exit(app.exec())
