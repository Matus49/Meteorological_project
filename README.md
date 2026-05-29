# <p align="center">🌤️ Weather & Sensors Project</p>

<p align="center">
  <img src="https://img.shields.io/badge/Status-Active-success?style=for-the-badge&logo=github" alt="Status">
  <img src="https://img.shields.io/badge/Location-Nitra,%20Slovakia-yellow?style=for-the-badge&logo=googlemaps" alt="Location">
  <img src="https://img.shields.io/badge/Focus-IoT%20%26%20Climate-blue?style=for-the-badge" alt="Focus">
</p>

---

<p align="center">
  Vítame ťa v našom repozitári! Tento projekt je zameraný na sledovanie meteorologických údajov, analýzu mikroklímy a prácu s rôznymi environmentálnymi senzormi v reálnom čase.
</p>

<p align="center">
  <a href="https://matus49.github.io/Meteorological_project/">
    <img src="https://img.shields.io/badge/%F0%9F%8C%90%20VSTÚPIŤ%20DO%20APLIKÁCIE-LIVE%20DASHBOARD-0078d4?style=for-the-badge&logo=microsoftedge&logoColor=white" width="320" alt="Live Dashboard Button">
  </a>
</p>

---

## 📋 O projekte

Tento repozitár slúži ako centrálny bod pre **zber, spracovanie a vizualizáciu klimatických metrík**. Obsahuje kompletný zdrojový kód, konfigurácie a dokumentáciu potrebnú na komunikáciu s hardvérovými senzormi a následnú interpretáciu získaných dát.

### 🗺️ Hardvér a Lokalita
* 📍 **Umiestnenie:** Senzory sú strategicky rozmiestnené v meste **Nitra** a jeho blízkom okolí.
* 📊 **Prístup k dátam:** Všetky historické aj aktuálne namerané informácie sú okamžite dostupné prostredníctvom nášho webového rozhrania.
* 📈 **Zber dát:** Monitorujeme kľúčové environmentálne faktory ako teplota, vlhkosť vzduchu, CO₂ a ďalšie parametre dôležité pre analýzu prostredia.

---

## 🛠️ Ako to funguje?

Architektúra projektu je rozdelená do troch základných vrstiev:

```mermaid
graph LR
    A[📡 Fyzické Senzory] --> B[💻 Riadiace Skripty]
    B --> C[📊 Live Dashboard]
