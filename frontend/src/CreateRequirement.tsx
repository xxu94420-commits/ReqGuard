import { useState } from "react";
import { api, type Requirement } from "./api";

interface Props {
  busy: boolean;
  run: (action: () => Promise<void>) => Promise<void>;
  onCreated: (id: string) => Promise<void>;
}
export function CreateRequirement({ busy, run, onCreated }: Props) {
  const [form, setForm] = useState({
    title: "",
    description: "",
    type: "feature",
    priority: "medium",
    source: "manual",
    owner: "",
    project: "",
  });
  const [issue, setIssue] = useState({ owner: "", repo: "", number: "" });
  function field(key: keyof typeof form, value: string) {
    setForm({ ...form, [key]: value });
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">CAPTURE / VERSION 01</div>
          <h1>记录需求的原始起点</h1>
          <p>原始描述永久保留。后续修改将生成新版本。</p>
        </div>
      </div>
      <div className="two-column">
        <section className="card padded">
          <h2>新建需求</h2>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              run(async () => {
                const r = await api<Requirement>("/requirements", form);
                await onCreated(r.id);
              });
            }}
          >
            <label>
              需求标题
              <input
                required
                maxLength={200}
                value={form.title}
                onChange={(e) => field("title", e.target.value)}
                placeholder="例如：运营订单导出支持日期筛选"
              />
            </label>
            <div className="form-row">
              <label>
                关联项目
                <input
                  required
                  maxLength={120}
                  value={form.project}
                  onChange={(e) => field("project", e.target.value)}
                />
              </label>
              <label>
                负责人
                <input
                  required
                  maxLength={120}
                  value={form.owner}
                  onChange={(e) => field("owner", e.target.value)}
                />
              </label>
            </div>
            <div className="form-row">
              <label>
                类型
                <select
                  value={form.type}
                  onChange={(e) => field("type", e.target.value)}
                >
                  <option value="feature">功能需求</option>
                  <option value="bug">缺陷修复</option>
                  <option value="technical">技术改进</option>
                </select>
              </label>
              <label>
                优先级
                <select
                  value={form.priority}
                  onChange={(e) => field("priority", e.target.value)}
                >
                  {["low", "medium", "high", "critical"].map((v) => (
                    <option key={v}>{v}</option>
                  ))}
                </select>
              </label>
            </div>
            <label>
              原始描述
              <textarea
                required
                rows={12}
                maxLength={30000}
                value={form.description}
                onChange={(e) => field("description", e.target.value)}
                placeholder="背景、用户与场景、目标、功能范围、验收标准、依赖、异常、风险及交付条件…"
              />
            </label>
            <button className="primary" disabled={busy}>
              保存原始需求
            </button>
          </form>
        </section>
        <div>
          <section className="card padded">
            <h2>导入公开 GitHub Issue</h2>
            <p>仅访问公开 Issue，不执行 GitHub 写操作。</p>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                run(async () => {
                  const r = await api<Requirement>("/github/import", {
                    ...issue,
                    number: Number(issue.number),
                  });
                  await onCreated(r.id);
                });
              }}
            >
              <label>
                仓库所有者
                <input
                  required
                  pattern="[A-Za-z0-9_.-]+"
                  value={issue.owner}
                  onChange={(e) =>
                    setIssue({ ...issue, owner: e.target.value })
                  }
                />
              </label>
              <label>
                仓库名称
                <input
                  required
                  pattern="[A-Za-z0-9_.-]+"
                  value={issue.repo}
                  onChange={(e) => setIssue({ ...issue, repo: e.target.value })}
                />
              </label>
              <label>
                Issue 编号
                <input
                  required
                  type="number"
                  min={1}
                  value={issue.number}
                  onChange={(e) =>
                    setIssue({ ...issue, number: e.target.value })
                  }
                />
              </label>
              <button disabled={busy}>导入并保留来源</button>
            </form>
          </section>
          <section className="callout">
            <h3>让证据支撑判断</h3>
            <p>
              质量分用于定位需要讨论的问题。缺少关键词可能是误报；所有建议都需要人来确认。
            </p>
          </section>
        </div>
      </div>
    </>
  );
}
