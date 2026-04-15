package com.ensam.SmartHire.controller;

import com.ensam.SmartHire.dto.OffreEmploiDTO;
import com.ensam.SmartHire.model.OffreEmploi;
import com.ensam.SmartHire.service.OffreEmploiService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;

@RestController
@RequestMapping("/offres")
@CrossOrigin(origins = "http://localhost:5173", allowCredentials = "true")
public class OffreEmploiController {

    @Autowired
    private OffreEmploiService offreEmploiService;

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<?> createOffre(@RequestPart(value = "offre") OffreEmploiDTO offreEmploi, @RequestPart("logo") MultipartFile logo, Authentication authentication) {
        try {
            String username = authentication.getName();
            return ResponseEntity.ok(offreEmploiService.CreateOffreEmploi(offreEmploi,logo,username));
        }catch(Exception e){
            System.out.println(e.getMessage());
            return ResponseEntity.status(500).build();
        }
    }

    @GetMapping
    public ResponseEntity<?>getAllOffre() {
        try{
            return ResponseEntity.ok(offreEmploiService.getOffreEmploi());
        }
        catch(RuntimeException e){
            return ResponseEntity
                    .status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Erreur serveur : " + e.getMessage());
        }

    }
    @GetMapping("/mes-offres")
    public ResponseEntity<?> getMesOffres(Authentication authentication) {
        try {
            String username = authentication.getName();
            return ResponseEntity.ok(offreEmploiService.getOffresByRecruteur(username));
        } catch (RuntimeException e) {
            return ResponseEntity
                    .status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Erreur serveur : " + e.getMessage());
        }
    }


    @PutMapping("/{id}")
    public ResponseEntity<?> updateOffre(@PathVariable Long id,@RequestPart("offre") OffreEmploiDTO offreDTO, @RequestPart("logo") MultipartFile logo, Authentication authentication){
        try {
            String username = authentication.getName();
            return ResponseEntity.ok(offreEmploiService.updateOffreEmploi(id,offreDTO,logo,username));
        }catch(Exception e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(e.getMessage());
        }

    }

    @GetMapping("/search")
    public ResponseEntity<?> filterOffre(Authentication authentication,@RequestParam(required = false) String poste,@RequestParam(required = false) String lieu,@RequestParam(required = false) String contrat){
        try{
            String username = authentication.getName();
            List<OffreEmploi> offreEmplois =  offreEmploiService.filterOffre(poste,lieu,contrat,username);
            if(!offreEmplois.isEmpty()){
                return ResponseEntity.ok(offreEmplois);
            }
            else{
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body("Aucune offre ne correspond aux critères");
            }

        }
        catch(Exception e){
            return ResponseEntity
                    .status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Erreur serveur : " + e.getMessage());
        }
    }


}