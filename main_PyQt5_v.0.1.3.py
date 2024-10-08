import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QListWidget,
                             QPushButton, QVBoxLayout, QWidget, QMessageBox)
from PyQt5.QtCore import Qt
import configparser
import subprocess


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings_file = 'settings.ini'
        self.config = configparser.ConfigParser()

        if os.path.exists(self.settings_file):
            self.config.read(self.settings_file)
        else:
            self.config.add_section('Settings')

        self.folder_path = ''
        self.program_path = ''

        self.initUI()
        self.check_and_create_settings()
        self.scan_directory()

    def check_and_create_settings(self):
        program_path = self.config.get('Settings', 'program_path', fallback=None)
        if not program_path:
            self.choose_program()
        else:
            self.program_path = program_path

        folder_path = self.config.get('Settings', 'folder_path', fallback=None)
        if not folder_path:
            self.choose_folder()
        else:
            self.folder_path = folder_path

        with open(self.settings_file, 'w') as configfile:
            self.config.write(configfile)

    def choose_program(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file, _ = QFileDialog.getOpenFileName(self, "Select Executable Program", "",
                                              "Executables (*.exe);;All Files (*)", options=options)
        if file:
            self.config.set('Settings', 'program_path', file)
            self.program_path = file

    def choose_folder(self):
        options = QFileDialog.Options()
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", options=options)
        if folder:
            self.config.set('Settings', 'folder_path', folder)
            self.folder_path = folder

    def scan_directory(self):
        if not self.folder_path:
            QMessageBox.warning(self, "Warning", "Folder path is not set.")
            return

        self.listWidget.clear()
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                if file.endswith('.DBY'):
                    self.listWidget.addItem(os.path.join(root, file))

    def open_file(self):
        selected_items = self.listWidget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a file to open.")
            return

        dby_file_path = selected_items[0].text()
        try:
            subprocess.Popen([self.program_path, dby_file_path])
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open the file: {e}")

    def initUI(self):
        self.setWindowTitle('DBY File Scanner')
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout()

        self.listWidget = QListWidget()
        self.listWidget.itemDoubleClicked.connect(self.open_file)
        layout.addWidget(self.listWidget)

        open_button = QPushButton("Open", self)
        open_button.clicked.connect(self.open_file)
        layout.addWidget(open_button)
        centralWidget.setLayout(layout)
        self.resize(600, 400)

    if __name__ == '__main__':
        app = QApplication(sys.argv)
        mainWin = QMainWindow()
        mainWin.show()
        sys.exit(app.exec_())
