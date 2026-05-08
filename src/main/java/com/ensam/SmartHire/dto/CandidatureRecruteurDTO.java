package com.ensam.SmartHire.dto;

import com.ensam.SmartHire.model.StatutCandidature;
import jakarta.persistence.Column;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CandidatureRecruteurDTO {
    private Long candidatureId;
    private Integer overallScore;

    @Column(length = 2000)
    private String scoreExplanation;

    private String nom;
    private String prenom;
    private String username;

    private Long cvId;
    private String cvName;

    private LocalDateTime dateCandidature;

    private StatutCandidature statut;
}
