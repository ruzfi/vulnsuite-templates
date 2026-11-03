package com.vulnsuite.actuator;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

// A stock Spring Boot web app with Actuator on the classpath. By default only
// /actuator/health and /actuator/info are exposed over HTTP. Exposing more
// (e.g. /actuator/env) is a deployment setting, driven here per state by the
// MANAGEMENT_ENDPOINTS_WEB_EXPOSURE_INCLUDE environment variable.
@SpringBootApplication
public class ActuatorDemoApplication {
    public static void main(String[] args) {
        SpringApplication.run(ActuatorDemoApplication.class, args);
    }
}
