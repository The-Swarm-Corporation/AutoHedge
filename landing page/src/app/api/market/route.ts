import { getSnapshot } from "@/lib/engine";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const snapshot = await getSnapshot();
    return Response.json(snapshot, {
      headers: { "Cache-Control": "no-store, max-age=0" },
    });
  } catch (error) {
    console.error("market snapshot failed", error);
    return Response.json({ error: "market_unavailable" }, { status: 500 });
  }
}
