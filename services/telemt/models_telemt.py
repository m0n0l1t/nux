from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator


# === Базовые обёртки ответов ===
class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    ok: Literal[False] = False
    error: ErrorDetail
    request_id: int


class SuccessResponse(BaseModel):
    ok: Literal[True] = True
    data: Any
    revision: str


# === HealthData ===
class HealthData(BaseModel):
    status: Literal["ok"]
    read_only: bool


# === SystemInfoData ===
class SystemInfoData(BaseModel):
    version: str
    target_arch: str
    target_os: str
    build_profile: str
    git_commit: Optional[str] = None
    build_time_utc: Optional[str] = None
    rustc_version: Optional[str] = None
    process_started_at_epoch_secs: int
    uptime_seconds: float
    config_path: str
    config_hash: str
    config_reload_count: int
    last_config_reload_epoch_secs: Optional[int] = None


# === RuntimeGatesData ===
class RuntimeGatesData(BaseModel):
    accepting_new_connections: bool
    conditional_cast_enabled: bool
    me_runtime_ready: bool
    me2dc_fallback_enabled: bool
    use_middle_proxy: bool
    startup_status: str
    startup_stage: str
    startup_progress_pct: float


# === RuntimeInitializationData ===
class RuntimeInitializationMeData(BaseModel):
    status: str
    current_stage: str
    progress_pct: float
    init_attempt: int
    retry_limit: str
    last_error: Optional[str] = None


class RuntimeInitializationComponentData(BaseModel):
    id: str
    title: str
    status: str
    started_at_epoch_ms: Optional[int] = None
    finished_at_epoch_ms: Optional[int] = None
    duration_ms: Optional[int] = None
    attempts: int
    details: Optional[str] = None


class RuntimeInitializationData(BaseModel):
    status: str
    degraded: bool
    current_stage: str
    progress_pct: float
    started_at_epoch_secs: int
    ready_at_epoch_secs: Optional[int] = None
    total_elapsed_ms: int
    transport_mode: str
    me: RuntimeInitializationMeData
    components: List[RuntimeInitializationComponentData]


# === EffectiveLimitsData ===
class EffectiveTimeoutLimits(BaseModel):
    client_handshake_secs: int
    tg_connect_secs: int
    client_keepalive_secs: int
    client_ack_secs: int
    me_one_retry: int
    me_one_timeout_ms: int


class EffectiveUpstreamLimits(BaseModel):
    connect_retry_attempts: int
    connect_retry_backoff_ms: int
    connect_budget_ms: int
    unhealthy_fail_threshold: int
    connect_failfast_hard_errors: bool


class EffectiveMiddleProxyLimits(BaseModel):
    floor_mode: str
    adaptive_floor_idle_secs: int
    adaptive_floor_min_writers_single_endpoint: int
    adaptive_floor_min_writers_multi_endpoint: int
    adaptive_floor_recover_grace_secs: int
    adaptive_floor_writers_per_core_total: int
    adaptive_floor_cpu_cores_override: int
    adaptive_floor_max_extra_writers_single_per_core: int
    adaptive_floor_max_extra_writers_multi_per_core: int
    adaptive_floor_max_active_writers_per_core: int
    adaptive_floor_max_warm_writers_per_core: int
    adaptive_floor_max_active_writers_global: int
    adaptive_floor_max_warm_writers_global: int
    reconnect_max_concurrent_per_dc: int
    reconnect_backoff_base_ms: int
    reconnect_backoff_cap_ms: int
    reconnect_fast_retry_count: int
    writer_pick_mode: str
    writer_pick_sample_size: int
    me2dc_fallback: bool


class EffectiveUserIpPolicyLimits(BaseModel):
    mode: str
    window_secs: int


class EffectiveLimitsData(BaseModel):
    update_every_secs: int
    me_reinit_every_secs: int
    me_pool_force_close_secs: int
    timeouts: EffectiveTimeoutLimits
    upstream: EffectiveUpstreamLimits
    middle_proxy: EffectiveMiddleProxyLimits
    user_ip_policy: EffectiveUserIpPolicyLimits


