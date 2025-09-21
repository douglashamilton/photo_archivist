"""Acceptance tests for shortlist generation and scoring."""

import pytest
from datetime import datetime
from uuid import uuid4

from app.models.domain import Asset, Score, Shortlist
from app.shortlist.builder import ShortlistBuilder

pytestmark = pytest.mark.asyncio

async def test_shortlist_capped_to_n_with_rationales(
    test_db,
    test_user
):
    """
    Scenario: Shortlist capped to N with rationales
    Given a folder containing >200 images
    When scoring completes with shortlistSize=20
    Then the latest shortlist contains <=20 items each with finalScore and reasons
    """
    # Create 200+ test assets
    assets = []
    for i in range(250):
        asset = Asset(
            item_id=f"bulk_item_{i}",
            user_id=test_user.id,
            path=f"/Photos/bulk_photo_{i}.jpg",
            mime_type="image/jpeg",
            taken_at=datetime.utcnow(),
            width=1920,
            height=1080,
            last_seen=datetime.utcnow()
        )
        test_db.add(asset)
        assets.append(asset)

        # Add varying scores
        score = Score(
            asset_item_id=asset.item_id,
            sharpness=0.5 + (i * 0.002),  # Varying sharpness
            exposure=0.6 + (i * 0.001),   # Varying exposure
            final_score=0.55 + (i * 0.0015),
            rationale=["sharp", "well-exposed"] if i % 2 == 0 else ["sharp"]
        )
        test_db.add(score)
    
    test_db.commit()

    # Build shortlist with size limit
    builder = ShortlistBuilder(test_db)
    shortlist = await builder.build_shortlist(test_user.id, size=20)

    # Verify size cap and item properties
    assert len(shortlist.items) <= 20
    
    # Verify items are sorted by score and have rationales
    prev_score = 1.0
    for item in shortlist.items:
        score = test_db.query(Score).filter_by(asset_item_id=item.asset_item_id).first()
        assert score is not None
        assert score.final_score <= prev_score  # Descending order
        assert len(score.rationale) > 0  # Has reasons
        prev_score = score.final_score

async def test_top_photos_selected_by_default(
    test_db,
    test_user,
    test_assets,
    test_scores
):
    """
    Scenario: Top scored photos pre-selected
    Given a new shortlist build
    When the build completes
    Then the top N photos are pre-selected
    """
    # Build shortlist with default selection
    builder = ShortlistBuilder(test_db)
    shortlist = await builder.build_shortlist(test_user.id, size=3)

    # Verify top 3 are selected
    selected_items = [item for item in shortlist.items if item.selected]
    assert len(selected_items) == 3

    # Verify they are the highest scored
    for i, item in enumerate(selected_items):
        score = test_db.query(Score).filter_by(asset_item_id=item.asset_item_id).first()
        assert score.final_score >= 0.75 + (i * 0.05)  # Based on test_scores fixture

async def test_shortlist_regeneration_preserves_selections(
    test_db,
    test_user,
    test_shortlist
):
    """
    Scenario: Shortlist regeneration preserves selections
    Given an existing shortlist with selections
    When the shortlist is regenerated
    Then user selections are preserved
    """
    # Get initial selections
    initial_selections = {
        item.asset_item_id: item.selected 
        for item in test_shortlist.items
    }

    # Regenerate shortlist
    builder = ShortlistBuilder(test_db)
    new_shortlist = await builder.build_shortlist(
        test_user.id,
        size=20,
        preserve_shortlist_id=test_shortlist.id
    )

    # Verify selections preserved
    for item in new_shortlist.items:
        if item.asset_item_id in initial_selections:
            assert item.selected == initial_selections[item.asset_item_id]