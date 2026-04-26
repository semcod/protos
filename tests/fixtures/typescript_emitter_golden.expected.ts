// =============================================================================
// AUTO-GENERATED FILE - DO NOT EDIT MANUALLY
// Generated from golden on <TIMESTAMP>
// Run: python demo_codegen.py
// =============================================================================

// =============================================================================
// ENUMS
// =============================================================================

export enum GoldenSeverity {
  LOW = "low",
  HIGH = "high",
}

// =============================================================================
// MODELS
// =============================================================================

export interface GoldenChild {
  score: number;
}

export interface GoldenModel {
  device_id: string;
  severity: GoldenSeverity;
  child: GoldenChild;
  tags: string[];
  props: Record<string, number>;
  either: string | number;
  note?: string | null;
  retries?: number;
}

// =============================================================================
// ALIASES
// =============================================================================

export type GoldenModelDto = GoldenModel;
