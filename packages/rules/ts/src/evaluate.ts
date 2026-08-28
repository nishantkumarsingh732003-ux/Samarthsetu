import type { Node, Profile, Ternary } from "./types";

export const UNKNOWN = "UNKNOWN" as const;

/**
 * Interprets the same compiled expression tree the Python engine uses, with the same
 * three-valued (Kleene) logic. The tree is produced once by the Python compiler and
 * shipped as dist/rules.json, so neither runtime parses the DSL and the two cannot
 * drift in how they read a rule.
 */
export function evaluateNode(node: Node, profile: Profile): Ternary {
  switch (node.op) {
    case "and": {
      let sawUnknown = false;
      for (const arg of node.args) {
        const value = evaluateNode(arg, profile);
        if (value === false) return false; // False dominates AND
        if (value === UNKNOWN) sawUnknown = true;
      }
      return sawUnknown ? UNKNOWN : true;
    }
    case "or": {
      let sawUnknown = false;
      for (const arg of node.args) {
        const value = evaluateNode(arg, profile);
        if (value === true) return true; // True dominates OR
        if (value === UNKNOWN) sawUnknown = true;
      }
      return sawUnknown ? UNKNOWN : false;
    }
    case "not": {
      const value = evaluateNode(node.arg, profile);
      return value === UNKNOWN ? UNKNOWN : !value;
    }
    case "cmp":
      return compare(node, profile);
    default:
      throw new Error(`cannot evaluate node of type ${(node as Node).op} as a condition`);
  }
}

function operand(node: Node, profile: Profile): unknown {
  switch (node.op) {
    case "field": {
      const value = profile[node.name];
      return value === undefined ? null : value;
    }
    case "const":
      return node.value;
    case "list":
      return node.items.map((item) => operand(item, profile));
    default:
      throw new Error(`cannot use node of type ${(node as Node).op} as an operand`);
  }
}

function compare(node: Extract<Node, { op: "cmp" }>, profile: Profile): Ternary {
  const left = operand(node.left, profile);
  const right = operand(node.right, profile);

  if (node.operator === "in" || node.operator === "not in") {
    if (left === null || right === null) return UNKNOWN;
    const found = (right as unknown[]).includes(left);
    return node.operator === "in" ? found : !found;
  }

  // An unknown operand makes the comparison unknown, never false. This is what keeps a
  // half-finished form from reading as "you do not qualify".
  if (left === null || right === null) return UNKNOWN;

  switch (node.operator) {
    case "==":
      return left === right;
    case "!=":
      return left !== right;
    case "<":
      return (left as number) < (right as number);
    case "<=":
      return (left as number) <= (right as number);
    case ">":
      return (left as number) > (right as number);
    case ">=":
      return (left as number) >= (right as number);
    default:
      throw new Error(`unknown comparison operator ${node.operator}`);
  }
}

export function referencedFields(node: Node): string[] {
  switch (node.op) {
    case "field":
      return [node.name];
    case "and":
    case "or":
      return node.args.flatMap(referencedFields);
    case "not":
      return referencedFields(node.arg);
    case "cmp":
      return [...referencedFields(node.left), ...referencedFields(node.right)];
    case "list":
      return node.items.flatMap(referencedFields);
    default:
      return [];
  }
}
