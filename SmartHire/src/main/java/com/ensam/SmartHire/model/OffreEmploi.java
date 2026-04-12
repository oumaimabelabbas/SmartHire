package com.ensam.SmartHire.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;
import java.util.List;

@Entity
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class OffreEmploi {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String titre;

    @Column(length = 5000)
    private String description;

    private String entreprise;
    @Lob
    private byte[] logoEntreprise;

    private String localisation;

    @Enumerated(EnumType.STRING)
    private TypeContrat typeContrat;

    @Enumerated(EnumType.STRING)
    private ModeTravail modeTravail;

    private LocalDateTime datePublication;

    private boolean actif;

    @Column(length = 3000)
    private String aProposEntreprise;

    @Column(length = 3000)
    private String aProposRole;

    @ElementCollection
    private List<String> responsabilites;

    @ElementCollection
    private List<String> profilRecherche;

    @ManyToOne
    private Utilisateur recruteur;

    @OneToMany(mappedBy = "offre")
    @JsonIgnore
    private List<Candidature> candidatures;
}