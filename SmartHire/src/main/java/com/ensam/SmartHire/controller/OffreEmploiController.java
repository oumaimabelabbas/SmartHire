package com.ensam.SmartHire.controller;

import com.ensam.SmartHire.model.OffreEmploi;
import com.ensam.SmartHire.repository.OffreEmploiRepository;
import com.ensam.SmartHire.service.OffreEmploiService;
import jakarta.websocket.server.PathParam;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

import org.springframework.web.bind.annotation.*;

        import java.util.List;

@RestController
@RequestMapping("/offres")
public class OffreEmploiController {

    @Autowired
    private OffreEmploiService offreEmploiService;

    @PostMapping
    public ResponseEntity<OffreEmploi> createOffre(@RequestParam("titre") String titre,@RequestParam("Content") String content,@RequestParam("recruteurId") long recruteurId) {
        return ResponseEntity.ok(offreEmploiService.CreateOffreEmploi(titre,content,recruteurId));
    }

    @GetMapping
    public ResponseEntity<?>getAll() {
        try{
            return ResponseEntity.ok(offreEmploiService.getOffreEmploi());
        }
        catch(Exception e){
            return ResponseEntity
                    .status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Erreur serveur : " + e.getMessage());
        }

    }

    @PutMapping
    public ResponseEntity<?> updateOffre(@RequestBody OffreEmploi offre){
        try {
            return ResponseEntity.ok(offreEmploiService.updateOffreEmploi(offre));
        }catch(RuntimeException e){
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(e.getMessage());
        }

    }
}