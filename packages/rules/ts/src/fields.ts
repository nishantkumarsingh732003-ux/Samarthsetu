import bundleJson from "../../dist/rules.json";

export interface FieldSpec {
  name: string;
  kind: string;
  choices: string[] | null;
  question_i18n: Record<string, string>;
  priority: number;
}

/**
 * The profile contract, generated from setu_rules.profile by
 * scripts/regenerate_golden.py. Never hand-edit: change profile.py and regenerate,
 * so the two runtimes cannot disagree about what may be asked.
 */
export const FIELDS = (bundleJson as unknown as { fields: Record<string, FieldSpec> }).fields;

export const FIELD_NAMES = Object.keys(FIELDS);
