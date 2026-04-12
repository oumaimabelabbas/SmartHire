package com.ensam.SmartHire.repository;

import com.ensam.SmartHire.model.Candidature;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface candidatureRepository extends JpaRepository<Candidature,Long> {
    List<Candidature> findByOffreId(Long offreId);
    List<Candidature> findByCandidatUsername(String username);
}