# === SecurityPostureData ===
class SecurityPostureData(BaseModel):
    api_read_only: bool
    api_whitelist_enabled: bool
    api_whitelist_entries: int
    api_auth_header_enabled: bool
    proxy_protocol_enabled: bool
    log_level: str
    telemetry_core_enabled: bool
    telemetry_user_enabled: bool
    telemetry_me_level: str


# === SecurityWhitelistData ===
class SecurityWhitelistData(BaseModel):
    generated_at_epoch_secs: int
    enabled: bool
    entries_total: int
    entries: List[str]


# === SummaryData ===
class SummaryData(BaseModel):
    uptime_seconds: float
    connections_total: int
    connections_bad_total: int
    handshake_timeouts_total: int
    configured_users: int


# === ZeroAllData (многие вложенные структуры) ===
class ZeroCodeCount(BaseModel):
    code: int
    total: int


class ZeroCoreData(BaseModel):
    uptime_seconds: float
    connections_total: int
    connections_bad_total: int
    handshake_timeouts_total: int
    configured_users: int
    telemetry_core_enabled: bool
    telemetry_user_enabled: bool
    telemetry_me_level: str


class ZeroUpstreamData(BaseModel):
    connect_attempt_total: int
    connect_success_total: int
    connect_fail_total: int
    connect_failfast_hard_error_total: int
    connect_attempts_bucket_1: int
    connect_attempts_bucket_2: int
    connect_attempts_bucket_3_4: int
    connect_attempts_bucket_gt_4: int
    connect_duration_success_bucket_le_100ms: int
    connect_duration_success_bucket_101_500ms: int
    connect_duration_success_bucket_501_1000ms: int
    connect_duration_success_bucket_gt_1000ms: int
    connect_duration_fail_bucket_le_100ms: int
    connect_duration_fail_bucket_101_500ms: int
    connect_duration_fail_bucket_501_1000ms: int
    connect_duration_fail_bucket_gt_1000ms: int


class ZeroMiddleProxyData(BaseModel):
    keepalive_sent_total: int
    keepalive_failed_total: int
    keepalive_pong_total: int
    keepalive_timeout_total: int
    rpc_proxy_req_signal_sent_total: int
    rpc_proxy_req_signal_failed_total: int
    rpc_proxy_req_signal_skipped_no_meta_total: int
    rpc_proxy_req_signal_response_total: int
    rpc_proxy_req_signal_close_sent_total: int
    reconnect_attempt_total: int
    reconnect_success_total: int
    handshake_reject_total: int
    handshake_error_codes: List[ZeroCodeCount]
    reader_eof_total: int
    idle_close_by_peer_total: int
    route_drop_no_conn_total: int
    route_drop_channel_closed_total: int
    route_drop_queue_full_total: int
    route_drop_queue_full_base_total: int
    route_drop_queue_full_high_total: int
    socks_kdf_strict_reject_total: int
    socks_kdf_compat_fallback_total: int
    endpoint_quarantine_total: int
    kdf_drift_total: int
    kdf_port_only_drift_total: int
    hardswap_pending_reuse_total: int
    hardswap_pending_ttl_expired_total: int
    single_endpoint_outage_enter_total: int
    single_endpoint_outage_exit_total: int
    single_endpoint_outage_reconnect_attempt_total: int
    single_endpoint_outage_reconnect_success_total: int
    single_endpoint_quarantine_bypass_total: int
    single_endpoint_shadow_rotate_total: int
    single_endpoint_shadow_rotate_skipped_quarantine_total: int
    floor_mode_switch_total: int
    floor_mode_switch_static_to_adaptive_total: int
    floor_mode_switch_adaptive_to_static_total: int


class ZeroPoolData(BaseModel):
    pool_swap_total: int
    pool_drain_active: int
    pool_force_close_total: int
    pool_stale_pick_total: int
    writer_removed_total: int
    writer_removed_unexpected_total: int
    refill_triggered_total: int
    refill_skipped_inflight_total: int
    refill_failed_total: int
    writer_restored_same_endpoint_total: int
    writer_restored_fallback_total: int


class ZeroDesyncData(BaseModel):
    secure_padding_invalid_total: int
    desync_total: int
    desync_full_logged_total: int
    desync_suppressed_total: int
    desync_frames_bucket_0: int
    desync_frames_bucket_1_2: int
    desync_frames_bucket_3_10: int
    desync_frames_bucket_gt_10: int


