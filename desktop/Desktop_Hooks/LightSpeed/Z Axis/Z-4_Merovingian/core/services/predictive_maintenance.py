"""
Predictive Maintenance Engine (Merovingian + Neo alignment)
LightSpeed Type I Civilization Platform

Provides lightweight, dependency-free forecasting and risk scoring based on:
- telemetry_data (cpu_percent, memory_percent, disk_percent, etc.)
- jobs table (failures / backlog)
- system_logs (error rate)

Design goals:
- No side effects during analysis (no imports of floor modules, no network)
- Graceful degradation when telemetry is missing
- Emits events for cross-floor reactions (Smith scheduling, Trinity dashboards, Neo explanations)
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_THRESHOLDS = {
    "cpu_percent": {"warning": 70.0, "critical": 90.0},
    "memory_percent": {"warning": 75.0, "critical": 90.0},
    "disk_percent": {"warning": 80.0, "critical": 95.0},
}


@dataclass(frozen=True)
class MetricForecast:
    metric: str
    window_points: int
    slope_per_min: float
    current_value: float
    forecast_5m: float
    forecast_15m: float
    forecast_60m: float
    time_to_warning_min: Optional[float]
    time_to_critical_min: Optional[float]
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PredictiveMaintenanceEngine:
    def __init__(self, db=None, event_bus=None, logger=None, thresholds: Optional[Dict[str, Dict[str, float]]] = None):
        self.db = db
        self.event_bus = event_bus
        self.logger = logger
        self.thresholds = thresholds or DEFAULT_THRESHOLDS

    def record_system_metrics(
        self,
        cpu_percent: float,
        memory_percent: float,
        disk_percent: float,
        health_score: Optional[float] = None,
        component: str = "system",
    ) -> None:
        """
        Store a minimal telemetry set into the unified DB.

        This can be called from Merovingian's live sampler (psutil-based), so that forecasting
        works even without a dedicated telemetry daemon.
        """
        if not self.db or not hasattr(self.db, "record_telemetry"):
            return

        try:
            self.db.record_telemetry(component, "cpu_percent", float(cpu_percent), unit="%")
            self.db.record_telemetry(component, "memory_percent", float(memory_percent), unit="%")
            self.db.record_telemetry(component, "disk_percent", float(disk_percent), unit="%")
            if health_score is not None:
                self.db.record_telemetry(component, "health_score", float(health_score), unit="score")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"[PredictiveMaintenance] record_system_metrics failed: {e}")

    def _fetch_series(
        self,
        metric_name: str,
        window_minutes: int,
        component: Optional[str] = None,
        limit: int = 2000,
    ) -> List[Tuple[datetime, float]]:
        if not self.db:
            return []

        cutoff = (datetime.now() - timedelta(minutes=window_minutes)).isoformat()

        params: List[Any] = [metric_name, cutoff]
        where_component = ""
        if component:
            where_component = " AND component = ?"
            params.append(component)

        query = f"""
            SELECT recorded_at, value
            FROM telemetry_data
            WHERE metric_name = ? AND recorded_at >= ?{where_component}
            ORDER BY recorded_at ASC
            LIMIT {int(limit)}
        """
        try:
            rows = self.db.execute_query(query, tuple(params))
        except Exception:
            try:
                rows = self.db.fetchall(query, tuple(params))
            except Exception:
                return []

        series: List[Tuple[datetime, float]] = []
        for r in rows:
            try:
                recorded_at = r["recorded_at"] if isinstance(r, dict) else r[0]
                value = r["value"] if isinstance(r, dict) else r[1]
                series.append((datetime.fromisoformat(str(recorded_at)), float(value)))
            except Exception:
                continue

        return series

    @staticmethod
    def _fit_linear(xs: List[float], ys: List[float]) -> Tuple[float, float]:
        """
        Fit y = a + b*x. Returns (a, b). Uses a stable closed-form regression.
        """
        n = len(xs)
        if n < 2:
            return (ys[0] if ys else 0.0, 0.0)

        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        sxx = sum((x - mean_x) ** 2 for x in xs)
        if sxx == 0:
            return (mean_y, 0.0)
        sxy = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
        b = sxy / sxx
        a = mean_y - b * mean_x
        return (a, b)

    def _forecast_metric(
        self,
        metric_name: str,
        window_minutes: int = 60,
        component: Optional[str] = "system",
    ) -> Optional[MetricForecast]:
        series = self._fetch_series(metric_name, window_minutes=window_minutes, component=component)
        if len(series) < 2:
            return None

        t0 = series[0][0]
        xs = [((t - t0).total_seconds() / 60.0) for t, _ in series]  # minutes
        ys = [v for _, v in series]

        a, b = self._fit_linear(xs, ys)  # y = a + b*x
        current = ys[-1]
        x_now = xs[-1]

        def predict(minutes_ahead: float) -> float:
            return float(a + b * (x_now + minutes_ahead))

        warn = self.thresholds.get(metric_name, {}).get("warning")
        crit = self.thresholds.get(metric_name, {}).get("critical")

        def time_to(threshold: Optional[float]) -> Optional[float]:
            if threshold is None:
                return None
            if b <= 0:
                return None
            remaining = threshold - current
            if remaining <= 0:
                return 0.0
            return float(remaining / b)

        t_warn = time_to(warn)
        t_crit = time_to(crit)

        status = "stable"
        if t_crit is not None and t_crit <= 30:
            status = "critical_risk"
        elif t_warn is not None and t_warn <= 30:
            status = "warning_risk"

        return MetricForecast(
            metric=metric_name,
            window_points=len(series),
            slope_per_min=float(b),
            current_value=float(current),
            forecast_5m=predict(5.0),
            forecast_15m=predict(15.0),
            forecast_60m=predict(60.0),
            time_to_warning_min=t_warn,
            time_to_critical_min=t_crit,
            status=status,
        )

    def _job_failure_stats(self, window_minutes: int = 60) -> Dict[str, Any]:
        if not self.db:
            return {"failed": 0, "total": 0}

        cutoff = (datetime.now() - timedelta(minutes=window_minutes)).isoformat()
        try:
            rows = self.db.fetchall(
                "SELECT status FROM jobs WHERE created_at >= ? OR (updated_at IS NOT NULL AND updated_at >= ?)",
                (cutoff, cutoff),
            )
        except Exception:
            return {"failed": 0, "total": 0}

        statuses = []
        for r in rows:
            try:
                statuses.append((r["status"] if isinstance(r, dict) else r[0]) or "")
            except Exception:
                continue

        total = len(statuses)
        failed = sum(1 for s in statuses if str(s).lower() == "failed")
        return {"failed": failed, "total": total}

    def _error_log_stats(self, window_minutes: int = 60) -> Dict[str, Any]:
        if not self.db:
            return {"errors": 0}

        cutoff = (datetime.now() - timedelta(minutes=window_minutes)).isoformat()
        try:
            rows = self.db.fetchall(
                "SELECT level FROM system_logs WHERE timestamp >= ?",
                (cutoff,),
            )
        except Exception:
            return {"errors": 0}

        errors = 0
        for r in rows:
            level = ""
            try:
                level = (r["level"] if isinstance(r, dict) else r[0]) or ""
            except Exception:
                level = ""
            if str(level).upper() in ("ERROR", "CRITICAL"):
                errors += 1

        return {"errors": errors}

    def compute_risk(self, window_minutes: int = 60, component: str = "system") -> Dict[str, Any]:
        forecasts: Dict[str, Dict[str, Any]] = {}
        alerts: List[Dict[str, Any]] = []

        for metric in ("cpu_percent", "memory_percent", "disk_percent"):
            f = self._forecast_metric(metric, window_minutes=window_minutes, component=component)
            if f is None:
                continue
            forecasts[metric] = f.to_dict()

            # Create actionable alerts when time-to-threshold is near.
            t_warn = f.time_to_warning_min
            t_crit = f.time_to_critical_min
            if t_crit is not None and t_crit <= 15:
                alerts.append({
                    "severity": "critical",
                    "metric": metric,
                    "message": f"{metric} projected to hit CRITICAL within {t_crit:.1f} min",
                    "time_to_critical_min": t_crit,
                    "slope_per_min": f.slope_per_min,
                })
            elif t_warn is not None and t_warn <= 15:
                alerts.append({
                    "severity": "warning",
                    "metric": metric,
                    "message": f"{metric} projected to hit WARNING within {t_warn:.1f} min",
                    "time_to_warning_min": t_warn,
                    "slope_per_min": f.slope_per_min,
                })

        job_stats = self._job_failure_stats(window_minutes=window_minutes)
        log_stats = self._error_log_stats(window_minutes=window_minutes)

        # Risk scoring (0..100)
        risk = 0.0
        for a in alerts:
            if a["severity"] == "critical":
                risk = max(risk, 90.0)
            else:
                risk = max(risk, 70.0)

        if job_stats["total"] >= 5 and job_stats["failed"] > 0:
            risk = max(risk, min(95.0, 60.0 + job_stats["failed"] * 10.0))

        if log_stats["errors"] >= 3:
            risk = max(risk, min(98.0, 50.0 + log_stats["errors"] * 8.0))

        recommendations: List[Dict[str, Any]] = []
        if any(a["severity"] == "critical" for a in alerts):
            recommendations.append({
                "type": "operational",
                "action": "reduce_load",
                "detail": "Reduce CPU/memory load; investigate runaway processes; consider pausing non-essential jobs.",
            })
        if job_stats["failed"] > 0:
            recommendations.append({
                "type": "smith",
                "action": "review_failed_jobs",
                "detail": f"{job_stats['failed']} job(s) failed in the last {window_minutes} minutes; inspect Smith queue + error details.",
            })
        if log_stats["errors"] > 0:
            recommendations.append({
                "type": "logging",
                "action": "inspect_errors",
                "detail": f"{log_stats['errors']} ERROR/CRITICAL log(s) in the last {window_minutes} minutes; inspect system_logs.",
            })

        return {
            "generated_at": datetime.now().isoformat(),
            "window_minutes": window_minutes,
            "component": component,
            "risk_score": round(float(risk), 2),
            "forecasts": forecasts,
            "job_stats": job_stats,
            "log_stats": log_stats,
            "alerts": alerts,
            "recommendations": recommendations,
        }

    def publish_alerts(self, risk_report: Dict[str, Any]) -> int:
        """
        Publish `merovingian.predictive_alert` events for each alert.
        Returns number of alerts emitted.
        """
        if not self.event_bus:
            return 0
        emitted = 0
        for alert in risk_report.get("alerts") or []:
            try:
                payload = {
                    "generated_at": risk_report.get("generated_at"),
                    "window_minutes": risk_report.get("window_minutes"),
                    "component": risk_report.get("component"),
                    "risk_score": risk_report.get("risk_score"),
                    "alert": alert,
                }
                self.event_bus.publish("merovingian.predictive_alert", payload)
                emitted += 1
            except Exception:
                continue
        return emitted

    def schedule_job(self, job_type: str, parameters: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """
        Create a Smith job row (queued/pending execution by other layers).
        This does not execute anything by itself.
        """
        if not self.db:
            return None

        meta = metadata or {}
        meta.setdefault("created_by", "predictive_maintenance")
        meta.setdefault("created_at", datetime.now().isoformat())

        try:
            # Prefer the DB helper if present (keeps schema logic centralized).
            if hasattr(self.db, "create_background_job"):
                job_id = self.db.create_background_job(job_type, parameters, scheduled_for=datetime.now().isoformat())
                # Best-effort metadata update
                try:
                    import json
                    self.db.execute_update(
                        "UPDATE jobs SET metadata_json = ?, updated_at = ? WHERE id = ?",
                        (json.dumps(meta), datetime.now().isoformat(), job_id),
                    )
                except Exception:
                    pass
                return int(job_id)
        except Exception:
            pass

        # Fallback: direct insert
        try:
            import json
            return_id = None
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO jobs (job_type, params_json, status, scheduled_for, created_at, metadata_json)
                    VALUES (?, ?, 'pending', ?, ?, ?)
                    """,
                    (
                        job_type,
                        json.dumps(parameters or {}),
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                        json.dumps(meta),
                    ),
                )
                return_id = cursor.lastrowid
            return int(return_id) if return_id is not None else None
        except Exception as e:
            if self.logger:
                self.logger.warning(f"[PredictiveMaintenance] schedule_job failed: {e}")
            return None


_engine: Optional[PredictiveMaintenanceEngine] = None


def get_predictive_maintenance_engine(db=None, event_bus=None, logger=None) -> PredictiveMaintenanceEngine:
    global _engine
    if _engine is None:
        _engine = PredictiveMaintenanceEngine(db=db, event_bus=event_bus, logger=logger)
    else:
        if db is not None:
            _engine.db = db
        if event_bus is not None:
            _engine.event_bus = event_bus
        if logger is not None:
            _engine.logger = logger
    return _engine
