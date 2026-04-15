package com.ensam.SmartHire.controller;

import com.ensam.SmartHire.dto.CVScoringResultDTO;
import com.ensam.SmartHire.model.CV;
import com.ensam.SmartHire.model.Candidature;
import com.ensam.SmartHire.model.OffreEmploi;
import com.ensam.SmartHire.model.StatutCandidature;
import com.ensam.SmartHire.model.Utilisateur;
import com.ensam.SmartHire.repository.CVRepository;
import com.ensam.SmartHire.repository.CandidatureRepository;
import com.ensam.SmartHire.repository.OffreEmploiRepository;
import com.ensam.SmartHire.repository.UtilisateurRepository;
import com.ensam.SmartHire.repository.candidatureRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.security.core.Authentication;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;
import java.time.LocalDateTime;

@Slf4j
@RestController
@RequestMapping("/api/cv-analysis")
@CrossOrigin(origins = "http://localhost:5173", allowCredentials = "true")
public class CVAnalysisController {

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private OffreEmploiRepository offreRepository;

    @Autowired
    private UtilisateurRepository utilisateurRepository;

    @Autowired
    private CVRepository cvRepository;

    @Autowired
    private candidatureRepository candidatureRepository;

    @Value("${rag.service.url:http://localhost:8000}")
    private String ragServiceUrl;

    @PostMapping("/score-for-offer")
    public ResponseEntity<?> scoreCV(
            @RequestParam("cvFile") MultipartFile cvFile,
            @RequestParam("offreId") Long offreId) {

        try {
            if (cvFile == null || cvFile.isEmpty()) {
                return ResponseEntity.badRequest().body(new ErrorResponse("Fichier CV vide"));
            }

            String contentType = cvFile.getContentType() != null ? cvFile.getContentType().toLowerCase() : "";
            if (!contentType.contains("pdf")) {
                return ResponseEntity.badRequest().body(new ErrorResponse("Seuls les fichiers PDF sont acceptes"));
            }

            OffreEmploi offre = offreRepository.findById(offreId)
                    .orElseThrow(() -> new NoSuchElementException("Offre non trouvee: " + offreId));

            Map<String, Object> extractedCv = extractCVFromRAG(cvFile);
            Map<String, Object> offrePayload = convertOffreToDTO(offre);
            CVScoringResultDTO scoringResult = scoreViaRAG(extractedCv, offrePayload);

            return ResponseEntity.ok(new ScoreResponse("SUCCESS", scoringResult, "Analyse RAG complete"));

        } catch (NoSuchElementException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(new ErrorResponse(e.getMessage()));
        } catch (RAGException e) {
            return ResponseEntity.status(e.getStatus()).body(new ErrorResponse(e.getMessage()));
        } catch (Exception e) {
            log.error("Erreur inattendue score-for-offer", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new ErrorResponse("Erreur serveur: " + e.getMessage()));
        }
    }

    @GetMapping("/offers-for-rag")
    public ResponseEntity<List<Map<String, Object>>> getOffersForRag() {
        List<Map<String, Object>> payload = offreRepository.findAll().stream().map(offre -> {
            Map<String, Object> item = new HashMap<>();
            item.put("id", offre.getId());
            item.put("titre", offre.getTitre());
            item.put("metier", offre.getTitre());
            item.put("description", offre.getDescription());
            item.put("entreprise", offre.getEntreprise());
            item.put("localisation", offre.getLocalisation());
            item.put("typeContrat", offre.getTypeContrat() != null ? offre.getTypeContrat().name() : null);
            item.put("modeTravail", offre.getModeTravail() != null ? offre.getModeTravail().name() : null);
            item.put("responsabilites", offre.getResponsabilites() != null ? offre.getResponsabilites() : List.of());
            item.put("profilRecherche", offre.getProfilRecherche() != null ? offre.getProfilRecherche() : List.of());
            item.put("aProposRole", offre.getAProposRole());
            item.put("aProposEntreprise", offre.getAProposEntreprise());
            return item;
        }).toList();

        return ResponseEntity.ok(payload);
    }

