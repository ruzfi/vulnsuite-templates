# A stock Spring Boot + Actuator app, built from source. Actuator's web
# exposure is a runtime setting (MANAGEMENT_ENDPOINTS_WEB_EXPOSURE_INCLUDE), so
# the same image is safe or over-exposed depending only on that env var.
FROM maven:3.9-eclipse-temurin-17@sha256:1a352420f7aba21f5ad08df31bab55f74c013fb491f1ae8ab1dd7ff9ed698584 AS build
WORKDIR /src
COPY pom.xml .
RUN mvn -q -B dependency:go-offline || true
COPY src ./src
RUN mvn -q -B package -DskipTests

FROM eclipse-temurin:17-jre@sha256:e04fa72be13b257a59fdec6dc14af78c8f80f035d3c1ed4e03e45552a231d4c8
COPY --from=build /src/target/actuatordemo-0.0.1.jar /app.jar
EXPOSE 8080
CMD ["java", "-jar", "/app.jar"]
