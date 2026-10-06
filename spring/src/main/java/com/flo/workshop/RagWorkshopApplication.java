package com.flo.workshop;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

/** Entry point for the Project Onboarding RAG workshop (Spring + LangChain4j edition). */
@SpringBootApplication
@ConfigurationPropertiesScan
public class RagWorkshopApplication {

    public static void main(String[] args) {
        SpringApplication.run(RagWorkshopApplication.class, args);
    }
}