    @PostMapping("/apply-for-offer")
    public ResponseEntity<?> applyForOffer(
            @RequestParam("cvFile") MultipartFile cvFile,
            @RequestParam("offreId") Long offreId,
            Authentication authentication) {

        try {
            if (authentication == null || authentication.getName() == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(new ErrorResponse("Utilisateur non authentifie"));
            }

            if (cvFile == null || cvFile.isEmpty()) {
                return ResponseEntity.badRequest().body(new ErrorResponse("Fichier CV vide"));
            }

            Utilisateur candidat = utilisateurRepository.findByUsername(authentication.getName());
            if (candidat == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(new ErrorResponse("Utilisateur introuvable"));
            }

            OffreEmploi offre = offreRepository.findById(offreId)
                    .orElseThrow(() -> new NoSuchElementException("Offre non trouvee: " + offreId));

            if (candidatureRepository.existsByCandidatIdAndOffreId(candidat.getId(), offreId)) {
                return ResponseEntity.status(HttpStatus.CONFLICT).body(new ErrorResponse("Vous avez deja postule a cette offre"));
            }

            Map<String, Object> extractedCv = extractCVFromRAG(cvFile);
            Map<String, Object> offrePayload = convertOffreToDTO(offre);
            CVScoringResultDTO scoringResult = scoreViaRAG(extractedCv, offrePayload);

            CV cv = CV.builder()
                    .fileName(cvFile.getOriginalFilename())
                    .data(cvFile.getBytes())
                    .extractedText(String.valueOf(extractedCv.getOrDefault("resume", "")))
                    .candidat(candidat)
                    .build();
            CV persistedCv = cvRepository.save(cv);

            Candidature candidature = Candidature.builder()
                    .candidat(candidat)
                    .offre(offre)
                    .cv(persistedCv)
                    .dateCandidature(LocalDateTime.now())
                    .statut(StatutCandidature.ENVOYEE)
                    .overallScore(scoringResult.getOverallScore())
                    .scoreExplanation(scoringResult.getScoreExplanation())
                    .build();
            Candidature saved = candidatureRepository.save(candidature);

            return ResponseEntity.ok(new ApplyResponse(
                    "SUCCESS",
                    saved.getId(),
                    scoringResult.getOverallScore(),
                    scoringResult.getScoreExplanation(),
                    "Candidature enregistree avec score"
            ));
        } catch (NoSuchElementException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(new ErrorResponse(e.getMessage()));
        } catch (RAGException e) {
            return ResponseEntity.status(e.getStatus()).body(new ErrorResponse(e.getMessage()));
        } catch (Exception e) {
            log.error("Erreur inattendue apply-for-offer", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new ErrorResponse("Erreur serveur: " + e.getMessage()));
        }
    }

