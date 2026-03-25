package com.ensam.SmartHire.model;


import jakarta.persistence.*;
import lombok.*;

@Entity
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class CV {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String fileName;

    @Lob
    private byte[] data;

    @Column(length = 10000)
    private String extractedText;

    @ManyToOne
    private Utilisateur candidat;
}