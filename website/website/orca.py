import sqlalchemy
from .views import app

engine = sqlalchemy.create_engine('postgresql://%s:%s@%s:%i/%s' %
                                 (app.config['DB_USER'], app.config['DB_PASS'],
                                  app.config['DB_HOST'], app.config['DB_PORT'],
                                  'orca'),
                                  pool_recycle=3600)

def get_orca_session_logs(limit=100, offset=0):
    """
    Returns a list of the latest orca sessions in the database.
    """
    conn = engine.connect()

    result = conn.execute("SELECT * FROM orca_sessions ORDER BY timestamp DESC LIMIT %s OFFSET %s", (limit,offset))

    if result is None:
        return None

    keys = result.keys()
    rows = result.fetchall()

    return [dict(zip(keys,row)) for row in rows]
