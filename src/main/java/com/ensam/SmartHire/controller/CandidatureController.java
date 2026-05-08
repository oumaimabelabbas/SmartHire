package com.ensam.SmartHire.controller;

import com.ensam.SmartHire.dto.CVResponseDTO;
import com.ensam.SmartHire.dto.CandidatureDTO;
import com.ensam.SmartHire.model.CV;
import com.ensam.SmartHire.model.StatutCandidature;
import com.ensam.SmartHire.service.CandidatureService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/candidatures")
@CrossOrigin(origins = "http://localhost:5173", allowCredentials = "true")

public class CandidatureController {

    @Autowired
    private CandidatureService candidatureService;

    @PostMapping
    public ResponseEntity<?> postuler(@RequestBody CandidatureDTO dto,
                                                  Authentication authentication){
        String username = authentication.getName();

        return ResponseEntity.ok(
                candidatureService.postuler(dto, username)
        );
    }
    @GetMapping("/mes-candidature")
    public ResponseEntity<?> get(Authentication authentication){
        String username = authentication.getName();

        return ResponseEntity.ok(
                candidatureService.getcandidature(username)
        );
    }
    @GetMapping("/offre/{offreId}")
    public ResponseEntity<?> getCandidature(Authentication authentication,@PathVariable("offreId") Long offreid){
        try{
            String username = authentication.getName();
            return ResponseEntity.ok(candidatureService.getcandidatoffre(username,offreid));
        }
        catch(RuntimeException e){
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(e.getMessage());

        }
    }

    @PutMapping("/{id}")
    public ResponseEntity<?> changeStatus(@PathVariable Long id,
                                          @RequestParam StatutCandidature statut, Authentication authentication){
        String username = authentication.getName();

        return ResponseEntity.ok(
                candidatureService.updateStatut(id, statut, username)
        );
    }

    @GetMapping("/download-cv/{cvid}")
    public ResponseEntity<?> getCV(@PathVariable Long cvid,Authentication authentication){
        String username = authentication.getName();

        CV cv = candidatureService.getCV(cvid);

        return ResponseEntity.ok()
                .header("Content-Disposition", "attachment; filename=\"" + cv.getFileName() + "\"")
                .header("Content-Type", "application/octet-stream")
                .body(cv.getData());
    }

}
