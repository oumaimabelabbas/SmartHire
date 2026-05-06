package com.ensam.SmartHire.dto;

import lombok.*;
import java.util.List;
import java.util.Map;
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class CVExtractedDataDTO {

    private String fullName;
    private String email;
    private String phone;

    private List<String> technicalSkills = List.of();
    private List<String> softSkills = List.of();

    private List<ExperienceDTO> experiences = List.of();
    private List<EducationDTO> education = List.of();
    private List<String> certifications = List.of();
    private List<LanguageDTO> languages = List.of();

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class ExperienceDTO {
        private String jobTitle;
        private String company;
        private Integer yearsOfExperience;
        private String description;
        private List<String> technologiesUsed = List.of();
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class EducationDTO {
        private String degree;
        private String field;
        private String institution;
        private Integer graduationYear;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class LanguageDTO {
        private String language;
        private String proficiency;
    }
}