package com.ensam.SmartHire.service;
import org.apache.pdfbox.Loader;
import org.apache.pdfbox.io.RandomAccessRead;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;

@Service
public class Pdfservice {

    public String readPdf(MultipartFile file) throws IOException {
        try (PDDocument document = Loader.loadPDF(file.getBytes())) {
            PDFTextStripper pdfTextStripper = new PDFTextStripper();
            String text = pdfTextStripper.getText(document);
            document.close();
            String cleantext = text.replaceAll("[^\\p{L}\\p{N}\\s:,.()\\-]", " ")
                    .replaceAll("—", "-")
                    .replaceAll("\\s+", " ")
                    .trim();

            return cleantext;
        }
    }
}
