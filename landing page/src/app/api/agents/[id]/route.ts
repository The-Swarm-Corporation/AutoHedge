import { getAgentDetail } from "@/lib/engine";

export const dynamic = "force-dynamic";

export async function GET(_request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  const agentId = Number(id);
  if (!Number.isFinite(agentId)) {
    return Response.json({ error: "invalid_agent_id" }, { status: 400 });
  }

  try {
    const detail = await getAgentDetail(agentId);
    if (!detail) return Response.json({ error: "not_found" }, { status: 404 });
    return Response.json(detail, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    console.error("agent detail failed", error);
    return Response.json({ error: "agent_unavailable" }, { status: 500 });
  }
}
