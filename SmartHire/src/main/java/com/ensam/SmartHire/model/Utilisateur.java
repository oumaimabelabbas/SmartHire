package com.ensam.SmartHire.model;

import com.ensam.SmartHire.model.CV;
import com.ensam.SmartHire.model.OffreEmploi;
import com.ensam.SmartHire.model.Role;
import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Entity
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Utilisateur {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(unique = true, nullable = false)
    private String username;
    private String email;
    private String password;

    @Enumerated(EnumType.STRING)
    private Role role;



    @OneToMany(mappedBy = "candidat")
    @JsonIgnore
    private List<CV> cvs;

    @OneToMany(mappedBy = "recruteur")
    @JsonIgnore
    private List<OffreEmploi> offres;
}