package com.ensam.SmartHire.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Candidature {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    private Utilisateur candidat;

    @ManyToOne
    private OffreEmploi offre;

    @ManyToOne
    private CV cv;

    private LocalDateTime dateCandidature;

    @Enumerated(EnumType.STRING)
    private StatutCandidature statut;

    private Integer overallScore;

    @Column(length = 2000)
    private String scoreExplanation;
}