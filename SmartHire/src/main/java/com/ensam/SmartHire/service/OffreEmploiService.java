package com.ensam.SmartHire.service;

import com.ensam.SmartHire.dto.OffreEmploiDTO;
import com.ensam.SmartHire.model.OffreEmploi;
import com.ensam.SmartHire.model.Utilisateur;
import com.ensam.SmartHire.repository.OffreEmploiRepository;
import com.ensam.SmartHire.model.OffreEmploi;
import com.ensam.SmartHire.repository.UtilisateurRepository;
import org.jspecify.annotations.Nullable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.List;
@Service
public class OffreEmploiService {
    @Autowired
    private OffreEmploiRepository offreEmploiRepository;
    @Autowired
    private UtilisateurRepository utilisateurRepository;

    public List<OffreEmploi> getOffreEmploi(){
        return offreEmploiRepository.findAll();
    }


    public OffreEmploi getOffreEmploibyId(Long id){
        return offreEmploiRepository.findById(id).orElseThrow(()-> new RuntimeException("Offre Emploi not found"));
    }
    public OffreEmploi CreateOffreEmploi(OffreEmploiDTO offreEmploi, MultipartFile logo, String username) throws IOException {
        Utilisateur recruteur = utilisateurRepository.findByUsername(username).orElseThrow(() -> new RuntimeException("Recruteur introuvable"));;
        //mapping between dto and model
        OffreEmploi offre = OffreEmploi.builder()
                .titre(offreEmploi.getTitre())
                .description(offreEmploi.getDescription())
                .entreprise(offreEmploi.getEntreprise())
                .localisation(offreEmploi.getLocalisation())
                .typeContrat(offreEmploi.getTypeContrat())
                .modeTravail(offreEmploi.getModeTravail())
                .aProposEntreprise(offreEmploi.getAProposEntreprise())
                .aProposRole(offreEmploi.getAProposRole())
                .responsabilites(offreEmploi.getResponsabilites())
                .profilRecherche(offreEmploi.getProfilRecherche())
                .actif(offreEmploi.isActif())
                .datePublication(LocalDateTime.now())
                .recruteur(recruteur)
                .build();
        if (logo != null && !logo.isEmpty()) {
            offre.setLogoEntreprise(logo.getBytes());
        }
        return offreEmploiRepository.save(offre);
    }
    public OffreEmploi updateOffreEmploi(Long id, OffreEmploiDTO dto,MultipartFile logo, String username) throws IOException {
        Utilisateur recruteur = utilisateurRepository.findByUsername(username).orElseThrow(() -> new RuntimeException("Recruteur introuvable"));
        OffreEmploi offre = offreEmploiRepository.findById(id).orElseThrow(() -> new RuntimeException("Offre Emploi not found"));
        offre.setTitre(dto.getTitre());
        offre.setDescription(dto.getDescription());
        offre.setEntreprise(dto.getEntreprise());
        offre.setLocalisation(dto.getLocalisation());
        offre.setTypeContrat(dto.getTypeContrat());
        offre.setModeTravail(dto.getModeTravail());
        offre.setAProposEntreprise(dto.getAProposEntreprise());
        offre.setAProposRole(dto.getAProposRole());
        offre.setResponsabilites(dto.getResponsabilites());
        offre.setProfilRecherche(dto.getProfilRecherche());

        offre.setActif(dto.isActif());
        if(logo != null && !logo.isEmpty()){
            offre.setLogoEntreprise(logo.getBytes());
        }

        return offreEmploiRepository.save(offre);

    }

    public List<OffreEmploi> getOffresByRecruteur(String username){
        return offreEmploiRepository.findByRecruteurUsername(username);
    }
}
