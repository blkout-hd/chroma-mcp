"""
UMAP integration for dimensionality reduction and visualization.
"""
from typing import List, Optional, Dict, Any
import numpy as np

try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False


class UMAPReducer:
    """Provides UMAP dimensionality reduction capabilities."""
    
    def __init__(
        self,
        n_components: int = 2,
        n_neighbors: int = 15,
        min_dist: float = 0.1,
        metric: str = 'cosine'
    ):
        if not UMAP_AVAILABLE:
            raise ImportError("UMAP not available. Install with: pip install umap-learn")
        
        self.n_components = n_components
        self.n_neighbors = n_neighbors
        self.min_dist = min_dist
        self.metric = metric
        self._reducer = None
    
    def fit_transform(self, embeddings: List[List[float]]) -> List[List[float]]:
        """
        Fit UMAP and transform embeddings.
        
        Args:
            embeddings: List of embedding vectors
        
        Returns:
            Reduced embeddings
        """
        embeddings_array = np.array(embeddings)
        
        self._reducer = umap.UMAP(
            n_components=self.n_components,
            n_neighbors=self.n_neighbors,
            min_dist=self.min_dist,
            metric=self.metric
        )
        
        reduced = self._reducer.fit_transform(embeddings_array)
        return reduced.tolist()
    
    def transform(self, embeddings: List[List[float]]) -> List[List[float]]:
        """
        Transform embeddings using fitted UMAP.
        
        Args:
            embeddings: List of embedding vectors
        
        Returns:
            Reduced embeddings
        """
        if self._reducer is None:
            raise ValueError("UMAP not fitted. Call fit_transform first.")
        
        embeddings_array = np.array(embeddings)
        reduced = self._reducer.transform(embeddings_array)
        return reduced.tolist()
    
    def visualize_embeddings(
        self,
        embeddings: List[List[float]],
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Reduce embeddings to 2D for visualization.
        
        Args:
            embeddings: List of embedding vectors
            labels: Optional labels for each embedding
        
        Returns:
            Dictionary with 2D coordinates and labels
        """
        # Force 2D for visualization
        original_components = self.n_components
        self.n_components = 2
        
        reduced = self.fit_transform(embeddings)
        
        # Restore original n_components
        self.n_components = original_components
        
        result = {
            "coordinates": reduced,
            "n_points": len(reduced)
        }
        
        if labels:
            result["labels"] = labels
        
        return result


# Global UMAP reducer instance
_umap_reducer = None

def get_umap_reducer() -> UMAPReducer:
    """Get or create the global UMAP reducer."""
    global _umap_reducer
    if _umap_reducer is None:
        _umap_reducer = UMAPReducer()
    return _umap_reducer