class ZeroAllData(BaseModel):
    generated_at_epoch_secs: int
    core: ZeroCoreData
    upstream: ZeroUpstreamData
    middle_proxy: ZeroMiddleProxyData
    pool: ZeroPoolData
    desync: ZeroDesyncData


# === UpstreamsData ===
class UpstreamDcStatus(BaseModel):
    dc: int
    latency_ema_ms: Optional[float] = None
    ip_preference: str


class UpstreamStatus(BaseModel):
    upstream_id: int
    route_kind: str
    address: str
    weight: int
    scopes: str
    healthy: bool
    fails: int
    last_check_age_secs: int
    effective_latency_ms: Optional[float] = None
    dc: List[UpstreamDcStatus]


class UpstreamSummaryData(BaseModel):
    configured_total: int
    healthy_total: int
    unhealthy_total: int
    direct_total: int
    socks4_total: int
    socks5_total: int
    shadowsocks_total: int


class UpstreamsData(BaseModel):
    enabled: bool
    reason: Optional[str] = None
    generated_at_epoch_secs: int
    zero: ZeroUpstreamData
    summary: Optional[UpstreamSummaryData] = None
    upstreams: Optional[List[UpstreamStatus]] = None


# === MinimalAllData ===
class MinimalQuarantineData(BaseModel):
    endpoint: str
    remaining_ms: int


class MinimalMeRuntimeData(BaseModel):
    active_generation: int
    warm_generation: int
    pending_hardswap_generation: int
    pending_hardswap_age_secs: Optional[int] = None
    hardswap_enabled: bool
    floor_mode: str
    adaptive_floor_idle_secs: int
    adaptive_floor_min_writers_single_endpoint: int
    adaptive_floor_min_writers_multi_endpoint: int
    adaptive_floor_recover_grace_secs: int
    adaptive_floor_writers_per_core_total: int
    adaptive_floor_cpu_cores_override: int
    adaptive_floor_max_extra_writers_single_per_core: int
    adaptive_floor_max_extra_writers_multi_per_core: int
    adaptive_floor_max_active_writers_per_core: int
    adaptive_floor_max_warm_writers_per_core: int
    adaptive_floor_max_active_writers_global: int
    adaptive_floor_max_warm_writers_global: int
    adaptive_floor_cpu_cores_detected: int
    adaptive_floor_cpu_cores_effective: int
    adaptive_floor_global_cap_raw: int
    adaptive_floor_global_cap_effective: int
    adaptive_floor_target_writers_total: int
    adaptive_floor_active_cap_configured: int
    adaptive_floor_active_cap_effective: int
    adaptive_floor_warm_cap_configured: int
    adaptive_floor_warm_cap_effective: int
    adaptive_floor_active_writers_current: int
    adaptive_floor_warm_writers_current: int
    me_keepalive_enabled: bool
    me_keepalive_interval_secs: int
    me_keepalive_jitter_secs: int
    me_keepalive_payload_random: bool
    rpc_proxy_req_every_secs: int
    me_reconnect_max_concurrent_per_dc: int
    me_reconnect_backoff_base_ms: int
    me_reconnect_backoff_cap_ms: int
    me_reconnect_fast_retry_count: int
    me_pool_drain_ttl_secs: int
    me_pool_force_close_secs: int
    me_pool_min_fresh_ratio: float
    me_bind_stale_mode: str
    me_bind_stale_ttl_secs: int
    me_single_endpoint_shadow_writers: int
    me_single_endpoint_outage_mode_enabled: bool
    me_single_endpoint_outage_disable_quarantine: bool
    me_single_endpoint_outage_backoff_min_ms: int
    me_single_endpoint_outage_backoff_max_ms: int
    me_single_endpoint_shadow_rotate_every_secs: int
    me_deterministic_writer_sort: bool
    me_writer_pick_mode: str
    me_writer_pick_sample_size: int
    me_socks_kdf_policy: str
    quarantined_endpoints_total: int
    quarantined_endpoints: List[MinimalQuarantineData]


class MinimalDcPathData(BaseModel):
    dc: int
    ip_preference: Optional[str] = None
    selected_addr_v4: Optional[str] = None
    selected_addr_v6: Optional[str] = None


