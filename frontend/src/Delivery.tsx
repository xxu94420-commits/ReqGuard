import { useState } from "react";
import { api } from "./api";

interface Props {
  path: string;
  version: number;
  busy: boolean;
  run: (action: () => Promise<void>) => Promise<void>;
  reload: () => Promise<void>;
}
export function Delivery({ path, version, busy, run, reload }: Props) {
  const [task, setTask] = useState({
    taskId: "",
    plan: "",
    plannedDelivery: "",
  });
  const [delivery, setDelivery] = useState({
    task_id: "",
    issue_id: "",
    delivery_cycle: 0,
    ai_assisted: false,
    test_passed: false,
    defect_count: 0,
    rework_count: 0,
    delivery_timestamp: "",
    commit: "",
    pull_request: "",
    test_summary: "",
    defects: "",
    rework_reason: "",
  });
  return (
    <section className="card padded">
      <h2>开发任务与交付证据 · v{version}</h2>
      <p>保存实际证据，未提供的信息不会由模型补造。</p>
      <div className="two-column">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            run(async () => {
              await api(`${path}/tasks`, { version, ...task });
              await reload();
            });
          }}
        >
          <h3>开发计划</h3>
          <label>
            任务 ID
            <input
              required
              maxLength={120}
              value={task.taskId}
              onChange={(e) => setTask({ ...task, taskId: e.target.value })}
            />
          </label>
          <label>
            计划交付日期
            <input
              type="date"
              required
              value={task.plannedDelivery}
              onChange={(e) =>
                setTask({ ...task, plannedDelivery: e.target.value })
              }
            />
          </label>
          <label>
            计划范围
            <textarea
              required
              maxLength={3000}
              value={task.plan}
              onChange={(e) => setTask({ ...task, plan: e.target.value })}
            />
          </label>
          <button disabled={busy}>保存任务计划</button>
        </form>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            run(async () => {
              await api(`${path}/delivery`, {
                version,
                ...delivery,
                delivery_timestamp: new Date(
                  delivery.delivery_timestamp,
                ).toISOString(),
              });
              await reload();
            });
          }}
        >
          <h3>实际交付 / DevFlow 数据</h3>
          <label>
            对应任务 ID
            <input
              required
              maxLength={120}
              value={delivery.task_id}
              onChange={(e) =>
                setDelivery({ ...delivery, task_id: e.target.value })
              }
            />
          </label>
          <label>
            Issue ID
            <input
              maxLength={120}
              value={delivery.issue_id}
              onChange={(e) =>
                setDelivery({ ...delivery, issue_id: e.target.value })
              }
            />
          </label>
          <label>
            实际交付时间
            <input
              type="datetime-local"
              required
              value={delivery.delivery_timestamp}
              onChange={(e) =>
                setDelivery({ ...delivery, delivery_timestamp: e.target.value })
              }
            />
          </label>
          <div className="form-row">
            {(["delivery_cycle", "defect_count", "rework_count"] as const).map(
              (key, i) => (
                <label key={key}>
                  {["周期（小时）", "缺陷数", "返工次数"][i]}
                  <input
                    type="number"
                    required
                    min={0}
                    step={key === "delivery_cycle" ? "0.1" : "1"}
                    value={delivery[key]}
                    onChange={(e) =>
                      setDelivery({
                        ...delivery,
                        [key]: Number(e.target.value),
                      })
                    }
                  />
                </label>
              ),
            )}
          </div>
          <div className="form-row">
            <label className="checkbox">
              <input
                type="checkbox"
                checked={delivery.ai_assisted}
                onChange={(e) =>
                  setDelivery({ ...delivery, ai_assisted: e.target.checked })
                }
              />
              AI 辅助开发
            </label>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={delivery.test_passed}
                onChange={(e) =>
                  setDelivery({ ...delivery, test_passed: e.target.checked })
                }
              />
              测试通过
            </label>
          </div>
          {(
            [
              "commit",
              "pull_request",
              "test_summary",
              "defects",
              "rework_reason",
            ] as const
          ).map((key, i) => (
            <label key={key}>
              {
                [
                  "Commit 链接或 SHA",
                  "PR 链接",
                  "测试结果摘要",
                  "缺陷记录",
                  "人工记录的返工原因",
                ][i]
              }
              <input
                maxLength={
                  key === "commit" || key === "pull_request" ? 500 : 2000
                }
                value={delivery[key]}
                onChange={(e) =>
                  setDelivery({ ...delivery, [key]: e.target.value })
                }
              />
            </label>
          ))}
          <button disabled={busy}>保存交付证据</button>
        </form>
      </div>
    </section>
  );
}
