package io.reqguard;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.*;
import java.time.*;
import java.util.*;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

@Service
public class LifecycleService {
  private final RequirementRepository requirements;
  private final VersionRepository versions;
  private final RecordRepository records;
  private final ObjectMapper mapper;
  private final AiGateway ai;

  public LifecycleService(
      RequirementRepository requirements,
      VersionRepository versions,
      RecordRepository records,
      ObjectMapper mapper,
      AiGateway ai) {
    this.requirements = requirements;
    this.versions = versions;
    this.records = records;
    this.mapper = mapper;
    this.ai = ai;
  }

  public Requirement require(String id) {
    return requirements.findById(id).orElseThrow(() -> error(404, "需求不存在"));
  }

  public List<Requirement> list() {
    return requirements.findAll().stream()
        .sorted(Comparator.comparing((Requirement r) -> r.createdAt).reversed())
        .toList();
  }

  @Transactional
  public Requirement create(Requests.Create input) {
    Requirement r = new Requirement();
    r.title = input.title();
    r.originalText = input.description();
    r.type = input.type();
    r.priority = input.priority();
    r.source = input.source();
    r.owner = input.owner();
    r.project = input.project();
    r.issueUrl = input.issueUrl();
    r.issueId = input.issueId();
    requirements.save(r);
    append(r.id, input.description(), "原始需求", 1);
    return r;
  }

  private RequirementVersion append(String id, String text, String reason, int number) {
    RequirementVersion v = new RequirementVersion();
    v.requirementId = id;
    v.text = text;
    v.reason = reason;
    v.number = number;
    return versions.save(v);
  }

  @Transactional
  public RequirementVersion revise(String id, Requests.Revise input) {
    requirements.lockById(id).orElseThrow(() -> error(404, "需求不存在"));
    var history = versions.findByRequirementIdOrderByNumberAsc(id);
    int current = history.get(history.size() - 1).number;
    if (input.baseVersion() != current) throw error(409, "版本已变化，请重新加载后修改");
    return append(id, input.text(), input.reason(), current + 1);
  }

  public RequirementVersion version(String id, int number) {
    require(id);
    return versions.findByRequirementIdOrderByNumberAsc(id).stream()
        .filter(v -> v.number == number)
        .findFirst()
        .orElseThrow(() -> error(404, "版本不存在"));
  }

  public Map<String, Object> detail(String id) {
    var r = require(id);
    var history = versions.findByRequirementIdOrderByNumberAsc(id);
    var rows = records.findByRequirementIdOrderByCreatedAtAsc(id).stream().map(this::view).toList();
    return Map.of("requirement", r, "versions", history, "records", rows);
  }

  public Map<String, Object> evaluate(String id, Requests.Evaluate input) {
    var r = require(id);
    var v = version(id, input.version());
    JsonNode result = ai.evaluate(v.text, r.priority, input.mode());
    if (result == null || !result.has("quality_score") || !result.path("suggestions").isArray())
      throw error(502, "AI 服务返回无效结果");
    return view(save(id, v.id, "evaluation", result));
  }

  private LifecycleRecord save(String id, String versionId, String kind, Object payload) {
    LifecycleRecord row = new LifecycleRecord();
    row.requirementId = id;
    row.versionId = versionId;
    row.kind = kind;
    try {
      row.payload = mapper.writeValueAsString(payload);
    } catch (JsonProcessingException e) {
      throw new IllegalStateException(e);
    }
    return records.save(row);
  }

  private JsonNode payload(LifecycleRecord row) {
    try {
      return mapper.readTree(row.payload);
    } catch (JsonProcessingException e) {
      throw new IllegalStateException(e);
    }
  }

  private Map<String, Object> view(LifecycleRecord row) {
    return Map.of(
        "id",
        row.id,
        "versionId",
        row.versionId,
        "kind",
        row.kind,
        "createdAt",
        row.createdAt,
        "payload",
        payload(row));
  }

  @Transactional
  public Map<String, Object> feedback(String id, Requests.Feedback input) {
    requirements.lockById(id).orElseThrow(() -> error(404, "需求不存在"));
    var evaluation =
        records
            .findById(input.evaluationId())
            .filter(r -> r.requirementId.equals(id) && r.kind.equals("evaluation"))
            .orElseThrow(() -> error(404, "评估不存在"));
    boolean exists = false;
    for (var suggestion : payload(evaluation).path("suggestions"))
      if (suggestion.path("id").asText().equals(input.suggestionId())) exists = true;
    if (!exists) throw error(400, "建议不属于指定评估");
    if (input.action().equals("reject") && (input.reason() == null || input.reason().isBlank()))
      throw error(400, "拒绝时必须填写原因");
    if (input.action().equals("modify")
        && (input.modifiedText() == null || input.modifiedText().isBlank()))
      throw error(400, "修改时必须填写修改内容");
    return view(save(id, evaluation.versionId, "feedback", input));
  }

