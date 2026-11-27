import { runSwarmScan } from "@/lib/engine";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  let count = 4;
  try {
    const body = (await request.json()) as { count?: number } | null;
    if (body && typeof body.count === "number") count = body.count;
  } catch {
    // body is optional
  }

  try {
    const result = await runSwarmScan(count);
    return Response.json(result, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    console.error("swarm scan failed", error);
    return Response.json({ error: "scan_failed" }, { status: 500 });
  }
}
