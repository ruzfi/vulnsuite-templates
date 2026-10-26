# A stock Spring Boot + Actuator app, built from source. Actuator's web
# exposure is a runtime setting (MANAGEMENT_ENDPOINTS_WEB_EXPOSURE_INCLUDE), so
# the same image is safe or over-exposed depending only on that env var.
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /src
COPY pom.xml .
RUN mvn -q -B dependency:go-offline || true
COPY src ./src
RUN mvn -q -B package -DskipTests

FROM eclipse-temurin:17-jre
COPY --from=build /src/target/actuatordemo-0.0.1.jar /app.jar
EXPOSE 8080
CMD ["java", "-jar", "/app.jar"]
