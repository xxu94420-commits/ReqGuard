package io.reqguard;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface VersionRepository extends JpaRepository<RequirementVersion, String> {
  List<RequirementVersion> findByRequirementIdOrderByNumberAsc(String requirementId);
}
