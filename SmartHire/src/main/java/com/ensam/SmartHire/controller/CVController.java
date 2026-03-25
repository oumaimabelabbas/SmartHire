package com.ensam.SmartHire.controller;

import com.ensam.SmartHire.model.CV;
import com.ensam.SmartHire.model.Utilisateur;
import com.ensam.SmartHire.repository.CVRepository;
import com.ensam.SmartHire.repository.UtilisateurRepository;
import com.ensam.SmartHire.service.CVService;
import com.ensam.SmartHire.service.Pdfservice;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;
import java.util.List;

import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@RestController
@RequestMapping("/cv")
public class CVController {

    @Autowired
    private CVRepository cvRepository;
    @Autowired
    private UtilisateurRepository utilisateurRepository;
    @Autowired
    private CVService cvService;


    @PostMapping(value="/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<CV> uploadCV(@RequestParam("file") MultipartFile file,@RequestParam("candidatId") Long candidatId)  {
        try {
            return ResponseEntity.ok(cvService.createCV(file,candidatId));
        }catch(IOException e){
            return ResponseEntity.status(500).build();
        }
    }
    @GetMapping
    public ResponseEntity<List<CV>> getAllCV() {
        return ResponseEntity.ok(cvService.getAllCvs());
    }
}