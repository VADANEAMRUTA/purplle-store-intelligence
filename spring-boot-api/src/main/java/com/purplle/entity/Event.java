package com.purplle.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "events")
public class Event {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "person_id")
    private String personId;
    
    @Column(name = "event_type")
    private String event;
    
    @Column(name = "camera_id")
    private String cameraId;
    
    @Column(name = "zone_id")
    private String zoneId;
    
    @Column(name = "event_time")
    private LocalDateTime timestamp;
    
    @Column(name = "dwell_time_seconds")
    private Integer dwellTimeSeconds;

    @Column(name = "staff_member")
    private boolean staffMember = false;
    
    public Event() {}

    public Event(String personId, String eventType, LocalDateTime timestamp) {
        this.personId = personId;
        this.event = eventType;
        this.timestamp = timestamp;
    }
    
    // Getters
    public Long getId() { return id; }
    public String getPersonId() { return personId; }
    public String getEvent() { return event; }
    public boolean isStaffMember() { return staffMember; }
    public String getCameraId() { return cameraId; }
    public String getZoneId() { return zoneId; }
    public LocalDateTime getTimestamp() { return timestamp; }
    public Integer getDwellTimeSeconds() { return dwellTimeSeconds; }
    
    // Setters
    public void setId(Long id) { this.id = id; }
    public void setPersonId(String personId) { this.personId = personId; }
    public void setEvent(String event) { this.event = event; }
    public void setCameraId(String cameraId) { this.cameraId = cameraId; }
    public void setZoneId(String zoneId) { this.zoneId = zoneId; }
    public void setTimestamp(LocalDateTime timestamp) { this.timestamp = timestamp; }
    public void setDwellTimeSeconds(Integer dwellTimeSeconds) { this.dwellTimeSeconds = dwellTimeSeconds; }
    public void setStaffMember(boolean staffMember) { this.staffMember = staffMember; }

    public String getEventType() {
        return this.event;
    }

    public void setEventType(String eventType) {
        this.event = eventType;
    }
}