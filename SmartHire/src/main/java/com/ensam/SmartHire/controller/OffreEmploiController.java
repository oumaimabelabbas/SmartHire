package com.ensam.SmartHire.controller;

import com.ensam.SmartHire.model.OffreEmploi;
import com.ensam.SmartHire.repository.OffreEmploiRepository;
import org.springframework.beans.factory.annotation.Autowired;
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
    private OffreEmploiRepository offreRepo;

    @PostMapping
    public ResponseEntity<OffreEmploi> createOffre(@RequestBody OffreEmploi offre) {
        return ResponseEntity.ok(offreRepo.save(offre));
    }

    @GetMapping
    public List<OffreEmploi> getAll() {
        return offreRepo.findAll();
    }
}