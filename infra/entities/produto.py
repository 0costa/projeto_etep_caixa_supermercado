from infra.config.base import Base

from sqlalchemy import Column, String, Integer, Float

class Produto(Base):
    __tablename__ = "produto"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    descricao = Column(String, nullable=False)
    valor = Column(Float, nullable=False)

    def __init__(self, id, descricao, valor):
        self.id = id
        self.descricao = descricao
        self.valor = valor