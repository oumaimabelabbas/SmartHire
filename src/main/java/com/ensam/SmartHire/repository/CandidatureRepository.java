package com.ensam.SmartHire.repository;

import com.ensam.SmartHire.model.Candidature;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface CandidatureRepository extends JpaRepository<Candidature,Long> {
    List<Candidature> findByOffreId(Long offreId);
    List<Candidature> findByOffreIdOrderByDateCandidatureDesc(Long offreId);
    List<Candidature> findByCandidatUsername(String username);
    boolean existsByCandidatIdAndOffreId(Long candidatId, Long offreId);
}
