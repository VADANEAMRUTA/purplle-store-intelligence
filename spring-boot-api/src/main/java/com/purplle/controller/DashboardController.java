package com.purplle.controller;

import com.purplle.entity.Event;
import com.purplle.entity.User;
import com.purplle.repository.EventRepository;
import com.purplle.repository.UserRepository;
import com.purplle.service.EventLogService;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

@RestController
@RequestMapping("/api")
public class DashboardController {

    @Autowired
    private EventRepository eventRepository;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private EventLogService eventLogService;

    private static final int MAX_CAPACITY = 50;
    private static final double OVERCROWD_PERCENTAGE = 0.8;
    private static final double CRITICAL_PERCENTAGE = 0.95;

    private int overcrowdThreshold = (int) (MAX_CAPACITY * OVERCROWD_PERCENTAGE);
    private int criticalThreshold = (int) (MAX_CAPACITY * CRITICAL_PERCENTAGE);
    private boolean alertAcknowledged = false;
    private LocalDateTime lastAcknowledgedAt = null;

    @PostConstruct
    public void initializeDemoData() {
        seedDemoUsers();
        seedDemoEvents();
    }

    private void seedDemoUsers() {
        if (userRepository.count() > 0) {
            return;
        }

        userRepository.save(new User("manager1", "manager123", "manager", "Ayesha Patel"));
        userRepository.save(new User("owner1", "owner123", "owner", "Karan Mehta"));
        userRepository.save(new User("security1", "security123", "security", "Nina Rao"));
        userRepository.save(new User("marketing1", "marketing123", "marketing", "Riya Kapoor"));
    }

    private void seedDemoEvents() {
        if (eventRepository.count() > 0) {
            return;
        }

        LocalDateTime now = LocalDateTime.now();
        for (int dayAgo = 0; dayAgo < 7; dayAgo++) {
            LocalDateTime base = now.minusDays(dayAgo).withHour(10).withMinute(0).withSecond(0).withNano(0);
            for (int eventIndex = 0; eventIndex < 8; eventIndex++) {
                Event entry = new Event();
                entry.setPersonId(String.valueOf(100 + dayAgo * 8 + eventIndex));
                entry.setEvent("ENTRY");
                entry.setTimestamp(base.plusMinutes(eventIndex * 45));
                entry.setDwellTimeSeconds(180 + eventIndex * 20);
                eventRepository.save(entry);

                Event exit = new Event();
                exit.setPersonId(entry.getPersonId());
                exit.setEvent("EXIT");
                exit.setTimestamp(base.plusMinutes(eventIndex * 45 + 22));
                exit.setDwellTimeSeconds(180 + eventIndex * 20);
                eventRepository.save(exit);
            }
        }
    }

    @PostMapping("/events")
    public ResponseEntity<?> receiveEvent(@RequestBody Map<String, Object> eventData) {
        try {
            String personId = eventData.get("personId") != null ? String.valueOf(eventData.get("personId")) : null;
            String eventType = null;
            if (eventData.get("eventType") != null) {
                eventType = String.valueOf(eventData.get("eventType"));
            } else if (eventData.get("event") != null) {
                eventType = String.valueOf(eventData.get("event"));
            }

            boolean isStaff = false;
            if (eventData.get("isStaff") != null) {
                isStaff = Boolean.parseBoolean(String.valueOf(eventData.get("isStaff")));
            } else if (eventData.get("staffMember") != null) {
                isStaff = Boolean.parseBoolean(String.valueOf(eventData.get("staffMember")));
            }

            if (personId == null || eventType == null || eventType.isBlank()) {
                return ResponseEntity.badRequest().body(Map.of("status", "error", "message", "personId and eventType are required."));
            }

            LocalDateTime timestamp;
            Object timestampObj = eventData.get("timestamp");
            if (timestampObj instanceof String) {
                String timestampText = (String) timestampObj;
                try {
                    timestamp = LocalDateTime.parse(timestampText, DateTimeFormatter.ISO_DATE_TIME);
                } catch (Exception parseError) {
                    try {
                        timestamp = OffsetDateTime.parse(timestampText, DateTimeFormatter.ISO_DATE_TIME).toLocalDateTime();
                    } catch (Exception convertError) {
                        timestamp = LocalDateTime.now();
                    }
                }
            } else {
                timestamp = LocalDateTime.now();
            }

            Event event = new Event(personId, eventType.toUpperCase(), timestamp);
            event.setStaffMember(isStaff);
            if (eventData.get("cameraId") != null) {
                event.setCameraId(String.valueOf(eventData.get("cameraId")));
            }
            if (eventData.get("zoneId") != null) {
                event.setZoneId(String.valueOf(eventData.get("zoneId")));
            }
            if (eventData.get("dwellTimeSeconds") != null) {
                try {
                    event.setDwellTimeSeconds(Integer.parseInt(String.valueOf(eventData.get("dwellTimeSeconds"))));
                } catch (NumberFormatException ignored) {
                }
            }

            eventRepository.save(event);
            eventLogService.logEvent(event);

            System.out.println("✅ Event saved: " + eventType + " - " + personId + " (staff=" + isStaff + ")");
            return ResponseEntity.ok(Map.of("status", "success", "id", String.valueOf(event.getId())));
        } catch (Exception e) {
            System.err.println("❌ Error: " + e.getMessage());
            e.printStackTrace();
            return ResponseEntity.status(500).body(Map.of("status", "error", "message", e.getMessage()));
        }
    }

