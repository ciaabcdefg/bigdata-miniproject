import { Kafka } from "kafkajs";

const KAFKA_BROKER = process.env.KAFKA_BROKER || "localhost:29092";
const KAFKA_TOPIC = process.env.KAFKA_TOPIC || "service-logs";

const kafka = new Kafka({
    clientId: "test-frontend",
    brokers: [KAFKA_BROKER],
    retry: { retries: 5, initialRetryTime: 1000 },
});

const producer = kafka.producer();
let isConnected = false;

async function ensureConnected() {
    if (!isConnected) {
        await producer.connect();
        isConnected = true;
    }
}

// ── Log templates (matches Python generator schema) ─────────────────
const SERVICE_SCENARIOS = {
    "auth-service": [
        { action: "login", level: "INFO", message: "User login successful", status_code: 200, rt: [50, 200] },
        { action: "refresh-token", level: "INFO", message: "Token refreshed", status_code: 200, rt: [30, 100] },
        { action: "failed-login", level: "WARN", message: "Multiple failed login attempts", status_code: 401, rt: [100, 500] },
        { action: "db-timeout", level: "ERROR", message: "Connection timeout to database", status_code: 500, rt: [3000, 5000] },
        { action: "unavailable", level: "ERROR", message: "Authentication service unavailable", status_code: 503, rt: [5000, 10000] },
    ],
    "payment-service": [
        { action: "process", level: "INFO", message: "Payment processed successfully", status_code: 200, rt: [100, 300] },
        { action: "refund", level: "INFO", message: "Refund initiated", status_code: 200, rt: [150, 400] },
        { action: "slow-gateway", level: "WARN", message: "Payment gateway slow response", status_code: 200, rt: [2000, 4000] },
        { action: "gateway-timeout", level: "ERROR", message: "Payment gateway timeout", status_code: 504, rt: [5000, 10000] },
        { action: "insufficient", level: "ERROR", message: "Insufficient funds", status_code: 402, rt: [80, 200] },
    ],
    "api-gateway": [
        { action: "route", level: "INFO", message: "Request routed successfully", status_code: 200, rt: [20, 100] },
        { action: "rate-check", level: "INFO", message: "Rate limit check passed", status_code: 200, rt: [10, 50] },
        { action: "high-memory", level: "WARN", message: "High memory usage detected", status_code: 200, rt: [500, 1500] },
        { action: "rate-limit", level: "WARN", message: "Rate limit threshold approaching", status_code: 429, rt: [10, 30] },
        { action: "upstream-down", level: "ERROR", message: "Upstream service unreachable", status_code: 502, rt: [5000, 10000] },
    ],
};

function randInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

export function getServices() {
    return Object.entries(SERVICE_SCENARIOS).map(([service, scenarios]) => ({
        service,
        actions: scenarios.map((s) => ({
            action: s.action,
            level: s.level,
            label: s.message,
        })),
    }));
}

export function buildLogEvent(service, action) {
    const scenarios = SERVICE_SCENARIOS[service];
    if (!scenarios) throw new Error(`Unknown service: ${service}`);

    let scenario;
    if (action) {
        scenario = scenarios.find((s) => s.action === action);
        if (!scenario) throw new Error(`Unknown action: ${action} for ${service}`);
    } else {
        scenario = scenarios[randInt(0, scenarios.length - 1)];
    }

    return {
        timestamp: new Date().toISOString().replace(/\.\d{3}Z$/, ""),
        service,
        level: scenario.level,
        message: scenario.message,
        response_time_ms: randInt(scenario.rt[0], scenario.rt[1]),
        status_code: scenario.status_code,
    };
}

export async function produceLog(service, action) {
    await ensureConnected();
    const event = buildLogEvent(service, action);
    await producer.send({
        topic: KAFKA_TOPIC,
        messages: [{ value: JSON.stringify(event) }],
    });
    return event;
}

export async function produceBurst(service, action, count) {
    await ensureConnected();
    const events = [];
    const messages = [];
    for (let i = 0; i < count; i++) {
        const event = buildLogEvent(service, action);
        events.push(event);
        messages.push({ value: JSON.stringify(event) });
    }
    await producer.send({ topic: KAFKA_TOPIC, messages });
    return events;
}

// ── In-memory stats ─────────────────────────────────────────────────
const stats = { total: 0, byService: {}, byLevel: {}, recentLogs: [] };
const MAX_RECENT = 50;

export function recordStats(events) {
    for (const e of events) {
        stats.total++;
        stats.byService[e.service] = (stats.byService[e.service] || 0) + 1;
        stats.byLevel[e.level] = (stats.byLevel[e.level] || 0) + 1;
        stats.recentLogs.unshift(e);
    }
    if (stats.recentLogs.length > MAX_RECENT) {
        stats.recentLogs = stats.recentLogs.slice(0, MAX_RECENT);
    }
}

export function getStats() {
    return { ...stats };
}
