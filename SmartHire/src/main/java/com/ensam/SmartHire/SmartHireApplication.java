package com.ensam.SmartHire;

import com.ensam.SmartHire.model.Role;
import com.ensam.SmartHire.model.Utilisateur;
import com.ensam.SmartHire.service.UserService;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

@SpringBootApplication
public class SmartHireApplication {

	public static void main(String[] args) {
		SpringApplication.run(SmartHireApplication.class, args);
	}
//    @Bean
//    public BCryptPasswordEncoder passwordEncoder(){
//        return new BCryptPasswordEncoder(12);
//    }
//    @Bean
//    CommandLineRunner start(UserService userService,BCryptPasswordEncoder passwordEncoder){
//        return args -> {
//            userService.AddUser(new Utilisateur(
//                    null,"user1","user1@gmail.com",
//                    passwordEncoder.encode("123")
//                    , Role.CANDIDAT,null,null));
//            userService.AddUser(new Utilisateur(
//                    null,"user2","user2@gmail.com",
//                    passwordEncoder.encode("123"), Role.RECRUTEUR,null,null));
//            userService.AddUser(new Utilisateur(
//                    null,"user3","user3@gmail.com",
//                    passwordEncoder.encode("123"), Role.CANDIDAT,null,null));
//        };
//    }
}
