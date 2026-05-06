package com.ensam.SmartHire.controller;

import com.ensam.SmartHire.dto.LoginDTO;
import com.ensam.SmartHire.dto.RegisterDTO;
import com.ensam.SmartHire.model.Utilisateur;
import com.ensam.SmartHire.service.JwtService;
import com.ensam.SmartHire.service.UserService;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping
@CrossOrigin(origins = "http://localhost:5173", allowCredentials = "true")
public class UtilisateurController {

    @Autowired
    private UserService userService;
    @Autowired
    AuthenticationManager authenticationManager;
    @Autowired
    JwtService jwtService;

    @PostMapping({"/Login", "/login"})
    public ResponseEntity<?> login(@RequestBody LoginDTO loginrequest, HttpServletResponse response){
        try{
            authenticationManager.authenticate(new UsernamePasswordAuthenticationToken(loginrequest.getUsername(),loginrequest.getPassword()));
            Utilisateur user = userService.loadUserByUsername(loginrequest.getUsername());
            String token = jwtService.generateToken(user.getUsername(),user.getRole().name()); //ajouter els roles dans le token
            Cookie cookie = new Cookie("jwt",token);
            cookie.setHttpOnly(true);
            cookie.setSecure(false);
            cookie.setPath("/");
            cookie.setMaxAge(60 * 60);

            response.addCookie(cookie);//sending the token via the cookie
            return ResponseEntity.ok(Map.of(
                    "message", "Login successful"
            ));

        }catch(Exception e){
            System.out.println(e.getMessage());
            throw new RuntimeException("Username or Password Incorrect");
        }
    }

    @GetMapping("/login")
    public ResponseEntity<?> loginHealth() {
        return ResponseEntity.ok(Map.of("message", "Login endpoint ready"));
    }

    @GetMapping("/me")
    public ResponseEntity<?> getCurrentUser(Authentication authentication) {

        UserDetails userDetails = (UserDetails) authentication.getPrincipal();

        return ResponseEntity.ok(Map.of(
                "username", userDetails.getUsername(),
                "role", userDetails.getAuthorities().iterator().next().getAuthority()
        ));
    }
    @PostMapping("/utilisateurs")
    public ResponseEntity<Utilisateur> createUtilisateur(@RequestBody RegisterDTO registerUser) {
        return ResponseEntity.ok(userService.AddUser(registerUser));
    }
    @GetMapping("/profile")
    public Utilisateur getProfile(Authentication auth) {
        return userService.loadUserByUsername(auth.getName());
    }
    @PutMapping("/profile")
    public Utilisateur updateProfile(@RequestBody Utilisateur user,Authentication authentication) {
        String username = authentication.getName();
        return userService.update(user,username);
    }
    @PostMapping("/logout")
    public ResponseEntity<?> logout(HttpServletResponse response) {

        Cookie cookie = new Cookie("jwt", null);
        cookie.setHttpOnly(true);
        cookie.setSecure(false);
        cookie.setPath("/");
        cookie.setMaxAge(0);

        response.addCookie(cookie);

        return ResponseEntity.ok(Map.of(
                "message", "Logout successful"
        ));
    }
    @GetMapping("/utilisateurs")
    public List<Utilisateur> getAllUtilisateurs() {
        return userService.getUsers();
    }
}