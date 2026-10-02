FROM maven:3.9.11-eclipse-temurin-17 AS build
WORKDIR /build
COPY backend/pom.xml ./
COPY backend/src ./src
RUN mvn -B -ntp verify
FROM eclipse-temurin:17-jre
WORKDIR /srv
RUN useradd --uid 10001 --create-home reqguard
COPY --from=build /build/target/reqguard-0.1.0.jar app.jar
USER reqguard
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/srv/app.jar"]
