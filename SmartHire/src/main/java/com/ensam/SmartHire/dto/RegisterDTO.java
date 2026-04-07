package com.ensam.SmartHire.dto;

import com.ensam.SmartHire.model.Role;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class RegisterDTO {
    private String username;
    private String password;
    private String email;
    @Enumerated(EnumType.STRING)
    private Role role;

}
