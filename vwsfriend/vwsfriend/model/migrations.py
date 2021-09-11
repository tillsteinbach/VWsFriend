from alembic.command import upgrade, stamp
from alembic.config import Config
import os


def run_database_migrations(dsn: str, stampOnly: bool = False):
    # retrieves the directory that *this* file is in
    migrations_dir = os.path.dirname(os.path.realpath(__file__))
    # this assumes the alembic.ini is also contained in this same directory
    config_file = os.path.join(migrations_dir, "alembic.ini")

    config = Config(file_=config_file)
    config.attributes['configure_logger'] = False
    config.set_main_option("script_location", migrations_dir + '/vwsfriend-schema')
    config.set_main_option('sqlalchemy.url', dsn)

    if stampOnly:
        stamp(config, "head")
    else:
        # upgrade the database to the latest revision
        upgrade(config, "head")
