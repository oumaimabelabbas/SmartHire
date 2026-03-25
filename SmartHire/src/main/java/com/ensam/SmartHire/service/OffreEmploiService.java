package com.ensam.SmartHire.service;

import com.ensam.SmartHire.model.OffreEmploi;
import com.ensam.SmartHire.model.Utilisateur;
import com.ensam.SmartHire.repository.OffreEmploiRepository;
import com.ensam.SmartHire.model.OffreEmploi;
import com.ensam.SmartHire.repository.UtilisateurRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

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
    public OffreEmploi CreateOffreEmploi(String titre,String content,long recruteur_id){
        Utilisateur recruteur = utilisateurRepository.findById(recruteur_id).orElseThrow(()->new RuntimeException("Recruteur not found"));
        OffreEmploi offre = new OffreEmploi();
        offre.setTitre(titre);
        offre.setDescription(content);
        offre.setRecruteur(recruteur);
        return offreEmploiRepository.save(offre);
    }
    public OffreEmploi updateOffreEmploi(OffreEmploi offre){
        OffreEmploi updatedoffre = offreEmploiRepository.findById(offre.getId()).orElseThrow(()-> new RuntimeException("Offre Emploi not found"));
        updatedoffre.setDescription(offre.getDescription());
        updatedoffre.setRecruteur(offre.getRecruteur());
        updatedoffre.setTitre(offre.getTitre());
        return offreEmploiRepository.save(updatedoffre);

    }
}
