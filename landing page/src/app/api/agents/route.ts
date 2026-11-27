import { listAgents } from "@/lib/engine";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const url = new URL(request.url);
  try {
    const result = await listAgents({
      q: url.searchParams.get("q") ?? undefined,
      focus: url.searchParams.get("focus") ?? undefined,
      status: url.searchParams.get("status") ?? undefined,
      sort: url.searchParams.get("sort") ?? undefined,
      page: Number(url.searchParams.get("page") ?? "1") || 1,
      perPage: Number(url.searchParams.get("perPage") ?? "12") || 12,
    });
    return Response.json(result, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    console.error("agent list failed", error);
    return Response.json({ error: "agents_unavailable" }, { status: 500 });
  }
}
