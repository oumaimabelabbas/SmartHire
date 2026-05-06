package com.ensam.SmartHire.dto;

import lombok.*;
import java.util.List;
import java.util.Map;
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class JobOfferNormalizedDTO {

    private Long offerId;
    private String title;
    private String description;

    @Builder.Default
    private List<String> requiredTechnologies = List.of();
    @Builder.Default
    private List<String> bonusTechnologies = List.of();

    @Builder.Default
    private List<String> requiredSkills = List.of();
    @Builder.Default
    private List<String> bonusSkills = List.of();

    private Integer minYearsExperience;
    private String experienceLevel;

    @Builder.Default
    private List<String> requiredEducation = List.of();
    @Builder.Default
    private List<String> requiredLanguages = List.of();
    @Builder.Default
    private List<String> bonusLanguages = List.of();

    private String location;
    private Boolean remoteAllowed;
}