from prometheus_client import Counter, Histogram, generate_latest, REGISTRY

# Counters
wol_requests_total = Counter(
    'wol_requests_total',
    'Total number of WoL requests',
    ['endpoint', 'status']
)
wol_success_total = Counter(
    'wol_success_total',
    'Total number of successful WoL packets sent',
    ['endpoint']
)
wol_failure_total = Counter(
    'wol_failure_total',
    'Total number of failed WoL attempts',
    ['endpoint']
)
wol_retries_total = Counter(
    'wol_retries_total',
    'Total number of WoL retry attempts',
    ['endpoint']
)

# Histograms
wol_duration_seconds = Histogram(
    'wol_duration_seconds',
    'Duration of WoL requests in seconds',
    ['endpoint']
)

# Helper to expose metrics for FastAPI
def get_metrics():
    """Return metrics in Prometheus text format."""
    return generate_latest(REGISTRY)