package io.reqguard;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "records")
public class LifecycleRecord {
  @Id public String id = UUID.randomUUID().toString();

  @Column(name = "requirement_id")
  public String requirementId;

  @Column(name = "version_id")
  public String versionId;

  public String kind;

  @Column(columnDefinition = "TEXT")
  public String payload;

  @Column(name = "created_at")
  public String createdAt = Instant.now().toString();
}
