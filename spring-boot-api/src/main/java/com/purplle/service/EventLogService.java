package com.purplle.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.purplle.entity.Event;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;

@Service
public class EventLogService {

    private final Path logPath;
    private final ObjectMapper mapper;

    public EventLogService(@Value("${store.event.log.path:event_log.jsonl}") String logFilePath) {
        this.logPath = Paths.get(logFilePath);
        this.mapper = new ObjectMapper();
        this.mapper.registerModule(new JavaTimeModule());
        this.mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
    }

    public synchronized void logEvent(Event event) {
        try {
            if (logPath.getParent() != null) {
                Files.createDirectories(logPath.getParent());
            }
            String json = mapper.writeValueAsString(event);
            Files.writeString(logPath, json + System.lineSeparator(), StandardOpenOption.CREATE, StandardOpenOption.APPEND);
        } catch (IOException e) {
            System.err.println("❌ Unable to write event log: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
