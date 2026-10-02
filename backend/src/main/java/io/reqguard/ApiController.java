package io.reqguard;

import com.fasterxml.jackson.databind.JsonNode;
import jakarta.validation.Valid;
import java.util.*;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestClient;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api")
public class ApiController {
  private final LifecycleService service;
  private final AiGateway ai;

  public ApiController(LifecycleService service, AiGateway ai) {
    this.service = service;
    this.ai = ai;
  }

  @GetMapping("/health")
  public Map<String, String> health() {
    return Map.of("status", "ok");
  }

  @GetMapping("/requirements")
  public List<Requirement> list() {
    return service.list();
  }

  @PostMapping("/requirements")
  @ResponseStatus(HttpStatus.CREATED)
  public Requirement create(@Valid @RequestBody Requests.Create input) {
    return service.create(input);
  }

  @GetMapping("/requirements/{id}")
  public Map<String, Object> detail(@PathVariable String id) {
    return service.detail(id);
  }

  @PostMapping("/requirements/{id}/versions")
  public RequirementVersion revise(
      @PathVariable String id, @Valid @RequestBody Requests.Revise input) {
    return service.revise(id, input);
  }

  @PostMapping("/requirements/{id}/evaluations")
  public Map<String, Object> evaluate(
      @PathVariable String id, @Valid @RequestBody Requests.Evaluate input) {
    return service.evaluate(id, input);
  }

  @PostMapping("/requirements/{id}/feedback")
  public Map<String, Object> feedback(
      @PathVariable String id, @Valid @RequestBody Requests.Feedback input) {
    return service.feedback(id, input);
  }

  @PostMapping("/requirements/{id}/tasks")
  public Map<String, Object> task(
      @PathVariable String id, @Valid @RequestBody Requests.Task input) {
    return service.task(id, input);
  }

  @PostMapping("/requirements/{id}/delivery")
  public Map<String, Object> delivery(
      @PathVariable String id, @Valid @RequestBody Requests.Delivery input) {
    return service.delivery(id, input);
  }

  @PostMapping("/requirements/{id}/retrospectives")
  public Map<String, Object> retro(@PathVariable String id, @RequestParam int version) {
    return service.retrospective(id, version);
  }

  @GetMapping("/integrations/devflow/requirements/{id}")
  public Map<String, Object> export(@PathVariable String id, @RequestParam int version) {
    return service.export(id, version);
  }

  @GetMapping("/analytics")
  public Map<String, Object> analytics() {
    return service.analytics();
  }

  @GetMapping("/benchmark")
  public JsonNode benchmark() {
    return ai.benchmark();
  }

  @PostMapping("/github/import")
  public Requirement importIssue(@Valid @RequestBody Requests.ImportIssue input) {
    // Fixed public GitHub API host. No tokens, writes, arbitrary URL fetches or redirects.
    JsonNode issue =
        RestClient.create("https://api.github.com")
            .get()
            .uri(
                "/repos/{owner}/{repo}/issues/{number}",
                input.owner(),
                input.repo(),
                input.number())
            .header("Accept", "application/vnd.github+json")
            .retrieve()
            .body(JsonNode.class);
    if (issue == null || issue.has("pull_request"))
      throw LifecycleService.error(400, "只能导入公开 Issue，不能导入 PR");
    String body = issue.path("body").asText("");
    if (body.isBlank()) body = "[Issue没有描述，请人工补充]";
    return service.create(
        new Requests.Create(
            issue.path("title").asText(),
            body,
            "feature",
            "medium",
            "github",
            "待分配",
            input.owner() + "/" + input.repo(),
            issue.path("html_url").asText(),
            input.number()));
  }

  @ExceptionHandler(ResponseStatusException.class)
  public ResponseEntity<Map<String, String>> statusError(ResponseStatusException ex) {
    return ResponseEntity.status(ex.getStatusCode())
        .body(Map.of("message", Objects.requireNonNullElse(ex.getReason(), "请求失败")));
  }

  @ExceptionHandler(org.springframework.web.client.RestClientException.class)
  public ResponseEntity<Map<String, String>> upstreamError() {
    return ResponseEntity.status(502).body(Map.of("message", "上游服务不可用，请检查 AI 服务或公开 GitHub Issue"));
  }
}
