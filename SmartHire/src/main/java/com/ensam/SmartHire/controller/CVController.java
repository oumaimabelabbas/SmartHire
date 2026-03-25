package com.ensam.SmartHire.controller;

import com.ensam.SmartHire.model.CV;
import com.ensam.SmartHire.repository.CVRepository;
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
@RequestMapping("/cv")
public class CVController {

    @Autowired
    private CVRepository cvRepository;

    @PostMapping("/upload")
    public ResponseEntity<CV> uploadCV(@RequestBody CV cv) {
        CV saved = cvRepository.save(cv);
        return ResponseEntity.ok(saved);
    }

    @GetMapping
    public List<CV> getAllCV() {
        return cvRepository.findAll();
    }
}