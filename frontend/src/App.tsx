import { useCallback, useEffect, useState } from "react";
import {
  ShieldCheck,
  ListChecks,
  Plus,
  FlaskConical,
  ArrowUpRight,
  GitBranch,
  CheckCircle2,
  ChevronRight,
  Search,
} from "lucide-react";
import {
  api,
  adoption,
  type Detail,
  type Evaluation,
  type RecordItem,
  type Requirement,
} from "./api";
import { CreateRequirement } from "./CreateRequirement";
import { Workbench } from "./Workbench";
import { Benchmark } from "./Benchmark";

const tabs = [
  "质量评分",
  "证据与问题",
  "澄清问题",
  "修改对比",
  "验收与测试",
  "人工反馈",
  "版本历史",
  "质量复盘",
];

export default function App() {
  const [page, setPage] = useState("list");
  const [tab, setTab] = useState(0);
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [detail, setDetail] = useState<Detail>();
  const [version, setVersion] = useState(1);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [mode, setMode] = useState("rule-only");
  const refresh = useCallback(async () => {
    setRequirements(await api<Requirement[]>("/requirements"));
  }, []);
  useEffect(() => {
    refresh().catch((e) => setError(e.message));
  }, [refresh]);
  async function open(id: string, preserve = false) {
    const data = await api<Detail>(`/requirements/${id}`);
    setDetail(data);
    if (!preserve) {
      setVersion(data.versions.at(-1)!.number);
      setTab(0);
    }
    setPage("detail");
  }
  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (e) {
      setError(e instanceof Error ? e.message : "请求失败");
    } finally {
      setBusy(false);
    }
  }
  const selected = detail?.versions.find((v) => v.number === version);
  const evaluationRecord: RecordItem | undefined = detail?.records
    .filter((r) => r.kind === "evaluation" && r.versionId === selected?.id)
    .at(-1);
  const evaluation = evaluationRecord?.payload as Evaluation | undefined;
  const feedback =
    detail && selected ? adoption(detail.records, selected.id) : undefined;
  const filtered = requirements.filter((r) =>
    `${r.title} ${r.project} ${r.owner}`
      .toLowerCase()
      .includes(search.toLowerCase()),
  );

  return (
    <div className="shell">
      <aside className="sidebar">
        <a className="brand" href="#" onClick={() => setPage("list")}>
          <span className="brand-icon">
            <ShieldCheck size={25} />
          </span>
          <span>
            ReqGuard<small>需求质量工作台</small>
          </span>
        </a>
        <div className="nav-label">WORKSPACE</div>
        <button
          className={
            page === "list" || page === "detail" ? "nav active" : "nav"
          }
          onClick={() => setPage("list")}
        >
          <ListChecks size={18} />
          需求工作台<span>{requirements.length}</span>
        </button>
        <button
          className={page === "create" ? "nav active" : "nav"}
          onClick={() => setPage("create")}
        >
          <Plus size={18} />
          新建需求
        </button>
        <button
          className={page === "benchmark" ? "nav active" : "nav"}
          onClick={() => setPage("benchmark")}
        >
          <FlaskConical size={18} />
          评测集表现
        </button>
        <div className="sidebar-note">
          <GitBranch size={20} />
          <strong>每一次修改，都有迹可循</strong>
          <p>从需求版本到交付证据，保留完整审查链路。</p>
        </div>
        <div className="sidebar-foot">
          <span className="dot" />
          Rule-only 默认可用<small>ReqGuard / v0.1.0</small>
        </div>
      </aside>
      <main>
        <header className="topbar">
          <span>
            工作空间 <ChevronRight size={14} />{" "}
            {page === "benchmark" ? "评测集表现" : "需求工作台"}
          </span>
          <span className="pill">
            <ShieldCheck size={14} /> 人工复核 · 可追溯
          </span>
        </header>
        <div className="content">
          {error && (
            <div className="error" role="alert">
              {error}
              <button onClick={() => setError("")}>关闭</button>
            </div>
          )}
          {page === "list" && (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">REQUIREMENT INTELLIGENCE</div>
                  <h1>让清晰的需求，成为交付的起点</h1>
                  <p>发现缺失信息，验证验收条件，将判断与交付证据连接起来。</p>
                </div>
                <button className="primary" onClick={() => setPage("create")}>
                  <Plus size={17} />
                  新建需求
                </button>
              </div>
              <div className="stats">
                <div>
                  <span>需求总数</span>
                  <strong>
                    {requirements.length}
                    <small>项</small>
                  </strong>
                  <p>完整保留原文与版本</p>
                </div>
                <div>
                  <span>评估维度</span>
                  <strong>
                    14<small>项</small>
                  </strong>
                  <p>原创加权标准与交付门槛</p>
                </div>
                <div>
                  <span>评估方式</span>
                  <strong className="stat-text">规则 + 语义</strong>
                  <p>无 API Key 也可运行</p>
                </div>
                <div>
                  <span>GitHub 接入</span>
                  <strong className="stat-text">只读导入</strong>
                  <p>保留 Issue 来源与编号</p>
                </div>
              </div>
              <section className="card">
                <div className="card-head">
                  <div>
                    <h2>
                      需求清单 <small>{filtered.length}</small>
                    </h2>
                    <p>选择需求，开始评估、澄清与复盘</p>
                  </div>
                  <label className="search">
                    <Search size={16} />
                    <input
                      placeholder="搜索需求、项目或负责人"
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                    />
                  </label>
                </div>
                {filtered.length ? (
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>需求 / 项目</th>
                          <th>优先级</th>
                          <th>负责人</th>
                          <th>来源</th>
                          <th>创建日期</th>
                          <th />
                        </tr>
                      </thead>
                      <tbody>
                        {filtered.map((r) => (
                          <tr key={r.id} onClick={() => run(() => open(r.id))}>
                            <td>
                              <strong>{r.title}</strong>
                              <small>
                                {r.project} · {r.id.slice(0, 8)}
                              </small>
                            </td>
                            <td>
                              <span className={`priority ${r.priority}`}>
                                {r.priority.toUpperCase()}
                              </span>
                            </td>
                            <td>{r.owner}</td>
                            <td>{r.source}</td>
                            <td>
                              {new Date(r.createdAt).toLocaleDateString(
                                "zh-CN",
                              )}
                            </td>
                            <td>
                              <ArrowUpRight size={17} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="empty">
                    <ListChecks size={40} />
                    <h3>从第一条需求开始</h3>
                    <p>
                      创建需求或导入公开 GitHub Issue，运行有证据的质量评估。
                    </p>
                    <button onClick={() => setPage("create")}>
                      创建第一条需求 →
                    </button>
                  </div>
                )}
              </section>
              <div className="workflow">
                <span>
                  <CheckCircle2 size={18} />
                  需求版本
                </span>
                →<span>质量评估</span>→<span>人工复核</span>→
                <span>开发与证据</span>→<span>质量复盘</span>
              </div>
            </>
          )}
          {page === "create" && (
            <CreateRequirement
              busy={busy}
              run={run}
              onCreated={async (id) => {
                await refresh();
                await open(id);
              }}
            />
          )}
          {page === "benchmark" && <Benchmark />}
          {page === "detail" && detail && selected && (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">
                    {detail.requirement.project} / REQUIREMENT
                  </div>
                  <h1>{detail.requirement.title}</h1>
                  <p>
                    {detail.requirement.owner} ·{" "}
                    {detail.requirement.priority.toUpperCase()} ·{" "}
                    {detail.requirement.source}
                    {detail.requirement.issueUrl && (
                      <>
                        {" "}
                        ·{" "}
                        <a
                          href={detail.requirement.issueUrl}
                          target="_blank"
                          rel="noreferrer"
                        >
                          原始 Issue ↗
                        </a>
                      </>
                    )}
                  </p>
                </div>
                <div className="actions">
                  <select
                    aria-label="需求版本"
                    value={version}
                    onChange={(e) => setVersion(Number(e.target.value))}
                  >
                    {detail.versions.map((v) => (
                      <option key={v.id} value={v.number}>
                        版本 v{v.number}
                      </option>
                    ))}
                  </select>
                  <select
                    aria-label="评估模式"
                    value={mode}
                    onChange={(e) => setMode(e.target.value)}
                  >
                    <option value="rule-only">Rule-only</option>
                    <option value="llm-enhanced">LLM-enhanced</option>
                  </select>
                  <button
                    disabled={busy}
                    className="primary"
                    onClick={() =>
                      run(async () => {
                        await api(
                          `/requirements/${detail.requirement.id}/evaluations`,
                          { version, mode },
                        );
                        await open(detail.requirement.id, true);
                      })
                    }
                  >
                    {busy ? "处理中…" : "运行质量评估"}
                  </button>
                </div>
              </div>
              <nav className="tabs">
                {tabs.map((name, i) => (
                  <button
                    key={name}
                    className={tab === i ? "selected" : ""}
                    onClick={() => setTab(i)}
                  >
                    {name}
                  </button>
                ))}
              </nav>
              <Workbench
                detail={detail}
                selected={selected}
                evaluation={evaluation}
                evaluationRecord={evaluationRecord}
                feedback={feedback}
                tab={tab}
                busy={busy}
                run={run}
                reload={() => open(detail.requirement.id, true)}
                onVersion={setVersion}
              />
            </>
          )}
        </div>
      </main>
    </div>
  );
}