  public Map<String, Object> task(String id, Requests.Task input) {
    var v = version(id, input.version());
    try {
      LocalDate.parse(input.plannedDelivery());
    } catch (DateTimeException e) {
      throw error(400, "计划交付日期必须为 YYYY-MM-DD");
    }
    return view(save(id, v.id, "task", input));
  }

  public Map<String, Object> delivery(String id, Requests.Delivery input) {
    var v = version(id, input.version());
    try {
      Instant.parse(input.delivery_timestamp());
    } catch (DateTimeException e) {
      throw error(400, "交付时间必须为 ISO UTC 时间");
    }
    boolean exists =
        records.findByRequirementIdOrderByCreatedAtAsc(id).stream()
            .anyMatch(
                r ->
                    r.kind.equals("task")
                        && r.versionId.equals(v.id)
                        && payload(r).path("taskId").asText().equals(input.task_id()));
    if (!exists) throw error(400, "请先在该版本创建对应开发任务");
    return view(save(id, v.id, "delivery", input));
  }

  private Map<String, JsonNode> latestFeedback(List<LifecycleRecord> rows) {
    Map<String, JsonNode> latest = new LinkedHashMap<>();
    for (var row : rows)
      if (row.kind.equals("feedback")) {
        var p = payload(row);
        latest.put(p.path("evaluationId").asText() + ":" + p.path("suggestionId").asText(), p);
      }
    return latest;
  }

  public Map<String, Object> export(String id, int number) {
    var v = version(id, number);
    var rows = records.findByRequirementIdOrderByCreatedAtAsc(id);
    var eval =
        rows.stream()
            .filter(r -> r.kind.equals("evaluation") && r.versionId.equals(v.id))
            .reduce((a, b) -> b)
            .orElseThrow(() -> error(409, "该版本尚未评估"));
    var p = payload(eval);
    List<String> accepted = new ArrayList<>();
    for (var f : latestFeedback(rows).values())
      if (f.path("evaluationId").asText().equals(eval.id)
          && !f.path("action").asText().equals("reject")) {
        for (var s : p.path("suggestions"))
          if (s.path("id").asText().equals(f.path("suggestionId").asText()))
            accepted.add(
                f.path("action").asText().equals("modify")
                    ? f.path("modifiedText").asText()
                    : s.path("text").asText());
      }
    return Map.of(
        "requirement_id",
        id,
        "requirement_version",
        v.number,
        "quality_score",
        p.path("quality_score"),
        "dimension_scores",
        p.path("dimension_scores"),
        "risk_level",
        p.path("risk_level"),
        "accepted_suggestions",
        accepted,
        "requirement_change_count",
        v.number - 1,
        "evaluation_timestamp",
        p.path("evaluation_timestamp"));
  }