class MinimalAllPayload(BaseModel):
    me_writers: "MeWritersData"
    dcs: "DcStatusData"
    me_runtime: Optional[MinimalMeRuntimeData] = None
    network_path: List[MinimalDcPathData]


class MinimalAllData(BaseModel):
    enabled: bool
    reason: Optional[str] = None
    generated_at_epoch_secs: int
    data: Optional[MinimalAllPayload] = None


# === MeWritersData ===
class MeWritersSummary(BaseModel):
    configured_dc_groups: int
    configured_endpoints: int
    available_endpoints: int
    available_pct: float
    required_writers: int
    alive_writers: int
    coverage_pct: float


class MeWriterStatus(BaseModel):
    writer_id: int
    dc: Optional[int] = None
    endpoint: str
    generation: int
    state: str
    draining: bool
    degraded: bool
    bound_clients: int
    idle_for_secs: Optional[int] = None
    rtt_ema_ms: Optional[float] = None


class MeWritersData(BaseModel):
    middle_proxy_enabled: bool
    reason: Optional[str] = None
    generated_at_epoch_secs: int
    summary: MeWritersSummary
    writers: List[MeWriterStatus]


# === DcStatusData ===
class DcEndpointWriters(BaseModel):
    endpoint: str
    active_writers: int


class DcStatus(BaseModel):
    dc: int
    endpoints: List[str]
    endpoint_writers: List[DcEndpointWriters]
    available_endpoints: int
    available_pct: float
    required_writers: int
    floor_min: int
    floor_target: int
    floor_max: int
    floor_capped: bool
    alive_writers: int
    coverage_pct: float
    rtt_ms: Optional[float] = None
    load: int


class DcStatusData(BaseModel):
    middle_proxy_enabled: bool
    reason: Optional[str] = None
    generated_at_epoch_secs: int
    dcs: List[DcStatus]


# === RuntimeMePoolStateData (сокращённо) ===
class RuntimeMePoolStateGenerationData(BaseModel):
    active_generation: int
    warm_generation: int
    pending_hardswap_generation: int
    pending_hardswap_age_secs: Optional[int] = None
    draining_generations: List[int]


class RuntimeMePoolStateHardswapData(BaseModel):
    enabled: bool
    pending: bool


class RuntimeMePoolStateWriterContourData(BaseModel):
    warm: int
    active: int
    draining: int


class RuntimeMePoolStateWriterHealthData(BaseModel):
    healthy: int
    degraded: int
    draining: int


class RuntimeMePoolStateWriterData(BaseModel):
    total: int
    alive_non_draining: int
    draining: int
    degraded: int
    contour: RuntimeMePoolStateWriterContourData
    health: RuntimeMePoolStateWriterHealthData


class RuntimeMePoolStateRefillDcData(BaseModel):
    dc: int
    family: str
    inflight: int


class RuntimeMePoolStateRefillData(BaseModel):
    inflight_endpoints_total: int
    inflight_dc_total: int
    by_dc: List[RuntimeMePoolStateRefillDcData]


class RuntimeMePoolStatePayload(BaseModel):
    generations: RuntimeMePoolStateGenerationData
    hardswap: RuntimeMePoolStateHardswapData
    writers: RuntimeMePoolStateWriterData
    refill: RuntimeMePoolStateRefillData


class RuntimeMePoolStateData(BaseModel):
    enabled: bool
    reason: Optional[str] = None
    generated_at_epoch_secs: int
    data: Optional[RuntimeMePoolStatePayload] = None


# === RuntimeMeQualityData (сокращённо) ===
class RuntimeMeQualityCountersData(BaseModel):
    idle_close_by_peer_total: int
    reader_eof_total: int
    kdf_drift_total: int
    kdf_port_only_drift_total: int
    reconnect_attempt_total: int
    reconnect_success_total: int


class RuntimeMeQualityRouteDropData(BaseModel):
    no_conn_total: int
    channel_closed_total: int
    queue_full_total: int
    queue_full_base_total: int
    queue_full_high_total: int


class RuntimeMeQualityDcRttData(BaseModel):
    dc: int
    rtt_ema_ms: Optional[float] = None
    alive_writers: int
    required_writers: int
    coverage_pct: float


