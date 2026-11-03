package com.vulnsuite.jolokia;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

// Spring Boot + Actuator with Jolokia on the classpath. Jolokia bridges HTTP to
// JMX (read/write/exec MBean operations). It is only reachable when Actuator is
// over-exposed (MANAGEMENT_ENDPOINTS_WEB_EXPOSURE_INCLUDE), set per state.
@SpringBootApplication
public class JolokiaDemoApplication {
    public static void main(String[] args) {
        SpringApplication.run(JolokiaDemoApplication.class, args);
    }
}
