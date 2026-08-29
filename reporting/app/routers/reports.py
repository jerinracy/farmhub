from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, get_current_user
from app.db import get_db
from app.models import Cow, Farm, FarmerProfile, MilkProduction, User
from app.schemas import (
    FarmInfo,
    FarmerInfo,
    FarmerReportResponse,
    FarmReportResponse,
    PerCowBreakdown,
    PerFarmBreakdown,
    SummaryReportResponse,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/farm/{farm_id}", response_model=FarmReportResponse, summary="Get Farm Aggregated Report")
async def get_farm_report(
    farm_id: int,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Lookup farm
    farm_stmt = select(Farm).where(Farm.id == farm_id)
    farm_res = await db.execute(farm_stmt)
    farm = farm_res.scalar_one_or_none()

    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found or not accessible.",
        )

    # Permission check: SuperAdmin or managing Agent
    is_superadmin = current_user.role == "SUPERADMIN"
    is_agent = current_user.role == "AGENT" and farm.agent_id == current_user.id

    if not (is_superadmin or is_agent):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found or not accessible.",
        )

    # Aggregates
    stmt = select(
        func.coalesce(func.sum(MilkProduction.quantity_liters), 0),
        func.count(MilkProduction.id),
    ).where(MilkProduction.farm_id == farm_id)

    if date_from:
        stmt = stmt.where(MilkProduction.date >= date_from)
    if date_to:
        stmt = stmt.where(MilkProduction.date <= date_to)

    agg_res = await db.execute(stmt)
    total_liters, record_count = agg_res.one()

    # Per-cow breakdown
    cow_stmt = (
        select(
            Cow.tag_id,
            func.coalesce(func.sum(MilkProduction.quantity_liters), 0).label("total_liters"),
        )
        .join(Cow, MilkProduction.cow_id == Cow.id)
        .where(MilkProduction.farm_id == farm_id)
    )

    if date_from:
        cow_stmt = cow_stmt.where(MilkProduction.date >= date_from)
    if date_to:
        cow_stmt = cow_stmt.where(MilkProduction.date <= date_to)

    cow_stmt = cow_stmt.group_by(Cow.tag_id).order_by(desc("total_liters"))
    cow_res = await db.execute(cow_stmt)

    per_cow = [
        PerCowBreakdown(tag_id=tag_id, total_liters=float(tot))
        for tag_id, tot in cow_res.all()
    ]

    return FarmReportResponse(
        farm=FarmInfo(id=farm.id, name=farm.name),
        total_liters=float(total_liters),
        record_count=int(record_count),
        date_from=date_from,
        date_to=date_to,
        per_cow=per_cow,
    )


@router.get("/farmer/{farmer_id}", response_model=FarmerReportResponse, summary="Get Farmer Aggregated Report")
async def get_farmer_report(
    farmer_id: int,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Lookup farmer user
    user_stmt = select(User).where(User.id == farmer_id, User.role == "FARMER")
    user_res = await db.execute(user_stmt)
    farmer_user = user_res.scalar_one_or_none()

    if not farmer_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer not found or not accessible.",
        )

    # Lookup farmer profile and farm
    profile_stmt = (
        select(FarmerProfile, Farm)
        .outerjoin(Farm, FarmerProfile.farm_id == Farm.id)
        .where(FarmerProfile.user_id == farmer_id)
    )
    profile_res = await db.execute(profile_stmt)
    profile_tuple = profile_res.first()

    farm_name = profile_tuple[1].name if profile_tuple and profile_tuple[1] else None
    farm_agent_id = profile_tuple[1].agent_id if profile_tuple and profile_tuple[1] else None

    # Permission check: SuperAdmin, self, or managing Agent
    is_superadmin = current_user.role == "SUPERADMIN"
    is_self = current_user.id == farmer_id
    is_agent = current_user.role == "AGENT" and farm_agent_id == current_user.id

    if not (is_superadmin or is_self or is_agent):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer not found or not accessible.",
        )

    # Aggregates
    stmt = select(
        func.coalesce(func.sum(MilkProduction.quantity_liters), 0),
        func.count(MilkProduction.id),
    ).where(MilkProduction.farmer_id == farmer_id)

    if date_from:
        stmt = stmt.where(MilkProduction.date >= date_from)
    if date_to:
        stmt = stmt.where(MilkProduction.date <= date_to)

    agg_res = await db.execute(stmt)
    total_liters, record_count = agg_res.one()

    # Per-cow breakdown
    cow_stmt = (
        select(
            Cow.tag_id,
            func.coalesce(func.sum(MilkProduction.quantity_liters), 0).label("total_liters"),
        )
        .join(Cow, MilkProduction.cow_id == Cow.id)
        .where(MilkProduction.farmer_id == farmer_id)
    )

    if date_from:
        cow_stmt = cow_stmt.where(MilkProduction.date >= date_from)
    if date_to:
        cow_stmt = cow_stmt.where(MilkProduction.date <= date_to)

    cow_stmt = cow_stmt.group_by(Cow.tag_id).order_by(desc("total_liters"))
    cow_res = await db.execute(cow_stmt)

    per_cow = [
        PerCowBreakdown(tag_id=tag_id, total_liters=float(tot))
        for tag_id, tot in cow_res.all()
    ]

    return FarmerReportResponse(
        farmer=FarmerInfo(id=farmer_user.id, username=farmer_user.username),
        farm=farm_name,
        total_liters=float(total_liters),
        record_count=int(record_count),
        date_from=date_from,
        date_to=date_to,
        per_cow=per_cow,
    )


@router.get("/summary", response_model=SummaryReportResponse, summary="Get System-Wide Summary Report")
async def get_summary_report(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "SUPERADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted",
        )

    # Aggregates
    stmt = select(
        func.coalesce(func.sum(MilkProduction.quantity_liters), 0),
        func.count(MilkProduction.id),
    )

    if date_from:
        stmt = stmt.where(MilkProduction.date >= date_from)
    if date_to:
        stmt = stmt.where(MilkProduction.date <= date_to)

    agg_res = await db.execute(stmt)
    total_liters, record_count = agg_res.one()

    # Per-farm breakdown
    farm_stmt = (
        select(
            Farm.id.label("farm_id"),
            Farm.name.label("farm_name"),
            func.coalesce(func.sum(MilkProduction.quantity_liters), 0).label("total_liters"),
        )
        .join(Farm, MilkProduction.farm_id == Farm.id)
    )

    if date_from:
        farm_stmt = farm_stmt.where(MilkProduction.date >= date_from)
    if date_to:
        farm_stmt = farm_stmt.where(MilkProduction.date <= date_to)

    farm_stmt = farm_stmt.group_by(Farm.id, Farm.name).order_by(desc("total_liters"))
    farm_res = await db.execute(farm_stmt)

    per_farm = [
        PerFarmBreakdown(farm_id=fid, farm_name=fname, total_liters=float(tot))
        for fid, fname, tot in farm_res.all()
    ]

    return SummaryReportResponse(
        total_liters=float(total_liters),
        record_count=int(record_count),
        date_from=date_from,
        date_to=date_to,
        per_farm=per_farm,
    )
