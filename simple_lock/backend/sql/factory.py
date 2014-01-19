from . import actor
from . import models
from ..base_factory import FactoryBase

import sqlalchemy


__all__ = ['SqlActorFactory']


class SqlActorFactory(FactoryBase):
    def __init__(self, connection_string):
        self._engine = sqlalchemy.create_engine(connection_string)
        self._Session = sqlalchemy.orm.sessionmaker(bind=self._engine)

    def initialize(self):
        return models.Base.metadata.create_all(self._engine)

    def create_actor(self):
        return actor.SqlActor(self._Session())
