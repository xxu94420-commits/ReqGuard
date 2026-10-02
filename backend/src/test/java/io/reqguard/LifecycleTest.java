package io.reqguard;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.web.server.ResponseStatusException;

@SpringBootTest(
    properties = {
      "spring.datasource.url=jdbc:h2:mem:reqguard;MODE=PostgreSQL;DATABASE_TO_LOWER=TRUE"
    })
class LifecycleTest {
  @Autowired LifecycleService service;
  @Autowired ObjectMapper mapper;
  @MockitoBean AiGateway ai;

  Requirement create() {
    return service.create(
        new Requests.Create("订单导出", "用户导出订单", "feature", "high", "manual", "运营", "演示", null, null));
  }

  @Test
  void originalAndVersionConflict() {
    var r = create();
    service.revise(r.id, new Requests.Revise("改写后的需求", "明确边界", 1));
    assertEquals("用户导出订单", service.require(r.id).originalText);
    assertEquals(2, ((List<?>) service.detail(r.id).get("versions")).size());
    assertEquals(
        409,
        assertThrows(
                ResponseStatusException.class,
                () -> service.revise(r.id, new Requests.Revise("stale", "冲突", 1)))
            .getStatusCode()
            .value());
  }

  @Test
  void evidenceFeedbackAndRetro() throws Exception {
    var r = create();
    when(ai.evaluate(anyString(), anyString(), anyString()))
        .thenReturn(
            mapper.readTree(
                "{\"quality_score\":65,\"risk_level\":\"medium\",\"dimension_scores\":[],\"evaluation_timestamp\":\"2026-10-01T00:00:00Z\",\"suggestions\":[{\"id\":\"s1\",\"text\":\"明确指标\"}]}"));
    var evaluation = service.evaluate(r.id, new Requests.Evaluate(1, "rule-only"));
    String eid = (String) evaluation.get("id");
    assertThrows(
        ResponseStatusException.class,
        () -> service.feedback(r.id, new Requests.Feedback(eid, "s1", "reject", "", null)));
    assertThrows(
        ResponseStatusException.class,
        () -> service.feedback(r.id, new Requests.Feedback(eid, "other", "accept", null, null)));
    service.feedback(r.id, new Requests.Feedback(eid, "s1", "accept", null, null));
    service.feedback(r.id, new Requests.Feedback(eid, "s1", "reject", "指标不适用", null));
    assertEquals(List.of(), service.export(r.id, 1).get("accepted_suggestions"));
    service.task(r.id, new Requests.Task(1, "task-1", "导出并测试", "2026-10-01"));
    service.delivery(
        r.id,
        new Requests.Delivery(
            1,
            "task-1",
            "123",
            12,
            true,
            true,
            1,
            2,
            "2026-10-02T00:00:00Z",
            "abc",
            "https://github.com/a/b/pull/1",
            "10 passed",
            "编码问题",
            "验收遗漏编码"));
    String report =
        mapper
            .valueToTree(service.retrospective(r.id, 1))
            .path("payload")
            .path("markdown")
            .asText();
    assertTrue(report.contains("偏差：1天"));
    assertTrue(report.contains("验收遗漏编码"));
    assertTrue(report.contains("采纳率 0%"));
  }

  @Test
  void analyticsDoesNotInventAndPearsonHandlesVariance() {
    assertEquals("insufficient_data", LifecycleService.pearson(List.of(), "defect_count"));
    List<Map<String, Object>> pairs = new ArrayList<>();
    for (int i = 0; i < 10; i++)
      pairs.add(Map.of("quality_score", (double) i, "defect_count", (double) (9 - i)));
    assertEquals(-1.0, (double) LifecycleService.pearson(pairs, "defect_count"), 1e-8);
  }

  @Test
  void deliveryRequiresTaskAndValidDate() {
    var r = create();
    assertThrows(
        ResponseStatusException.class,
        () -> service.task(r.id, new Requests.Task(1, "x", "plan", "tomorrow")));
    assertThrows(
        ResponseStatusException.class,
        () ->
            service.delivery(
                r.id,
                new Requests.Delivery(
                    1,
                    "x",
                    null,
                    1,
                    false,
                    false,
                    0,
                    0,
                    "2026-10-02T00:00:00Z",
                    null,
                    null,
                    null,
                    null,
                    null)));
  }
}
