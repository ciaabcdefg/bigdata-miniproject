import { NextResponse } from "next/server";
import { getStats } from "../../../lib/kafka";

// GET /api/logs/stats — return event stats + recent logs
export async function GET() {
    return NextResponse.json(getStats());
}
