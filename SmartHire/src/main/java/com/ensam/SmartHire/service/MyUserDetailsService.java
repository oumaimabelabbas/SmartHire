package com.ensam.SmartHire.service;

import com.ensam.SmartHire.model.UserPrincipal;
import com.ensam.SmartHire.model.Utilisateur;
import com.ensam.SmartHire.repository.UtilisateurRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

@Service
public class MyUserDetailsService implements UserDetailsService {
    @Autowired
    private UtilisateurRepository repo;
    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        Utilisateur user = repo.findByUsername(username).orElseThrow(() -> new RuntimeException("User introuvable"));
        if(user ==null){
            System.out.println("user not found");
            throw  new UsernameNotFoundException("user not found");
        }
        return new UserPrincipal(user);

    }
}
