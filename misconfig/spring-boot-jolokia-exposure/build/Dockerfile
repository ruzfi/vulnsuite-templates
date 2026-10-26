# Stock Spring Boot + Actuator + Jolokia, built from source. Jolokia is exposed
# over HTTP only when Actuator's web exposure is widened
# (MANAGEMENT_ENDPOINTS_WEB_EXPOSURE_INCLUDE), which is the per-state toggle.
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /src
COPY pom.xml .
RUN mvn -q -B dependency:go-offline || true
COPY src ./src
RUN mvn -q -B package -DskipTests

FROM eclipse-temurin:17-jre
COPY --from=build /src/target/jolokiademo-0.0.1.jar /app.jar
EXPOSE 8080
CMD ["java", "-jar", "/app.jar"]
