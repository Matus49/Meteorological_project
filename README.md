# <p align="center">🌤️ Weather & Sensors Project</p>

<p align="center">
  <img src="https://img.shields.io/badge/Status-Active-0078d4?style=for-the-badge&logo=github" alt="Status">
  <img src="https://img.shields.io/badge/Location-Nitra,%20Slovakia-E64A19?style=for-the-badge&logo=googlemaps&logoColor=white" alt="Location">
  <img src="https://img.shields.io/badge/Focus-IoT%20%26%20Climate-FBC02D?style=for-the-badge&logoColor=black" alt="Focus">
</p>

---

<p align="center">
  Vítame ťa v našom repozitári! Tento projekt je zameraný na sledovanie meteorologických údajov, analýzu mikroklímy a prácu s environmentálnymi senzormi v reálnom čase.
</p>

<p align="center">
  <a href="https://matus49.github.io/Meteorological_project/">
    <img src="https://img.shields.io/badge/%F0%9F%8C%90%20VSTÚPIŤ%20DO%20APLIKÁCIE-LIVE%20DASHBOARD-0078d4?style=for-the-badge&logo=microsoftedge&logoColor=white" width="340" alt="Live Dashboard Button">
  </a>
</p>

---

## 📋 O projekte

Tento repozitár slúži ako centrálny bod pre **zber, spracovanie a vizualizáciu klimatických metrík**. Obsahuje kompletný zdrojový kód, konfigurácie a dokumentáciu potrebnú na komunikáciu s hardvérovými senzormi a následnú interpretáciu získaných dát, ako sú teplota, vlhkosť vzduchu, atmosférický tlak a koncentrácia CO₂.

### 🗺️ Hardvér a Lokalita
* 📍 **Umiestnenie:** Senzory sú umiestnené v meste **Nitra** a jeho okolí.
* 📊 **Prístup k dátam:** Všetky historické aj aktuálne namerané informácie sú dostupné cez náš webový panel.
* 📈 **Zber dát:** Neustále monitorujeme kľúčové environmentálne faktory pre presnú analýzu okolitého prostredia.

---

## 🛠️ Ako to funguje?

Architektúra projektu a zapojenie tímu do jednotlivých vrstiev:

```mermaid
graph TD
    subgraph Tím [👥 Vývojový Tým]
        D[🔌 HW Inžiniering]
        E[🧠 Backend logika]
        F[🎨 Frontend & UX]
        G[📦 DevOps & Servery]
    end

    A[📡 Fyzické Senzory] -->|Zber dát| B[💻 Riadiace Skripty]
    B -->|Spracovanie| C[📊 Live Dashboard]

    D -.-> A
    E -.-> B
    F -.-> C
    G -.-> C



<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/7beba836-ac3f-4797-bb72-e4e2d872b647" />

