package com.purplle.repository;

import com.purplle.entity.Event;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDateTime;
import java.util.List;

public interface EventRepository extends JpaRepository<Event, Long> {

    long countByEvent(String event);

    long countByEventAndStaffMemberIsFalse(String event);

    @Query("SELECT COALESCE(AVG(e.dwellTimeSeconds), 0) FROM Event e WHERE e.event = :event")
    double averageDwellTime(@Param("event") String event);

    @Query("SELECT COALESCE(AVG(e.dwellTimeSeconds), 0) FROM Event e WHERE e.event = :event AND e.staffMember = false")
    double averageNonStaffDwellTime(@Param("event") String event);

    List<Event> findTop20ByOrderByTimestampDesc();

    // Real-data queries
    @Query("SELECT COUNT(e) FROM Event e WHERE e.event = 'ENTRY' AND e.staffMember = false AND e.timestamp >= :time")
    long countNonStaffEntriesSince(@Param("time") LocalDateTime time);

    @Query("SELECT COUNT(e) FROM Event e WHERE e.event = 'EXIT' AND e.staffMember = false AND e.timestamp >= :time")
    long countNonStaffExitsSince(@Param("time") LocalDateTime time);

    @Query("SELECT COUNT(e) FROM Event e WHERE e.event = 'ENTRY' AND e.staffMember = false AND e.timestamp BETWEEN :start AND :end")
    long countNonStaffEntriesBetween(@Param("start") LocalDateTime start, @Param("end") LocalDateTime end);

    @Query("SELECT COUNT(e) FROM Event e WHERE e.event = 'ENTRY' AND e.staffMember = false AND CAST(e.timestamp AS DATE) = CURRENT_DATE")
    long countTodayNonStaffEntries();

    @Query("SELECT COUNT(e) FROM Event e WHERE e.event = 'ENTRY' AND e.timestamp >= :time")
    long countEntriesSince(@Param("time") LocalDateTime time);

    @Query("SELECT COUNT(e) FROM Event e WHERE e.event = 'EXIT' AND e.timestamp >= :time")
    long countExitsSince(@Param("time") LocalDateTime time);

    List<Event> findTop10ByOrderByTimestampDesc();

    @Query("SELECT COUNT(e) FROM Event e WHERE e.event = 'EXIT' AND e.staffMember = false AND CAST(e.timestamp AS DATE) = CURRENT_DATE")
    long countTodayNonStaffExits();

    @Query("SELECT e FROM Event e WHERE e.staffMember = false ORDER BY e.timestamp DESC")
    List<Event> findAllNonStaffEventsOrderByTimestampDesc();

    @Query("SELECT e FROM Event e ORDER BY e.timestamp DESC")
    List<Event> findAllEvents();

    @Modifying
    @Transactional
    @Query("DELETE FROM Event")
    void deleteAllEvents();

    @Query("SELECT COUNT(e) FROM Event e WHERE e.event = 'ENTRY' AND CAST(e.timestamp AS DATE) = CURRENT_DATE")
    long countTodayEntries();

    @Query("SELECT COUNT(e) FROM Event e WHERE e.event = 'EXIT' AND CAST(e.timestamp AS DATE) = CURRENT_DATE")
    long countTodayExits();
}