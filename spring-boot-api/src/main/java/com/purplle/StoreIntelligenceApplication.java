package com.purplle;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class StoreIntelligenceApplication {
    
    public static void main(String[] args) {
        SpringApplication.run(StoreIntelligenceApplication.class, args);
        System.out.println("""
                
                ╔════════════════════════════════════════╗
                ║   🏪 Purplle Store Intelligence API   ║
                ║        Running on http://localhost:8080    ║
                ║                                        ║
                ║  Endpoints:                            ║
                ║  POST /api/events     - Send event     ║
                ║  GET  /api/dashboard  - Get stats      ║
                ║  GET  /api/events     - List events    ║
                ║  GET  /api/health     - Health check   ║
                ╚════════════════════════════════════════╝
                """);
    }
}