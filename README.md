# Mediola Shutters Integration für Home Assistant

This Integration makes it possible to use shutters commected to a Mediola Gateway in Home Assistant. As Mediola seems to be a pure German system this readme is also in German. If you try to use it, please use an autotranslator of your choice to translate this readme. The frontend itself is translated to english and german.

Diese Integration ermöglicht die Steuerung von Rollos über ein Mediola Gateway in Home Assistant.

## 📋 Features

- ✅ Automatische Erkennung aller Rollos am Gateway
- ✅ Jedes Rollo als separates Gerät mit mehreren Entitäten
- ✅ Cover-Entität zum Öffnen, Schließen, Stoppen und Positionieren
- ✅ Positions-Sensor (0-100%)
- ✅ Binary Sensor für Öffnungsstatus
- ✅ Config Flow für einfache Installation
- ✅ Konfigurierbares Aktualisierungsintervall (Standard: 15 Sekunden)
- ✅ Eigene Services für erweiterte Steuerung
- ✅ Deutsche und englische Übersetzungen

## Bekannste Probleme
Die Integration wurde mit Rollos der Firma WiR erstellt, diese erzeugen einen Device-Code "WR", an diesem filtert die Integration Rollos aus. Wenn ihr Rollos anderer Hersteller benutzt, wird der Code ein anderer sein. Ihr könnt im Browser diese URL aufrufen: http://(mediola-ip)/command?XC_USER=user&XC_PASS=(passwort)&XC_FNC=GetStates
In der Antwort könnt ihr hinter "Type" das Herstellerkürzel sehen. Dieses muss in der const.py ausgetauscht werden. Bitte lasst mich wissen, wenn ihr es mit einem anderen Hersteller testen konntet und lasst mich den Type des Herstellers wissen, dann kann ich die Integration entsprechend erweitern.

## 🚀 Installation

### Methode 1: Manuell

1. Erstellen Sie das Verzeichnis `custom_components/mediola_shutters` in Ihrer Home Assistant Konfiguration
2. Kopieren Sie alle Dateien in dieses Verzeichnis:
   ```
   custom_components/mediola_shutters/
   ├── __init__.py
   ├── config_flow.py
   ├── const.py
   ├── cover.py
   ├── sensor.py
   ├── binary_sensor.py
   ├── mediola_api.py
   ├── manifest.json
   ├── strings.json
   ├── services.yaml
   └── translations/
       ├── de.json
       └── en.json
   ```
3. Starten Sie Home Assistant neu

## ⚙️ Konfiguration

1. Gehen Sie zu **Einstellungen** → **Geräte & Dienste**
2. Klicken Sie auf **Integration hinzufügen**
3. Suchen Sie nach "Mediola Shutters"
4. Geben Sie die folgenden Daten ein:
   - **IP-Adresse**: Die IP-Adresse Ihres Mediola Gateways (z.B. `192.168.178.64`)
   - **Benutzername**: Ihr Mediola Benutzername (dieser scheint von Mediola standardmäßig nicht verwendet zu werden, man kann hier einfach "user" eintragen)
   - **Passwort**: Ihr Mediola Passwort
   - **Aktualisierungsintervall**: Wie oft der Status abgefragt wird (5-300 Sekunden, Standard: 15)
5. Klicken Sie auf **Absenden**

### Aktualisierungsintervall ändern

Sie können das Aktualisierungsintervall jederzeit ändern:
1. Gehe zu **Einstellungen** → **Geräte & Dienste**
2. Finde "Mediola Shutters"
3. Klicke auf **Konfigurieren** (⚙️ Symbol)
4. Ändere das Aktualisierungsintervall
5. Die Integration wird automatisch neu geladen

## 📊 Entitäten

Für jedes Rollo werden folgende Entitäten erstellt:

### Cover (Rollladensteuerung)
- **Entity ID**: `cover.shutter_XX`
- **Funktionen**:
  - Öffnen (100%)
  - Schließen (0%)
  - Stoppen
  - Position setzen (0-100%)

### Positions-Sensor
- **Entity ID**: `sensor.shutter_XX_position`
- **Einheit**: Prozent (%)
- **Werte**: 0% = vollständig offen, 100% = vollständig geschlossen

### Öffnungsstatus
- **Entity ID**: `binary_sensor.shutter_XX_opening`
- **Werte**: 
  - `on` = Rollo ist offen
  - `off` = Rollo ist geschlossen

## 🔧 Services

Die Integration stellt folgende Services bereit:

### `mediola_shutters.open_shutter`
Öffnet ein bestimmtes Rollo vollständig.

```yaml
service: mediola_shutters.open_shutter
target:
  entity_id: cover.shutter_01
```

### `mediola_shutters.close_shutter`
Schließt ein bestimmtes Rollo vollständig.

```yaml
service: mediola_shutters.close_shutter
target:
  entity_id: cover.shutter_02
```

### `mediola_shutters.stop_shutter`
Stoppt ein bewegtes Rollo.

```yaml
service: mediola_shutters.stop_shutter
target:
  entity_id: cover.shutter_01
```

### `mediola_shutters.set_shutter_position`
Setzt ein Rollo auf eine bestimmte Position (0-100%).

```yaml
service: mediola_shutters.set_shutter_position
target:
  entity_id: cover.shutter_03
data:
  position: 50
```

