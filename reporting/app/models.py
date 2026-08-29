from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "accounts_user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    email = Column(String)
    role = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)


class Farm(Base):
    __tablename__ = "farms_farm"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    agent_id = Column(Integer, ForeignKey("accounts_user.id"), nullable=True)
    is_active = Column(Boolean, default=True)


class FarmerProfile(Base):
    __tablename__ = "farmers_farmerprofile"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"), nullable=False)
    farm_id = Column(Integer, ForeignKey("farms_farm.id"), nullable=False)


class Cow(Base):
    __tablename__ = "cattle_cow"

    id = Column(Integer, primary_key=True, index=True)
    tag_id = Column(String, nullable=False)
    farm_id = Column(Integer, ForeignKey("farms_farm.id"), nullable=False)
    farmer_id = Column(Integer, ForeignKey("accounts_user.id"), nullable=False)
    breed = Column(String)
    is_active = Column(Boolean, default=True)


class MilkProduction(Base):
    __tablename__ = "production_milkproduction"

    id = Column(Integer, primary_key=True, index=True)
    cow_id = Column(Integer, ForeignKey("cattle_cow.id"), nullable=False)
    farm_id = Column(Integer, ForeignKey("farms_farm.id"), nullable=False)
    farmer_id = Column(Integer, ForeignKey("accounts_user.id"), nullable=False)
    date = Column(Date, nullable=False)
    quantity_liters = Column(Numeric(6, 2), nullable=False)
    session = Column(String, nullable=False)
