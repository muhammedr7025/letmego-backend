from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Request, Query

from apps.api.admin.schema import (
    UserWithCountsSchema,
    VehicleReportSchema,
    VehicleSearchLogResponse,
    VehicleWithCountsSchema,
    UserSchema,
    UserRoleUpdate,
    SlotStatusUpdate,
)
from apps.api.admin.service import AdminDashboardServiceDependency
from apps.api.auth.dependency import AdminUserDependency
from apps.api.vehicle.models import SearchTermStatus
from avcfastapi.core.fastapi.response.pagination import (
    PaginatedResponse,
    PaginationParams,
    paginated_response,
)

router = APIRouter(prefix="/admin")


@router.get("/statistics", description="Get admin statistics")
async def get_statistics(
    user: AdminUserDependency,
    admin_dashboard_service: AdminDashboardServiceDependency,
    from_date: datetime | None = Query(
        None, description="Filter from this datetime (inclusive, timezone-aware)"
    ),
    to_date: datetime | None = Query(
        None, description="Filter to this datetime (inclusive, timezone-aware)"
    ),
):
    total_users = await admin_dashboard_service.get_users_count(from_date, to_date)
    total_vehicles = await admin_dashboard_service.get_vehicles_count(
        from_date, to_date
    )
    total_reports = await admin_dashboard_service.get_reports_count(from_date, to_date)
    success_total_search_terms = await admin_dashboard_service.count_search_logs(
        from_date=from_date, to_date=to_date, status=SearchTermStatus.SUCCESS
    )
    not_found_total_search_terms = await admin_dashboard_service.count_search_logs(
        from_date=from_date, to_date=to_date, status=SearchTermStatus.NOT_FOUND
    )

    return {
        "total_users": total_users,
        "total_vehicles": total_vehicles,
        "total_reports": total_reports,
        "total_search_terms": {
            "success": success_total_search_terms,
            "not_found": not_found_total_search_terms,
        },
    }


@router.get("/users", description="List users")
async def list_users(
    user: AdminUserDependency,
    request: Request,
    admin_dashboard_service: AdminDashboardServiceDependency,
    params: PaginationParams,
    from_date: datetime | None = Query(
        None, description="Filter from this datetime (inclusive, timezone-aware)"
    ),
    to_date: datetime | None = Query(
        None, description="Filter to this datetime (inclusive, timezone-aware)"
    ),
) -> PaginatedResponse[UserWithCountsSchema]:
    users = await admin_dashboard_service.list_users(
        offset=params.offset, limit=params.limit, from_date=from_date, to_date=to_date
    )
    return paginated_response(
        result=users, request=request, schema=UserWithCountsSchema
    )


@router.get("/vehicles", description="List vehicles")
async def list_vehicles(
    user: AdminUserDependency,
    request: Request,
    admin_dashboard_service: AdminDashboardServiceDependency,
    params: PaginationParams,
    user_id: str | None = None,
    from_date: datetime | None = Query(
        None, description="Filter from this datetime (inclusive, timezone-aware)"
    ),
    to_date: datetime | None = Query(
        None, description="Filter to this datetime (inclusive, timezone-aware)"
    ),
) -> PaginatedResponse[VehicleWithCountsSchema]:
    vehicles = await admin_dashboard_service.list_vehicles(
        user_id=user_id,
        offset=params.offset,
        limit=params.limit,
        from_date=from_date,
        to_date=to_date,
    )
    return paginated_response(
        result=vehicles, request=request, schema=VehicleWithCountsSchema
    )


@router.get("/reports", description="List reports")
async def list_reports(
    user: AdminUserDependency,
    request: Request,
    admin_dashboard_service: AdminDashboardServiceDependency,
    params: PaginationParams,
    vehicle_id: str | None = None,
    user_id: str | None = None,
    from_date: datetime | None = Query(
        None, description="Filter from this datetime (inclusive, timezone-aware)"
    ),
    to_date: datetime | None = Query(
        None, description="Filter to this datetime (inclusive, timezone-aware)"
    ),
) -> PaginatedResponse[VehicleReportSchema]:
    reports = await admin_dashboard_service.list_reports(
        vehicle_id=vehicle_id,
        user_id=user_id,
        offset=params.offset,
        limit=params.limit,
        from_date=from_date,
        to_date=to_date,
    )
    return paginated_response(
        result=reports, request=request, schema=VehicleReportSchema
    )