    @PostMapping("/auth/register")
    public ResponseEntity<Map<String, Object>> register(@RequestBody RegisterRequest request) {
        Map<String, Object> response = new HashMap<>();
        if (request == null || request.username == null || request.password == null || request.role == null) {
            response.put("status", "error");
            response.put("message", "Username, password and role are required.");
            return ResponseEntity.badRequest().body(response);
        }

        if (userRepository.findByUsername(request.username).isPresent()) {
            response.put("status", "error");
            response.put("message", "Username already exists.");
            return ResponseEntity.badRequest().body(response);
        }

        String displayName = request.fullName == null || request.fullName.isBlank() ? request.username : request.fullName;
        User user = new User(request.username, request.password, request.role.toLowerCase(), displayName);
        userRepository.save(user);
        response.put("status", "success");
        response.put("message", "Registration complete.");
        return ResponseEntity.ok(response);
    }

    @PostMapping("/auth/login")
    public ResponseEntity<Map<String, Object>> login(@RequestBody LoginRequest request) {
        Map<String, Object> response = new HashMap<>();
        if (request == null || request.username == null || request.password == null) {
            response.put("status", "error");
            response.put("message", "Username and password are required.");
            return ResponseEntity.badRequest().body(response);
        }

        Optional<User> optionalUser = userRepository.findByUsername(request.username);
        if (optionalUser.isEmpty() || !optionalUser.get().getPassword().equals(request.password)) {
            response.put("status", "error");
            response.put("message", "Invalid username or password.");
            return ResponseEntity.status(401).body(response);
        }

        User user = optionalUser.get();
        user.setLastLogin(LocalDateTime.now());
        userRepository.save(user);

        response.put("status", "success");
        response.put("username", user.getUsername());
        response.put("fullName", user.getFullName());
        response.put("role", user.getRole());
        response.put("lastLogin", user.getLastLogin().toString());
        return ResponseEntity.ok(response);
    }

    @GetMapping("/auth/me")
    public ResponseEntity<Map<String, Object>> getCurrentUser(@RequestParam String username) {
        Optional<User> optionalUser = userRepository.findByUsername(username);
        if (optionalUser.isEmpty()) {
            return ResponseEntity.status(401).body(Map.of("status", "error", "message", "User not found."));
        }

        User user = optionalUser.get();
        Map<String, Object> response = new HashMap<>();
        response.put("username", user.getUsername());
        response.put("fullName", user.getFullName());
        response.put("role", user.getRole());
        response.put("lastLogin", user.getLastLogin() == null ? null : user.getLastLogin().toString());
        return ResponseEntity.ok(response);
    }

    @GetMapping("/dashboard")
    public ResponseEntity<Map<String, Object>> getDashboard() {
        Map<String, Object> stats = new HashMap<>();
        long entries = eventRepository.countByEventAndStaffMemberIsFalse("ENTRY");
        long exits = eventRepository.countByEventAndStaffMemberIsFalse("EXIT");
        long occupancy = entries - exits;
        double avgDwell = eventRepository.averageNonStaffDwellTime("EXIT");
        stats.put("entries", entries);
        stats.put("exits", exits);
        stats.put("occupancy", Math.max(occupancy, 0));
        stats.put("averageDwellMinutes", Math.round(avgDwell / 60.0));
        stats.put("alert", occupancy > 50 ? "⚠️ STORE CROWDED! Current occupancy: " + occupancy : null);
        stats.put("staffExcluded", true);
        return ResponseEntity.ok(stats);
    }

