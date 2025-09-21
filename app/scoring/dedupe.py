"""Photo deduplication using perceptual hashing."""
from typing import List, Set, Dict
import imagehash
from PIL import Image
from ..models.domain import Asset, Score


def compute_phash(image, hash_size: int = 8) -> str:
    """
    Generate perceptual hash for deduplication.
    
    Args:
        image: Image data (PIL Image or numpy array)
        hash_size: Size of the hash (default 8, producing 64-bit hash)
            Smaller hash size is more tolerant of small changes
        
    Returns:
        str: Hex string representation of pHash
    """
    # Convert to PIL Image if needed
    if not isinstance(image, Image.Image):
        image = Image.fromarray(image)
        
    # Convert to grayscale and downscale for hash computation
    prep_image = image.convert('L').resize((hash_size * 4, hash_size * 4), 
                                         Image.Resampling.LANCZOS)
        
    # Use perceptual hash for better feature discrimination
    phash = imagehash.phash(prep_image, hash_size=hash_size)
    
    # Convert hash to hex string
    return str(phash)


def hamming_distance(hash1: str, hash2: str) -> int:
    """
    Calculate Hamming distance between two hashes with special handling for edge cases.
    
    Args:
        hash1: First hash string
        hash2: Second hash string
        
    Returns:
        int: Number of different bits with extra distance added for edge cases
    """
    if not hash1 or not hash2:
        return 64  # Maximum possible Hamming distance for 64-bit hash
        
    # Handle special cases - all zeros or all ones
    if hash1 == '0' * 16 and hash2 == '0' * 16:
        return 0  # Identical black images
    elif hash1 == 'f' * 16 and hash2 == 'f' * 16:
        return 0  # Identical white images
    elif (hash1 == '0' * 16 or hash2 == '0' * 16 or 
          hash1 == 'f' * 16 or hash2 == 'f' * 16):
        return 64  # Don't match edge cases with normal images
    
    # Handle normal cases
    # Convert hex strings to binary
    bin1 = bin(int(hash1, 16))[2:].zfill(64)
    bin2 = bin(int(hash2, 16))[2:].zfill(64)
    
    # Count differing bits
    diff = sum(b1 != b2 for b1, b2 in zip(bin1, bin2))
    return diff


async def find_duplicates(photos: List[Asset], threshold: int = 5) -> Dict[str, Set[Asset]]:
    """
    Group photos by similarity using hash distance.
    
    Args:
        photos: List of photo assets with pHash values
        threshold: Maximum Hamming distance for similar images
        
    Returns:
        Dict mapping representative photo ID to set of its duplicates
    """
    groups: Dict[str, Set[Asset]] = {}
    processed = set()
    
    for photo in photos:
        if photo.item_id in processed or not photo.phash:
            continue
            
        # Start new group with this photo as representative
        group = {photo}
        processed.add(photo.item_id)
        
        # Find similar photos
        for other in photos:
            if (other.item_id not in processed and 
                other.phash and 
                hamming_distance(photo.phash, other.phash) <= threshold):
                group.add(other)
                processed.add(other.item_id)
        
        if len(group) > 1:  # Only store if duplicates found
            groups[photo.item_id] = group
    
    return groups


async def select_best_from_group(photos: Set[Asset], scores: Dict[str, Score]) -> Asset:
    """
    Select highest quality photo from duplicate group.
    
    Args:
        photos: Set of similar photos
        scores: Dict mapping photo ID to quality score
        
    Returns:
        Asset: Photo with highest quality score
    """
    return max(
        photos,
        key=lambda p: scores.get(p.item_id, Score(
            asset_item_id=p.item_id,
            sharpness=0.0,
            exposure=0.0,
            final_score=0.0,
            rationale=["no-score"]
        )).final_score
    )


def cluster_similar_photos(photos: List[Asset], hamming_threshold: int = 5) -> Dict[str, List[Asset]]:
    """
    Group photos into clusters based on perceptual hash similarity.
    
    This function analyzes a list of photos and groups them into clusters where each cluster
    contains visually similar images based on their perceptual hash values. Photos within
    a cluster have Hamming distances less than or equal to the specified threshold.
    
    Args:
        photos: List of photo assets, each with a pHash value
        hamming_threshold: Maximum Hamming distance for photos to be considered similar
            Default is 5, which allows for small variations while preventing false matches
            
    Returns:
        Dict mapping representative photo ID to list of similar photos
    """
    # Group similar photos
    groups: Dict[str, List[Asset]] = {}
    processed_ids = set()
    
    # Find duplicate groups
    for i, photo in enumerate(photos):
        if photo.item_id in processed_ids or not photo.phash:
            continue
            
        # Start new group with this photo
        current_group = [photo]
        processed_ids.add(photo.item_id)
        
        # Find similar photos
        for other in photos[i+1:]:  # Only look at remaining photos
            if (other.item_id not in processed_ids and 
                other.phash and 
                hamming_distance(photo.phash, other.phash) <= hamming_threshold):
                current_group.append(other)
                processed_ids.add(other.item_id)
        
        # Store all clusters, including single-photo ones
        groups[photo.item_id] = current_group
            
    return groups