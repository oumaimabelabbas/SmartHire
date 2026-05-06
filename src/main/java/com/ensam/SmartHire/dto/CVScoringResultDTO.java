package com.ensam.SmartHire.dto;

import lombok.*;
import java.util.List;
import java.util.Map;

/**
 * DTO pour le résultat du scoring RAG
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class CVScoringResultDTO {

    private Integer overallScore;
    private Map<String, Integer> subScores;
    private String scoreExplanation;
    private List<String> strengths = List.of();
    private List<GapDTO> gaps = List.of();
    private List<String> improvements = List.of();
    private Map<String, Integer> improvementPriority;
    private String status = "SUCCESS";

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class GapDTO {
        private String requirement;
        private String reason;
        private Integer impact;
    }
}