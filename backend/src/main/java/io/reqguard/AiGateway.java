package io.reqguard;

import com.fasterxml.jackson.databind.JsonNode;
import java.net.http.HttpClient;
import java.time.Duration;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

@Component
public class AiGateway {
  private final RestClient client;

  public AiGateway(@Value("${ai.url}") String url) {
    var factory =
        new JdkClientHttpRequestFactory(
            HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(3)).build());
    factory.setReadTimeout(Duration.ofSeconds(30));
    client = RestClient.builder().baseUrl(url).requestFactory(factory).build();
  }

  public JsonNode evaluate(String text, String priority, String mode) {
    return client
        .post()
        .uri("/evaluate")
        .body(Map.of("text", text, "priority", priority, "mode", mode))
        .retrieve()
        .body(JsonNode.class);
  }

  public JsonNode benchmark() {
    return client.get().uri("/benchmark").retrieve().body(JsonNode.class);
  }
}
