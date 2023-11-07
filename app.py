import sys, pandas as pd, locale, os, random, re, subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QLabel, QLineEdit, QTableView, QGridLayout, QDialog, QButtonGroup, QStyledItemDelegate, QHeaderView, QHBoxLayout, QAbstractItemView, QMessageBox
from PyQt5.QtCore import Qt, QAbstractTableModel
from PyQt5.QtGui import QCursor, QPainter, QStandardItemModel, QValidator, QIntValidator
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from infra.repository.repo_produto import ProdutoRepository
from datetime import datetime

app = QApplication(sys.argv)

class ConverterValorParaReal:
    def __init__(self, valor:float):
    
        locale.setlocale(locale.LC_MONETARY, 'pt_BR.UTF-8')
        self.valor = valor 

    def valorFormatadoComCifrao(self):
        return locale.currency(self.valor, grouping=True, symbol=True)
    
    def valorFormatadoSemCifrao(self):
        return locale.currency(self.valor, grouping=True, symbol=False)

class CabecalhoTabela(QWidget):
    def __init__(self):
        super().__init__()

        valores = ["Código", "Decrição", "Valor"]

        layout = QHBoxLayout()

        for x in valores:
            label = QLabel(x)

            if valores.index(x) == 0 or valores.index(x) == 2:
                label.setFixedWidth(89)

            label.setFixedHeight(40)
            label.setStyleSheet("background: #cbd0d8; border: 1px solid lightgray; color: #333d51; font-weight: 700; font-size: 12px; margin-top: 15px;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter )
            layout.addWidget(label)

        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)
        layout.setStretch(1,1)
        self.setLayout(layout)
        self.setFixedWidth(882)

class ModeloDeTabela(QAbstractTableModel):
    def __init__(self, dados:list):
        super().__init__()
        self._dados = dados
        self._cabecalhos = ["Código", "Descrição","Valor"]
        self.tabela = pd.DataFrame(self._dados)
        
    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            linha = index.row()
            coluna = self._cabecalhos[index.column()]
            
            valor = self.tabela.iloc[linha][self._cabecalhos.index(coluna)]

            if coluna == "Código":
                return str(valor)

            if coluna == "Descrição":
                return str(valor)

            if coluna == "Valor":
                return format(valor, ".2f")

            return valor
    
    def rowCount(self, index):
        return len(self.tabela.index)

    def columnCount(self, index):
        return len(self.tabela.columns.values)

class CenterCellTable(QStyledItemDelegate):
    def paint(self, painter, option, index):
        coluna = index.model().headerData(index.column(), Qt.Orientation.Horizontal, Qt.DisplayRole)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if coluna == 'Descrição':
            option.displayAlignment = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        else:
            option.displayAlignment = Qt.AlignmentFlag.AlignCenter

        super(CenterCellTable, self).paint(painter, option, index)
        painter.restore()

class Tabela(QTableView):
    def __init__(self):
        super().__init__()
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setVisible(False)
        self.setItemDelegate(CenterCellTable())
        self.setSelectionMode(QAbstractItemView.SingleSelection)

class Mensagem(QMessageBox):
    def __init__(self, texto):
        super().__init__()
        self.setWindowTitle("Aviso")
        self.setText(texto)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.exec()

class Botao(QPushButton):
    def __init__(self, text, id, **kwargs):
        super().__init__()
        self.setText(text)
        self.__id = id

        btn_style = """
            QPushButton{
                border: 1px solid lightgray; 
                background: #e9ecef; 
                margin-right: 10px;
                border-radius: 3px;
            }

            QPushButton:hover{
                background: #4D00a8e8;
                border: 1px solid #00a8e8;
            }"""
 
        self.setStyleSheet(btn_style)
        self.setFixedSize(100, 25)
        self.setCursor(QCursor(Qt.PointingHandCursor))
    
        if 'atalho' in kwargs:
            atalho = kwargs["atalho"]
            self.setShortcut(atalho)
            self.setToolTip(f'Atalho: {str(atalho).replace("Ctrl+Return", "Ctrl+Enter")}')
    
    @property
    def id(self):
        return self.__id