@router.get("/search-logs", description="List vehicle search logs")
async def list_search_logs(
    user: AdminUserDependency,
    request: Request,
    admin_dashboard_service: AdminDashboardServiceDependency,
    params: PaginationParams,
    status: SearchTermStatus | None = Query(None, description="Filter by status"),
    user_id: UUID | None = Query(None, description="Filter by user ID"),
    from_date: datetime | None = Query(
        None, description="Filter from this datetime (inclusive, timezone-aware)"
    ),
    to_date: datetime | None = Query(
        None, description="Filter to this datetime (inclusive, timezone-aware)"
    ),
) -> PaginatedResponse[VehicleSearchLogResponse]:
    search_logs = await admin_dashboard_service.get_search_logs(
        status=status,
        user_id=user_id,
        limit=params.limit,
        offset=params.offset,
        from_date=from_date,
        to_date=to_date,
    )
    return paginated_response(
        result=search_logs, request=request, schema=VehicleSearchLogResponse
    )


from apps.api.parking.schema import ParkingSlotResponse
from apps.api.parking.models import SlotStatus

@router.patch("/users/{user_id}/role", description="Change a user's role (Super Admin only)")
async def update_user_role(
    user_id: UUID,
    role_update: UserRoleUpdate,
    admin: AdminUserDependency,
    admin_dashboard_service: AdminDashboardServiceDependency,
) -> UserSchema:
    """
    Change the role of a user. (e.g. promote to admin or demote to user).
    Only accessible by Super Admins.
    """
    updated_user = await admin_dashboard_service.update_user_role(user_id, role_update.role)
    return UserSchema.model_validate(updated_user)


@router.get("/slots", description="List all parking slots (Super Admin only)")
async def list_all_slots(
    admin: AdminUserDependency,
    request: Request,
    admin_dashboard_service: AdminDashboardServiceDependency,
    params: PaginationParams,
    status: SlotStatus | None = Query(None, description="Filter by status"),
    from_date: datetime | None = Query(
        None, description="Filter from this datetime (inclusive, timezone-aware)"
    ),
    to_date: datetime | None = Query(
        None, description="Filter to this datetime (inclusive, timezone-aware)"
    ),
) -> PaginatedResponse[ParkingSlotResponse]:
    slots = await admin_dashboard_service.list_all_slots(
        offset=params.offset, limit=params.limit, status=status, from_date=from_date, to_date=to_date
    )
    return paginated_response(
        result=slots, request=request, schema=ParkingSlotResponse
    )


@router.patch("/slots/{slot_id}/status", description="Update a parking slot's status (Super Admin only)")
async def update_slot_status(
    slot_id: UUID,
    status_update: SlotStatusUpdate,
    admin: AdminUserDependency,
    admin_dashboard_service: AdminDashboardServiceDependency,
) -> ParkingSlotResponse:
    """
    Change the status of a parking slot (e.g., approve, reject, suspend).
    """
    updated_slot = await admin_dashboard_service.update_slot_status(
        slot_id, status_update.status, status_update.reason
    )
    return ParkingSlotResponse.model_validate(updated_slot)


@router.get("/analytics/timeseries", description="Get timeseries analytics data (Super Admin only)")
async def get_analytics_timeseries(
    admin: AdminUserDependency,
    admin_dashboard_service: AdminDashboardServiceDependency,
    months: int = Query(6, description="Number of months to retrieve history for"),
) -> dict:
    """
    Get monthly grouped statistics for charts (User Growth, Revenue, Sessions).
    """
    return await admin_dashboard_service.get_timeseries_analytics(months=months)
