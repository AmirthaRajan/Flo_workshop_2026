package com.flo.workshop;

import java.io.IOException;
import java.net.Inet6Address;
import java.net.InetAddress;
import java.net.URI;
import java.net.UnknownHostException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

import dev.langchain4j.data.document.Document;
import dev.langchain4j.data.document.Metadata;
import dev.langchain4j.data.document.loader.FileSystemDocumentLoader;
import dev.langchain4j.data.document.parser.apache.tika.ApacheTikaDocumentParser;
import dev.langchain4j.data.document.transformer.jsoup.HtmlToTextDocumentTransformer;
import org.jsoup.Jsoup;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

/** Load workshop knowledge sources into LangChain4j Documents (equivalent of {@code loaders.py}). */
@Component
public class DocumentLoaders {

    private final WorkshopSettings settings;

    public DocumentLoaders(WorkshopSettings settings) {
        this.settings = settings;
    }

    /** Save an upload locally so it can be inspected after the workshop. */
    public Path saveUploadedFile(MultipartFile uploadedFile) throws IOException {
        Path documentsDir = Files.createDirectories(Path.of(settings.documentsPath()));
        // Keep only the filename so an upload cannot write outside the data folder.
        Path fileName = Path.of(String.valueOf(uploadedFile.getOriginalFilename())).getFileName();
        if (fileName == null || fileName.toString().equals("..")) {
            throw new IllegalArgumentException("The uploaded file has no usable name.");
        }
        Path filePath = documentsDir.resolve(fileName);
        uploadedFile.transferTo(filePath.toAbsolutePath());
        return filePath;
    }

    /** Load a PDF or DOCX file. Apache Tika detects the real format, including Confluence MHTML exports. */
    public Document loadFile(Path path) {
        String name = path.getFileName().toString().toLowerCase();
        if (!name.endsWith(".pdf") && !name.endsWith(".docx")) {
            throw new IllegalArgumentException("Unsupported file type. Please upload a PDF or DOCX file.");
        }
        Document document = FileSystemDocumentLoader.loadDocument(path, new ApacheTikaDocumentParser());
        document.metadata().put("source", path.getFileName().toString());
        return document;
    }

    /** Extract readable text from a public or locally accessible web page. */
    public Document loadUrl(String url) throws IOException {
        URI uri = URI.create(url);
        if (!("http".equals(uri.getScheme()) || "https".equals(uri.getScheme())) || uri.getHost() == null) {
            throw new IllegalArgumentException("Enter a complete URL beginning with http:// or https://.");
        }
        if (uri.getUserInfo() != null) {
            throw new IllegalArgumentException("URLs containing usernames or passwords are not supported.");
        }
        if (!settings.allowPrivateUrls() && !Arrays.stream(resolve(uri.getHost())).allMatch(DocumentLoaders::isPublic)) {
            throw new IllegalArgumentException("Private network URLs are blocked. Set ALLOW_PRIVATE_URLS=true "
                    + "only when intentionally loading a trusted internal wiki.");
        }

        // Redirects are not followed so a public URL cannot bounce us into the private network.
        String html = Jsoup.connect(url).userAgent("RAG-Workshop/1.0").timeout(15_000).followRedirects(false).get().html();
        Document page = new HtmlToTextDocumentTransformer().transform(Document.from(html, Metadata.from("source", url)));
        if (page.text().isBlank()) {
            throw new IllegalArgumentException("No readable text was found at that URL.");
        }
        return page;
    }

    /** Resolve a hostname; overridable so tests do not depend on DNS. */
    protected InetAddress[] resolve(String host) {
        try {
            return InetAddress.getAllByName(host);
        } catch (UnknownHostException error) {
            throw new IllegalArgumentException("The URL hostname could not be resolved.", error);
        }
    }

    /** True for internet addresses; false for loopback, private, link-local and similar internal ranges. */
    static boolean isPublic(InetAddress address) {
        byte[] b = address.getAddress();
        boolean carrierGradeNat = b.length == 4 && (b[0] & 0xff) == 100 && (b[1] & 0xc0) == 64;
        boolean ipv6UniqueLocal = address instanceof Inet6Address && (b[0] & 0xfe) == 0xfc;
        return !(address.isAnyLocalAddress() || address.isLoopbackAddress() || address.isLinkLocalAddress()
                || address.isSiteLocalAddress() || address.isMulticastAddress() || carrierGradeNat || ipv6UniqueLocal);
    }
}
