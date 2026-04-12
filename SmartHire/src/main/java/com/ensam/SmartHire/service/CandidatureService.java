package com.ensam.SmartHire.service;

import com.ensam.SmartHire.dto.CandidatureDTO;
import com.ensam.SmartHire.dto.CandidatureRecruteurDTO;
import com.ensam.SmartHire.dto.CandidatureResponseDTO;
import com.ensam.SmartHire.model.*;
import com.ensam.SmartHire.repository.CVRepository;
import com.ensam.SmartHire.repository.OffreEmploiRepository;
import com.ensam.SmartHire.repository.UtilisateurRepository;
import com.ensam.SmartHire.repository.candidatureRepository;
import org.jspecify.annotations.Nullable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
@Service
public class CandidatureService {
    @Autowired
    private candidatureRepository candidatureRepository;
    @Autowired
    private CVRepository cvRepository;
    @Autowired
    private UtilisateurRepository utilisateurRepository;
    @Autowired
    private OffreEmploiRepository offreEmploiRepository;

    public CandidatureResponseDTO postuler(CandidatureDTO dto, String username){

        Utilisateur candidat = utilisateurRepository.findByUsername(username)
                .orElseThrow(() -> new RuntimeException("Utilisateur introuvable"));

        OffreEmploi offre = offreEmploiRepository.findById(dto.getOffreId())
                .orElseThrow(() -> new RuntimeException("Offre introuvable"));

        CV cv = cvRepository.findById(dto.getCvId())
                .orElseThrow(() -> new RuntimeException("CV introuvable"));

        Candidature candidature = Candidature.builder()
                .candidat(candidat)
                .offre(offre)
                .cv(cv)
                .dateCandidature(LocalDateTime.now())
                .statut(StatutCandidature.EN_ATTENTE)
                .build();

        Candidature saved = candidatureRepository.save(candidature);

        return new CandidatureResponseDTO(
                saved.getId(),
                saved.getStatut().name()
        );
    }

    public List<CandidatureRecruteurDTO> getcandidatoffre(String username, Long offreid) {
        List<Candidature> candidatures = candidatureRepository.findByOffreId(offreid);
        CandidatureRecruteurDTO candidaturedto = new CandidatureRecruteurDTO();
        return candidatures.stream().map(c -> CandidatureRecruteurDTO.builder()
                .candidatureId(c.getId())
                .nom(c.getCandidat().getNom())
                .prenom(c.getCandidat().getPrenom())
                .username(c.getCandidat().getUsername())
                .cvName(c.getCv().getFileName())
                .cvId(c.getCv().getId())
                .dateCandidature(c.getDateCandidature())
                .statut(c.getStatut())
                .build()
        ).toList();

    }

    public Candidature updateStatut(Long id, StatutCandidature statut, String username) {
        Candidature candidature = candidatureRepository.findById(id).orElseThrow(() -> new RuntimeException("Candidature introuvable"));
        candidature.setStatut(statut);
        return candidatureRepository.save(candidature);
    }

    public CV getCV(Long cvid) {
        CV cv = cvRepository.findById(cvid).orElseThrow(() -> new RuntimeException("CV introuvable"));
        return cv;
    }

    public List<Candidature> getcandidature(String username) {

        List<Candidature> mescandidature = candidatureRepository.findByCandidatUsername(username);
        return mescandidature;
    }
}
