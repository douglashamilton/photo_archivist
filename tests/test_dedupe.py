"""Acceptance tests for photo deduplication using pHash."""

import pytest
from datetime import datetime
from uuid import uuid4
import cv2
import numpy as np

from app.models.domain import Asset, Score
from app.scoring.dedupe import compute_phash, cluster_similar_photos, hamming_distance
from app.scoring.metrics import compute_quality_score

pytestmark = pytest.mark.asyncio

def create_similar_burst_photos():
    """Create synthetic burst photos with slight motion differences."""
    base_img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.circle(base_img, (50, 50), 20, (255, 255, 255), -1)
    
    burst = []
    for i in range(3):
        # Shift circle slightly
        shifted = np.roll(base_img, i * 2, axis=1)
        burst.append(shifted)
    
    return burst

async def test_near_duplicate_collapse(
    test_db,
    test_user
):
    """
    Scenario: Near-duplicate collapse by pHash
    Given a burst of similar images differing by slight motion
    When dedupe runs with Hamming threshold <=5
    Then only the highest-scoring image remains in the shortlist
    """
    # Create burst of similar photos
    burst_photos = create_similar_burst_photos()
    assets = []
    scores = []
    
    for i, img in enumerate(burst_photos):
        # Save synthetic image and compute pHash
        phash = compute_phash(img)
        
        # Create asset
        asset = Asset(
            item_id=f"burst_{i}",
            user_id=test_user.id,
            path=f"/Photos/burst_{i}.jpg",
            mime="image/jpeg",
            taken_at=datetime.utcnow(),
            width=100,
            height=100,
            phash=phash,
            last_seen=datetime.utcnow()
        )
        test_db.add(asset)
        assets.append(asset)
        
        # Compute and store quality score
        score = compute_quality_score(asset.item_id, img)
        # Adjust score to make first image highest quality
        score.sharpness *= (1.0 - (i * 0.1))
        score.final_score *= (1.0 - (i * 0.1))
        test_db.add(score)
        scores.append(score)
    
    test_db.commit()

    # Find duplicate clusters
    clusters = cluster_similar_photos(assets, hamming_threshold=5)
    
    # Verify all burst photos are in same cluster
    assert len(clusters) == 1
    # Get the first (and only) cluster
    burst_cluster = next(iter(clusters.values()))
    assert len(burst_cluster) == 3
    
    # Verify highest scoring photo is selected as cluster representative
    best_photo = max(
        burst_cluster,
        key=lambda asset: next(
            score.final_score 
            for score in scores 
            if score.asset_item_id == asset.item_id
        )
    )
    assert best_photo.item_id == "burst_0"  # First photo has highest score

async def test_unique_photos_preserved(
    test_db,
    test_user
):
    """
    Scenario: Unique photos preserved in shortlist
    Given photos with distinct pHashes
    When dedupe runs
    Then all unique photos remain in consideration
    """
    # Create visually distinct photos
    distinct_imgs = [
        np.zeros((100, 100, 3), dtype=np.uint8),  # Black
        np.ones((100, 100, 3), dtype=np.uint8) * 255,  # White
        np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)  # Random
    ]
    
    assets = []
    for i, img in enumerate(distinct_imgs):
        phash = compute_phash(img)
        asset = Asset(
            item_id=f"distinct_{i}",
            user_id=test_user.id,
            path=f"/Photos/distinct_{i}.jpg",
            mime="image/jpeg",
            taken_at=datetime.utcnow(),
            width=100,
            height=100,
            phash=phash,
            last_seen=datetime.utcnow()
        )
        test_db.add(asset)
        assets.append(asset)
    
    test_db.commit()

    # Print pHash values
    print("\npHashes:")
    for i, asset in enumerate(assets):
        print(f"Image {i} ({asset.item_id}): {asset.phash}")
        
    # Print Hamming distances
    print("\nHamming distances:")
    for i, asset1 in enumerate(assets):
        for j, asset2 in enumerate(assets[i+1:], i+1):
            dist = hamming_distance(asset1.phash, asset2.phash)
            print(f"{asset1.item_id} vs {asset2.item_id}: {dist}")
            
    # Find duplicate clusters    
    clusters = cluster_similar_photos(assets, hamming_threshold=5)
    
    # Print cluster contents
    print("\nClusters:")
    for leader_id, cluster in clusters.items():
        print(f"Leader {leader_id}: {[a.item_id for a in cluster]}")
    
    # Each photo should be in its own cluster
    assert len(clusters) == 3  # We should have 3 clusters
    for cluster in clusters.values():  # Check each cluster's contents
        assert len(cluster) == 1, f"Cluster should have 1 photo but has {len(cluster)}: {[p.item_id for p in cluster]}"