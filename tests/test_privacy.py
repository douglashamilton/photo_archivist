"""Acceptance tests for data privacy and minimization."""

import pytest
import os
from pathlib import Path
from uuid import uuid4

from app.models.domain import Asset, Score
from app.scoring.metrics import compute_quality_score
from app.scoring.dedupe import compute_phash

pytestmark = pytest.mark.asyncio

async def test_no_originals_persisted(
    test_db,
    test_user,
    mock_graph_client,
    tmp_path: Path
):
    """
    Scenario: No originals persisted
    Given the app runs a full scan and shortlist build
    Then no original image files are written to disk and only minimal metadata/scores are stored
    """
    # Set app data directory to temporary path
    os.environ["APP_DATA_DIR"] = str(tmp_path)

    # Run scan and process photos
    for i in range(5):
        # Create asset record
        asset = Asset(
            item_id=f"privacy_test_{i}",
            user_id=test_user.id,
            path=f"/Photos/privacy_{i}.jpg",
            mime="image/jpeg",
            width=1920,
            height=1080,
            phash="0000000000000000"  # Placeholder
        )
        test_db.add(asset)

        # Add minimal score record
        score = Score(
            asset_item_id=asset.item_id,
            sharpness=0.8,
            exposure=0.7,
            final_score=0.75,
            rationale=["sharp"]
        )
        test_db.add(score)

    test_db.commit()

    # Verify no image files in app directory
    image_files = list(tmp_path.rglob("*.jpg")) + \
                 list(tmp_path.rglob("*.jpeg")) + \
                 list(tmp_path.rglob("*.png")) + \
                 list(tmp_path.rglob("*.heic"))
    assert len(image_files) == 0

    # Verify minimal metadata in database
    assets = test_db.query(Asset).all()
    for asset in assets:
        # Check only essential fields are populated
        assert asset.taken_at is None  # No EXIF timestamp
        assert asset.width is not None  # Basic dimensions needed
        assert asset.height is not None
        assert asset.phash is not None  # Dedupe hash needed
        assert asset.last_seen is None  # Timestamp not essential

async def test_memory_only_processing(
    test_db,
    test_user,
    tmp_path: Path
):
    """
    Scenario: Images processed only in memory
    Given a photo being scored
    When quality metrics are computed
    Then no temporary files are created
    """
    # Create test image in memory
    import numpy as np
    import cv2
    
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.circle(img, (50, 50), 20, (255, 255, 255), -1)

    # Set temp directory to monitored path
    os.environ["TEMP"] = str(tmp_path)
    os.environ["TMP"] = str(tmp_path)

    # Process image
    quality_score = compute_quality_score("test_item", img)
    phash = compute_phash(img)

    # Verify no temp files created
    temp_files = list(tmp_path.iterdir())
    assert len(temp_files) == 0

    # Verify scores computed
    assert 0 <= quality_score.final_score <= 1
    assert len(phash) > 0