package com.ensam.SmartHire.controller;

import com.ensam.SmartHire.dto.CVResponseDTO;
import com.ensam.SmartHire.model.CV;
import com.ensam.SmartHire.model.Utilisateur;
import com.ensam.SmartHire.repository.CVRepository;
import com.ensam.SmartHire.repository.UtilisateurRepository;
import com.ensam.SmartHire.service.CVService;
import com.ensam.SmartHire.service.Pdfservice;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
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
@CrossOrigin(origins = "http://localhost:5173", allowCredentials = "true")
@RequestMapping("/cv")
public class CVController {

    @Autowired
    private CVRepository cvRepository;
    @Autowired
    private UtilisateurRepository utilisateurRepository;
    @Autowired
    private CVService cvService;


    @PostMapping(value="/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<CVResponseDTO> uploadCV(@RequestParam("file") MultipartFile file, Authentication authentication)  {
        try {
            String username = authentication.getName();
            CV cv = cvService.createCV(file,username);
            return ResponseEntity.ok(new CVResponseDTO(cv.getId()));
        }catch(IOException e){
            return ResponseEntity.status(500).build();
        }
    }
    @GetMapping
    public ResponseEntity<List<CV>> getAllCV() {
        return ResponseEntity.ok(cvService.getAllCvs());
    }


}