class JanelaPrincial(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.setFixedSize(900, 700)
        self.setWindowTitle("Caixa de Super Mercado")
        self.interface()
        self.layout()
        self.sinais_de_botao()

    def interface(self):

        #labels
        self.label_produto = QLabel('Produto')

        #input
        self.input_cod_produto = QLineEdit()

        #botoes
        self.btn_filtrar = Botao('Adicionar', 4, atalho= 'Ctrl+Return')
        self.btn_cadastrar = Botao("Cadastrar produto", 1)
        self.btn_cadastrar.setFixedWidth(120)
        self.btn_pagamento = Botao("Pagamento", 2)
        self.btn_excluir_produto = Botao("Remover", 3, atalho= 'Ctrl+Del')

        self.btn_group = QButtonGroup()
        for btn in [self.btn_cadastrar, self.btn_pagamento, self.btn_excluir_produto]:
            self.btn_group.addButton(btn)

        #tabela

        self.cabecalho = CabecalhoTabela()
        self.tabela_compra = Tabela()
        self.produtos_compra = []

        #widgets
        self.soma_total_da_compra = 0
        self.total_da_compra = QLabel("Total da compra: R$ 0,00")

        #style
        self.label_produto.setFixedSize(120, 35)
        self.label_produto.setStyleSheet("background: #cbd0d8; border: 1px solid lightgray; color: #333d51; font-weight: 700; font-size: 12px;")
        self.label_produto.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.input_cod_produto.setFixedHeight(35)
        self.input_cod_produto.setStyleSheet("border: 1px solid lightgray; padding-left: 10px; margin-right: 15px;")

        self.tabela_compra.setStyleSheet("margin-top: 0; margin-bottom: 15px; border: 1px solid lightgray;")

        self.total_da_compra.setFixedHeight(40)
        self.total_da_compra.setStyleSheet("border: 1px solid #a0bcc9; background: #000000; color: #c0d3dc; font-weight: bold; font-size: 13px; border-radius: 5px;")
        self.total_da_compra.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def layout(self):
        widget = QWidget()
        layout = QGridLayout()
        layout.setSpacing(0)

        layout.addWidget(self.label_produto, 0, 0)
        layout.addWidget(self.input_cod_produto, 0, 1, 1, 4)
        layout.addWidget(self.btn_filtrar, 0, 5 )
        layout.addWidget(self.btn_excluir_produto, 0, 6)

        layout.addWidget(self.cabecalho, 1, 0, 1, 7)
        layout.addWidget(self.tabela_compra, 2, 0, 1, 7)

        layout.addWidget(self.btn_cadastrar, 3, 0)
        
        layout.addWidget(self.btn_pagamento, 3, 1)
        layout.addWidget(self.total_da_compra, 3, 2, 1, 5)

        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def sinais_de_botao(self):
        self.btn_group.buttonClicked.connect(self.show_popup)
        self.btn_filtrar.clicked.connect(self.adicionar_produto)
        self.btn_excluir_produto.clicked.connect(self.remover_produto)

    def show_popup(self, button):
        if button.id == 1:
            CadastrarProduto().exec()

        if button.id == 2:
            model = self.tabela_compra.model()
            
            if not model:
                return Mensagem('O carrinho de compras está vazio!')
            
            dialog_pagamento = Pagamento(self.soma_total_da_compra)

            if dialog_pagamento.exec() == QDialog.DialogCode.Accepted:
                dados_pagamento = dialog_pagamento.compra_finalizada()

                if not dados_pagamento:
                    return

                if dados_pagamento['troco'] >= 0:
                    
                    self.tabela_compra.setModel(QStandardItemModel())
                    self.soma_total_da_compra = 0
                    self.atualizar_total_da_compra()

                    tabela_produtos = [list(x) for x in self.produtos_compra]
                    tabela_produtos.insert(0, ['Código', 'Descrição do produto', 'Valor (R$)'])
                    Mensagem("Compra finalizada!")
                    self.produtos_compra = []
                    GerarNotinha(tabela_produtos, dados_pagamento)

                else:
                    Mensagem("O Valor pago é menor que o total da compra!")

    def adicionar_produto(self):
        try: 
            id_produto = self.input_cod_produto.text()

            if not id_produto:
                return Mensagem("Por favor dígite o código do produto!")

            id_produto = int(id_produto)
            produtos = ProdutoRepository().add_produto(id_produto)

            if not produtos:
                return Mensagem("Produto não cadastrado!")
            
            self.produtos_compra.append(produtos[0])
            self.filtrar()
            self.input_cod_produto.clear()

            self.soma_total_da_compra += produtos[0][2]
            self.atualizar_total_da_compra()

        except Exception as erro:
            Mensagem(str(erro))

    def atualizar_total_da_compra(self):
        valor = ConverterValorParaReal(self.soma_total_da_compra).valorFormatadoComCifrao()

        self.total_da_compra.clear()
        self.total_da_compra.setText(f'Total da compra: {valor}')

    def remover_produto(self):
        produtos_selecionado = self.tabela_compra.selectedIndexes()
        if not produtos_selecionado:
            return Mensagem("Nenhum produto selecionado!")
        indexes = []

        for index in produtos_selecionado:
            model = self.tabela_compra.model()
            row = index.row()
            id = model.index(row, 0)
            id_value = model.data(id, Qt.ItemDataRole.DisplayRole)

            indexes.append(int(id_value))

        for i in self.produtos_compra:
            id = i[0]
            valor_produto = i[2]

            if id in indexes:
                self.produtos_compra.pop(self.produtos_compra.index(i))
                self.soma_total_da_compra -= valor_produto if self.soma_total_da_compra > 0 else 0
                self.atualizar_total_da_compra()

        if not self.produtos_compra:
            self.tabela_compra.setModel(QStandardItemModel())
        else:
            self.filtrar()

    def filtrar(self):
        tabela = ModeloDeTabela(self.produtos_compra)
        
        self.tabela_compra.setModel(tabela)
        self.tabela_compra.resizeColumnsToContents()

        for column in range(self.tabela_compra.model().columnCount(1)):
            self.tabela_compra.setColumnWidth(column, self.tabela_compra.columnWidth(column)+50)

        self.tabela_compra.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

class CadastrarProduto(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint )
        self.setFixedSize(400, 200)
        self.setWindowTitle('Cadastrar Produto')

        self.interface()
        self.layout()
        self.sinal_de_botao()

    def interface(self):
        height = 40

        self.label_codigo = QLabel("Código")
        self.label_produto = QLabel("Descrição do produto")
        self.label_valor = QLabel("Valor R$")

        self.label_codigo.setFixedHeight(height)
        self.label_produto.setFixedHeight(height)
        self.label_valor.setFixedHeight(height)
        
        self.input_codigo = QLineEdit()
        self.input_produto = QLineEdit()
        self.input_valor = QLineEdit()

        self.input_codigo.setValidator(QIntValidator())

        self.input_valor.setPlaceholderText("Não use virgula para o valor, somente ponto!!")

        self.input_codigo.setFixedHeight(height)
        self.input_produto.setFixedHeight(height)
        self.input_valor.setFixedHeight(height)

        self.btn_cadastrar = Botao("Cadastrar", 1)

        self.setStyleSheet("""
            QLabel{background: #cbd0d8; border: 1px solid lightgray; color: #333d51; font-weight: 700; font-size: 12px;}
            QLineEdit{border: 1px solid lightgray; padding-left: 10px; margin-right: 15px;}
        """)

    def layout(self):
        layout = QGridLayout()
        
        layout.addWidget(self.label_codigo, 0, 1)
        layout.addWidget(self.input_codigo, 0, 2)
        layout.addWidget(self.label_produto, 1, 1)
        layout.addWidget(self.input_produto, 1, 2)
        layout.addWidget(self.label_valor, 2, 1)
        layout.addWidget(self.input_valor, 2, 2)
        layout.addWidget(self.btn_cadastrar, 3, 1)

        layout.setSpacing(0)
        self.setLayout(layout)

    def sinal_de_botao(self):
        self.btn_cadastrar.clicked.connect(self.cadastrar_produto)
        self.input_codigo.textChanged.connect(self.format_codigo)
        self.input_valor.textChanged.connect(self.format_valor)
    
    def format_codigo(self, text):
        input = re.sub(r'[^\d.]', '', text)
        input = re.sub(r'\.', '', text)
        self.input_codigo.setText(input)

    def format_valor(self, text):
        text = re.sub(r'[^\d.]', '', text)
        text = re.sub(r'\.+', '.', text)
        text = re.sub(r'\.(?=.*\.)', '', text)

        self.input_valor.setText(text)

    def cadastrar_produto(self):
        try:
            codigo = int(self.input_codigo.text())
            produto = self.input_produto.text()
            valor = float(self.input_valor.text())
        except:
            return Mensagem('Preencha todos os campos!')

        try:
            ProdutoRepository().inserir_produto(codigo, produto, valor)

            self.input_codigo.clear()
            self.input_produto.clear()
            self.input_valor.clear()

            return Mensagem("Produto Cadastrado com sucesso!")
        
        except:
            produto_ja_cadastrado = ProdutoRepository().pesquisar_produto_por_codigo(codigo)
            return Mensagem(f"Esse código já está associado ao produto {produto_ja_cadastrado[0]} no valor de {ConverterValorParaReal(produto_ja_cadastrado[1]).valorFormatadoComCifrao()}. Por favor cadastre outro código!")

class Pagamento(QDialog):
    def __init__(self, total_da_compra):
        super().__init__()
        self._total_da_compra = total_da_compra
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint )
        self.setFixedSize(400, 200)
        self.setWindowTitle('Pagamento')

        self.interface()
        self.layout()
        self.sinal_de_botao()

    def interface(self):
        height = 40

        self.label_total = QLabel(f"Total da Compra {ConverterValorParaReal(self._total_da_compra).valorFormatadoComCifrao()}")
        self.label_recebido = QLabel("Valor recebido")
        self.label_troco = QLabel("Troco R$ 0")

        self.label_total.setFixedHeight(height)
        self.label_recebido.setFixedHeight(height)
        self.label_troco.setFixedHeight(height)
        
        self.input_recebido = QLineEdit()
        self.input_recebido.setPlaceholderText("Não use virgula para o valor, somente ponto!!")

        self.input_recebido.setFixedHeight(height)

        self.btn_confirmar = Botao("Confirmar", 1)

        self.setStyleSheet("""
            QLabel{background: #cbd0d8; border: 1px solid lightgray; color: #333d51; font-weight: 700; font-size: 12px;}
            QLineEdit{border: 1px solid lightgray; padding-left: 10px; margin-right: 15px;}
        """)

    def layout(self):
        layout = QGridLayout()
        
        layout.addWidget(self.label_total, 0, 0, 1, 2)
        layout.addWidget(self.label_recebido, 1, 0)
        layout.addWidget(self.input_recebido, 1, 1)
        layout.addWidget(self.label_troco, 2, 0, 1, 2)
        layout.addWidget(self.btn_confirmar, 3, 0)

        layout.setSpacing(0)
        self.setLayout(layout)

    def sinal_de_botao(self):
        self.btn_confirmar.clicked.connect(self.accept)
        self.input_recebido.textChanged.connect(self.atualizar_troco)
    
    def atualizar_troco(self):
        input = self.input_recebido.text()
        input = re.sub(r'[^\d.]', '', input)
        input = re.sub(r'\.+', '.', input)
        input = re.sub(r'\.(?=.*\.)', '', input)
        
        self.input_recebido.setText(input)
        valor_recebido = self.input_recebido.text()

        if valor_recebido:
            valor_recebido = float(valor_recebido)
            troco = -abs(self._total_da_compra) + valor_recebido
            
            self.label_troco.clear()
            self.label_troco.setText(f"Troco {ConverterValorParaReal(troco).valorFormatadoComCifrao()}")

        if not valor_recebido:
            self.label_troco.setText("Troco R$ 0")

    def compra_finalizada(self):
        try: 
            valor_recebido = float(self.input_recebido.text().replace(',', '.'))
            troco =  -abs(self._total_da_compra) + valor_recebido
            compra = ConverterValorParaReal(self._total_da_compra).valorFormatadoComCifrao()

            return {"total_da_compra": compra, "valor_recebido": ConverterValorParaReal(valor_recebido).valorFormatadoComCifrao(), "troco": troco}
        
        except:
            Mensagem('Dígite o valor recebido!')
            return False
        
