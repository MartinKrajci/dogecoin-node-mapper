from base import engine, base
from node import Node

base.metadata.drop_all(engine)
base.metadata.create_all(engine)