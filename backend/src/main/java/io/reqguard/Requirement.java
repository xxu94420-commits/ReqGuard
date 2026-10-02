package io.reqguard;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "requirements")
public class Requirement {
  @Id public String id = UUID.randomUUID().toString();
  public String title;

  @Column(name = "original_text", columnDefinition = "TEXT")
  public String originalText;

  public String type;
  public String priority;
  public String source;
  public String owner;
  public String project;

  @Column(name = "issue_url")
  public String issueUrl;

  @Column(name = "issue_id")
  public Integer issueId;

  @Column(name = "created_at")
  public String createdAt = Instant.now().toString();
}
