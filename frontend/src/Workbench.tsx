import { useState } from "react";
import {
  api,
  lineDiff,
  type Detail,
  type Version,
  type Evaluation,
  type RecordItem,
  type adoption,
} from "./api";
import { Delivery } from "./Delivery";

interface Props {
  detail: Detail;
  selected: Version;
  evaluation?: Evaluation;
  evaluationRecord?: RecordItem;
  feedback?: ReturnType<typeof adoption>;
  tab: number;
  busy: boolean;
  run: (action: () => Promise<void>) => Promise<void>;
  reload: () => Promise<void>;
  onVersion: (n: number) => void;
}

export function Workbench({
  detail,
  selected,
  evaluation: ev,
  evaluationRecord: er,
  feedback,
  tab,
  busy,
  run,
  reload,
  onVersion,
}: Props) {
  const [revision, setRevision] = useState("");
  const [reason, setReason] = useState("");
  const [review, setReview] = useState<
    Record<string, { action: string; reason: string; modifiedText: string }>
  >({});
  const path = `/requirements/${detail.requirement.id}`;
  const previous =
    detail.versions.find((v) => v.number === selected.number - 1) || selected;
  const diff = lineDiff(previous.text, selected.text);
  const suggestions = ev?.suggestions || [];
  const report = detail.records
    .filter((r) => r.kind === "retrospective" && r.versionId === selected.id)
    .at(-1)?.payload as { markdown: string } | undefined;
  const saveVersion = (text: string) =>
    run(async () => {
      const created = await api<Version>(`${path}/versions`, {
        text,
        reason: reason || "人工确认建议后修改",
        baseVersion: detail.versions.at(-1)!.number,
      });
      await reload();
      onVersion(created.number);
      setRevision("");
      setReason("");
    });
  if ([0, 1, 2, 4, 5].includes(tab) && !ev)
    return (
      <div className="card empty">
        <h3>当前版本尚未评估</h3>
        <p>点击“运行质量评估”，生成可追溯的评分、问题与建议。</p>
      </div>
    );
  return (
    <>
      {tab === 0 && ev && (
        <>
          <div className="score-layout">
            <section className="card score-card">
              <div className="eyebrow">WEIGHTED QUALITY SCORE</div>
              <div className="score-number">
                {ev.quality_score}
                <span>/ 100</span>
              </div>
              <span className={`risk ${ev.risk_level}`}>
                {
                  (
                    {
                      high: "高风险",
                      medium: "中风险",
                      low: "低风险",
                    } as Record<string, string>
                  )[ev.risk_level]
                }
              </span>
              <p>评分是规则审查基准，建议需要人工确认。</p>
            </section>
            <section className="card padded">
              <h2>评估运行信息</h2>
              <dl>
                <dt>实际模式</dt>
                <dd>{ev.mode}</dd>
                <dt>模型</dt>
                <dd>{ev.model || "未调用模型"}</dd>
                <dt>Prompt 版本</dt>
                <dd>{ev.prompt_version}</dd>
                <dt>模型响应时间</dt>
                <dd>{ev.latency_ms} ms</dd>
                <dt>已复核建议采纳率</dt>
                <dd>
                  {feedback?.rate === null ? "尚未复核" : `${feedback?.rate}%`}
                </dd>
              </dl>
              {ev.fallback_reason && (
                <div className="callout">
                  已降级至规则模式：{ev.fallback_reason}
                </div>
              )}
            </section>
          </div>
          <section className="card padded">
            <h2>14 维质量剖面</h2>
            <div className="dimensions">
              {ev.dimension_scores.map((d) => (
                <div className="dimension" key={d.id}>
                  <div>
                    <strong>{d.name}</strong>
                    <span>{d.score} / 5</span>
                  </div>
                  <progress max={5} value={d.score} />
                  <small>
                    权重 {d.weight}% · 置信度 {Math.round(d.confidence * 100)}%
                  </small>
                  <p>{d.evidence.join("；") || "未发现匹配证据，待人工补充"}</p>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
      {tab === 1 && (
        <section className="card padded">
          <h2>判断依据与待确认问题</h2>
          <p>缺少词语不等于缺少业务信息；语义结论不是事实。</p>
          <div className="findings">
            {ev?.findings.map((f) => (
              <article key={f.id}>
                <div className="finding-meta">
                  <span className="pill">{f.kind}</span>
                  <span>
                    {f.source} · {Math.round(f.confidence * 100)}% · 待人工确认
                  </span>
                </div>
                <h3>{f.message}</h3>
                <blockquote>{f.evidence}</blockquote>
              </article>
            ))}
          </div>
        </section>
      )}
      {tab === 2 && (
        <section className="card padded">
          <h2>把缺口变成可回答的问题</h2>
          <p>与业务方核对后，在“修改对比”中保存新版本。</p>
          {suggestions
            .filter((s) => s.kind === "clarification")
            .map((s, i) => (
              <article className="question" key={s.id}>
                <span>{String(i + 1).padStart(2, "0")}</span>
                <div>
                  <strong>{s.text}</strong>
                  <small>{s.source} · 待人工确认</small>
                </div>
              </article>
            ))}
        </section>
      )}
      {tab === 3 && (
        <>
          <section className="card padded">
            <h2>
              版本 v{previous.number} → v{selected.number}
            </h2>
            <div className="two-column diff">
              <div>
                <h3>修改前</h3>
                <pre>{previous.text}</pre>
              </div>
              <div>
                <h3>修改后</h3>
                <pre>{selected.text}</pre>
              </div>
            </div>
            <div className="two-column">
              <div className="removed">
                <strong>移除的行</strong>
                <pre>{diff.removed.join("\n") || "无"}</pre>
              </div>
              <div className="added">
                <strong>新增的行</strong>
                <pre>{diff.added.join("\n") || "无"}</pre>
              </div>
            </div>
          </section>
          <section className="card padded">
            <h2>形成下一版需求</h2>
            <p>
              基于最新版本 v{detail.versions.at(-1)!.number}{" "}
              追加；不会覆盖原文。
            </p>
            <button
              onClick={() =>
                setRevision(
                  suggestions.find((s) => s.kind === "revision")?.text ||
                    selected.text,
                )
              }
            >
              载入改写建议 / 当前原文
            </button>
            <label>
              人工确认后的需求
              <textarea
                rows={12}
                value={revision}
                onChange={(e) => setRevision(e.target.value)}
                maxLength={30000}
              />
            </label>
            <label>
              变更原因
              <input
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                maxLength={500}
              />
            </label>
            <button
              className="primary"
              disabled={busy || !revision.trim() || !reason.trim()}
              onClick={() => saveVersion(revision)}
            >
              保存为新版本
            </button>
          </section>
        </>
      )}
      {tab === 4 && (
        <section className="card padded">
          <h2>验收标准与测试场景</h2>
          <p>
            规则模式提供待填模板；LLM
            模式生成的具体建议仍需确认。接受反馈不会自动修改需求，需另存新版本。
          </p>
          {suggestions
            .filter((s) => ["acceptance", "test"].includes(s.kind))
            .map((s) => (
              <article className="suggestion" key={s.id}>
                <span className="pill">
                  {s.kind === "acceptance" ? "Given / When / Then" : "测试场景"}
                </span>
                <pre>{s.text}</pre>
                <small>{s.source} · 待人工确认</small>
              </article>
            ))}
        </section>
      )}
      {tab === 5 && (
        <section className="card padded">
          <h2>人工建议复核</h2>
          <p>
            已复核 {feedback?.reviewed} 条 · 采纳/修改 {feedback?.accepted} 条 ·
            采纳率 {feedback?.rate === null ? "N/A" : `${feedback?.rate}%`}
            。每次复核追加记录，以最新决定统计。
          </p>
          {suggestions.map((s) => {
            const value = review[s.id] || {
              action: "accept",
              reason: "",
              modifiedText: s.text,
            };
            const latest = feedback?.latest.get(`${er!.id}:${s.id}`);
            return (
              <article className="suggestion" key={s.id}>
                <div className="finding-meta">
                  <span className="pill">{s.kind}</span>
                  <small>
                    {latest ? `最近决定：${latest.action}` : "尚未复核"}
                  </small>
                </div>
                <pre>{s.text}</pre>
                <label>
                  复核决定
                  <select
                    value={value.action}
                    onChange={(e) =>
                      setReview({
                        ...review,
                        [s.id]: { ...value, action: e.target.value },
                      })
                    }
                  >
                    <option value="accept">接受</option>
                    <option value="reject">拒绝</option>
                    <option value="modify">修改</option>
                  </select>
                </label>
                {value.action === "modify" && (
                  <label>
                    修改内容
                    <textarea
                      value={value.modifiedText}
                      onChange={(e) =>
                        setReview({
                          ...review,
                          [s.id]: { ...value, modifiedText: e.target.value },
                        })
                      }
                    />
                  </label>
                )}
                <label>
                  原因{value.action === "reject" ? "（必填）" : "（可选）"}
                  <input
                    maxLength={2000}
                    value={value.reason}
                    onChange={(e) =>
                      setReview({
                        ...review,
                        [s.id]: { ...value, reason: e.target.value },
                      })
                    }
                  />
                </label>
                <button
                  disabled={
                    busy ||
                    (value.action === "reject" && !value.reason.trim()) ||
                    (value.action === "modify" && !value.modifiedText.trim())
                  }
                  onClick={() =>
                    run(async () => {
                      await api(`${path}/feedback`, {
                        evaluationId: er!.id,
                        suggestionId: s.id,
                        ...value,
                      });
                      await reload();
                    })
                  }
                >
                  保存复核记录
                </button>
              </article>
            );
          })}
          <h3>该版本的人工修改记录</h3>
          {detail.records
            .filter((r) => r.kind === "feedback" && r.versionId === selected.id)
            .map((r) => (
              <pre key={r.id}>
                {r.createdAt}\n{JSON.stringify(r.payload, null, 2)}
              </pre>
            ))}
        </section>
      )}
      {tab === 6 && (
        <section className="card padded">
          <h2>不可覆盖的版本历史</h2>
          {detail.versions.map((v) => (
            <article className="history" key={v.id}>
              <span>v{v.number}</span>
              <div>
                <h3>{v.reason}</h3>
                <small>{new Date(v.createdAt).toLocaleString("zh-CN")}</small>
                <p>
                  {v.text.slice(0, 160)}
                  {v.text.length > 160 && "…"}
                </p>
                <button onClick={() => onVersion(v.number)}>查看此版本</button>
              </div>
            </article>
          ))}
        </section>
      )}
      {tab === 7 && (
        <>
          <Delivery
            path={path}
            version={selected.number}
            busy={busy}
            run={run}
            reload={reload}
          />
          <section className="card padded">
            <div className="card-head">
              <div>
                <h2>质量复盘报告</h2>
                <p>冻结当前版本证据、人工反馈及计划与实际交付。</p>
              </div>
              <button
                className="primary"
                disabled={busy}
                onClick={() =>
                  run(async () => {
                    await api(
                      `${path}/retrospectives?version=${selected.number}`,
                      {},
                    );
                    await reload();
                  })
                }
              >
                生成复盘快照
              </button>
            </div>
            {report ? (
              <>
                <pre className="report">{report.markdown}</pre>
                <button
                  onClick={() => {
                    const url = URL.createObjectURL(
                      new Blob([report.markdown], { type: "text/markdown" }),
                    );
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `reqguard-v${selected.number}-retro.md`;
                    a.click();
                    URL.revokeObjectURL(url);
                  }}
                >
                  下载 Markdown
                </button>
              </>
            ) : (
              <p>尚无报告。先记录开发计划和交付证据，再生成复盘。</p>
            )}
          </section>
        </>
      )}
    </>
  );
}