    @GetMapping("/events/recent")
    public ResponseEntity<List<Event>> getRecentEvents() {
        return ResponseEntity.ok(eventRepository.findTop20ByOrderByTimestampDesc());
    }

    @GetMapping("/events")
    public ResponseEntity<List<Event>> getEvents(@RequestParam(required = false) String eventType) {
        if (eventType != null && !eventType.isBlank()) {
            return ResponseEntity.ok(eventRepository.findAllEvents().stream()
                .filter(e -> eventType.equalsIgnoreCase(e.getEvent()))
                .toList());
        }
        return ResponseEntity.ok(eventRepository.findAllEvents());
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        Map<String, String> health = new HashMap<>();
        health.put("status", "UP");
        health.put("timestamp", LocalDateTime.now().toString());
        return ResponseEntity.ok(health);
    }

    @GetMapping("/dashboard/manager")
    public ResponseEntity<Map<String, Object>> getManagerDashboard() {
        Map<String, Object> data = new HashMap<>();
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime thirtyMinsAgo = now.minusMinutes(30);
        long entries30min = eventRepository.countNonStaffEntriesSince(thirtyMinsAgo);
        long exits30min = eventRepository.countNonStaffExitsSince(thirtyMinsAgo);
        long currentOccupancy = Math.max(0, entries30min - exits30min);
        data.put("currentOccupancy", currentOccupancy);
        data.put("todayEntries", eventRepository.countTodayNonStaffEntries());
        data.put("todayExits", eventRepository.countTodayNonStaffExits());
        List<Integer> hourlyTrends = new ArrayList<>();
        for (int i = 11; i >= 0; i--) {
            LocalDateTime hourStart = now.minusHours(i).withMinute(0).withSecond(0).withNano(0);
            LocalDateTime hourEnd = hourStart.plusHours(1);
            long count = eventRepository.countNonStaffEntriesBetween(hourStart, hourEnd);
            hourlyTrends.add((int) count);
        }
        data.put("hourlyTrends", hourlyTrends);
        long totalEntries = eventRepository.countTodayNonStaffEntries();
        double conversionRate = Math.min(45.0, totalEntries * 0.28);
        data.put("conversionRate", String.format("%.1f", conversionRate));
        String staffAlert;
        if (currentOccupancy > 40) staffAlert = "🔴 CRITICAL: Add 2+ staff members immediately";
        else if (currentOccupancy > 30) staffAlert = "🟡 HIGH TRAFFIC: Monitor checkout queue";
        else if (currentOccupancy > 20) staffAlert = "🟢 NORMAL: Current staffing sufficient";
        else staffAlert = "💡 OPTIMIZE: Consider reducing staff for cost savings";
        data.put("staffAlert", staffAlert);
        data.put("peakHours", getPeakHoursFromHistory());
        List<Event> recentEvents = eventRepository.findAllNonStaffEventsOrderByTimestampDesc().stream().limit(10).toList();
        data.put("recentEvents", recentEvents);
        int capacityPercent = (int) Math.min(100, (currentOccupancy * 100) / MAX_CAPACITY);
        data.put("capacityPercent", capacityPercent);
        return ResponseEntity.ok(data);
    }

    @GetMapping("/alerts/overcrowding")
    public ResponseEntity<Map<String, Object>> checkOvercrowding() {
        LocalDateTime thirtyMinsAgo = LocalDateTime.now().minusMinutes(30);
        long currentOccupancy = Math.max(0, eventRepository.countEntriesSince(thirtyMinsAgo) - eventRepository.countExitsSince(thirtyMinsAgo));

        Map<String, Object> alert = new HashMap<>();
        alert.put("currentOccupancy", currentOccupancy);
        alert.put("maxCapacity", MAX_CAPACITY);
        alert.put("threshold", overcrowdThreshold);
        alert.put("criticalThreshold", criticalThreshold);
        alert.put("safeSpace", Math.max(0, MAX_CAPACITY - currentOccupancy));
        alert.put("acknowledged", alertAcknowledged);

        if (currentOccupancy >= criticalThreshold) {
            alert.put("level", "CRITICAL");
            alert.put("message", "⚠️ CRITICAL: Store overcrowded! Immediate action required");
            alert.put("action", "Open all counters, request staff backup");
            alert.put("color", "red");
        } else if (currentOccupancy >= overcrowdThreshold) {
            alert.put("level", "WARNING");
            alert.put("message", "🟡 WARNING: High occupancy. Monitor closely");
            alert.put("action", "Open additional billing counters");
            alert.put("color", "orange");
        } else {
            alert.put("level", "NORMAL");
            alert.put("message", "✅ Normal occupancy levels");
            alert.put("action", "Continue normal operations");
            alert.put("color", "green");
            alertAcknowledged = false;
        }

        return ResponseEntity.ok(alert);
    }

