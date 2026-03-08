import { NextResponse } from "next/server";
import { produceLog, produceBurst, recordStats, getServices } from "../../lib/kafka";

// POST /api/logs — produce one or burst of log events
export async function POST(request) {
    try {
        const body = await request.json();
        const { service, action, count } = body;

        if (!service) {
            return NextResponse.json({ error: "service is required" }, { status: 400 });
        }

        let events;
        if (count && count > 1) {
            events = await produceBurst(service, action, Math.min(count, 1000));
        } else {
            const event = await produceLog(service, action);
            events = [event];
        }

        recordStats(events);
        return NextResponse.json({ success: true, count: events.length, events });
    } catch (err) {
        console.error("[api/logs] Error:", err);
        return NextResponse.json({ error: err.message }, { status: 500 });
    }
}

// GET /api/logs — return available services and actions
export async function GET() {
    return NextResponse.json({ services: getServices() });
}
