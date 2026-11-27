import { TerminalShell } from "@/components/TerminalShell";
import { getSnapshot } from "@/lib/engine";
import type { MarketSnapshot } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  let snapshot: MarketSnapshot | null = null;

  try {
    snapshot = await getSnapshot();
  } catch (error) {
    console.error("terminal bootstrap failed", error);
  }

  if (!snapshot) {
    return <BootFallback />;
  }

  return <TerminalShell initialSnapshot={snapshot} />;
}

function BootFallback() {
  return (
    <main className="grid min-h-screen place-items-center px-6">
      <section className="panel panel-gold w-full max-w-lg rounded-xl px-6 py-8 text-center">
        <div className="mx-auto grid h-12 w-12 place-items-center rounded-full border border-gold/40 bg-gold/10 font-mono text-lg text-gold">
          Ω
        </div>
        <h1 className="mt-4 font-mono text-lg tracking-[0.16em] text-gold uppercase">Synod core booting</h1>
        <p className="mt-2 font-mono text-[10.5px] leading-relaxed tracking-[0.06em] text-muted">
          The 550-agent swarm is provisioning its Postgres memory. Refresh in a moment — the terminal will sync
          automatically once the agent grid is online.
        </p>
        <div className="mt-4 flex items-center justify-center gap-2 font-mono text-[9px] tracking-[0.14em] text-muted uppercase">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-gold" />
          awaiting database handshake
        </div>
      </section>
    </main>
  );
}