  public Map<String, Object> retrospective(String id, int number) {
    var r = require(id);
    var v = version(id, number);
    var rows = records.findByRequirementIdOrderByCreatedAtAsc(id);
    var feedback = latestFeedback(rows.stream().filter(row -> row.versionId.equals(v.id)).toList());
    long adopted =
        feedback.values().stream().filter(f -> !f.path("action").asText().equals("reject")).count();
    StringBuilder md =
        new StringBuilder(
            "# " + r.title + " · 质量复盘\n\n版本 v" + number + "；变更次数 " + (number - 1) + "。\n\n");
    md.append("## 需求变更\n");
    for (var h : versions.findByRequirementIdOrderByNumberAsc(id))
      if (h.number <= number)
        md.append("- v").append(h.number).append("：").append(h.reason).append("\n");
    md.append("\n## 质量与人工复核\n");
    rows.stream()
        .filter(row -> row.kind.equals("evaluation") && row.versionId.equals(v.id))
        .reduce((a, b) -> b)
        .ifPresent(
            e ->
                md.append("规则质量分：")
                    .append(payload(e).path("quality_score"))
                    .append("；风险：")
                    .append(payload(e).path("risk_level").asText())
                    .append("。\n"));
    md.append("已复核建议 ")
        .append(feedback.size())
        .append("；采纳/修改 ")
        .append(adopted)
        .append("；采纳率 ")
        .append(feedback.isEmpty() ? "N/A" : Math.round(100.0 * adopted / feedback.size()) + "%")
        .append("（分母为已复核的唯一建议）。\n");
    md.append("\n## 计划与实际交付\n");
    var tasks =
        rows.stream().filter(row -> row.kind.equals("task") && row.versionId.equals(v.id)).toList();
    var deliveries =
        rows.stream()
            .filter(row -> row.kind.equals("delivery") && row.versionId.equals(v.id))
            .toList();
    if (deliveries.isEmpty()) md.append("证据不足：尚无交付记录，不能推断完成状态。\n");
    for (var t : tasks) {
      var p = payload(t);
      md.append("- 任务 ")
          .append(p.path("taskId").asText())
          .append("：计划 ")
          .append(p.path("plan").asText())
          .append("；计划日期 ")
          .append(p.path("plannedDelivery").asText())
          .append("\n");
    }
    for (var d : deliveries) {
      var p = payload(d);
      md.append("- 实际任务 ")
          .append(p.path("task_id").asText())
          .append("：交付 ")
          .append(p.path("delivery_timestamp").asText())
          .append("；周期 ")
          .append(p.path("delivery_cycle"))
          .append(" 小时；测试通过 ")
          .append(p.path("test_passed"))
          .append("；缺陷 ")
          .append(p.path("defect_count"))
          .append("；返工 ")
          .append(p.path("rework_count"))
          .append("\n  - Commit：")
          .append(p.path("commit").asText())
          .append("；PR：")
          .append(p.path("pull_request").asText())
          .append("\n  - 测试：")
          .append(p.path("test_summary").asText())
          .append("；缺陷说明：")
          .append(p.path("defects").asText())
          .append("\n  - 人工记录的返工原因：")
          .append(p.path("rework_reason").asText("未记录"))
          .append("\n");
      for (var t : tasks) {
        var plan = payload(t);
        if (plan.path("taskId").asText().equals(p.path("task_id").asText())) {
          long delta =
              java.time.temporal.ChronoUnit.DAYS.between(
                  LocalDate.parse(plan.path("plannedDelivery").asText()),
                  Instant.parse(p.path("delivery_timestamp").asText())
                      .atZone(ZoneOffset.UTC)
                      .toLocalDate());
          md.append("  - 实际相对计划日期偏差：").append(delta).append("天（UTC日期；负数为提前）。\n");
        }
      }
    }
    md.append("\n## 局限\n交付证据由使用者提交，未经独立验证。相关性仅为探索性，不能解释因果。\n");
    return view(
        save(
            id,
            v.id,
            "retrospective",
            Map.of(
                "markdown",
                md.toString(),
                "evidence_record_ids",
                rows.stream().map(row -> row.id).toList())));
  }

  public Map<String, Object> analytics() {
    List<Map<String, Object>> pairs = new ArrayList<>();
    for (var r : list()) {
      var rows = records.findByRequirementIdOrderByCreatedAtAsc(r.id);
      // One latest task delivery per requirement to avoid duplicate repeated evidence
      // overweighting.
      rows.stream()
          .filter(row -> row.kind.equals("delivery"))
          .reduce((a, b) -> b)
          .ifPresent(
              d -> {
                rows.stream()
                    .filter(
                        row ->
                            row.kind.equals("evaluation")
                                && row.versionId.equals(d.versionId)
                                && row.createdAt.compareTo(d.createdAt) <= 0)
                    .reduce((a, b) -> b)
                    .ifPresent(
                        e -> {
                          var p = payload(d);
                          var v = versions.findById(d.versionId).orElseThrow();
                          pairs.add(
                              Map.of(
                                  "requirement_id",
                                  r.id,
                                  "quality_score",
                                  payload(e).path("quality_score").asDouble(),
                                  "delivery_cycle",
                                  p.path("delivery_cycle").asDouble(),
                                  "defect_count",
                                  p.path("defect_count").asDouble(),
                                  "rework_count",
                                  p.path("rework_count").asDouble(),
                                  "requirement_change_count",
                                  (double) (v.number - 1)));
                        });
              });
    }
    Map<String, Object> correlations = new LinkedHashMap<>();
    for (String metric :
        List.of("delivery_cycle", "defect_count", "rework_count", "requirement_change_count"))
      correlations.put(metric, pearson(pairs, metric));
    return Map.of(
        "sample_size",
        pairs.size(),
        "warning",
        "探索性分析：样本不足或存在混杂因素；相关性不代表因果。至少10条独立需求才展示相关系数。",
        "pairs",
        pairs,
        "correlations",
        correlations);
  }

  static Object pearson(List<Map<String, Object>> pairs, String metric) {
    if (pairs.size() < 10) return "insufficient_data";
    double
        mx = pairs.stream().mapToDouble(p -> (double) p.get("quality_score")).average().orElse(0),
        my = pairs.stream().mapToDouble(p -> (double) p.get(metric)).average().orElse(0);
    double sum = 0, x2 = 0, y2 = 0;
    for (var p : pairs) {
      double x = (double) p.get("quality_score") - mx, y = (double) p.get(metric) - my;
      sum += x * y;
      x2 += x * x;
      y2 += y * y;
    }
    return x2 == 0 || y2 == 0 ? "zero_variance" : sum / Math.sqrt(x2 * y2);
  }

  static ResponseStatusException error(int code, String message) {
    return new ResponseStatusException(HttpStatus.valueOf(code), message);
  }
}
