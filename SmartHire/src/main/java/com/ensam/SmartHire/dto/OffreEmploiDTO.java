package com.ensam.SmartHire.dto;

import com.ensam.SmartHire.model.ModeTravail;
import com.ensam.SmartHire.model.TypeContrat;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class OffreEmploiDTO {

    private String titre;
    private String description;

    private String entreprise;

    private String localisation;

    private TypeContrat typeContrat;
    private ModeTravail modeTravail;
    private boolean actif;

    private String aProposEntreprise;
    private String aProposRole;

    private List<String> responsabilites;
    private List<String> profilRecherche;
}