    @PostMapping("/alerts/threshold")
    public ResponseEntity<Map<String, Object>> updateThreshold(@RequestBody Map<String, Object> payload) {
        Object thresholdObj = payload.get("threshold");
        if (thresholdObj == null) {
            return ResponseEntity.badRequest().body(Map.of("status", "error", "message", "threshold is required."));
        }

        try {
            int newThreshold = Integer.parseInt(String.valueOf(thresholdObj));
            overcrowdThreshold = Math.max(0, Math.min(newThreshold, MAX_CAPACITY));
            return ResponseEntity.ok(Map.of("status", "updated", "newThreshold", overcrowdThreshold));
        } catch (NumberFormatException e) {
            return ResponseEntity.badRequest().body(Map.of("status", "error", "message", "threshold must be a number."));
        }
    }

    @PostMapping("/alerts/acknowledge")
    public ResponseEntity<Map<String, Object>> acknowledgeAlert(@RequestBody Map<String, Object> payload) {
        alertAcknowledged = Boolean.parseBoolean(String.valueOf(payload.getOrDefault("acknowledged", "true")));
        lastAcknowledgedAt = LocalDateTime.now();
        return ResponseEntity.ok(Map.of("status", "acknowledged", "when", lastAcknowledgedAt.toString()));
    }

    @GetMapping("/dashboard/owner")
    public ResponseEntity<Map<String, Object>> getOwnerDashboard() {
        Map<String, Object> data = new HashMap<>();

        String[] days = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"};
        double[] revenue = {12500, 13200, 12800, 14100, 13800, 15200, 14800};
        int[] footfall = {145, 152, 148, 163, 158, 175, 168};

        List<Map<String, Object>> weeklyData = new ArrayList<>();
        for (int i = 0; i < 7; i++) {
            Map<String, Object> dayMap = new HashMap<>();
            dayMap.put("day", days[i]);
            dayMap.put("revenue", revenue[i]);
            dayMap.put("footfall", footfall[i]);
            weeklyData.add(dayMap);
        }

        data.put("weeklyData", weeklyData);

        Map<String, Object> storeComparison = new HashMap<>();
        storeComparison.put("Purplle Downtown", 12450);
        storeComparison.put("Purplle Mall", 15680);
        storeComparison.put("Purplle Plaza", 9870);
        data.put("storeComparison", storeComparison);

        data.put("totalRevenue", 124500);
        data.put("growthRate", 15.3);
        data.put("avgTicketSize", 875);
        data.put("totalFootfall", 12450);
        data.put("conversionRate", 28.5);

        return ResponseEntity.ok(data);
    }

    @GetMapping("/dashboard/security")
    public ResponseEntity<Map<String, Object>> getSecurityDashboard() {
        Map<String, Object> data = new HashMap<>();
        List<Event> recentEvents = eventRepository.findTop10ByOrderByTimestampDesc();
        Map<String, Integer> personFrequency = new HashMap<>();
        for (Event event : recentEvents) {
            String pid = event.getPersonId() == null ? "unknown" : event.getPersonId().toString();
            personFrequency.put(pid, personFrequency.getOrDefault(pid, 0) + 1);
        }
        List<String> suspiciousPersons = new ArrayList<>();
        for (Map.Entry<String, Integer> entry : personFrequency.entrySet()) {
            if (entry.getValue() >= 3) suspiciousPersons.add(entry.getKey());
        }
        data.put("suspiciousPersons", suspiciousPersons);
        LocalDateTime thirtyMinsAgo = LocalDateTime.now().minusMinutes(30);
        long currentOccupancy = eventRepository.countNonStaffEntriesSince(thirtyMinsAgo) - eventRepository.countNonStaffExitsSince(thirtyMinsAgo);
        data.put("currentOccupancy", Math.max(0, currentOccupancy));
        List<Map<String, Object>> incidents = new ArrayList<>();
        for (int idx = 0; idx < Math.min(5, recentEvents.size()); idx++) {
            Event event = recentEvents.get(idx);
            Map<String, Object> incident = new HashMap<>();
            incident.put("timestamp", event.getTimestamp());
            incident.put("type", event.getEvent());
            incident.put("personId", event.getPersonId());
            incident.put("severity", "ENTRY".equals(event.getEvent()) ? "Info" : "Warning");
            incidents.add(incident);
        }
        data.put("incidents", incidents);
        return ResponseEntity.ok(data);
    }

