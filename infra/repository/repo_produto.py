
from infra.config.connections import DBConnectionHandler
from infra.entities.produto import Produto

class ProdutoRepository:
    def inserir_produto(self, id:int, descricao:str, valor:float):
        with DBConnectionHandler() as db:
            try:
                data_isert = Produto(id=id, descricao=descricao, valor=valor)
                db.session.add(data_isert)
                db.session.commit()

            except Exception as exception:
                db.session.rollback()
                raise exception

    def add_produto(self, id):
        with DBConnectionHandler() as db:
            query = db.session\
                .query(Produto.id, Produto.descricao, Produto.valor)\
                .filter(Produto.id == id)\
                .all()

            return query
        
    def pesquisar_produto_por_codigo(self, codigo:int):
        with DBConnectionHandler() as db:
            query = db.session\
                .query(Produto.descricao, Produto.valor)\
                .filter(Produto.id == codigo)\
                .one()

            return query