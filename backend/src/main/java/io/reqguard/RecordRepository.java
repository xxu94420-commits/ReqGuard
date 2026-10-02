package io.reqguard;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RecordRepository extends JpaRepository<LifecycleRecord, String> {
  List<LifecycleRecord> findByRequirementIdOrderByCreatedAtAsc(String requirementId);
}
