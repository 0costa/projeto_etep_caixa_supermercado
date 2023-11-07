from PyQt5.QtWidgets import QWidget, QLineEdit, QLabel, QHBoxLayout

class Input(QWidget):
    def __init__(self, legenda, placeholder):
        self.__legenda = legenda
        self.__placeholder = placeholder

        self.interface()
        self.layout()

    def interface(self):
        self.legenda = QLabel(self.__legenda)

        self.input = QLineEdit()
        self.input.setPlaceholderText(self.__placeholder)


    def layout(self):
        layout = QHBoxLayout()
        layout.addWidget(self.legenda)
        layout.addWidget(self.input)

        self.setLayout(layout)