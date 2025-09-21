"""Print service API routes."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from ..models.domain import PrintOrder, PrintOrderStatus, PrintOrderItem, PrintMode
from ..models.repo import Repository
from ..deps import get_repository
from .kite_client import KiteClient


router = APIRouter()


@router.post("/submit")
async def submit_photo_print(
    shortlist_id: UUID,
    repo: Repository = Depends(get_repository)
) -> PrintOrder:
    """Submit photos from shortlist for printing."""
    # Get approved photos from shortlist
    shortlist = await repo.get_latest_shortlist(shortlist_id)
    if not shortlist:
        raise HTTPException(status_code=404, detail="Shortlist not found")

    selected_items = [item for item in shortlist.items if item.selected]
    if not selected_items:
        raise HTTPException(status_code=400, detail="No photos selected for printing")

    # Create print order
    order = await repo.create_print_order(PrintOrder(
        shortlist_id=shortlist_id,
        items=[
            PrintOrderItem(asset_item_id=item.asset_item_id, qty=1)
            for item in selected_items
        ],
        mode=PrintMode.LIVE
    ))
    
    raise NotImplementedError("Need to implement Kite client integration")


@router.get("/status/{order_id}")
async def check_print_status(
    order_id: UUID, 
    repo: Repository = Depends(get_repository)
) -> PrintOrderStatus:
    """Check print order status."""
    order = await repo.get_print_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Print order not found")
    return order.status


@router.post("/test")
async def submit_test_print(
    shortlist_id: UUID,
    repo: Repository = Depends(get_repository)
) -> PrintOrder:
    """Submit test print job."""
    # Get approved photos from shortlist
    shortlist = await repo.get_latest_shortlist(shortlist_id)
    if not shortlist:
        raise HTTPException(status_code=404, detail="Shortlist not found")

    selected_items = [item for item in shortlist.items if item.selected]
    if not selected_items:
        raise HTTPException(status_code=400, detail="No photos selected for printing")

    # Create test print order
    order = await repo.create_print_order(PrintOrder(
        shortlist_id=shortlist_id,
        items=[
            PrintOrderItem(asset_item_id=item.asset_item_id, qty=1)
            for item in selected_items
        ],
        mode=PrintMode.TEST
    ))
    
    raise NotImplementedError("Need to implement Kite client integration")


@router.get("/shipping-rates")
async def get_shipping_rates() -> dict:
    """Get available shipping rates."""
    raise NotImplementedError("Need to implement Kite shipping rates")