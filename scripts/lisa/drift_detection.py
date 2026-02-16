import math

class HealthReport:
    def __init__(self, saturation, signal_ratio, drift_metric, status):
        self.saturation = saturation
        self.signal_ratio = signal_ratio
        self.drift_metric = drift_metric
        self.status = status

class DriftDetector:
    def __init__(self, token_count, limit):
        self.token_count = token_count
        self.limit = limit
        
    def check_health(self):
        # 1. Calculate Saturation
        if self.limit > 0:
            saturation = self.token_count / self.limit
        else:
            saturation = 0.0
            
        # 2. Estimate Signal Ratio
        # Heuristic: If saturation is low, signal ratio is likely high (less noise).
        # If saturation is high, signal ratio drops.
        signal_ratio = "High" if saturation < 0.7 else "Medium"
        if saturation > 0.9: signal_ratio = "Low"
        
        # 3. Drift Metric (Jaccard Distance Heuristic)
        # Without real embeddings, we assume "Drift" increases as we approach the limit
        # because the original "Goal" (at 0 tokens) is diluted by subsequent turns.
        # This is a proxy until we have embeddings.
        drift_metric = saturation * 0.5 # Proxy: more context = more drift potential
        
        # Determine Status
        status = "HEALTHY"
        if saturation > 0.9:
            status = "CRITICAL (Saturation)"
        elif saturation > 0.75:
            status = "WARNING (Saturation)"
        elif drift_metric > 0.4:
            status = "WARNING (Drift Risk)"
            
        return HealthReport(
            saturation=saturation,
            signal_ratio=signal_ratio,
            drift_metric=drift_metric,
            status=status
        )
