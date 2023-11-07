# Caixa de Supermercado Desktop
Este é um projeto de aplicativo de caixa de supermercado desenvolvido em Python como projeto multidisciplinar engenharia de software na universidade Etep-sjc. O aplicativo permite que os usuários simulem simples carinho de compras em um supermercado fictício, calcular o total da compra e gerar recibos para os clientes.

# Funcionalidades
- Adicionar e remover produtos do carrinho de compras.
- Cadastrar produto no estoque caso o código não exista.
- Calcular o total da compra com base nos produtos no carrinho.
- Gerar um recibo para a compra.

# Requisitos
 - Windows 10+
 - Python 3.x instalado no sistema.
 - Criar ambiente virtual e ativa-lo:
   ```
     python -m venv .venv
     source .venv/scripts/activate
   ```
 - intalar a bibliotecas necessárias:
   ```
     pip install -r requirements.txt
   ```

# Como Executar o Aplicativo
 - Gerar executavel com auto-py-to-exe atraves do terminal e após preencher os campos no auto-py-to-exe:
   ```terminal
     auto-py-to-exe
   ```
- Copiar o arquivo database.db para dentro do diretorio criado pelo auto-py-to-exe.
- Executar o app.exe dentro do diretorio criado pelo auto-py-to-exe.
