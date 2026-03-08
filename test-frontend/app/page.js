"use client";

import { useState, useEffect, useCallback } from "react";
import styles from "./page.module.css";

const LEVEL_COLORS = {
  INFO: "#4ade80",
  WARN: "#facc15",
  ERROR: "#f87171",
};

export default function Dashboard() {
  const [services, setServices] = useState([]);
  const [stats, setStats] = useState({ total: 0, byService: {}, byLevel: {}, recentLogs: [] });
  const [burstCount, setBurstCount] = useState(50);
  const [sending, setSending] = useState(null);

  // Fetch available services on mount
  useEffect(() => {
    fetch("/api/logs").then((r) => r.json()).then((d) => setServices(d.services || []));
  }, []);

  // Poll stats every 2s
  useEffect(() => {
    const poll = () => fetch("/api/logs/stats").then((r) => r.json()).then(setStats).catch(() => { });
    poll();
    const id = setInterval(poll, 2000);
    return () => clearInterval(id);
  }, []);

  const sendLog = useCallback(async (service, action, count = 1) => {
    const key = `${service}-${action}`;
    setSending(key);
    try {
      await fetch("/api/logs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ service, action, count }),
      });
      // Quick refresh
      const s = await fetch("/api/logs/stats").then((r) => r.json());
      setStats(s);
    } catch (e) {
      console.error(e);
    } finally {
      setSending(null);
    }
  }, []);

  const errorRate = stats.total > 0
    ? (((stats.byLevel?.ERROR || 0) / stats.total) * 100).toFixed(1)
    : "0.0";

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>⚡ Bigdata Log Dashboard</h1>
        <p className={styles.subtitle}>Trigger microservice log events → Kafka → PySpark → Elasticsearch → Kibana</p>
      </header>

      {/* Stats Bar */}
      <section className={styles.statsBar}>
        <div className={styles.statCard}>
          <span className={styles.statValue}>{stats.total}</span>
          <span className={styles.statLabel}>Total Events</span>
        </div>
        {Object.entries(stats.byService || {}).map(([svc, count]) => (
          <div key={svc} className={styles.statCard}>
            <span className={styles.statValue}>{count}</span>
            <span className={styles.statLabel}>{svc}</span>
          </div>
        ))}
        <div className={`${styles.statCard} ${parseFloat(errorRate) > 20 ? styles.statDanger : ""}`}>
          <span className={styles.statValue}>{errorRate}%</span>
          <span className={styles.statLabel}>Error Rate</span>
        </div>
      </section>

      {/* Burst Control */}
      <section className={styles.burstSection}>
        <label>Burst count:</label>
        <input
          type="number"
          min={1}
          max={1000}
          value={burstCount}
          onChange={(e) => setBurstCount(Math.max(1, Math.min(1000, parseInt(e.target.value) || 1)))}
          className={styles.burstInput}
        />
      </section>

      {/* Service Cards */}
      <section className={styles.services}>
        {services.map(({ service, actions }) => (
          <div key={service} className={styles.serviceCard}>
            <h2 className={styles.serviceName}>{service}</h2>
            <div className={styles.actions}>
              {actions.map(({ action, level, label }) => (
                <div key={action} className={styles.actionRow}>
                  <button
                    className={styles.actionBtn}
                    style={{ borderLeftColor: LEVEL_COLORS[level] }}
                    disabled={sending !== null}
                    onClick={() => sendLog(service, action)}
                  >
                    <span className={styles.levelBadge} style={{ background: LEVEL_COLORS[level] }}>
                      {level}
                    </span>
                    {label}
                  </button>
                  <button
                    className={styles.burstBtn}
                    disabled={sending !== null}
                    onClick={() => sendLog(service, action, burstCount)}
                    title={`Send ${burstCount} events`}
                  >
                    🔥 ×{burstCount}
                  </button>
                </div>
              ))}
            </div>
          </div>
        ))}
      </section>

      {/* Live Log Feed */}
      <section className={styles.logSection}>
        <h2>📡 Live Log Feed</h2>
        <div className={styles.logFeed}>
          {stats.recentLogs?.length === 0 && (
            <p className={styles.emptyFeed}>No events yet — click an action above to start</p>
          )}
          {stats.recentLogs?.map((log, i) => (
            <div key={i} className={styles.logEntry}>
              <span className={styles.logTime}>{log.timestamp?.split("T")[1] || ""}</span>
              <span className={styles.levelBadge} style={{ background: LEVEL_COLORS[log.level] }}>
                {log.level}
              </span>
              <span className={styles.logService}>{log.service}</span>
              <span className={styles.logMsg}>{log.message}</span>
              <span className={styles.logRt}>{log.response_time_ms}ms</span>
              <span className={styles.logStatus}>{log.status_code}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