class GerarNotinha:
    def __init__(self, tabela, pagamento):
        try:
            numero_nfc = random.randint(1, 999999999)
            local_salvar = f'C:/Users/{os.getlogin()}/Downloads/'
            data_e_hora = datetime.now().strftime('%d/%m/%Y %H:%M')
            elements = []
            style = ParagraphStyle('heading1',
                                fontName = 'Helvetica',
                                fontSize = 9,
                                textColor = colors.black,
                                leading = 10,
                                alignment=TA_CENTER)
            
            header = Paragraph(f'''
                <b>Consumidor não identificado</b><br/>
                <b>NFC-e Nº {numero_nfc}</b> {data_e_hora} <br />
                CNPJ: 00.000.000/0000-00  <b> - SuperMercados CoinMaster</b> <br />
                Avenida ficticia, 000, São José dos campos - SP <br />
                Documento fictício para fins de estudo
                ''', style)

            paragraph_pagamento = Paragraph(f'''
                <b>Formar de pagamento</b> DINHEIRO<br/>
                <b>Total da compra</b> {pagamento['total_da_compra']}<br/>
                <b>Valor pago</b> {pagamento['valor_recebido']}<br/>
                <b>Troco</b> {ConverterValorParaReal(pagamento['troco']).valorFormatadoComCifrao()}
                ''', style)

            tabela=Table(tabela)
            tabela.setStyle(TableStyle([
                                ('LINEABOVE',(0,1),(-1,1),1,colors.black),
                                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                                ('TEXTCOLOR',(0,0),(1,-1), colors.black)]))

            elements.append(header)
            elements.append(Spacer(1,0.2*100))
            elements.append(tabela)
            elements.append(Spacer(1,0.2*200))
            elements.append(paragraph_pagamento)

            pdf = SimpleDocTemplate(f'{local_salvar}NFCe#{numero_nfc}.pdf', pagesize=A4)
            pdf.build(elements)

            Mensagem(f'Notinha salva em {local_salvar}')

            try:
                subprocess.run(["start", f'{local_salvar}NFCe#{numero_nfc}.pdf'], shell=True)
                
            except Exception as e:
                print(f"Erro ao abrir o arquivo PDF: {e}")

        except Exception as erro:
            Mensagem(str(erro))

if __name__ == "__main__":
    window = JanelaPrincial()
    window.show()
    app.exec()