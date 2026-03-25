package com.ensam.SmartHire.repository;

import com.ensam.SmartHire.model.OffreEmploi;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;


@Repository
public interface OffreEmploiRepository extends JpaRepository<OffreEmploi, Long> {}