    @GetMapping("/dashboard/marketing")
    public ResponseEntity<Map<String, Object>> getMarketingDashboard() {
        Map<String, Object> data = new HashMap<>();
        List<Integer> totalContacts = new ArrayList<>();
        List<List<Integer>> heatmapData = new ArrayList<>();
        for (int day = 6; day >= 0; day--) {
            List<Integer> hourlyData = new ArrayList<>();
            LocalDateTime dayStart = LocalDateTime.now().minusDays(day).withHour(0).withMinute(0).withSecond(0).withNano(0);
            for (int hour = 0; hour < 24; hour++) {
                LocalDateTime hourStart = dayStart.plusHours(hour);
                LocalDateTime hourEnd = hourStart.plusHours(1);
                long count = eventRepository.countNonStaffEntriesBetween(hourStart, hourEnd);
                hourlyData.add((int) count);
            }
            heatmapData.add(hourlyData);
            totalContacts.add(hourlyData.stream().mapToInt(Integer::intValue).sum());
        }
        data.put("heatmapData", heatmapData);
        Map<Integer, Integer> hourPerformance = new HashMap<>();
        for (int hour = 0; hour < 24; hour++) hourPerformance.put(hour, 0);
        for (List<Integer> dayData : heatmapData) {
            for (int hour = 0; hour < dayData.size(); hour++) {
                hourPerformance.put(hour, hourPerformance.get(hour) + dayData.get(hour));
            }
        }
        List<Map.Entry<Integer, Integer>> sortedHours = new ArrayList<>(hourPerformance.entrySet());
        sortedHours.sort((a, b) -> b.getValue().compareTo(a.getValue()));
        List<String> topHours = new ArrayList<>();
        for (int i = 0; i < Math.min(5, sortedHours.size()); i++) topHours.add(sortedHours.get(i).getKey() + ":00");
        data.put("topHours", topHours);
        List<Event> allEvents = eventRepository.findAllNonStaffEventsOrderByTimestampDesc();
        Set<String> uniquePersons = new HashSet<>();
        Map<String, Integer> personVisits = new HashMap<>();
        for (Event event : allEvents) {
            String pid = event.getPersonId() == null ? "unknown" : event.getPersonId().toString();
            uniquePersons.add(pid);
            personVisits.put(pid, personVisits.getOrDefault(pid, 0) + 1);
        }
        long returningCustomers = personVisits.values().stream().filter(v -> v > 1).count();
        long newCustomers = uniquePersons.size() - returningCustomers;
        data.put("newCustomers", newCustomers);
        data.put("returningCustomers", returningCustomers);
        Map<String, Integer> campaignImpact = new HashMap<>();
        campaignImpact.put("before", 120);
        campaignImpact.put("during", 185);
        campaignImpact.put("after", 160);
        data.put("campaignImpact", campaignImpact);
        data.put("promotionROI", "12.5%");
        Map<String, String> weatherCorrelation = Map.of(
            "Sunny", "+8% footfall",
            "Rain", "-4% traffic",
            "Weekend", "+12% engagement"
        );
        data.put("weatherCorrelation", weatherCorrelation);
        return ResponseEntity.ok(data);
    }

    private List<Integer> getPeakHoursFromHistory() {
        List<Integer> peaks = new ArrayList<>();
        LocalDateTime now = LocalDateTime.now();
        for (int i = 0; i < 3; i++) {
            peaks.add((now.minusHours(i * 2).getHour() + 24) % 24);
        }
        return peaks;
    }

    private static class LoginRequest {
        public String username;
        public String password;
    }

    private static class RegisterRequest {
        public String username;
        public String password;
        public String role;
        public String fullName;
    }
}
