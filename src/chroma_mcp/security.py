"""
Security and encryption module for sensitive data.
Provides selective encryption based on algorithmic sensing.
"""
from typing import Dict, List, Optional, Any
import re
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
import os


class SensitiveDataDetector:
    """Detects sensitive information in text using pattern matching."""
    
    # Common patterns for sensitive data
    PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
        "api_key": r'(?i)(api[_-]?key|apikey|access[_-]?token)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]+)',
        "password": r'(?i)(password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^\s"\']+)',
        "private_key": r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----',
        "ip_address": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    }
    
    # Sensitivity scores
    SENSITIVITY_SCORES = {
        "email": 0.3,
        "phone": 0.5,
        "ssn": 1.0,
        "credit_card": 1.0,
        "api_key": 0.9,
        "password": 0.95,
        "private_key": 1.0,
        "ip_address": 0.2
    }
    
    def detect(self, text: str) -> Dict[str, Any]:
        """
        Detect sensitive information in text.
        
        Args:
            text: Text to analyze
        
        Returns:
            Dictionary with detection results and sensitivity score
        """
        detections = {}
        max_score = 0.0
        
        for pattern_name, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                detections[pattern_name] = len(matches)
                score = self.SENSITIVITY_SCORES.get(pattern_name, 0.5)
                max_score = max(max_score, score)
        
        return {
            "has_sensitive_data": bool(detections),
            "detections": detections,
            "sensitivity_score": max_score,
            "should_encrypt": max_score >= 0.5
        }


class EncryptionManager:
    """Manages encryption and decryption of sensitive data."""
    
    def __init__(self, password: Optional[str] = None):
        self.password = password or os.getenv('ENCRYPTION_PASSWORD', 'default-password-change-me')
        self._cipher = None
        self._detector = SensitiveDataDetector()
    
    def _get_cipher(self) -> Fernet:
        """Get or create cipher instance."""
        if self._cipher is None:
            # Derive key from password
            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'chroma-mcp-salt',  # In production, use a random salt
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.password.encode()))
            self._cipher = Fernet(key)
        return self._cipher
    
    def encrypt(self, data: str) -> str:
        """Encrypt data."""
        cipher = self._get_cipher()
        encrypted = cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data."""
        cipher = self._get_cipher()
        decoded = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = cipher.decrypt(decoded)
        return decrypted.decode()
    
    def selective_encrypt(
        self,
        data: str,
        metadata: Optional[Dict] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Selectively encrypt data based on sensitive information detection.
        
        Args:
            data: Data to potentially encrypt
            metadata: Optional metadata
            project_id: Optional project ID
        
        Returns:
            Dictionary with encrypted data and metadata
        """
        # Detect sensitive information
        detection_result = self._detector.detect(data)
        
        result = {
            "data": data,
            "encrypted": False,
            "detection": detection_result,
            "metadata": metadata or {}
        }
        
        # Encrypt if sensitive data detected
        if detection_result["should_encrypt"]:
            result["data"] = self.encrypt(data)
            result["encrypted"] = True
            result["metadata"]["_encrypted"] = True
            result["metadata"]["_sensitivity_score"] = detection_result["sensitivity_score"]
        
        if project_id:
            result["metadata"]["_project_id"] = project_id
        
        return result
    
    def batch_selective_encrypt(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict]] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Selectively encrypt a batch of documents.
        
        Args:
            documents: List of documents
            metadatas: Optional list of metadata dicts
            project_id: Optional project ID
        
        Returns:
            Dictionary with processed documents and metadata
        """
        processed_docs = []
        processed_metas = []
        encryption_stats = {
            "total": len(documents),
            "encrypted": 0,
            "detections": {}
        }
        
        for i, doc in enumerate(documents):
            meta = metadatas[i] if metadatas and i < len(metadatas) else {}
            result = self.selective_encrypt(doc, meta, project_id)
            
            processed_docs.append(result["data"])
            processed_metas.append(result["metadata"])
            
            if result["encrypted"]:
                encryption_stats["encrypted"] += 1
            
            # Aggregate detections
            for det_type, count in result["detection"]["detections"].items():
                encryption_stats["detections"][det_type] = \
                    encryption_stats["detections"].get(det_type, 0) + count
        
        return {
            "documents": processed_docs,
            "metadatas": processed_metas,
            "stats": encryption_stats
        }


# Global encryption manager instance
_encryption_manager = None

def get_encryption_manager() -> EncryptionManager:
    """Get or create the global encryption manager."""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager
