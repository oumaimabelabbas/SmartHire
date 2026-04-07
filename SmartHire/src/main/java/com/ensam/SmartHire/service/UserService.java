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
        Utilisateur user = utilisateurRepository.findByUsername(username);
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
    Utilisateur loadUserByUsername(String username){
        return utilisateurRepository.findByUsername(username);
    }
    public List<Utilisateur> getUsers(){
        return utilisateurRepository.findAll();
    }
}
