package io.reqguard;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "versions")
public class RequirementVersion {
  @Id public String id = UUID.randomUUID().toString();

  @Column(name = "requirement_id")
  public String requirementId;

  public int number;

  @Column(columnDefinition = "TEXT")
  public String text;

  public String reason;

  @Column(name = "created_at")
  public String createdAt = Instant.now().toString();
}
