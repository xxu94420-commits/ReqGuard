package io.reqguard;

import jakarta.validation.constraints.*;

public class Requests {
  public record Create(
      @NotBlank @Size(max = 200) String title,
      @NotBlank @Size(max = 30000) String description,
      @NotBlank @Size(max = 40) String type,
      @Pattern(regexp = "low|medium|high|critical") @NotNull String priority,
      @NotBlank @Size(max = 40) String source,
      @NotBlank @Size(max = 120) String owner,
      @NotBlank @Size(max = 120) String project,
      @Size(max = 500) String issueUrl,
      @Positive Integer issueId) {}

  public record Revise(
      @NotBlank @Size(max = 30000) String text,
      @NotBlank @Size(max = 500) String reason,
      @Positive int baseVersion) {}

  public record Evaluate(
      @Positive int version, @NotNull @Pattern(regexp = "rule-only|llm-enhanced") String mode) {}

  public record Feedback(
      @NotBlank String evaluationId,
      @NotBlank String suggestionId,
      @NotNull @Pattern(regexp = "accept|reject|modify") String action,
      @Size(max = 2000) String reason,
      @Size(max = 30000) String modifiedText) {}

  public record Task(
      @Positive int version,
      @NotBlank @Size(max = 120) String taskId,
      @NotBlank @Size(max = 3000) String plan,
      @NotBlank @Size(max = 40) String plannedDelivery) {}

  public record Delivery(
      @Positive int version,
      @NotBlank @Size(max = 120) String task_id,
      @Size(max = 120) String issue_id,
      @PositiveOrZero double delivery_cycle,
      boolean ai_assisted,
      boolean test_passed,
      @PositiveOrZero int defect_count,
      @PositiveOrZero int rework_count,
      @NotBlank @Size(max = 40) String delivery_timestamp,
      @Size(max = 500) String commit,
      @Size(max = 500) String pull_request,
      @Size(max = 3000) String test_summary,
      @Size(max = 3000) String defects,
      @Size(max = 2000) String rework_reason) {}

  public record ImportIssue(
      @NotBlank @Pattern(regexp = "[A-Za-z0-9_.-]+") String owner,
      @NotBlank @Pattern(regexp = "[A-Za-z0-9_.-]+") String repo,
      @Positive int number) {}
}
