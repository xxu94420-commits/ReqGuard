import { useEffect, useState } from "react";
import { api } from "./api";

interface Metric {
  precision: number;
  recall: number;
  f1: number;
  tp: number;
  fp: number;
  fn: number;
}
interface Result {
  annotation_status: string;
  llm: string;
  test: {
    sample_count: number;
    micro: Metric;
    per_label: Record<string, Metric>;
    errors: { id: string; label: string; type: string }[];
  };
}
interface Analytics {
  sample_size: number;
  warning: string;
  correlations: Record<string, number | string>;
}
export function Benchmark() {
  const [result, setResult] = useState<Result>();
  const [analysis, setAnalysis] = useState<Analytics>();
  const [error, setError] = useState("");
  useEffect(() => {
    Promise.all([api<Result>("/benchmark"), api<Analytics>("/analytics")])
      .then(([r, a]) => {
        setResult(r);
        setAnalysis(a);
      })
      .catch((e) => setError(e.message));
  }, []);
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">EVALUATION / EXPLORATORY ANALYSIS</div>
          <h1>看见规则的能力，也看见它的局限</h1>
          <p>原创自建评测集，真实计算识别结果；无虚构模型准确率。</p>
        </div>
      </div>
      {error && <div className="error">{error}</div>}
      {result?.test ? (
        <>
          <div className="callout">
            {result.annotation_status}。{result.llm}
          </div>
          <div className="stats">
            {(["precision", "recall", "f1"] as const).map((key) => (
              <div key={key}>
                <span>Test micro {key.toUpperCase()}</span>
                <strong>
                  {(result.test.micro[key] * 100).toFixed(1)}
                  <small>%</small>
                </strong>
                <p>{result.test.sample_count} 条测试样本 / 多标签统计</p>
              </div>
            ))}
          </div>
          <section className="card padded">
            <h2>逐标签识别表现</h2>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>问题标签</th>
                    <th>Precision</th>
                    <th>Recall</th>
                    <th>F1</th>
                    <th>TP / FP / FN</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(result.test.per_label).map(([key, m]) => (
                    <tr key={key}>
                      <td>{key}</td>
                      <td>{m.precision}</td>
                      <td>{m.recall}</td>
                      <td>{m.f1}</td>
                      <td>
                        {m.tp} / {m.fp} / {m.fn}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <h3>误报与漏报记录</h3>
            {result.test.errors.map((e, i) => (
              <div className="error-row" key={i}>
                {e.id} · {e.label} · {e.type}
              </div>
            ))}
          </section>
        </>
      ) : (
        <section className="card padded">
          评测未生成，请运行 scripts/evaluate.py。
        </section>
      )}
      {analysis && (
        <section className="card padded">
          <h2>需求质量与交付指标</h2>
          <p>{analysis.warning}</p>
          <p>独立配对需求数：{analysis.sample_size}</p>
          <dl>
            {Object.entries(analysis.correlations).map(([key, v]) => (
              <div key={key}>
                <dt>{key}</dt>
                <dd>
                  {typeof v === "number"
                    ? v.toFixed(3)
                    : v === "insufficient_data"
                      ? "数据不足（少于 10 条）"
                      : "零方差，无法计算"}
                </dd>
              </div>
            ))}
          </dl>
        </section>
      )}
    </>
  );
}