    @GetMapping("/applications-by-offer")
    public ResponseEntity<?> getApplicationsByOffer(@RequestParam("offreId") Long offreId) {
        try {
            List<Candidature> candidatures = candidatureRepository.findByOffreIdOrderByDateCandidatureDesc(offreId);
            List<Map<String, Object>> payload = candidatures.stream().map(item -> {
                Map<String, Object> row = new HashMap<>();
                row.put("candidatureId", item.getId());
                row.put("dateCandidature", item.getDateCandidature());
                row.put("statut", item.getStatut() != null ? item.getStatut().name() : null);
                row.put("overallScore", item.getOverallScore());
                row.put("scoreExplanation", item.getScoreExplanation());
                row.put("candidat", item.getCandidat() != null ? item.getCandidat().getUsername() : null);
                row.put("cvId", item.getCv() != null ? item.getCv().getId() : null);
                row.put("cvFileName", item.getCv() != null ? item.getCv().getFileName() : null);
                return row;
            }).toList();

            return ResponseEntity.ok(payload);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new ErrorResponse("Erreur lecture candidatures: " + e.getMessage()));
        }
    }

    @PostMapping("/chatbot-cv-advice")
    public ResponseEntity<?> chatbotCvAdvice(
            @RequestParam("cvFile") MultipartFile cvFile,
            @RequestParam("offreId") Long offreId,
            @RequestParam("question") String question) {

        try {
            if (cvFile == null || cvFile.isEmpty()) {
                return ResponseEntity.badRequest().body(new ErrorResponse("Fichier CV vide"));
            }

            if (question == null || question.trim().length() < 2) {
                return ResponseEntity.badRequest().body(new ErrorResponse("Question invalide"));
            }

            OffreEmploi offre = offreRepository.findById(offreId)
                    .orElseThrow(() -> new NoSuchElementException("Offre non trouvee: " + offreId));

            Map<String, Object> extractedCv = extractCVFromRAG(cvFile);
            Map<String, Object> offrePayload = convertOffreToDTO(offre);
            Map<String, Object> answer = chatbotViaRAG(extractedCv, offrePayload, question.trim());

            return ResponseEntity.ok(new ChatbotResponse("SUCCESS", answer, "Conseils generes"));
        } catch (NoSuchElementException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(new ErrorResponse(e.getMessage()));
        } catch (RAGException e) {
            return ResponseEntity.status(e.getStatus()).body(new ErrorResponse(e.getMessage()));
        } catch (Exception e) {
            log.error("Erreur inattendue chatbot-cv-advice", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new ErrorResponse("Erreur serveur: " + e.getMessage()));
        }
    }

    private Map<String, Object> extractCVFromRAG(MultipartFile cvFile) {
        String url = ragServiceUrl + "/api/extract-cv";

        try {
            ByteArrayResource fileResource = new ByteArrayResource(cvFile.getBytes()) {
                @Override
                public String getFilename() {
                    return cvFile.getOriginalFilename() != null ? cvFile.getOriginalFilename() : "cv.pdf";
                }
            };

            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("file", fileResource);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);

            HttpEntity<MultiValueMap<String, Object>> request = new HttpEntity<>(body, headers);
            ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);

            if (!response.getStatusCode().is2xxSuccessful() || response.getBody() == null) {
                throw new RAGException(HttpStatus.BAD_GATEWAY, "Reponse invalide du service RAG (extract-cv)");
            }

            Map<String, Object> responseBody = response.getBody();
            if (!"SUCCESS".equals(String.valueOf(responseBody.get("status")))) {
                String message = String.valueOf(responseBody.getOrDefault("message", "Erreur extraction CV"));
                throw new RAGException(resolveRagErrorStatus(message), message);
            }

            Object data = responseBody.get("data");
            if (!(data instanceof Map<?, ?> dataMap)) {
                throw new RAGException(HttpStatus.BAD_GATEWAY, "Format de CV extrait invalide");
            }

            return new HashMap<>((Map<String, Object>) dataMap);

        } catch (ResourceAccessException e) {
            throw new RAGException(HttpStatus.SERVICE_UNAVAILABLE, "Service RAG indisponible");
        } catch (HttpStatusCodeException e) {
            HttpStatus status = HttpStatus.resolve(e.getStatusCode().value());
            throw new RAGException(status != null ? status : HttpStatus.BAD_GATEWAY, "Echec appel RAG extract-cv: " + e.getResponseBodyAsString());
        } catch (RestClientException e) {
            throw new RAGException(HttpStatus.BAD_GATEWAY, "Echec appel RAG extract-cv: " + e.getMessage());
        } catch (Exception e) {
            throw new RAGException(HttpStatus.BAD_GATEWAY, "Erreur extraction CV: " + e.getMessage());
        }
    }

    private CVScoringResultDTO scoreViaRAG(Map<String, Object> cv, Map<String, Object> offre) {
        String url = ragServiceUrl + "/api/score-cv-vs-offer";

        try {
            Map<String, Object> payload = new HashMap<>();
            payload.put("cv", cv);
            payload.put("offre", offre);

            HttpEntity<Map<String, Object>> request = new HttpEntity<>(payload, createJsonHeaders());
            ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);

            if (!response.getStatusCode().is2xxSuccessful() || response.getBody() == null) {
                throw new RAGException(HttpStatus.BAD_GATEWAY, "Reponse invalide du service RAG (score)");
            }

            Map<String, Object> body = response.getBody();
            if (!"SUCCESS".equals(String.valueOf(body.get("status")))) {
                String message = String.valueOf(body.getOrDefault("message", "Erreur de scoring RAG"));
                throw new RAGException(resolveRagErrorStatus(message), message);
            }

            Object data = body.get("data");
            if (!(data instanceof Map<?, ?> dataMap)) {
                throw new RAGException(HttpStatus.BAD_GATEWAY, "Format de score invalide");
            }

            return toScoringDto((Map<String, Object>) dataMap);

        } catch (ResourceAccessException e) {
            throw new RAGException(HttpStatus.SERVICE_UNAVAILABLE, "Service RAG indisponible");
        } catch (HttpStatusCodeException e) {
            HttpStatus status = HttpStatus.resolve(e.getStatusCode().value());
            throw new RAGException(status != null ? status : HttpStatus.BAD_GATEWAY, "Echec appel RAG score: " + e.getResponseBodyAsString());
        } catch (RestClientException e) {
            throw new RAGException(HttpStatus.BAD_GATEWAY, "Echec appel RAG score: " + e.getMessage());
        }
    }

    private Map<String, Object> chatbotViaRAG(Map<String, Object> cv, Map<String, Object> offre, String question) {
        String url = ragServiceUrl + "/api/chatbot/cv-improvement";

        try {
            Map<String, Object> payload = new HashMap<>();
            payload.put("question", question);
            payload.put("cv", cv);
            payload.put("offre", offre);
            payload.put("history", List.of());

            HttpEntity<Map<String, Object>> request = new HttpEntity<>(payload, createJsonHeaders());
            ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);

            if (!response.getStatusCode().is2xxSuccessful() || response.getBody() == null) {
                throw new RAGException(HttpStatus.BAD_GATEWAY, "Reponse invalide du service RAG (chatbot)");
            }

            Map<String, Object> body = response.getBody();
            if (!"SUCCESS".equals(String.valueOf(body.get("status")))) {
                String message = String.valueOf(body.getOrDefault("message", "Erreur chatbot RAG"));
                throw new RAGException(resolveRagErrorStatus(message), message);
            }

            Object data = body.get("data");
            if (!(data instanceof Map<?, ?> dataMap)) {
                throw new RAGException(HttpStatus.BAD_GATEWAY, "Format de reponse chatbot invalide");
            }

            Map<String, Object> mapped = new HashMap<>((Map<String, Object>) dataMap);
            mapped.put("answer", String.valueOf(mapped.getOrDefault("answer", "")));
            mapped.put("pointsForts", toStringList(mapped.get("strengths")));
            mapped.put("pointsARenforcer", toStringList(mapped.get("improvement_areas")));
            mapped.put("actionItems", toStringList(mapped.get("action_items")));
            mapped.put("rewrittenBullets", toStringList(mapped.get("rewritten_bullets")));
            return mapped;
        } catch (ResourceAccessException e) {
            throw new RAGException(HttpStatus.SERVICE_UNAVAILABLE, "Service chatbot RAG indisponible");
        } catch (HttpStatusCodeException e) {
            HttpStatus status = HttpStatus.resolve(e.getStatusCode().value());
            throw new RAGException(status != null ? status : HttpStatus.BAD_GATEWAY, "Echec appel RAG chatbot: " + e.getResponseBodyAsString());
        } catch (RestClientException e) {
            throw new RAGException(HttpStatus.BAD_GATEWAY, "Echec appel RAG chatbot: " + e.getMessage());
        }
    }

    private HttpStatus resolveRagErrorStatus(String message) {
        String lower = message != null ? message.toLowerCase() : "";
        if (lower.contains("429") || lower.contains("rate limit") || lower.contains("limite openai embeddings atteinte")) {
            return HttpStatus.TOO_MANY_REQUESTS;
        }
        return HttpStatus.BAD_GATEWAY;
    }

    private CVScoringResultDTO toScoringDto(Map<String, Object> data) {
        int overallScore = toInt(data.get("overall_score"));
        String explanation = String.valueOf(data.getOrDefault("explanation", "Analyse terminee"));

        return CVScoringResultDTO.builder()
                .overallScore(overallScore)
                .scoreExplanation(explanation)
                .strengths(toStringList(data.get("strengths")))
                .gaps(toGapList(data.get("gaps")))
                .improvements(toStringList(data.get("improvements")))
                .subScores(toIntMap(data.get("sub_scores")))
                .status(String.valueOf(data.getOrDefault("status", "SUCCESS")))
                .build();
    }

    private Map<String, Object> convertOffreToDTO(OffreEmploi offre) {
        Map<String, Object> dto = new HashMap<>();
        dto.put("id", offre.getId());
        dto.put("titre", offre.getTitre() != null ? offre.getTitre() : "");
        dto.put("description", offre.getDescription() != null ? offre.getDescription() : "");
        dto.put("entreprise", offre.getEntreprise() != null ? offre.getEntreprise() : "");
        dto.put("localisation", offre.getLocalisation() != null ? offre.getLocalisation() : "");
        dto.put("mode_travail", offre.getModeTravail() != null ? offre.getModeTravail().name() : "ON_SITE");
        dto.put("type_contrat", offre.getTypeContrat() != null ? offre.getTypeContrat().name() : "CDI");
        dto.put("responsabilites", offre.getResponsabilites() != null ? offre.getResponsabilites() : List.of());
        dto.put("profil_recherche", offre.getProfilRecherche() != null ? offre.getProfilRecherche() : List.of());
        dto.put("a_propos_role", offre.getAProposRole());
        dto.put("a_propos_entreprise", offre.getAProposEntreprise());
        return dto;
    }

    private HttpHeaders createJsonHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.setAccept(List.of(MediaType.APPLICATION_JSON));
        return headers;
    }

    private int toInt(Object value) {
        if (value instanceof Number number) {
            return (int) Math.round(number.doubleValue());
        }
        return 0;
    }

    private List<String> toStringList(Object value) {
        if (!(value instanceof List<?> values)) {
            return List.of();
        }
        List<String> mapped = new ArrayList<>();
        for (Object item : values) {
            if (item != null) {
                mapped.add(String.valueOf(item));
            }
        }
        return mapped;
    }

    private List<CVScoringResultDTO.GapDTO> toGapList(Object value) {
        if (!(value instanceof List<?> values)) {
            return List.of();
        }

        List<CVScoringResultDTO.GapDTO> mapped = new ArrayList<>();
        for (Object gap : values) {
            if (gap instanceof Map<?, ?> gapMap) {
                Object requirementValue = gapMap.containsKey("requirement") ? gapMap.get("requirement") : gapMap.get("name");
                String requirement = String.valueOf(requirementValue != null ? requirementValue : "Gap");
                Object reasonValue = gapMap.get("reason");
                String reason = String.valueOf(reasonValue != null ? reasonValue : "Point a ameliorer");
                Object impactValue = gapMap.get("impact");
                int impact = toInt(impactValue != null ? impactValue : 10);
                mapped.add(CVScoringResultDTO.GapDTO.builder()
                        .requirement(requirement)
                        .reason(reason)
                        .impact(impact)
                        .build());
            } else if (gap != null) {
                mapped.add(CVScoringResultDTO.GapDTO.builder()
                        .requirement(String.valueOf(gap))
                        .reason("Point a ameliorer")
                        .impact(10)
                        .build());
            }
        }
        return mapped;
    }

    private Map<String, Integer> toIntMap(Object value) {
        if (!(value instanceof Map<?, ?> rawMap)) {
            return Map.of();
        }
        Map<String, Integer> mapped = new HashMap<>();
        rawMap.forEach((key, val) -> mapped.put(String.valueOf(key), toInt(val)));
        return mapped;
    }

    private static class RAGException extends RuntimeException {
        private final HttpStatus status;

        private RAGException(HttpStatus status, String message) {
            super(message);
            this.status = status;
        }

        public HttpStatus getStatus() {
            return status;
        }
    }

    public static class ScoreResponse {
        public String status;
        public CVScoringResultDTO data;
        public String message;

        public ScoreResponse(String status, CVScoringResultDTO data, String message) {
            this.status = status;
            this.data = data;
            this.message = message;
        }
    }

    public static class ErrorResponse {
        public String status = "ERROR";
        public String message;

        public ErrorResponse(String message) {
            this.message = message;
        }
    }

    public static class ApplyResponse {
        public String status;
        public Long candidatureId;
        public Integer overallScore;
        public String scoreExplanation;
        public String message;

        public ApplyResponse(String status, Long candidatureId, Integer overallScore, String scoreExplanation, String message) {
            this.status = status;
            this.candidatureId = candidatureId;
            this.overallScore = overallScore;
            this.scoreExplanation = scoreExplanation;
            this.message = message;
        }
    }

    public static class ChatbotResponse {
        public String status;
        public Map<String, Object> data;
        public String message;

        public ChatbotResponse(String status, Map<String, Object> data, String message) {
            this.status = status;
            this.data = data;
            this.message = message;
        }
    }
}