class RuntimeMeQualityPayload(BaseModel):
    counters: RuntimeMeQualityCountersData
    route_drops: RuntimeMeQualityRouteDropData
    dc_rtt: List[RuntimeMeQualityDcRttData]


class RuntimeMeQualityData(BaseModel):
    enabled: bool
    reason: Optional[str] = None
    generated_at_epoch_secs: int
    data: Optional[RuntimeMeQualityPayload] = None


# === RuntimeUpstreamQualityData ===
class RuntimeUpstreamQualityPolicyData(BaseModel):
    connect_retry_attempts: int
    connect_retry_backoff_ms: int
    connect_budget_ms: int
    unhealthy_fail_threshold: int
    connect_failfast_hard_errors: bool


class RuntimeUpstreamQualityCountersData(BaseModel):
    connect_attempt_total: int
    connect_success_total: int
    connect_fail_total: int
    connect_failfast_hard_error_total: int


class RuntimeUpstreamQualitySummaryData(BaseModel):
    configured_total: int
    healthy_total: int
    unhealthy_total: int
    direct_total: int
    socks4_total: int
    socks5_total: int
    shadowsocks_total: int


class RuntimeUpstreamQualityDcData(BaseModel):
    dc: int
    latency_ema_ms: Optional[float] = None
    ip_preference: str


class RuntimeUpstreamQualityUpstreamData(BaseModel):
    upstream_id: int
    route_kind: str
    address: str
    weight: int
    scopes: str
    healthy: bool
    fails: int
    last_check_age_secs: int
    effective_latency_ms: Optional[float] = None
    dc: List[RuntimeUpstreamQualityDcData]


class RuntimeUpstreamQualityData(BaseModel):
    enabled: bool
    reason: Optional[str] = None
    generated_at_epoch_secs: int
    policy: RuntimeUpstreamQualityPolicyData
    counters: RuntimeUpstreamQualityCountersData
    summary: Optional[RuntimeUpstreamQualitySummaryData] = None
    upstreams: Optional[List[RuntimeUpstreamQualityUpstreamData]] = None


# === RuntimeNatStunData ===
class RuntimeNatStunFlagsData(BaseModel):
    nat_probe_enabled: bool
    nat_probe_disabled_runtime: bool
    nat_probe_attempts: int


class RuntimeNatStunServersData(BaseModel):
    configured: List[str]
    live: List[str]
    live_total: int


class RuntimeNatStunReflectionData(BaseModel):
    addr: str
    age_secs: int


class RuntimeNatStunReflectionBlockData(BaseModel):
    v4: Optional[RuntimeNatStunReflectionData] = None
    v6: Optional[RuntimeNatStunReflectionData] = None


class RuntimeNatStunPayload(BaseModel):
    flags: RuntimeNatStunFlagsData
    servers: RuntimeNatStunServersData
    reflection: RuntimeNatStunReflectionBlockData
    stun_backoff_remaining_ms: Optional[int] = None


class RuntimeNatStunData(BaseModel):
    enabled: bool
    reason: Optional[str] = None
    generated_at_epoch_secs: int
    data: Optional[RuntimeNatStunPayload] = None


# === RuntimeMeSelftestData ===
class RuntimeMeSelftestKdfData(BaseModel):
    state: str
    ewma_errors_per_min: float
    threshold_errors_per_min: float
    errors_total: int


class RuntimeMeSelftestTimeskewData(BaseModel):
    state: str
    max_skew_secs_15m: Optional[int] = None
    samples_15m: int
    last_skew_secs: Optional[int] = None
    last_source: Optional[str] = None
    last_seen_age_secs: Optional[int] = None


class RuntimeMeSelftestIpFamilyData(BaseModel):
    addr: str
    state: str


class RuntimeMeSelftestIpData(BaseModel):
    v4: Optional[RuntimeMeSelftestIpFamilyData] = None
    v6: Optional[RuntimeMeSelftestIpFamilyData] = None


class RuntimeMeSelftestPidData(BaseModel):
    pid: int
    state: str


class RuntimeMeSelftestBndData(BaseModel):
    addr_state: str
    port_state: str
    last_addr: Optional[str] = None
    last_seen_age_secs: Optional[int] = None


