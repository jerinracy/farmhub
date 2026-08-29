from datetime import date
import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db import get_db
from app.main import app
from app.models import Base, Cow, Farm, FarmerProfile, MilkProduction, User

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def create_token(user_id: int, username: str, role: str) -> str:
    payload = {
        "id": user_id,
        "username": username,
        "role": role,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


@pytest.fixture(autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        superadmin = User(id=1, username="admin", email="admin@farmhub.com", role="SUPERADMIN", is_active=True)
        agent_1 = User(id=2, username="agent1", email="agent1@farmhub.com", role="AGENT", is_active=True)
        agent_2 = User(id=3, username="agent2", email="agent2@farmhub.com", role="AGENT", is_active=True)
        farmer_1 = User(id=4, username="farmer1", email="farmer1@farmhub.com", role="FARMER", is_active=True)
        farmer_2 = User(id=5, username="farmer2", email="farmer2@farmhub.com", role="FARMER", is_active=True)

        session.add_all([superadmin, agent_1, agent_2, farmer_1, farmer_2])
        await session.commit()

        farm_1 = Farm(id=1, name="Green Valley Farm", agent_id=2, is_active=True)
        farm_2 = Farm(id=2, name="Sunrise Dairy Farm", agent_id=3, is_active=True)

        session.add_all([farm_1, farm_2])
        await session.commit()

        prof_1 = FarmerProfile(id=1, user_id=4, farm_id=1)
        prof_2 = FarmerProfile(id=2, user_id=5, farm_id=2)

        session.add_all([prof_1, prof_2])
        await session.commit()

        cow_1 = Cow(id=1, tag_id="COW-101", farm_id=1, farmer_id=4, breed="Holstein", is_active=True)
        cow_2 = Cow(id=2, tag_id="COW-202", farm_id=2, farmer_id=5, breed="Jersey", is_active=True)

        session.add_all([cow_1, cow_2])
        await session.commit()

        m1 = MilkProduction(id=1, cow_id=1, farm_id=1, farmer_id=4, date=date(2026, 8, 10), quantity_liters=10.0, session="MORNING")
        m2 = MilkProduction(id=2, cow_id=1, farm_id=1, farmer_id=4, date=date(2026, 8, 20), quantity_liters=15.0, session="EVENING")
        m3 = MilkProduction(id=3, cow_id=2, farm_id=2, farmer_id=5, date=date(2026, 8, 20), quantity_liters=20.0, session="MORNING")

        session.add_all([m1, m2, m3])
        await session.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_superadmin_summary_report():
    token = create_token(user_id=1, username="admin", role="SUPERADMIN")
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/reports/summary", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["total_liters"] == 45.0
        assert data["record_count"] == 3
        assert len(data["per_farm"]) == 2
        assert data["per_farm"][0]["farm_name"] == "Green Valley Farm"
        assert data["per_farm"][0]["total_liters"] == 25.0


@pytest.mark.asyncio
async def test_agent_farm_report_own_and_other():
    token = create_token(user_id=2, username="agent1", role="AGENT")
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/reports/farm/1", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["farm"]["name"] == "Green Valley Farm"
        assert data["total_liters"] == 25.0
        assert len(data["per_cow"]) == 1
        assert data["per_cow"][0]["tag_id"] == "COW-101"

        res_other = await client.get("/api/v1/reports/farm/2", headers=headers)
        assert res_other.status_code == 404


@pytest.mark.asyncio
async def test_farmer_report_own_and_other():
    token = create_token(user_id=4, username="farmer1", role="FARMER")
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/reports/farmer/4", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["farmer"]["username"] == "farmer1"
        assert data["total_liters"] == 25.0

        res_other = await client.get("/api/v1/reports/farmer/5", headers=headers)
        assert res_other.status_code == 404


@pytest.mark.asyncio
async def test_invalid_jwt():
    headers = {"Authorization": "Bearer invalid_token_string"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/reports/summary", headers=headers)
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_date_range_filtering():
    token = create_token(user_id=1, username="admin", role="SUPERADMIN")
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/reports/summary?date_from=2026-08-15&date_to=2026-08-25",
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total_liters"] == 35.0
        assert data["record_count"] == 2
