export interface Requirement {
  id: string;
  title: string;
  originalText: string;
  type: string;
  priority: string;
  owner: string;
  project: string;
  source: string;
  issueUrl?: string;
  createdAt: string;
}
export interface Version {
  id: string;
  number: number;
  text: string;
  reason: string;
  createdAt: string;
}
export interface Finding {
  id: string;
  dimension: string;
  kind: string;
  message: string;
  evidence: string;
  confidence: number;
  source: string;
  needs_confirmation: boolean;
}
export interface Suggestion {
  id: string;
  kind: string;
  text: string;
  source: string;
  needs_confirmation: boolean;
}
export interface Evaluation {
  quality_score: number;
  risk_level: string;
  mode: string;
  model?: string;
  prompt_version: string;
  latency_ms: number;
  fallback_reason?: string;
  findings: Finding[];
  suggestions: Suggestion[];
  dimension_scores: {
    id: string;
    name: string;
    score: number;
    weight: number;
    evidence: string[];
    confidence: number;
  }[];
}
export interface RecordItem {
  id: string;
  kind: string;
  versionId: string;
  createdAt: string;
  payload: unknown;
}
export interface Feedback {
  evaluationId: string;
  suggestionId: string;
  action: string;
  reason?: string;
  modifiedText?: string;
}
export interface Detail {
  requirement: Requirement;
  versions: Version[];
  records: RecordItem[];
}

export async function api<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(
    `/api${path}`,
    body === undefined
      ? undefined
      : {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
  );
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.message || `请求失败 (${response.status})`);
  }
  return response.json();
}

export function adoption(records: RecordItem[], versionId: string) {
  const latest = new Map<string, Feedback>();
  records
    .filter((r) => r.kind === "feedback" && r.versionId === versionId)
    .forEach((r) => {
      const f = r.payload as Feedback;
      latest.set(`${f.evaluationId}:${f.suggestionId}`, f);
    });
  const reviewed = latest.size;
  const accepted = [...latest.values()].filter(
    (f) => f.action !== "reject",
  ).length;
  return {
    reviewed,
    accepted,
    rate: reviewed ? Math.round((accepted / reviewed) * 100) : null,
    latest,
  };
}

export function lineDiff(before: string, after: string) {
  const oldLines = before.split("\n");
  const newLines = after.split("\n");
  // LCS retains unchanged repeated lines rather than set-membership guesses.
  if (oldLines.length * newLines.length > 100000)
    return { removed: oldLines, added: newLines };
  const dp = Array.from({ length: oldLines.length + 1 }, () =>
    new Array<number>(newLines.length + 1).fill(0),
  );
  for (let i = oldLines.length - 1; i >= 0; i--)
    for (let j = newLines.length - 1; j >= 0; j--)
      dp[i][j] =
        oldLines[i] === newLines[j]
          ? dp[i + 1][j + 1] + 1
          : Math.max(dp[i + 1][j], dp[i][j + 1]);
  const removed: string[] = [];
  const added: string[] = [];
  let i = 0;
  let j = 0;
  while (i < oldLines.length && j < newLines.length) {
    if (oldLines[i] === newLines[j]) {
      i++;
      j++;
    } else if (dp[i + 1][j] >= dp[i][j + 1]) removed.push(oldLines[i++]);
    else added.push(newLines[j++]);
  }
  return {
    removed: removed.concat(oldLines.slice(i)),
    added: added.concat(newLines.slice(j)),
  };
}
