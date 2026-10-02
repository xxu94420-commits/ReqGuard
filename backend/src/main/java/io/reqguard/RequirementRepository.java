package io.reqguard;

import jakarta.persistence.LockModeType;
import java.util.Optional;
import org.springframework.data.jpa.repository.*;
import org.springframework.data.repository.query.Param;

public interface RequirementRepository extends JpaRepository<Requirement, String> {
  @Lock(LockModeType.PESSIMISTIC_WRITE)
  @Query("select r from Requirement r where r.id = :id")
  Optional<Requirement> lockById(@Param("id") String id);
}
