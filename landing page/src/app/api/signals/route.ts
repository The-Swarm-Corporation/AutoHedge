import { getRecentSignals } from "@/lib/engine";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const limit = Math.min(80, Math.max(1, Number(url.searchParams.get("limit") ?? "24") || 24));
  try {
    const signals = await getRecentSignals(limit);
    return Response.json({ signals }, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    console.error("signals failed", error);
    return Response.json({ error: "signals_unavailable" }, { status: 500 });
  }
}
