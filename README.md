# Zeekr Home Assistant Integratie (7X)

Deze integratie verbindt jouw Zeekr (geoptimaliseerd voor de 7X) met Home Assistant via de officiële API. 

## 🔑 Installatie & Configuratie

Voor de installatie zijn specifieke tokens nodig die je moet onderscheppen uit het netwerkverkeer van de Zeekr app (bijvoorbeeld via een proxy zoals Charles of HTTP Toolkit):

- **X-VIN**: Het unieke identificatienummer van je voertuig.
- **Access Token**: Je autorisatie-token.
  - *Let op:* Dit token is momenteel slechts **één week geldig**. Hierna moet je het token handmatig vernieuwen in de configuratie.

## ✨ Functionaliteiten

### 🚗 Voertuig Status
- **Algemen voortuiginformatie:** Vin, kenteken, Softwareversie, locatie 
- **Batterij:** Accu percentage, actieradius, laadstatus en laadvermogen.
- **Banden:** Real-time bandenspanning en temperatuur per wiel.
- **Onderhoud:** Kilometerstand, afstand en dagen tot de volgende onderhoudsbeurt.
- **Klimaat:** Binnentemperatuur en status van de pre-conditioning. Klimaat met instelling voor snel verwarmen en snel koelen. Switch voor stuurverwarming en defrost.

### 📅 Reisplanning (Travel Plan)
- **Laad Planning:** Instellen limiet en laadtijden
- **Flexibele Planning:** Ondersteuning voor zowel eenmalige ritten (Dagelijks) als een wekelijks schema (Cyclus).
- **Update Knop:** Pas tijden en dagen aan in HA en "push" de hele planning naar de auto.

## ⚠️ Bekende Problemen (Known Issues)

Hoewel de integratie stabiel is, zijn er enkele bekende beperkingen (vaak gerelateerd aan de Zeekr API):

1. **Airco Bediening:** Net als in de officiële Zeekr app reageert de auto niet altijd op het 'Stop' commando voor de airco. Soms moet je de airco **twee keer handmatig uitzetten** voordat deze daadwerkelijk stopt.
2. **Token Refresh:** Omdat de Access Token verloopt na 7 dagen, moet de integratie daarna opnieuw worden ingesteld met een vers token.

## 🛠 Installatie
1. Kopieer de map `Zeekr_7x` naar je `custom_components` map.
2. Herstart Home Assistant.
3. Voeg de integratie toe en vul je `X-VIN` en `Access Token` in.

<img width="516" height="977" alt="image" src="https://github.com/user-attachments/assets/648973b0-06fd-410c-8c34-f5a4462d1324" />

