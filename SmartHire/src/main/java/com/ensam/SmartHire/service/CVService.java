package com.ensam.SmartHire.service;

import com.ensam.SmartHire.model.CV;
import com.ensam.SmartHire.model.Utilisateur;
import com.ensam.SmartHire.repository.CVRepository;
import com.ensam.SmartHire.repository.UtilisateurRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;

@Service
public class CVService {
    @Autowired
    private CVRepository cvRepository;
    @Autowired
    private Pdfservice pdfservice;
    @Autowired
    private UtilisateurRepository utilisateurRepository;

    public CV createCV(MultipartFile file,String username) throws IOException {
        Utilisateur candidat = utilisateurRepository.findByUsername(username).orElseThrow(() -> new RuntimeException("Candidat introuvable"));
        String text = pdfservice.readPdf(file);
        CV cv = new CV();
        cv.setFileName(file.getOriginalFilename());
        cv.setData(file.getBytes());
        cv.setExtractedText(text);
        cv.setCandidat(candidat);
        return cvRepository.save(cv);

    }

    public List<CV> getAllCvs(){
        return cvRepository.findAll();
    }
}