class RuntimeMeSelftestPayload(BaseModel):
    kdf: RuntimeMeSelftestKdfData
    timeskew: RuntimeMeSelftestTimeskewData
    ip: RuntimeMeSelftestIpData
    pid: RuntimeMeSelftestPidData
    bnd: RuntimeMeSelftestBndData


class RuntimeMeSelftestData(BaseModel):
    enabled: bool
    reason: Optional[str] = None
    generated_at_epoch_secs: int
    data: Optional[RuntimeMeSelftestPayload] = None


# === RuntimeEdgeConnectionsSummaryData ===
class RuntimeEdgeConnectionUserData(BaseModel):
    username: str
    current_connections: int
    total_octets: int


class RuntimeEdgeConnectionTotalsData(BaseModel):
    current_connections: int
    current_connections_me: int
    current_connections_direct: int
    active_users: int


class RuntimeEdgeConnectionTopData(BaseModel):
    limit: int
    by_connections: List[RuntimeEdgeConnectionUserData]
    by_throughput: List[RuntimeEdgeConnectionUserData]


class RuntimeEdgeConnectionTelemetryData(BaseModel):
    user_enabled: bool
    throughput_is_cumulative: bool


class RuntimeEdgeConnectionCacheData(BaseModel):
    ttl_ms: int
    served_from_cache: bool
    stale_cache_used: bool


class RuntimeEdgeConnectionsSummaryPayload(BaseModel):
    cache: RuntimeEdgeConnectionCacheData
    totals: RuntimeEdgeConnectionTotalsData
    top: RuntimeEdgeConnectionTopData
    telemetry: RuntimeEdgeConnectionTelemetryData


class RuntimeEdgeConnectionsSummaryData(BaseModel):
    enabled: bool
    reason: Optional[str] = None
    generated_at_epoch_secs: int
    data: Optional[RuntimeEdgeConnectionsSummaryPayload] = None


# === RuntimeEdgeEventsData ===
class ApiEventRecord(BaseModel):
    seq: int
    ts_epoch_secs: int
    event_type: str
    context: str


class RuntimeEdgeEventsPayload(BaseModel):
    capacity: int
    dropped_total: int
    events: List[ApiEventRecord]


class RuntimeEdgeEventsData(BaseModel):
    enabled: bool
    reason: Optional[str] = None
    generated_at_epoch_secs: int
    data: Optional[RuntimeEdgeEventsPayload] = None


# === UserInfo ===
class UserLinks(BaseModel):
    classic: List[str]
    secure: List[str]
    tls: List[str]


class UserInfo(BaseModel):
    username: str
    user_ad_tag: Optional[str] = None
    max_tcp_conns: Optional[int] = None
    expiration_rfc3339: Optional[str] = None
    data_quota_bytes: Optional[int] = None
    max_unique_ips: Optional[int] = None
    current_connections: int
    active_unique_ips: int
    active_unique_ips_list: List[str]
    recent_unique_ips: int
    recent_unique_ips_list: List[str]
    total_octets: int
    links: UserLinks


# === Запросы на создание/обновление пользователя ===
class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    secret: Optional[str] = Field(None, pattern=r"^[0-9a-fA-F]{32}$")
    user_ad_tag: Optional[str] = Field(None, pattern=r"^[0-9a-fA-F]{32}$")
    max_tcp_conns: Optional[int] = None
    expiration_rfc3339: Optional[str] = None
    data_quota_bytes: Optional[int] = None
    max_unique_ips: Optional[int] = None


class PatchUserRequest(BaseModel):
    secret: Optional[str] = Field(None, pattern=r"^[0-9a-fA-F]{32}$")
    user_ad_tag: Optional[str] = Field(None, pattern=r"^[0-9a-fA-F]{32}$")
    max_tcp_conns: Optional[int] = None
    expiration_rfc3339: Optional[str] = None
    data_quota_bytes: Optional[int] = None
    max_unique_ips: Optional[int] = None


class CreateUserResponse(BaseModel):
    user: UserInfo
    secret: str


# === RotateSecretRequest ===
class RotateSecretRequest(BaseModel):
    secret: Optional[str] = Field(None, pattern=r"^[0-9a-fA-F]{32}$")


# Для циклических ссылок (MinimalAllPayload ссылается на MeWritersData и DcStatusData)
MinimalAllPayload.model_rebuild()