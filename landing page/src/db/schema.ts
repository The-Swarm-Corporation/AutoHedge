import {
  bigint,
  doublePrecision,
  index,
  integer,
  pgTable,
  serial,
  text,
  timestamp,
  uniqueIndex,
} from "drizzle-orm/pg-core";

export const instruments = pgTable(
  "instruments",
  {
    id: serial("id").primaryKey(),
    symbol: text("symbol").notNull(),
    name: text("name").notNull(),
    market: text("market").notNull(),
    kind: text("kind").notNull(),
    currency: text("currency").notNull(),
    unit: text("unit").notNull(),
    decimals: integer("decimals").notNull().default(2),
    price: doublePrecision("price").notNull(),
    prevClose: doublePrecision("prev_close").notNull(),
    dayOpen: doublePrecision("day_open").notNull(),
    dayHigh: doublePrecision("day_high").notNull(),
    dayLow: doublePrecision("day_low").notNull(),
    volume: bigint("volume", { mode: "number" }).notNull().default(0),
    volatility: doublePrecision("volatility").notNull().default(0.0006),
    updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (table) => [uniqueIndex("instruments_symbol_uidx").on(table.symbol)],
);

export const candles = pgTable(
  "candles",
  {
    id: serial("id").primaryKey(),
    instrumentId: integer("instrument_id").notNull(),
    price: doublePrecision("price").notNull(),
    volume: integer("volume").notNull().default(0),
    ts: timestamp("ts", { withTimezone: true }).notNull().defaultNow(),
  },
  (table) => [index("candles_instrument_ts_idx").on(table.instrumentId, table.ts)],
);

export const agents = pgTable(
  "agents",
  {
    id: serial("id").primaryKey(),
    codename: text("codename").notNull(),
    callsign: text("callsign").notNull(),
    role: text("role").notNull(),
    focus: text("focus").notNull(),
    model: text("model").notNull(),
    status: text("status").notNull().default("active"),
    accuracy: doublePrecision("accuracy").notNull().default(60),
    pnl: doublePrecision("pnl").notNull().default(0),
    signalsCount: integer("signals_count").notNull().default(0),
    latencyMs: integer("latency_ms").notNull().default(120),
    hue: integer("hue").notNull().default(42),
    specialty: text("specialty").notNull(),
    generation: integer("generation").notNull().default(1),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (table) => [
    uniqueIndex("agents_codename_uidx").on(table.codename),
    index("agents_focus_idx").on(table.focus),
  ],
);

export const signals = pgTable(
  "signals",
  {
    id: serial("id").primaryKey(),
    agentId: integer("agent_id").notNull(),
    symbol: text("symbol").notNull(),
    market: text("market").notNull(),
    direction: text("direction").notNull(),
    confidence: integer("confidence").notNull(),
    timeframe: text("timeframe").notNull(),
    rationale: text("rationale").notNull(),
    entry: doublePrecision("entry").notNull(),
    target: doublePrecision("target").notNull(),
    stop: doublePrecision("stop").notNull(),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (table) => [index("signals_created_idx").on(table.createdAt)],
);

export const agentEvents = pgTable(
  "agent_events",
  {
    id: serial("id").primaryKey(),
    agentId: integer("agent_id").notNull(),
    kind: text("kind").notNull(),
    message: text("message").notNull(),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (table) => [index("agent_events_created_idx").on(table.createdAt)],
);