<details>
  <summary><b>Klik hier om de Dashboard YAML te bekijken</b></summary>

  ```yaml
  type: custom:stack-in-card
  cards:
    - type: vertical-stack
      cards:
        - type: grid
          columns: 2
          square: false
          cards:
            - type: custom:mushroom-entity-card
              entity: sensor.zeekr_accu_percentage
              primary_info: name
              secondary_info: state
              icon_color: green
            - type: custom:mushroom-entity-card
              entity: sensor.zeekr_actieradius
              icon: mdi:map-marker-distance
              icon_color: blue
        - type: grid
          columns: 2
          square: false
          cards:
            - type: custom:mushroom-lock-card
              entity: lock.zeekr_deurslot
              name: Auto Slot
              fill_container: true
            - type: custom:mushroom-entity-card
              entity: button.zeekr_data_verversen
              name: Update Status
              icon: mdi:refresh
              primary_info: name
              tap_action:
                action: perform-action
                target:
                  entity_id: button.zeekr_data_verversen
                perform_action: button.press
        - type: custom:mushroom-climate-card
          entity: climate.zeekr_thermostaat
          show_temperature_control: true
          hvac_modes:
            - heat_cool
            - "off"
          fill_container: true
          collapsible_controls: false
        - type: picture-elements
          image: /local/images/zeekr_7x_top.png
          elements:
            - type: state-label
              entity: sensor.zeekr_bandenspanning_rv
              style:
                top: 15%
                left: 25%
                font-size: 14px
                font-weight: bold
            - type: state-label
              entity: sensor.zeekr_bandentemperatuur_rv
              style:
                top: 20%
                left: 25%
                font-size: 11px
                opacity: 0.8
            - type: state-label
              entity: sensor.zeekr_bandenspanning_ra
              style:
                top: 15%
                left: 75%
                font-size: 14px
                font-weight: bold
            - type: state-label
              entity: sensor.zeekr_bandentemperatuur_ra
              style:
                top: 20%
                left: 75%
                font-size: 11px
                opacity: 0.8
            - type: state-label
              entity: sensor.zeekr_bandenspanning_lv
              style:
                top: 80%
                left: 25%
                font-size: 14px
                font-weight: bold
            - type: state-label
              entity: sensor.zeekr_bandentemperatuur_lv
              style:
                top: 85%
                left: 25%
                font-size: 11px
                opacity: 0.8
            - type: state-label
              entity: sensor.zeekr_bandenspanning_la
              style:
                top: 80%
                left: 75%
                font-size: 14px
                font-weight: bold
            - type: state-label
              entity: sensor.zeekr_bandentemperatuur_la
              style:
                top: 85%
                left: 75%
                font-size: 11px
                opacity: 0.8
        - type: map
          entities:
            - entity: device_tracker.zeekr_locatie
          aspect_ratio: "16:9"
          default_zoom: 15

</details>


<img width="517" height="685" alt="image" src="https://github.com/user-attachments/assets/6c9bb838-7316-4e0b-b190-c4011d2dc27b" />

<details>
  <summary><b>Klik hier om de Ultra Vehicle Card YAML te bekijken</b></summary>

  ```yaml
  vehicle_image_type: default
  status_image_type: none
  layout_type: half_full
  formatted_entities: true
  show_location: true
  show_mileage: true
  show_car_state: true
  show_info_icons: true
  help_highlight: true
  sections_order:
    - title
    - info_row_bfcpdsw
    - info_row_5v6thwx
    - image
    - info
    - icon_row_a4kqiyr
    - icon_row_2rskpl7
    - icon_row_pev6gmr
    - bar_0
  bars:
    - left_title: Bereik
      left_entity: sensor.zeekr_actieradius
      right_entity: number.zeekr_laadlimiet
      bar_color: "var(--primary-color, #3498db)"
      background_color: "var(--card-background-color, #121212)"
      border_color: "var(--divider-color, #555555)"
      left_title_color: "var(--secondary-text-color, #999999)"
      left_text_color: "var(--primary-text-color, #ffffff)"
      right_title_color: "var(--secondary-text-color, #999999)"
      right_text_color: "var(--primary-text-color, #ffffff)"
      limit_indicator_color: "var(--error-color, #ff0000)"
      left_title_size: 14
      left_text_size: 14
      right_title_size: 14
      right_text_size: 14
      percentage_text_size: 14
      bar_size: thick
      bar_radius: round
      bar_style: metallic
      show_left: true
      show_right: true
      show_percentage: true
      show_left_title: true
      show_left_value: true
      show_right_title: true
      show_right_value: true
      percentage_type: entity
      percentage_amount_entity: ""
      percentage_total_entity: ""
      percentage_attribute: ""
      percentage_template: ""
      alignment: space-between
      width: "100"
      use_gradient: true
      gradient_display_mode: value_based
      gradient_stops:
        - id: "1"
          position: 0
          color: "#ff0000"
        - id: "2"
          position: 100
          color: "#00ff00"
      animation_entity: sensor.zeekr_laadstatus
      animation_type: charging-lines
      action_animation_entity: ""
      action_animation_state: ""
      action_animation: none
      entity: sensor.zeekr_accu_percentage
      bar_name: ""
      animation_state: Aan het laden
      limit_entity: number.zeekr_laadlimiet
      left_condition:
        type: none
        entity: ""
        state: ""
      right_condition:
        type: none
        entity: ""
        state: ""
      right_title: Laadlimiet
  icon_rows:
    - id: a4kqiyr
      width: "100"
      alignment: center
      vertical_alignment: center
      spacing: none
      columns: 0
      icons:
        - entity: switch.zeekr_airco
          icon_inactive: mdi:fan
          icon_active: mdi:fan
          color_inactive: var(--secondary-text-color)
          color_active: var(--primary-color)
          name_color_inactive: var(--primary-text-color)
          name_color_active: var(--primary-text-color)
          state_color_inactive: var(--secondary-text-color)
          state_color_active: var(--primary-text-color)
          inactive_state: "off"
          active_state: "on"
          inactive_template_mode: false
          active_template_mode: false
          inactive_template: ""
          active_template: ""
          active_state_text: ""
          inactive_state_text: ""
          show_state: true
          show_name: false
          show_name_active: false
          show_name_inactive: false
          show_state_active: true
          show_state_inactive: true
          show_units: true
          show_icon_active: true
          show_icon_inactive: true
          use_entity_color_for_icon: false
          use_entity_color_for_icon_active: false
          use_entity_color_for_icon_inactive: false
          use_entity_color_for_icon_background: false
          use_entity_color_for_container_background: false
          name: ""
          single_click_action: toggle
          on_click_action: more-info
          text_position: bottom
          vertical_alignment: center
          text_alignment: center
          icon_size: 24
          text_size: 14
          icon_background: none
          icon_background_color: var(--secondary-background-color)
          container_background: none
          container_background_color: var(--secondary-background-color)
          draggable: true
          dynamic_icon_template_mode: false
          dynamic_icon_template: ""
          dynamic_color_template_mode: false
          dynamic_color_template: ""
          action: ""
          service_data: {}
          single_entity: switch.zeekr_airco_switch
          active_animation: rotate-left
        - entity: lock.zeekr_deurslot
          icon_inactive: mdi:lock
          icon_active: mdi:lock-open-variant
          color_inactive: var(--secondary-text-color)
          color_active: "#669c35"
          name_color_inactive: var(--primary-text-color)
          name_color_active: var(--primary-text-color)
          state_color_inactive: var(--secondary-text-color)
          state_color_active: var(--primary-text-color)
          inactive_state: "off"
          inactive_template_mode: false
          active_template_mode: false
          inactive_template: ""
          active_template: ""
          active_state_text: ""
          inactive_state_text: ""
          show_state: true
          show_name: false
          show_name_active: false
          show_name_inactive: false
          show_state_active: true
          show_state_inactive: true
          show_units: true
          show_icon_active: true
          show_icon_inactive: true
          use_entity_color_for_icon: false
          use_entity_color_for_icon_active: false
          use_entity_color_for_icon_inactive: false
          use_entity_color_for_icon_background: false
          use_entity_color_for_container_background: false
          name: Deurslot
          single_click_action: trigger
          on_click_action: more-info
          text_position: bottom
          vertical_alignment: center
          text_alignment: center
          icon_size: 24
          text_size: 14
          icon_background: none
          icon_background_color: var(--secondary-background-color)
          container_background: none
          container_background_color: var(--secondary-background-color)
          draggable: true
          dynamic_icon_template_mode: false
          dynamic_icon_template: ""
          dynamic_color_template_mode: false
          dynamic_color_template: ""
          action: ""
          service_data: {}
          active_state: Unlocked
          single_entity: lock.zeekr_deurslot
        - entity: sensor.zeekr_binnen_temperatuur
          icon_inactive: mdi:thermometer
          icon_active: mdi:thermometer
          color_inactive: var(--secondary-text-color)
          color_active: var(--primary-color)
          name_color_inactive: var(--primary-text-color)
          name_color_active: var(--primary-text-color)
          state_color_inactive: var(--secondary-text-color)
          state_color_active: var(--primary-text-color)
          inactive_state: "off"
          active_state: "on"
          inactive_template_mode: false
          active_template_mode: false
          inactive_template: ""
          active_template: ""
          active_state_text: ""
          inactive_state_text: ""
          show_state: true
          show_name: false
          show_name_active: false
          show_name_inactive: false
          show_state_active: true
          show_state_inactive: true
          show_units: true
          show_icon_active: true
          show_icon_inactive: true
          use_entity_color_for_icon: false
          use_entity_color_for_icon_active: false
          use_entity_color_for_icon_inactive: false
          use_entity_color_for_icon_background: false
          use_entity_color_for_container_background: false
          name: ""
          on_click_action: more-info
          text_position: bottom
          vertical_alignment: center
          text_alignment: center
          icon_size: 24
          text_size: 14
          icon_background: none
          icon_background_color: var(--secondary-background-color)
          container_background: none
          container_background_color: var(--secondary-background-color)
          draggable: true
          dynamic_icon_template_mode: false
          dynamic_icon_template: ""
          dynamic_color_template_mode: false
          dynamic_color_template: ""
          action: ""
          service_data: {}
        - entity: binary_sensor.zeekr_kofferbak_slot
          icon_inactive: mdi:lock
          icon_active: mdi:lock-open-variant
          color_inactive: var(--secondary-text-color)
          color_active: "#77bb41"
          name_color_inactive: var(--primary-text-color)
          name_color_active: var(--primary-text-color)
          state_color_inactive: var(--secondary-text-color)
          state_color_active: "#77bb41"
          inactive_template_mode: false
          active_template_mode: false
          inactive_template: ""
          active_template: ""
          active_state_text: ""
          inactive_state_text: ""
          show_state: true
          show_name: false
          show_name_active: true
          show_name_inactive: true
          show_state_active: false
          show_state_inactive: false
          show_units: true
          show_icon_active: true
          show_icon_inactive: true
          use_entity_color_for_icon: false
          use_entity_color_for_icon_active: false
          use_entity_color_for_icon_inactive: false
          use_entity_color_for_icon_background: false
          use_entity_color_for_container_background: false
          name: Kofferbak
          on_click_action: more-info
          text_position: bottom
          vertical_alignment: center
          text_alignment: center
          icon_size: 24
          text_size: 14
          icon_background: none
          icon_background_color: var(--secondary-background-color)
          container_background: none
          container_background_color: var(--secondary-background-color)
          draggable: true
          dynamic_icon_template_mode: false
          dynamic_icon_template: ""
          dynamic_color_template_mode: false
          dynamic_color_template: ""
          action: ""
          service_data: {}
          single_service_data: {}
          single_entity: button.zeekr_kofferbak
          inactive_state: Gesloten
          active_state: Open
          single_click_action: call-service
          single_service: button.press
        - entity: switch.zeekr_sentry_mode
          icon_inactive: mdi:shield-lock
          icon_active: mdi:shield-lock
          color_inactive: var(--secondary-text-color)
          color_active: "#b51a00"
          name_color_inactive: var(--primary-text-color)
          name_color_active: var(--primary-text-color)
          state_color_inactive: var(--secondary-text-color)
          state_color_active: var(--primary-text-color)
          inactive_state: "off"
          active_state: "on"
          inactive_template_mode: false
          active_template_mode: false
          inactive_template: ""
          active_template: ""
          active_state_text: ""
          inactive_state_text: ""
          show_state: true
          show_name: false
          show_name_active: false
          show_name_inactive: false
          show_state_active: true
          show_state_inactive: true
          show_units: true
          show_icon_active: true
          show_icon_inactive: true
          use_entity_color_for_icon: false
          use_entity_color_for_icon_active: false
          use_entity_color_for_icon_inactive: false
          use_entity_color_for_icon_background: false
          use_entity_color_for_container_background: false
          name: ""
          single_click_action: toggle
          on_click_action: more-info
          text_position: bottom
          vertical_alignment: center
          text_alignment: center
          icon_size: 24
          text_size: 14
          icon_background: none
          icon_background_color: var(--secondary-background-color)
          container_background: none
          container_background_color: var(--secondary-background-color)
          draggable: true
          dynamic_icon_template_mode: false
          dynamic_icon_template: ""
          dynamic_color_template_mode: false
          dynamic_color_template: ""
          action: ""
          service_data: {}
          single_entity: switch.zeekr_sentry_mode
          active_animation: pulse
      confirmation_mode: false
    - id: pev6gmr
      width: "100"
      alignment: center
      vertical_alignment: center
      spacing: none
      columns: 0
      icons:
        - entity: binary_sensor.zeekr_laadkabel
          icon_inactive: mdi:power-plug
          icon_active: mdi:power-plug
          color_inactive: var(--secondary-text-color)
          color_active: var(--primary-color)
          name_color_inactive: var(--primary-text-color)
          name_color_active: var(--primary-text-color)
          state_color_inactive: var(--secondary-text-color)
          state_color_active: var(--primary-text-color)
          inactive_state: "off"
          active_state: "on"
          inactive_template_mode: false
          active_template_mode: false
          inactive_template: ""
          active_template: ""
          active_state_text: ""
          inactive_state_text: ""
          show_state: true
          show_name: false
          show_name_active: false
          show_name_inactive: false
          show_state_active: true
          show_state_inactive: true
          show_units: true
          show_icon_active: true
          show_icon_inactive: true
          use_entity_color_for_icon: false
          use_entity_color_for_icon_active: false
          use_entity_color_for_icon_inactive: false
          use_entity_color_for_icon_background: false
          use_entity_color_for_container_background: false
          name: ""
          single_click_action: more-info
          on_click_action: more-info
          text_position: bottom
          vertical_alignment: center
          text_alignment: center
          icon_size: 24
          text_size: 14
          icon_background: none
          icon_background_color: var(--secondary-background-color)
          container_background: none
          container_background_color: var(--secondary-background-color)
          draggable: true
          dynamic_icon_template_mode: false
          dynamic_icon_template: ""
          dynamic_color_template_mode: false
          dynamic_color_template: ""
          action: ""
          service_data: {}
        - entity: sensor.zeekr_laadvermogen
          icon_inactive: mdi:flash
          icon_active: mdi:flash
          color_inactive: var(--secondary-text-color)
          color_active: var(--primary-color)
          name_color_inactive: var(--primary-text-color)
          name_color_active: var(--primary-text-color)
          state_color_inactive: var(--secondary-text-color)
          state_color_active: var(--primary-text-color)
          inactive_state: "off"
          active_state: "on"
          inactive_template_mode: false
          active_template_mode: false
          inactive_template: ""
          active_template: ""
          active_state_text: ""
          inactive_state_text: ""
          show_state: true
          show_name: false
          show_name_active: false
          show_name_inactive: false
          show_state_active: true
          show_state_inactive: true
          show_units: true
          show_icon_active: true
          show_icon_inactive: true
          use_entity_color_for_icon: false
          use_entity_color_for_icon_active: false
          use_entity_color_for_icon_inactive: false
          use_entity_color_for_icon_background: false
          use_entity_color_for_container_background: false
          name: ""
          single_click_action: more-info
          on_click_action: more-info
          text_position: bottom
          vertical_alignment: center
          text_alignment: center
          icon_size: 24
          text_size: 14
          icon_background: none
          icon_background_color: var(--secondary-background-color)
          container_background: none
          container_background_color: var(--secondary-background-color)
          draggable: true
          dynamic_icon_template_mode: false
          dynamic_icon_template: ""
          dynamic_color_template_mode: false
          dynamic_color_template: ""
          action: ""
          service_data: {}
        - entity: sensor.zeekr_laadtijd_resterend
          icon_inactive: mdi:timer-sand
          icon_active: mdi:timer-sand
          color_inactive: var(--secondary-text-color)
          color_active: var(--primary-color)
          name_color_inactive: var(--primary-text-color)
          name_color_active: var(--primary-text-color)
          state_color_inactive: var(--secondary-text-color)
          state_color_active: var(--primary-text-color)
          inactive_state: "off"
          active_state: "on"
          inactive_template_mode: false
          active_template_mode: false
          inactive_template: ""
          active_template: ""
          active_state_text: ""
          inactive_state_text: ""
          show_state: true
          show_name: false
          show_name_active: false
          show_name_inactive: false
          show_state_active: true
          show_state_inactive: true
          show_units: true
          show_icon_active: true
          show_icon_inactive: true
          use_entity_color_for_icon: false
          use_entity_color_for_icon_active: false
          use_entity_color_for_icon_inactive: false
          use_entity_color_for_icon_background: false
          use_entity_color_for_container_background: false
          name: ""
          single_click_action: more-info
          on_click_action: more-info
          text_position: bottom
          vertical_alignment: center
          text_alignment: center
          icon_size: 24
          text_size: 14
          icon_background: none
          icon_background_color: var(--secondary-background-color)
          container_background: none
          container_background_color: var(--secondary-background-color)
          draggable: true
          dynamic_icon_template_mode: false
          dynamic_icon_template: ""
          dynamic_color_template_mode: false
          dynamic_color_template: ""
          action: ""
          service_data: {}
        - entity: sensor.zeekr_laadstatus
          icon_inactive: mdi:gauge
          icon_active: mdi:gauge
          color_inactive: var(--secondary-text-color)
          color_active: var(--primary-color)
          name_color_inactive: var(--primary-text-color)
          name_color_active: var(--primary-text-color)
          state_color_inactive: var(--secondary-text-color)
          state_color_active: var(--primary-text-color)
          inactive_state: "off"
          active_state: "on"
          inactive_template_mode: false
          active_template_mode: false
          inactive_template: ""
          active_template: ""
          active_state_text: ""
          inactive_state_text: ""
          show_state: true
          show_name: false
          show_name_active: false
          show_name_inactive: false
          show_state_active: true
          show_state_inactive: true
          show_units: true
          show_icon_active: true
          show_icon_inactive: true
          use_entity_color_for_icon: false
          use_entity_color_for_icon_active: false
          use_entity_color_for_icon_inactive: false
          use_entity_color_for_icon_background: false
          use_entity_color_for_container_background: false
          name: ""
          single_click_action: more-info
          on_click_action: more-info
          text_position: bottom
          vertical_alignment: center
          text_alignment: center
          icon_size: 24
          text_size: 14
          icon_background: none
          icon_background_color: var(--secondary-background-color)
          container_background: none
          container_background_color: var(--secondary-background-color)
          draggable: true
          dynamic_icon_template_mode: false
          dynamic_icon_template: ""
          dynamic_color_template_mode: false
          dynamic_color_template: ""
          action: ""
          service_data: {}
      confirmation_mode: false
    - id: 2rskpl7
      width: "100"
      alignment: center
      vertical_alignment: center
      spacing: none
      columns: 0
      icons:
        - entity: switch.zeekr_ontdooien
          icon_inactive: mdi:car-defrost-front
          icon_active: mdi:car-defrost-front
          color_inactive: var(--secondary-text-color)
          color_active: var(--primary-color)
          name_color_inactive: var(--primary-text-color)
          name_color_active: var(--primary-text-color)
          state_color_inactive: var(--secondary-text-color)
          state_color_active: var(--primary-text-color)
          inactive_state: "off"
          active_state: "on"
          inactive_template_mode: false
          active_template_mode: false
          inactive_template: ""
          active_template: ""
          active_state_text: ""
          inactive_state_text: ""
          show_state: true
          show_name: false
          show_name_active: false
          show_name_inactive: false
          show_state_active: true
          show_state_inactive: true
          show_units: true
          show_icon_active: true
          show_icon_inactive: true
          use_entity_color_for_icon: false
          use_entity_color_for_icon_active: false
          use_entity_color_for_icon_inactive: false
          use_entity_color_for_icon_background: false
          use_entity_color_for_container_background: false
          name: ""
          single_click_action: more-info
          on_click_action: more-info
          text_position: bottom
          vertical_alignment: center
          text_alignment: center
          icon_size: 24
          text_size: 14
          icon_background: none
          icon_background_color: var(--secondary-background-color)
          container_background: none
          container_background_color: var(--secondary-background-color)
          draggable: true
          dynamic_icon_template_mode: false
          dynamic_icon_template: ""
          dynamic_color_template_mode: false
          dynamic_color_template: ""
          action: ""
          service_data: {}
          active_animation: scale
        - icon_inactive: mdi:steering
          icon_active: mdi:steering
          color_inactive: var(--secondary-text-color)
          color_active: var(--primary-color)
          name_color_inactive: var(--primary-text-color)
          name_color_active: var(--primary-text-color)
          state_color_inactive: var(--secondary-text-color)
          state_color_active: var(--primary-text-color)
          inactive_state: "off"
          active_state: "on"
          inactive_template_mode: false
          active_template_mode: false
          inactive_template: ""
          active_template: ""
          active_state_text: ""
          inactive_state_text: ""
          show_state: true
          show_name: false
          show_name_active: false
          show_name_inactive: false
          show_state_active: true
          show_state_inactive: true
          show_units: true
          show_icon_active: true
          show_icon_inactive: true
          use_entity_color_for_icon: false
          use_entity_color_for_icon_active: false
          use_entity_color_for_icon_inactive: false
          use_entity_color_for_icon_background: false
          use_entity_color_for_container_background: false
          name: ""
          on_click_action: more-info
          text_position: bottom
          vertical_alignment: center
          text_alignment: center
          icon_size: 24
          text_size: 14
          icon_background: none
          icon_background_color: var(--secondary-background-color)
          container_background: none
          container_background_color: var(--secondary-background-color)
          draggable: true
          dynamic_icon_template_mode: false
          dynamic_icon_template: ""
          dynamic_color_template_mode: false
          dynamic_color_template: ""
          action: ""
          service_data: {}
          entity: switch.zeekr_stuurwielverwarming
          active_animation: scale
        - entity: cover.zeekr_zonnescherm
          icon_inactive: mdi:window-shutter
          icon_active: mdi:window-shutter
          color_inactive: var(--secondary-text-color)
          color_active: var(--primary-color)
          name_color_inactive: var(--primary-text-color)
          name_color_active: var(--primary-text-color)
          state_color_inactive: var(--secondary-text-color)
          state_color_active: var(--primary-text-color)
          inactive_state: "off"
          active_state: "on"
          inactive_template_mode: false
          active_template_mode: false
          inactive_template: ""
          active_template: ""
          active_state_text: ""
          inactive_state_text: ""
          show_state: true
          show_name: false
          show_name_active: false
          show_name_inactive: false
          show_state_active: true
          show_state_inactive: true
          show_units: true
          show_icon_active: true
          show_icon_inactive: true
          use_entity_color_for_icon: false
          use_entity_color_for_icon_active: false
          use_entity_color_for_icon_inactive: false
          use_entity_color_for_icon_background: false
          use_entity_color_for_container_background: false
          name: ""
          single_click_action: more-info
          on_click_action: more-info
          text_position: bottom
          vertical_alignment: center
          text_alignment: center
          icon_size: 24
          text_size: 14
          icon_background: none
          icon_background_color: var(--secondary-background-color)
          container_background: none
          container_background_color: var(--secondary-background-color)
          draggable: true
          dynamic_icon_template_mode: false
          dynamic_icon_template: ""
          dynamic_color_template_mode: false
          dynamic_color_template: ""
          action: ""
          service_data: {}
        - entity: binary_sensor.zeekr_laadkabel
          icon_inactive: mdi:power-plug
          icon_active: mdi:power-plug
          color_inactive: var(--secondary-text-color)
          color_active: var(--primary-color)
          name_color_inactive: var(--primary-text-color)
          name_color_active: var(--primary-text-color)
          state_color_inactive: var(--secondary-text-color)
          state_color_active: var(--primary-text-color)
          inactive_state: "off"
          active_state: "on"
          inactive_template_mode: false
          active_template_mode: false
          inactive_template: ""
          active_template: ""
          active_state_text: ""
          inactive_state_text: ""
          show_state: true
          show_name: false
          show_name_active: false
          show_name_inactive: false
          show_state_active: true
          show_state_inactive: true
          show_units: true
          show_icon_active: true
          show_icon_inactive: true
          use_entity_color_for_icon: false
          use_entity_color_for_icon_active: false
          use_entity_color_for_icon_inactive: false
          use_entity_color_for_icon_background: false
          use_entity_color_for_container_background: false
          name: ""
          single_click_action: more-info
          on_click_action: more-info
          text_position: bottom
          vertical_alignment: center
          text_alignment: center
          icon_size: 24
          text_size: 14
          icon_background: none
          icon_background_color: var(--secondary-background-color)
          container_background: none
          container_background_color: var(--secondary-background-color)
          draggable: true
          dynamic_icon_template_mode: false
          dynamic_icon_template: ""
          dynamic_color_template_mode: false
          dynamic_color_template: ""
          action: ""
          service_data: {}
      confirmation_mode: false
    type: custom:ultra-vehicle-card
    title: Zeekr 7X
    title_alignment: center
    title_size: 24
    title_bold: true
    show_units: true
    vehicle_image_width: 100
    action_image_width: 100
    images:
      - id: op5ku9t
        name: ""
        image_type: url
        image_width: 100
        priority: 0
        image: /local/images/zeekr_7x.png
      - name: Vehicle Image
        image_type: default
        image_width: 100
        priority: 0
        id: l4fd63o
    image_priority_mode: order
    info_rows:
      - id: 5v6thwx
        width: "100"
        alignment: center
        vertical_alignment: center
        spacing: small
        columns: 0
        allow_wrap: false
        info_entities:
          - id: 6bem25m
            entity: device_tracker.zeekr_locatie
            name: ""
            icon: mdi:car-connected
            show_icon: true
            show_name: false
            text_size: 14
            name_size: 14
            icon_size: 24
            icon_color: var(--secondary-text-color)
            text_color: var(--primary-text-color)
            on_click_action: more-info
            dynamic_icon_template_mode: false
            dynamic_icon_template: ""
            dynamic_color_template_mode: false
            dynamic_color_template: ""
          - id: pql52r2
            entity: sensor.zeekr_kilometerstand
            name: ""
            icon: mdi:counter
            show_icon: true
            show_name: false
            text_size: 14
            name_size: 14
            icon_size: 24
            icon_color: var(--secondary-text-color)
            text_color: var(--primary-text-color)
            on_click_action: more-info
            dynamic_icon_template_mode: false
            dynamic_icon_template: ""
            dynamic_color_template_mode: false
            dynamic_color_template: ""
          - id: 27kuqrj
            name: ""
            icon: mdi:car-info
            show_icon: true
            show_name: false
            text_size: 14
            name_size: 14
            icon_size: 24
            icon_color: var(--secondary-text-color)
            text_color: var(--primary-text-color)
            on_click_action: more-info
            dynamic_icon_template_mode: false
            dynamic_icon_template: ""
            dynamic_color_template_mode: false
            dynamic_color_template: ""
            entity: sensor.zeekr_software_versie
        row_name: ""
      - id: bfcpdsw
        width: "100"
        alignment: center
        vertical_alignment: center
        spacing: small
        columns: 0
        allow_wrap: false
        info_entities:
          - id: swctvtm
            entity: sensor.zeekr_voertuig_status
            name: ""
            icon: mdi:car
            show_icon: true
            show_name: false
            text_size: 14
            name_size: 14
            icon_size: 24
            icon_color: var(--secondary-text-color)
            text_color: var(--primary-text-color)
            on_click_action: more-info
            dynamic_icon_template_mode: false
            dynamic_icon_template: ""
            dynamic_color_template_mode: false
            dynamic_color_template: ""
    sections_columns:
      title: half_full_row1_left
      info_row_5v6thwx: half_full_row2_full
      info_row_bfcpdsw: half_full_row1_right
    section_conditions:
      icon_row_pev6gmr:
        type: show
        entity: ""
        state: ""
    section_templates:
      icon_row_pev6gmr:
        template_mode: true
        template: "{{ states('binary.sensor.zeekr_laadkabel') == 'Losgekoppeld'}}"

</details>

