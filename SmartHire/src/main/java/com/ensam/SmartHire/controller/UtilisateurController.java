package com.ensam.SmartHire.controller;

import com.ensam.SmartHire.model.Utilisateur;
import com.ensam.SmartHire.repository.UtilisateurRepository;
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
@RequestMapping("/utilisateurs")
public class UtilisateurController {

    @Autowired
    private UtilisateurRepository utilisateurRepo;

    @PostMapping
    public ResponseEntity<Utilisateur> createUtilisateur(@RequestBody Utilisateur user) {
        Utilisateur saved = utilisateurRepo.save(user);
        return ResponseEntity.ok(saved);
    }

    @GetMapping
    public List<Utilisateur> getAllUtilisateurs() {
        return utilisateurRepo.findAll();
    }
}