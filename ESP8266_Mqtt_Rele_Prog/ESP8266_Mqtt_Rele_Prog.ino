#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <EEPROM.h>

#define EEPROM_SIZE 512
#define DEVICE_ID "esp001"
#define RELAY_PIN 5 // Pin del relé (D1)

// WiFi configuration
const char* ssid = "IoT_Network";
const char* password = "107_NetWork";

// MQTT configuration
const char* mqtt_server = "192.168.12.1";//Raspberry 4 //"192.168.0.28";//MV//"192.168.4.1";//Raspberry 400
const char* topic_config = "CONFIG/" DEVICE_ID;
const char* topic_relay = "RELAY";
WiFiClient espClient;
PubSubClient client(espClient);

// Variables for device configuration
String zone = "";
String type = "";
// Variable for relay state
String state = "";
String zoneSet = "";
void setup() {
  Serial.begin(115200);
  EEPROM.begin(EEPROM_SIZE);
  loadConfig();

  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW); // Default state

  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);

  if (client.connect(DEVICE_ID)) {
    client.subscribe(topic_config);
    client.subscribe(topic_relay);
  }
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}

void setup_wifi() {
  delay(10);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");
}

void callback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  //lo siguiente comentado, con propósito de depuración
  //Serial.println("Recibido type: " + type + " Tópico: " + String(topic));
  // Handle configuration
  if (String(topic) == topic_config) {
    processConfig(message);
  }
  // Handle relay control
  else if (String(topic) == topic_relay && type == "relay") {
    processRelay(message);
    if (zone == zoneSet) {
      if (state == "ON") {
        digitalWrite(RELAY_PIN, HIGH);
        Serial.println("Relay ON");
      } else if (state == "OFF") {
        digitalWrite(RELAY_PIN, LOW);
        Serial.println("Relay OFF");
      }
    }
  }
}
void processRelay(String message){
  int zoneStart = message.indexOf("\"zone\":\"") + 8;
  int zoneEnd = message.indexOf("\"", zoneStart);
  zoneSet = message.substring(zoneStart, zoneEnd);
  int stateStart = message.indexOf("\"state\":\"") + 9;
  int stateEnd = message.indexOf("\"", stateStart);
  state = message.substring(stateStart, stateEnd);   
  Serial.println("Relay information received:");
  Serial.println("Relay message: " + message);
  Serial.println("Zone: " + zoneSet);
  Serial.println("State: " + state); 
}
void processConfig(String config) {
  int zoneStart = config.indexOf("\"zone\":\"") + 8;
  int zoneEnd = config.indexOf("\"", zoneStart);
  zone = config.substring(zoneStart, zoneEnd);

  int typeStart = config.indexOf("\"type\":\"") + 8;
  int typeEnd = config.indexOf("\"", typeStart);
  type = config.substring(typeStart, typeEnd);

  Serial.println("Configuration received:");
  Serial.println("Zone: " + zone);
  Serial.println("Type: " + type);

  saveConfig();
}

void saveConfig() {
  // Save zone
  for (int i = 0; i < zone.length(); i++) {
    EEPROM.write(i, zone[i]);
  }
  EEPROM.write(zone.length(), '\0');

  // Save type
  int offset = 100;
  for (int i = 0; i < type.length(); i++) {
    EEPROM.write(offset + i, type[i]);
  }
  EEPROM.write(offset + type.length(), '\0');

  EEPROM.commit();
  Serial.println("Configuration saved in EEPROM");
}

void loadConfig() {
  // Load zone
  char zoneBuffer[100];
  for (int i = 0; i < 100; i++) {
    zoneBuffer[i] = EEPROM.read(i);
    if (zoneBuffer[i] == '\0') break;
  }
  zone = String(zoneBuffer);

  // Load type
  char typeBuffer[100];
  int offset = 100;
  for (int i = 0; i < 100; i++) {
    typeBuffer[i] = EEPROM.read(offset + i);
    if (typeBuffer[i] == '\0') break;
  }
  type = String(typeBuffer);

  if (zone == "" || type == "") {
    Serial.println("No configuration found");
  } else {
    Serial.println("Configuration loaded from EEPROM:");
    Serial.println("Zone: " + zone);
    Serial.println("Type: " + type);
  }
}

void reconnect() {
  while (!client.connected()) {
    if (client.connect(DEVICE_ID)) {
      client.subscribe(topic_config);
      client.subscribe(topic_relay);
    } else {
      delay(5000);
    }
  }
}
