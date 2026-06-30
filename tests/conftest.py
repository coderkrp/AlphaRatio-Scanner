import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Base

@pytest.fixture
def db_session():
    """Provides a fresh in-memory SQLite database session for each test."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

from src.config.models import FullConfig

@pytest.fixture
def sample_config():
    """Provides a safe mocked configuration object."""
    return FullConfig(
        telegram={'token': 'test_token', 'chat_id': ['123']},
        database={'url': 'sqlite:///:memory:'},
        benchmarks=[{'ticker': '^NSEI', 'name': 'Nifty 50'}],
        symbols=[{'ticker': 'RELIANCE.NS', 'name': 'Reliance', 'sector': 'Energy', 'benchmarks': ['^NSEI']}]
    )
