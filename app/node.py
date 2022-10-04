from sqlalchemy.sql.expression import null
from base import session, base, engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import insert

class Node(base):
    __tablename__ = "node"

    ip = Column(String, primary_key=True)
    port = Column(Integer, primary_key=True)
    ip_version = Column(Integer)
    user_agent = Column(String)
    doge_version = Column(Integer)
    services = Column(String)
    unix_time = Column(Integer)

    def __init__(self, ip, port, ip_version, user_agent, doge_version, services, unix_time):
        self.ip = ip
        self.port = port
        self.ip_version = ip_version
        self.user_agent = user_agent
        self.doge_version = doge_version
        self.services = services
        self.unix_time = unix_time

    def update_time(ip, port, unix_time):
        session.query(Node).filter(Node.ip == ip and Node.port == port).update({"unix_time": unix_time})
        session.commit()
        return

    def upsert_node(ip, port, ip_version, user_agent, doge_version, services, unix_time):
        insert_stmt = insert(Node).values(
            ip = ip,
            port = port,
            ip_version = ip_version,
            user_agent = user_agent,
            doge_version = doge_version,
            services = services,
            unix_time = unix_time)

        do_update_stmt = insert_stmt.on_conflict_do_update(
            index_elements=['ip', 'port'],
            set_=dict(ip = ip, port = port, ip_version = ip_version, user_agent = user_agent,
             doge_version = doge_version, services = services, unix_time = unix_time))

        with engine.connect() as conn:
            conn.execute(do_update_stmt)

    def get_all_nodes():
            nodes = session.query(Node).filter(1 == 1).all()
            session.close()
            return nodes

    def node_exists(ip, port):
            node = session.query(Node).filter(Node.ip == ip and Node.port == port).first()
            if node:
                return True
            else:
                return False

"""     def add_node(ip, port, ip_version, user_agent, doge_version, services, unix_time):
        node = Node(ip, port, ip_version, user_agent, doge_version, services, unix_time)
        session.add(node)
        session.commit()
        session.close() """
