"""Acceptance tests for     order = PrintOrder(
        id=uuid4(),
        shortlist_id=test_shortlist.id,
        provider=PrintProvider.KITE,
        mode=PrintMode.TEST,
        sku=PrintSku.PHOTO_4X6,
        items=[
            PrintOrderItem(asset_item_id=item.asset_item_id, qty=1)
            for item in test_shortlist.items
            if item.selected
        ],
        status=PrintOrderStatus.QUEUEDcreation via Kite API."""

import pytest
from datetime import datetime
from uuid import uuid4

from app.models.domain import PrintOrder, PrintProvider, PrintMode, PrintSku, PrintOrderStatus, PrintOrderItem
from app.print.kite_client import KiteClient

pytestmark = pytest.mark.asyncio

async def test_print_test_order_created(
    test_db,
    test_shortlist,
    mock_kite_client
):
    """
    Scenario: Print test order created
    Given an approved shortlist and Kite test keys
    When the user clicks "Print (Test)"
    Then an order is created with providerOrderId and status queued
    """
    # Create test order
    kite = mock_kite_client.return_value  # Use the mock
    order = PrintOrder(
        id=uuid4(),
        shortlist_id=test_shortlist.id,
        provider=PrintProvider.KITE,
        mode=PrintMode.TEST,
        sku=PrintSku.PHOTO_4X6,
        items=[
            PrintOrderItem(asset_item_id=item.asset_item_id, qty=1)
            for item in test_shortlist.items
            if item.selected
        ],
        status=PrintOrderStatus.QUEUED
    )
    test_db.add(order)
    test_db.commit()

    # Submit to Kite with db session
    result = await kite.create_order(order, db=test_db)

    # Verify order creation
    assert result["order_id"] == "ko_test_123"
    assert result["status"] == "submitted"

    # Commit the changes and refresh order from db
    test_db.commit()
    test_db.refresh(order)

    # Verify order status in DB
    assert order.provider_order_id == "ko_test_123"
    assert order.status == PrintOrderStatus.SUBMITTED
    assert order.status == PrintOrderStatus.SUBMITTED

async def test_print_order_validates_selection(
    test_db,
    test_shortlist
):
    """
    Scenario: Print order requires selected photos
    Given a shortlist with no selected photos
    When attempting to create print order
    Then order creation is rejected
    """
    # Clear all selections
    for item in test_shortlist.items:
        item.selected = False
    test_db.commit()

    # Attempt order creation
    with pytest.raises(ValueError) as exc:
        order = PrintOrder(
            id=uuid4(),
            shortlist_id=test_shortlist.id,
            provider=PrintProvider.KITE,
            mode=PrintMode.TEST,
            sku=PrintSku.PHOTO_4X6,
            items=[],  # No selected items
            status=PrintOrderStatus.QUEUED
        )
        test_db.add(order)
        test_db.commit()
    
    assert "No photos selected for printing" in str(exc.value)

async def test_print_order_enforces_test_mode(
    test_db,
    test_shortlist
):
    """
    Scenario: Print order enforces test mode
    Given a print order attempt
    When mode is not 'test'
    Then order creation is rejected
    """
    with pytest.raises(ValueError) as exc:
        order = PrintOrder(
            id=uuid4(),
            shortlist_id=test_shortlist.id,
            provider=PrintProvider.KITE,
            mode=PrintMode.LIVE,  # Not allowed in MVP
            sku=PrintSku.PHOTO_4X6,
            items=[
                PrintOrderItem(asset_item_id=item.asset_item_id, qty=1)
                for item in test_shortlist.items
                if item.selected
            ],
            status=PrintOrderStatus.QUEUED
        )
        test_db.add(order)
        test_db.commit()
    
    assert "Only test mode orders are supported" in str(exc.value)