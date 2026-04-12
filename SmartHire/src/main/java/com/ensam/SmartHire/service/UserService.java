package com.ensam.SmartHire.service;

import com.ensam.SmartHire.dto.RegisterDTO;
import com.ensam.SmartHire.model.Role;
import com.ensam.SmartHire.model.Utilisateur;
import com.ensam.SmartHire.repository.UtilisateurRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.List;
@Service
public class UserService {
    @Autowired
    UtilisateurRepository utilisateurRepository;
    @Autowired
    private BCryptPasswordEncoder passwordEncoder;


    public Utilisateur AddUser(RegisterDTO registeruser){
       Utilisateur user = new Utilisateur();
       user.setEmail(registeruser.getEmail());
       user.setUsername(registeruser.getUsername());
       user.setPassword(passwordEncoder.encode(registeruser.getPassword()));
       if(registeruser.getRole() != null){
           user.setRole(registeruser.getRole());
       }
       else{
           throw new IllegalArgumentException("Role is required");
       }
       return utilisateurRepository.save(user);
    }

    public void addRoleUser(String username,String role){
        Utilisateur user = utilisateurRepository.findByUsername(username).orElseThrow(() -> new RuntimeException("Utilisateur introuvable"));;
        if(user==null){
            throw new RuntimeException("User not found");
        }
        try{
           Role newRole = Role.valueOf(role);
           user.setRole(newRole);
           utilisateurRepository.save(user);
        }catch(Exception e){
            throw  new RuntimeException("Invalid role "+role);
        }

    }
    public Utilisateur loadUserByUsername(String username){

        Utilisateur user = utilisateurRepository.findByUsername(username).orElseThrow(() -> new RuntimeException("Utilisateur introuvable"));
        return user;
    }
    public List<Utilisateur> getUsers(){
        return utilisateurRepository.findAll();
    }

    public Utilisateur update(Utilisateur user,String username) {
       Utilisateur utilisateur = utilisateurRepository.findByUsername(username).orElseThrow(() -> new RuntimeException("user not found"));
        if (user.getNom() != null) {
            utilisateur.setNom(user.getNom());
        }

        if (user.getPrenom() != null) {
            utilisateur.setPrenom(user.getPrenom());
        }

        if (user.getEmail() != null) {
            utilisateur.setEmail(user.getEmail());
        }

        if (user.getPassword() != null) {
            utilisateur.setPassword(passwordEncoder.encode(user.getPassword()));
        }

        return utilisateurRepository.save(utilisateur);

    }
}