### `mediola_shutters.open_all_shutters`
Öffnet alle Rollos gleichzeitig.

```yaml
service: mediola_shutters.open_all_shutters
```

### `mediola_shutters.close_all_shutters`
Schließt alle Rollos gleichzeitig.

```yaml
service: mediola_shutters.close_all_shutters
```

### `mediola_shutters.stop_all_shutters`
Stoppt alle bewegten Rollos gleichzeitig.

```yaml
service: mediola_shutters.stop_all_shutters
```

## 🔧 Verwendung in Automatisierungen

### Beispiel 1: Rollo bei Sonnenaufgang öffnen

```yaml
automation:
  - alias: "Rollo morgens öffnen"
    trigger:
      - platform: sun
        event: sunrise
        offset: "00:30:00"
    action:
      - service: mediola_shutters.open_shutter
        target:
          entity_id: cover.shutter_01
```

### Beispiel 2: Alle Rollos bei Sonnenuntergang schließen

```yaml
automation:
  - alias: "Alle Rollos abends schließen"
    trigger:
      - platform: sun
        event: sunset
        offset: "-00:30:00"
    action:
      - service: mediola_shutters.close_all_shutters
```

### Beispiel 3: Rollo auf 50% bei hoher Temperatur

```yaml
automation:
  - alias: "Rollo teilweise schließen bei Hitze"
    trigger:
      - platform: numeric_state
        entity_id: sensor.outdoor_temperature
        above: 28
    action:
      - service: mediola_shutters.set_shutter_position
        target:
          entity_id: cover.shutter_02
        data:
          position: 50
```

### Beispiel 4: Benachrichtigung wenn Rollo offen bleibt

```yaml
automation:
  - alias: "Warnung: Rollo nachts offen"
    trigger:
      - platform: time
        at: "22:00:00"
    condition:
      - condition: state
        entity_id: binary_sensor.shutter_01_opening
        state: "on"
    action:
      - service: notify.mobile_app
        data:
          message: "Rollo 1 ist noch offen!"
```

### Beispiel 5: Alle Rollos bei Wind stoppen

```yaml
automation:
  - alias: "Rollos bei starkem Wind stoppen"
    trigger:
      - platform: numeric_state
        entity_id: sensor.wind_speed
        above: 50
    action:
      - service: mediola_shutters.stop_all_shutters
```

## 🔍 Technische Details

### API-Kommunikation

Die Integration kommuniziert über HTTP mit dem Mediola Gateway:

- **Status abrufen**: `GET /command?XC_USER=...&XC_PASS=...&XC_FNC=GetStates`
- **Befehle senden**: `GET /command?XC_USER=...&XC_PASS=...&XC_FNC=SendSC&type=WR&data=...`

### Befehlsstruktur

- **Öffnen**: `01` + Adresse + `010101`
- **Schließen**: `01` + Adresse + `010102`
- **Stoppen**: `01` + Adresse + `010103`
- **Position**: `01` + Adresse + `0107` + Position (Hex)

### Positionswerte

- **Home Assistant**: 0 = geschlossen, 100 = offen
- **Mediola**: 0 = offen, 100 = geschlossen (wird automatisch umgerechnet)

### Aktualisierungsintervall

- **Standard**: 15 Sekunden
- **Konfigurierbar**: 5-300 Sekunden
- **Nach Befehl**: Sofortige Aktualisierung

## 🐛 Fehlerbehebung

### Problem: Keine Verbindung zum Gateway

1. Überprüfen Sie die IP-Adresse
2. Stellen Sie sicher, dass das Gateway im selben Netzwerk ist
3. Testen Sie die Verbindung manuell im Browser: `http://IP-ADRESSE/command?XC_USER=...&XC_PASS=...&XC_FNC=GetStates`

### Problem: Rollos werden nicht gefunden

1. Prüfen Sie, ob die Rollos im Gateway konfiguriert sind
2. Aktivieren Sie Debug-Logging:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.mediola_shutters: debug
   ```
3. Überprüfen Sie die Logs unter **Einstellungen** → **System** → **Protokolle**

### Problem: Befehle werden nicht ausgeführt

1. Überprüfen Sie die Benutzerdaten
2. Testen Sie Befehle manuell im Browser
3. Prüfen Sie die Logs auf Fehlermeldungen
4. Erhöhen Sie das Aktualisierungsintervall falls Timeouts auftreten

### Problem: Services werden nicht angezeigt

1. Starten Sie Home Assistant neu
2. Prüfen Sie, ob die `services.yaml` vorhanden ist
3. Überprüfen Sie die Logs auf Fehler beim Laden der Services

## 📝 Changelog

### Version 1.0.0
- Initiale Version
- Config Flow Support
- Cover, Sensor und Binary Sensor Entitäten
- Deutsche und englische Übersetzungen
- Konfigurierbares Aktualisierungsintervall (Standard: 15 Sekunden)
- 7 Services für erweiterte Steuerung
- Unterstützung für eigenes Icon

## 🤝 Beitragen

Fehler gefunden oder Verbesserungsvorschläge? Erstellen Sie ein Issue oder Pull Request auf GitHub!

## 📄 Lizenz

MIT License

## ⚠️ Haftungsausschluss

Diese Integration ist nicht offiziell von Mediola unterstützt. Verwendung auf eigene Gefahr.
 