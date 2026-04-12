package com.ensam.SmartHire.model;


import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.*;

import java.util.List;

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
    private Double scoreMatching;

    @ManyToOne
    private Utilisateur candidat;

    @OneToMany(mappedBy = "cv")
    @JsonIgnore
    private List<Candidature> candidatures;

}