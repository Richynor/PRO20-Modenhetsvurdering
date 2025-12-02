"""
MODENHETSVURDERING - GEVINSTREALISERING
Bane NOR - Konsern Controlling

Komplett løsning med:
- Alle 23 spørsmål per fase
- Multidimensjonale radardiagrammer
- Multi-intervju støtte
- Automatisk lagring

Versjon: 3.0
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime
import pickle
import os

# ============================================================================
# KONFIGURASJON
# ============================================================================
st.set_page_config(
    page_title="Modenhetsvurdering - Gevinstrealisering",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Datafil for automatisk lagring
DATA_FILE = "modenhet_data.pkl"

# ============================================================================
# KOMPLETT SPØRSMÅLSSETT - ALLE 23 SPØRSMÅL PER FASE
# ============================================================================
phases_data = {
    "Planlegging": [
        {
            "id": 1,
            "title": "Bruk av tidligere læring og gevinstdata",
            "question": "Hvordan anvendes erfaringer og læring fra tidligere prosjekter og gevinstarbeid i planleggingen av nye gevinster?",
            "scale": [
                "Nivå 1: Ingen læring fra tidligere arbeid anvendt.",
                "Nivå 2: Enkelte erfaringer omtalt, men ikke strukturert brukt.",
                "Nivå 3: Læring inkludert i planlegging for enkelte områder.",
                "Nivå 4: Systematisk bruk av tidligere gevinstdata i planlegging og estimering.",
                "Nivå 5: Kontinuerlig læring integrert i planleggingsprosessen og gevinststrategien."
            ]
        },
        {
            "id": 2,
            "title": "Strategisk retning og gevinstforståelse",
            "question": "Hvilke gevinster arbeider dere med, og hvorfor er de viktige for organisasjonens strategiske mål?",
            "scale": [
                "Nivå 1: Gevinster er vagt definert, uten tydelig kobling til strategi.",
                "Nivå 2: Gevinster er identifisert, men mangler klare kriterier og prioritering.",
                "Nivå 3: Gevinster er dokumentert og delvis knyttet til strategiske mål, men grunnlaget har usikkerheit.",
                "Nivå 4: Gevinster er tydelig koblet til strategiske mål med konkrete måltall.",
                "Nivå 5: Gevinster er fullt integrert i styringssystemet og brukes i beslutninger."
            ]
        },
        {
            "id": 3,
            "title": "Gevinstkart og visualisering",
            "question": "Er gevinstene synliggjort i gevinstkartet, med tydelig sammenheng mellom tiltak, effekter og mål?",
            "scale": [
                "Nivå 1: Gevinstkart finnes ikke eller er utdatert.",
                "Nivå 2: Et foreløpig gevinstkart eksisterer, men dekker ikke hele området.",
                "Nivå 3: Kartet inkluderer hovedgevinster, men mangler validering og detaljer.",
                "Nivå 4: Kartet er brukt aktivt i planlegging og oppfølging.",
                "Nivå 5: Gevinstkartet oppdateres kontinuerlig og er integrert i styringsdialoger."
            ]
        },
        {
            "id": 4,
            "title": "Strategisk kobling og KPI-er",
            "question": "Er gevinstene tydelig knyttet til strategiske mål og eksisterende KPI-er?",
            "scale": [
                "Nivå 1: Ingen kobling mellom gevinster og strategi eller KPI-er.",
                "Nivå 2: Kobling er antatt, men ikke dokumentert.",
                "Nivå 3: Kobling er etablert for enkelte KPI-er, men ikke konsistent.",
                "Nivå 4: Tydelig kobling mellom gevinster og relevante KPI-er.",
                "Nivå 5: Koblingen følges opp i styringssystem og rapportering."
            ]
        },
        {
            "id": 5,
            "title": "Avgrensning av programgevinst",
            "question": "Er det tydelig avklart hvilke effekter som stammer fra programmet versus andre tiltak eller økte rammer?",
            "scale": [
                "Nivå 1: Ingen skille mellom program- og eksterne effekter.",
                "Nivå 2: Delvis omtalt, maar uklart hva som er innenfor programmet.",
                "Nivå 3: Avgrensning er gjort i plan, men ikke dokumentert grundig.",
                "Nivå 4: Avgrensning er dokumentert og anvendt i beregninger.",
                "Nivå 5: Effektisolering er standard praksis og brukes systematisk."
            ]
        },
        {
            "id": 6,
            "title": "Nullpunkter og estimater",
            "question": "Er nullpunkter og estimater etablert, testet og dokumentert på en konsistent og troverdig måte med hensyn til variasjoner mellom strekninger (værforhold, driftsmessige vilkår, togfremføring og andre relevante elementer)?",
            "scale": [
                "Nivå 1: Nullpunkter mangler eller bygger på uprøvde antagelser, uten hensyn til strekningens spesifikke forhold.",
                "Nivå 2: Enkelte nullpunkter finnes, men uten felles metode og uten vurdering av variasjoner mellom strekninger.",
                "Nivå 3: Nullpunkter og estimater er definert, men med høy usikkerhet knyttet til lokale forhold (vær, drift, togfremføring).",
                "Nivå 4: Nullpunkter og estimater er basert på testede data og validerte metoder, med tilpasning til strekningens vilkår.",
                "Nivå 5: Nullpunkter og estimater kvalitetssikres jevnlig, tar systematisk hensyn til variasjoner mellom strekninger og brukes aktivt til læring og forbedring."
            ]
        },
        {
            "id": 7,
            "title": "Hypotesetesting og datagrunnlag",
            "question": "Finnes formell prosess for hypotesetesting på representative caser - og var casene representative for faktisk arbeidsflyt/vilkår inkludert strekningsspesifikke forhold?",
            "scale": [
                "Nivå 1: Ikke etablert/uklart; ingen dokumenterte praksiser.",
                "Nivå 2: Delvis definert; uformell praksis uten forankring/validering.",
                "Nivå 3: Etablert for deler av området; variabel kvalitet og usikkerhet knyttet til lokale forhold.",
                "Nivå 4: Godt forankret og systematisk anvendt; måles og følges opp med tilpasning til ulike strekninger.",
                "Nivå 5: Fullt integrert i styring; kontinuerlig forbedring og læring basert på strekningsspesifikke erfaringer."
            ]
        },
        {
            "id": 8,
            "title": "Interessentengasjement",
            "question": "Ble relevante interessenter involvert i utarbeidelsen av gevinstgrunnlag, nullpunkter og estimater?",
            "scale": [
                "Nivå 1: Ingen involvering av interessenter.",
                "Nivå 2: Begrenset og ustrukturert involvering.",
                "Nivå 3: Bred deltakelse, men uten systematisk prosess.",
                "Nivå 4: Systematisk og koordinert involvering med klar rollefordeling.",
                "Nivå 5: Kontinuerlig engasjement med dokumentert medvirkning."
            ]
        },
        {
            "id": 9,
            "title": "Gevinstforutsetninger",
            "question": "Er alle vesentlige forutsetninger ivaretatt og under arbeid - enten av prosjektet, linjen eller eksterne aktører - for å muliggjøre gevinstrealisering?",
            "scale": [
                "Nivå 1: Ingen kartlegging av gevinstforutsetninger.",
                "Nivå 2: Noen forutsetninger er identifisert, men ikke systematisk dokumentert.",
                "Nivå 3: Hovedforutsetninger er dokumentert, men uten klar eierskap og oppfølging.",
                "Nivå 4: Alle kritiske forutsetninger er kartlagt, med tildelt ansvar og oppfølgingsplan.",
                "Nivå 5: Gevinstforutsetninger er integrert i risikostyring og oppfølges kontinuerlig i styringsdialoger."
            ]
        },
        {
            "id": 10,
            "title": "Prinsipielle og vilkårsmessige kriterier",
            "question": "Er forutsetninger og kriterier som påvirker gevinstene (f.eks. driftsvilkår, tilgang til sporet, kapasitetsrammer) tydelig definert og dokumentert i planen?",
            "scale": [
                "Nivå 1: Ingen kriterier dokumentert.",
                "Nivå 2: Kriterier er beskrevet uformelt.",
                "Nivå 3: Kriterier dokumentert i deler av planverket.",
                "Nivå 4: Vesentlige kriterier er analysert og håndtert i gevinstrealiseringsplanen.",
                "Nivå 5: Kriterier overvåkes, følges opp og inngår i risikostyringen."
            ]
        },
        {
            "id": 11,
            "title": "Enighet om nullpunkter/estimater",
            "question": "Er det oppnådd enighet blant nøkkelinteressenter om nullpunkter og estimater?",
            "scale": [
                "Nivå 1: Ingen enighet eller dokumentert praksis.",
                "Nivå 2: Delvis enighet, men ikke formalisert.",
                "Nivå 3: Enighet for hovedestimater, men med reservasjoner knyttet til strekningsvariasjoner.",
                "Nivå 4: Full enighet dokumentert og forankret, inkludert forståelse for lokale variasjoner.",
                "Nivå 5: Kontinuerlig dialog og justering av estimater med interessentene basert på operativ erfaring."
            ]
        },
        {
            "id": 12,
            "title": "Disponering av kostnads- og tidsbesparelser",
            "question": "Hvordan er kostnads- og tidsbesparelser planlagt disponert mellom prissatte gevinster (som trekkes fra budsjett) og ikke-prissatte gevinster (som økt kvalitet eller mer arbeid), og hvordan måles effektene av bruken av disse ressursene?",
            "scale": [
                "Nivå 1: Ingen plan for disponering eller måling av besparelser.",
                "Nivå 2: Delvis oversikt, men ikke dokumentert eller fulgt opp. Fokus på enten prissatte eller ikke-prissatte gevinster.",
                "Nivå 3: Plan finnes for enkelte områder, men uten systematikk for både prissatte og ikke-prissatte gevinster.",
                "Nivå 4: Disponering og effekter dokumentert og målt for både prissatte og ikke-prissatte gevinster.",
                "Nivå 5: Frigjorte ressurser disponeres strategisk mellom prissatte og ikke-prissatte gevinster, og måles som del av gevinstrealiseringen."
            ]
        },
        {
            "id": 13,
            "title": "Måling av effektivitet og produktivitet",
            "question": "Hvordan måles økt effektivitet (f.eks. økte maskintimer) og produktivitet (f.eks. reduserte AKV, økte UKV) som følge av besparelser, og sikres bærekraft i disse gevinstene over tid?",
            "scale": [
                "Nivå 1: Ingen måling av effektivitet eller produktivitet.",
                "Nivå 2: Enkelte målinger, men ikke systematisk og uten vurdering av bærekraft.",
                "Nivå 3: Måling av effektivitet og produktivitet for enkelte gevinster, men begrenset fokus på bærekraft.",
                "Nivå 4: Systematisk måling av effektivitet og produktivitet, og vurdering av om gevinster opprettholdes over tid.",
                "Nivå 5: Måling av effektivitet og produktivitet er integrert i gevinstoppfølgingen, og bærekraftige gevinster sikres gjennom tilpassede tiltak og læring."
            ]
        },
        {
            "id": 14,
            "title": "Operasjonell risiko og ulemper",
            "question": "Er mulige negative konsekvenser eller ulemper knyttet til operasjonelle forhold (strekninger, togfremføring, tilgang til sporet) identifisert, vurdert og håndtert i planen?",
            "scale": [
                "Nivå 1: Negative effekter ikke vurdert.",
                "Nivå 2: Kjent, men ikke håndtert.",
                "Nivå 3: Beskrevet, men ikke fulgt opp systematisk.",
                "Nivå 4: Håndtert og overvåket med tilpasning til ulike operasjonelle scenarier.",
                "Nivå 5: Systematisk vurdert og del av gevinstdialogen med kontinuerlig justering."
            ]
        },
        {
            "id": 15,
            "title": "Balanse mellom gevinster og ulemper",
            "question": "Hvordan sikres det at balansen mellom gevinster og ulemper vurderes i styringsdialoger?",
            "scale": [
                "Nivå 1: Ingen vurdering av balanse.",
                "Nivå 2: Diskuteres uformelt.",
                "Nivå 3: Del av enkelte oppfølgingsmøter.",
                "Nivå 4: Systematisk vurdert i gevinststyring.",
                "Nivå 5: Inngår som fast punkt i styrings- og gevinstdialoger."
            ]
        },
        {
            "id": 16,
            "title": "Dokumentasjon og gevinstrealiseringsplan",
            "question": "Er det utarbeidet en forankret gevinstrealiseringsplan som beskriver hvordan gevinstene skal hentes ut og måles?",
            "scale": [
                "Nivå 1: Ingen formell gevinstrealiseringsplan.",
                "Nivå 2: Utkast til plan finnes, men er ufullstendig.",
                "Nivå 3: Plan er etablert, men ikke validet eller periodisert.",
                "Nivå 4: Planen er forankret, oppdatert og koblet til gevinstkartet.",
                "Nivå 5: Planen brukes aktivt som styringsdokument med revisjon."
            ]
        },
        {
            "id": 17,
            "title": "Gevinstrealiseringsplan som operativ handlingsplan",
            "question": "Hvordan sikres det at gevinstrealiseringsplanen fungerer som en operativ handlingsplan i linjen med tilpasning til ulike strekningsforhold?",
            "scale": [
                "Nivå 1: Planen brukes ikke som operativt styringsverktøy.",
                "Nivå 2: Plan finnes, men uten operativ oppfølging.",
                "Nivå 3: Planen følges delvis opp i linjen.",
                "Nivå 4: Planen brukes aktivt som handlingsplan og styringsverktøy.",
                "Nivå 5: Gevinstplanen er fullt operativt integrert i linjens handlingsplaner og rapportering med tilpasning til lokale forhold."
            ]
        },
        {
            "id": 18,
            "title": "Endringsberedskap og operativ mottaksevne",
            "question": "Er organisasjonen forberedt og har den tilstrekkelig kapasitet til å ta imot endringer og nye arbeidsformer som følger av programmet, inkludert tilpasning til ulike strekningsforhold?",
            "scale": [
                "Nivå 1: Ingen plan for endringsberedskap.",
                "Nivå 2: Kapasitet vurderes uformelt, men ikke håndtert.",
                "Nivå 3: Endringskapasitet omtales, men uten konkrete tiltak.",
                "Nivå 4: Tilfredsstillende beredskap etablert og koordinert med linjen.",
                "Nivå 5: Endringskapasitet er strukturert, overvåket og integrert i styring med tilpasning til lokale forhold."
            ]
        },
        {
            "id": 19,
            "title": "Kommunikasjon og forankring",
            "question": "Er gevinstgrunnlag, roller og forventninger godt kommunisert i organisasjonen?",
            "scale": [
                "Nivå 1: Ingen felles forståelse eller kommunikasjon.",
                "Nivå 2: Informasjon deles sporadisk.",
                "Nivå 3: Kommunikasjon er planlagt, men ikke systematisk målt.",
                "Nivå 4: Kommunikasjon er systematisk og forankret i organisasjonen.",
                "Nivå 5: Forankring skjer løpende som del av styringsdialog."
            ]
        },
        {
            "id": 20,
            "title": "Eierskap og ansvar",
            "question": "Er ansvar og roller tydelig definert for å sikre gjennomføring og gevinstuttak?",
            "scale": [
                "Nivå 1: Ansvar er uklart eller mangler.",
                "Nivå 2: Ansvar er delvis definert, maar ikke praktisert.",
                "Nivå 3: Ansvar er kjent, men samhandling varierer.",
                "Nivå 4: Roller og ansvar fungerer godt i praksis.",
                "Nivå 5: Sterkt eierskap og kultur for ansvarliggjøring."
            ]
        },
        {
            "id": 21,
            "title": "Periodisering og forankring",
            "question": "Er gevinstrealiseringsplanen periodisert, validet og godkjent av ansvarlige?",
            "scale": [
                "Nivå 1: Ingen tidsplan eller forankring.",
                "Nivå 2: Tidsplan foreligger, men ikke validet.",
                "Nivå 3: Delvis forankret hos enkelte ansvarlige/eiere.",
                "Nivå 4: Fullt forankret og koordinert med budsjett- og styringsprosesser.",
                "Nivå 5: Planen brukes aktivt i styringsdialog og rapportering."
            ]
        },
        {
            "id": 22,
            "title": "Realisme og engasjement",
            "question": "Opplever dere at gevinstplanen og estimatene oppleves realistiske og engasjerer eierne og interessentene?",
            "scale": [
                "Nivå 1: Ingen troverdighet eller engasjement.",
                "Nivå 2: Begrenset tillit til estimater.",
                "Nivå 3: Delvis aksept, men varierende engasjement.",
                "Nivå 4: Høy troverdighet og engasjement.",
                "Nivå 5: Sterk troverdighet og aktiv motivasjon i organisasjonen."
            ]
        },
        {
            "id": 23,
            "title": "Bygge momentum og tidlig gevinstuttak",
            "question": "Hvordan planlegges det for å bygge momentum og realisere tidlige gevinster underveis i programmet?",
            "scale": [
                "Nivå 1: Ingen plan for tidlig gevinstuttak eller oppbygging av momentum.",
                "Nivå 2: Enkelte uformelle vurderinger av tidlige gevinster.",
                "Nivå 3: Plan for tidlig gevinstuttak er identifisert, men ikke koordinert.",
                "Nivå 4: Strukturert tilnærming for tidlig gevinstuttak med tildelt ansvar.",
                "Nivå 5: Tidlig gevinstuttak er integrert i programmets DNA og brukes aktivt for å bygge momentum."
            ]
        }
    ],
    "Gjennomføring": [
        {
            "id": 1,
            "title": "Bruk av tidligere læring og gevinstdata",
            "question": "Hvordan brukes erfaringer og læring fra tidligere prosjekter og gevinstarbeid til å justere tiltak under gjennomføringen?",
            "scale": [
                "Nivå 1: Ingen læring fra tidligere arbeid anvendt under gjennomføring.",
                "Nivå 2: Enkelte erfaringer omtalt, men ikke strukturert brukt for justering.",
                "Nivå 3: Læring inkludert i justering for enkelte områder under gjennomføring.",
                "Nivå 4: Systematisk bruk av tidligere gevinstdata for å justere tiltak underveis.",
                "Nivå 5: Kontinuerlig læring integrert i gjennomføringsprosessen og gevinstjustering."
            ]
        },
        {
            "id": 2,
            "title": "Strategisk retning og gevinstforståelse",
            "question": "Hvordan opprettholdes den strategiske retningen og forståelsen av gevinster under gjennomføring?",
            "scale": [
                "Nivå 1: Strategisk kobling glemmes under gjennomføring.",
                "Nivå 2: Strategi omtales, men ikke operasjonalisert i gjennomføring.",
                "Nivå 3: Strategisk kobling vedlikeholdes i deler av gjennomføringen.",
                "Nivå 4: Tydelig strategisk retning i gjennomføring med regelmessig oppdatering.",
                "Nivå 5: Strategi og gevinstforståelse dynamisk tilpasses underveis basert på læring."
            ]
        },
        {
            "id": 3,
            "title": "Gevinstkart og visualisering",
            "question": "Hvordan brukes gevinstkartet aktivt under gjennomføring for å styre og kommunisere fremdrift?",
            "scale": [
                "Nivå 1: Gevinstkartet brukes ikke under gjennomføring.",
                "Nivå 2: Gevinstkartet vises, men ikke aktivt brukt i beslutninger.",
                "Nivå 3: Gevinstkartet oppdateres og brukes i noen beslutninger.",
                "Nivå 4: Gevinstkartet er aktivt styringsverktøy med regelmessig oppdatering.",
                "Nivå 5: Gevinstkartet brukes dynamisk til å justere strategi og tiltak underveis."
            ]
        },
        {
            "id": 4,
            "title": "Strategisk kobling og KPI-er",
            "question": "Hvordan følges opp den strategiske koblingen og KPI-ene under gjennomføring?",
            "scale": [
                "Nivå 1: Ingen oppfølging av strategisk kobling under gjennomføring.",
                "Nivå 2: KPI-er måles, men kobling til strategi mangler.",
                "Nivå 3: Noen KPI-er følges opp med strategisk kobling.",
                "Nivå 4: Systematisk oppfølging av KPI-er med tydelig strategisk kobling.",
                "Nivå 5: Dynamisk justering av KPI-er basert på strategisk utvikling underveis."
            ]
        },
        {
            "id": 5,
            "title": "Avgrensning av programgevinst",
            "question": "Hvordan håndteres avgrensning av programgevinster under gjennomføring når nye forhold oppstår?",
            "scale": [
                "Nivå 1: Avgrensning glemmes under gjennomføring.",
                "Nivå 2: Avgrensning omtales, men ikke operasjonalisert.",
                "Nivå 3: Avgrensning håndteres for større endringer.",
                "Nivå 4: System for å håndtere avgrensning under gjennomføring.",
                "Nivå 5: Dynamisk avgrensningshåndtering integrert i beslutningsprosesser."
            ]
        },
        {
            "id": 6,
            "title": "Nullpunkter og estimater",
            "question": "Hvordan justeres nullpunkter og estimater under gjennomføring basert på nye data og erfaringer?",
            "scale": [
                "Nivå 1: Nullpunkter og estimater justeres ikke under gjennomføring.",
                "Nivå 2: Justering skjer ad hoc uten struktur.",
                "Nivå 3: Systematisk justering for store avvik.",
                "Nivå 4: Regelmessig revisjon og justering av nullpunkter og estimater.",
                "Nivå 5: Kontinuerlig justering basert på realtidsdata og læring."
            ]
        },
        {
            "id": 7,
            "title": "Hypotesetesting og datagrunnlag",
            "question": "Hvordan testes hypoteser og datagrunnlag under gjennomføring for å validere tilnærmingen?",
            "scale": [
                "Nivå 1: Hypoteser testes ikke under gjennomføring.",
                "Nivå 2: Noen uformelle tester gjennomføres.",
                "Nivå 3: Formell testing for kritiske hypoteser.",
                "Nivå 4: Systematisk testing og validering under gjennomføring.",
                "Nivå 5: Kontinuerlig hypotesetesting integrert i læringsprosesser."
            ]
        },
        {
            "id": 8,
            "title": "Interessentengasjement",
            "question": "Hvordan opprettholdes interessentengasjement under gjennomføring?",
            "scale": [
                "Nivå 1: Interessentengasjement avtar under gjennomføring.",
                "Nivå 2: Begrenset engasjement for viktige beslutninger.",
                "Nivå 3: Regelmessig engasjement for større endringer.",
                "Nivå 4: Systematisk interessentoppfølging under gjennomføring.",
                "Nivå 5: Kontinuerlig dialog og samskaping med interessenter."
            ]
        },
        {
            "id": 9,
            "title": "Gevinstforutsetninger",
            "question": "Hvordan overvåkes og håndteres gevinstforutsetninger under gjennomføring?",
            "scale": [
                "Nivå 1: Forutsetninger overvåkes ikke under gjennomføring.",
                "Nivå 2: Noen forutsetninger overvåkes uformelt.",
                "Nivå 3: Systematisk overvåkning av kritiske forutsetninger.",
                "Nivå 4: Aktiv håndtering av endrede forutsetninger.",
                "Nivå 5: Forutsetningsstyring integrert i risikostyring og beslutninger."
            ]
        },
        {
            "id": 10,
            "title": "Prinsipielle og vilkårsmessige kriterier",
            "question": "Hvordan håndteres endringer i prinsipielle og vilkårsmessige kriterier under gjennomføring?",
            "scale": [
                "Nivå 1: Endringer i kriterier håndteres ikke.",
                "Nivå 2: Store endringer håndteres reaktivt.",
                "Nivå 3: System for å håndtere endringer i kriterier.",
                "Nivå 4: Proaktiv håndtering av endrede kriterier.",
                "Nivå 5: Dynamisk tilpasning til endrede kriterier i sanntid."
            ]
        },
        {
            "id": 11,
            "title": "Enighet om nullpunkter/estimater",
            "question": "Hvordan opprettholdes enighet om nullpunkter og estimater under gjennomføring?",
            "scale": [
                "Nivå 1: Enighet testes ikke under gjennomføring.",
                "Nivå 2: Enighet bekreftes ved store endringer.",
                "Nivå 3: Regelmessig bekreftelse av enighet.",
                "Nivå 4: Systematisk arbeid for å opprettholde enighet.",
                "Nivå 5: Kontinuerlig dialog og justering for å opprettholde enighet."
            ]
        },
        {
            "id": 12,
            "title": "Disponering av kostnads- og tidsbesparelser",
            "question": "Hvordan håndteres disponering av besparelser under gjennomføring?",
            "scale": [
                "Nivå 1: Disponering håndteres ikke under gjennomføring.",
                "Nivå 2: Disponering justeres for store avvik.",
                "Nivå 3: Systematisk revisjon av disponeringsplaner.",
                "Nivå 4: Dynamisk tilpasning av disponering basert på resultater.",
                "Nivå 5: Optimal disponering integrert i beslutningsstøtte."
            ]
        },
        {
            "id": 13,
            "title": "Måling av effektivitet og produktivitet",
            "question": "Hvordan måles og følges opp effektivitet og produktivitet under gjennomføring?",
            "scale": [
                "Nivå 1: Effektivitet og produktivitet måles ikke underveis.",
                "Nivå 2: Noen målinger registreres, men ikke analysert.",
                "Nivå 3: Systematisk måling med begrenset analyse.",
                "Nivå 4: Regelmessig analyse og justering basert på målinger.",
                "Nivå 5: Realtids overvåkning og proaktiv justering."
            ]
        },
        {
            "id": 14,
            "title": "Operasjonell risiko og ulemper",
            "question": "Hvordan identifiseres og håndteres nye operasjonelle risikoer og ulemper under gjennomføring?",
            "scale": [
                "Nivå 1: Nye risikoer identifiseres ikke underveis.",
                "Nivå 2: Store risikoer håndteres reaktivt.",
                "Nivå 3: Systematisk identifisering av nye risikoer.",
                "Nivå 4: Proaktiv håndtering av nye risikoer.",
                "Nivå 5: Risikostyring integrert i daglig drift."
            ]
        },
        {
            "id": 15,
            "title": "Balanse mellom gevinster og ulemper",
            "question": "Hvordan vurderes balansen mellom gevinster og ulemper under gjennomføring?",
            "scale": [
                "Nivå 1: Balansen vurderes ikke under gjennomføring.",
                "Nivå 2: Balansen vurderes ved store endringer.",
                "Nivå 3: Regelmessig vurdering av balansen.",
                "Nivå 4: Systematisk overvåkning av balansen.",
                "Nivå 5: Balansevurdering integrert i beslutningsprosesser."
            ]
        },
        {
            "id": 16,
            "title": "Dokumentasjon og gevinstrealiseringsplan",
            "question": "Hvordan oppdateres og brukes gevinstrealiseringsplanen under gjennomføring?",
            "scale": [
                "Nivå 1: Gevinstrealiseringsplanen oppdateres ikke.",
                "Nivå 2: Planen oppdateres ved store endringer.",
                "Nivå 3: Regelmessig oppdatering av planen.",
                "Nivå 4: Planen brukes aktivt i styring og beslutninger.",
                "Nivå 5: Dynamisk oppdatering og bruk av planen i sanntid."
            ]
        },
        {
            "id": 17,
            "title": "Gevinstrealiseringsplan som operativ handlingsplan",
            "question": "Hvordan fungerer gevinstrealiseringsplanen som operativ handlingsplan under gjennomføring?",
            "scale": [
                "Nivå 1: Planen brukes ikke som operativ handlingsplan.",
                "Nivå 2: Planen brukes til visse operasjoner.",
                "Nivå 3: Planen er integrert i deler av den operative styringen.",
                "Nivå 4: Planen er aktivt operativt styringsverktøy.",
                "Nivå 5: Planen er fullt integrert i alle operative beslutninger."
            ]
        },
        {
            "id": 18,
            "title": "Endringsberedskap og operativ mottaksevne",
            "question": "Hvordan utvikles endringsberedskap og operativ mottaksevne under gjennomføring?",
            "scale": [
                "Nivå 1: Endringsberedskap utvikles ikke underveis.",
                "Nivå 2: Begrenset fokus på endringsberedskap.",
                "Nivå 3: Systematisk arbeid med endringsberedskap.",
                "Nivå 4: Målrettet utvikling av mottaksevne.",
                "Nivå 5: Kontinuerlig tilpasning og læring i endringsprosessen."
            ]
        },
        {
            "id": 19,
            "title": "Kommunikasjon og forankring",
            "question": "Hvordan opprettholdes kommunikasjon og forankring under gjennomføring?",
            "scale": [
                "Nivå 1: Kommunikasjon avtar under gjennomføring.",
                "Nivå 2: Begrenset kommunikasjon om viktige endringer.",
                "Nivå 3: Regelmessig kommunikasjon om fremdrift.",
                "Nivå 4: Systematisk kommunikasjonsplan under gjennomføring.",
                "Nivå 5: Kontinuerlig dialog og tilbakemelding integrert i prosessen."
            ]
        },
        {
            "id": 20,
            "title": "Eierskap og ansvar",
            "question": "Hvordan utøves eierskap og ansvar under gjennomføring?",
            "scale": [
                "Nivå 1: Eierskap og ansvar svekkes under gjennomføring.",
                "Nivå 2: Begrenset eierskap i kritiske faser.",
                "Nivå 3: Tydelig eierskap for sentrale ansvarsområder.",
                "Nivå 4: Aktivt utøvd eierskap gjennom hele prosessen.",
                "Nivå 5: Sterk eierskapskultur som driver gjennomføring."
            ]
        },
        {
            "id": 21,
            "title": "Periodisering og forankring",
            "question": "Hvordan justeres periodisering og forankring under gjennomføring?",
            "scale": [
                "Nivå 1: Periodisering justeres ikke under gjennomføring.",
                "Nivå 2: Store justeringer i periodisering.",
                "Nivå 3: Regelmessig revisjon av periodisering.",
                "Nivå 4: Dynamisk tilpasning av periodisering.",
                "Nivå 5: Fleksibel periodisering integrert i styringssystemet."
            ]
        },
        {
            "id": 22,
            "title": "Realisme og engasjement",
            "question": "Hvordan opprettholdes realisme og engasjement under gjennomføring?",
            "scale": [
                "Nivå 1: Realisme og engasjement avtar.",
                "Nivå 2: Begrenset fokus på å opprettholde engasjement.",
                "Nivå 3: Arbeid med å opprettholde realisme og engasjement.",
                "Nivå 4: Systematisk arbeid for å styrke troverdighet.",
                "Nivå 5: Høy troverdighet og engasjement gjennom hele prosessen."
            ]
        },
        {
            "id": 23,
            "title": "Bygge momentum og tidlig gevinstuttak",
            "question": "Hvordan bygges momentum gjennom tidlig gevinstuttak under gjennomføringsfasen?",
            "scale": [
                "Nivå 1: Ingen fokus på momentum eller tidlig gevinstuttak.",
                "Nivå 2: Noen tidlige gevinster realiseres, men uten strategi.",
                "Nivå 3: Planlagt for tidlig gevinstuttak, men begrenset gjennomføring.",
                "Nivå 4: Systematisk arbeid med tidlig gevinstuttak for å bygge momentum.",
                "Nivå 5: Kontinuerlig fokus på momentum gjennom suksessiv gevinstrealisering."
            ]
        }
    ],
    "Realisering": [
        {
            "id": 1,
            "title": "Bruk av tidligere læring og gevinstdata",
            "question": "Hvordan anvendes læring fra tidligere prosjekter og gevinstarbeid for å optimalisere gevinstuttak under realiseringen?",
            "scale": [
                "Nivå 1: Ingen læring anvendt i realiseringsfasen.",
                "Nivå 2: Enkelte erfaringer tas i betraktning.",
                "Nivå 3: Systematisk bruk av læring for å optimalisere uttak.",
                "Nivå 4: Læring integrert i realiseringsprosessen.",
                "Nivå 5: Kontinuerlig læring og optimalisering under realisering."
            ]
        },
        {
            "id": 2,
            "title": "Strategisk retning og gevinstforståelse",
            "question": "Hvordan sikres strategisk retning og gevinstforståelse under realiseringen?",
            "scale": [
                "Nivå 1: Strategisk retning glemmes under realisering.",
                "Nivå 2: Strategi refereres til, men ikke operasjonalisert.",
                "Nivå 3: Tydelig strategisk retning i realiseringsarbeid.",
                "Nivå 4: Strategi dynamisk tilpasses under realisering.",
                "Nivå 5: Strategi og realisering fullt integrert og sammenvevd."
            ]
        },
        {
            "id": 3,
            "title": "Gevinstkart og visualisering",
            "question": "Hvordan brukes gevinstkartet for å styre realiseringsarbeidet?",
            "scale": [
                "Nivå 1: Gevinstkartet brukes ikke under realisering.",
                "Nivå 2: Gevinstkartet vises, men ikke aktivt brukt.",
                "Nivå 3: Gevinstkartet brukes til å prioritere realisering.",
                "Nivå 4: Gevinstkartet er aktivt styringsverktøy.",
                "Nivå 5: Gevinstkartet dynamisk oppdateres basert på realisering."
            ]
        },
        {
            "id": 4,
            "title": "Strategisk kobling og KPI-er",
            "question": "Hvordan følges opp strategisk kobling og KPI-er under realiseringen?",
            "scale": [
                "Nivå 1: Ingen oppfølging av strategisk kobling.",
                "Nivå 2: KPI-er måles, men kobling til strategi svak.",
                "Nivå 3: Systematisk oppfølging av strategisk kobling.",
                "Nivå 4: Dynamisk justering basert på KPI-utvikling.",
                "Nivå 5: Full integrasjon mellom strategi, KPI-er og realisering."
            ]
        },
        {
            "id": 5,
            "title": "Avgrensning av programgevinst",
            "question": "Hvordan håndteres avgrensning av programgevinster under realiseringen?",
            "scale": [
                "Nivå 1: Avgrensning håndteres ikke under realisering.",
                "Nivå 2: Store avgrensningsutfordringer håndteres.",
                "Nivå 3: System for å håndtere avgrensning.",
                "Nivå 4: Proaktiv håndtering av avgrensning.",
                "Nivå 5: Avgrensning integrert i realiseringsprosessen."
            ]
        },
        {
            "id": 6,
            "title": "Nullpunkter og estimater",
            "question": "Hvordan valideres og justeres nullpunkter og estimater under realiseringen?",
            "scale": [
                "Nivå 1: Nullpunkter og estimater valideres ikke.",
                "Nivå 2: Store avvik håndteres reaktivt.",
                "Nivå 3: Systematisk validering under realisering.",
                "Nivå 4: Kontinuerlig justering basert på realisering.",
                "Nivå 5: Dynamisk oppdatering av nullpunkter og estimater."
            ]
        },
        {
            "id": 7,
            "title": "Hypotesetesting og datagrunnlag",
            "question": "Hvordan valideres hypoteser og datagrunnlag under realiseringen?",
            "scale": [
                "Nivå 1: Hypoteser valideres ikke under realisering.",
                "Nivå 2: Noen hypoteser testes uformelt.",
                "Nivå 3: Systematisk testing av kritiske hypoteser.",
                "Nivå 4: Omfattende validering under realisering.",
                "Nivå 5: Kontinuerlig hypotesetesting og læring."
            ]
        },
        {
            "id": 8,
            "title": "Interessentengasjement",
            "question": "Hvordan opprettholdes interessentengasjement under realiseringen?",
            "scale": [
                "Nivå 1: Interessentengasjement avtar under realisering.",
                "Nivå 2: Begrenset engasjement for viktige beslutninger.",
                "Nivå 3: Regelmessig dialog med interessenter.",
                "Nivå 4: Aktivt interessentengasjement gjennom realisering.",
                "Nivå 5: Interessenter er drivkrefter i realiseringsarbeidet."
            ]
        },
        {
            "id": 9,
            "title": "Gevinstforutsetninger",
            "question": "Hvordan overvåkes og realiseres gevinstforutsetninger under realiseringen?",
            "scale": [
                "Nivå 1: Forutsetninger overvåkes ikke under realisering.",
                "Nivå 2: Noen forutsetninger følges opp.",
                "Nivå 3: Systematisk overvåkning av forutsetninger.",
                "Nivå 4: Aktiv realisering av forutsetninger.",
                "Nivå 5: Forutsetningsrealisering integrert i gevinstuttak."
            ]
        },
        {
            "id": 10,
            "title": "Prinsipielle og vilkårsmessige kriterier",
            "question": "Hvordan håndteres prinsipielle og vilkårsmessige kriterier under realiseringen?",
            "scale": [
                "Nivå 1: Kriterier håndteres ikke under realisering.",
                "Nivå 2: Store avvik fra kriterier håndteres.",
                "Nivå 3: Systematisk håndtering av kriterier.",
                "Nivå 4: Proaktiv tilpasning til kriterier.",
                "Nivå 5: Kriterier integrert i realiseringsbeslutninger."
            ]
        },
        {
            "id": 11,
            "title": "Enighet om nullpunkter/estimater",
            "question": "Hvordan opprettholdes enighet om nullpunkter og estimater under realiseringen?",
            "scale": [
                "Nivå 1: Enighet testes ikke under realisering.",
                "Nivå 2: Enighet bekreftes ved store endringer.",
                "Nivå 3: Regelmessig bekreftelse av enighet.",
                "Nivå 4: Kontinuerlig arbeid for å opprettholde enighet.",
                "Nivå 5: Full enighet gjennom hele realiseringsfasen."
            ]
        },
        {
            "id": 12,
            "title": "Disponering av kostnads- og tidsbesparelser",
            "question": "Hvordan håndteres disponering av besparelser under realiseringen?",
            "scale": [
                "Nivå 1: Disponering håndteres ikke under realisering.",
                "Nivå 2: Store endringer i disponering håndteres.",
                "Nivå 3: Systematisk revisjon av disponering.",
                "Nivå 4: Dynamisk tilpasning av disponering.",
                "Nivå 5: Optimal disponering under realisering."
            ]
        },
        {
            "id": 13,
            "title": "Måling av effektivitet og produktivitet",
            "question": "Hvordan måles og forbedres effektivitet og produktivitet under realiseringen?",
            "scale": [
                "Nivå 1: Effektivitet og produktivitet måles ikke.",
                "Nivå 2: Noen målinger registreres.",
                "Nivå 3: Systematisk måling og rapportering.",
                "Nivå 4: Målinger brukes til forbedring.",
                "Nivå 5: Kontinuerlig forbedring basert på målinger."
            ]
        },
        {
            "id": 14,
            "title": "Operasjonell risiko og ulemper",
            "question": "Hvordan håndteres operasjonelle risikoer og ulemper under realiseringen?",
            "scale": [
                "Nivå 1: Risikoer og ulemper håndteres ikke.",
                "Nivå 2: Store risikoer håndteres reaktivt.",
                "Nivå 3: Systematisk identifisering og håndtering.",
                "Nivå 4: Proaktiv risikohåndtering.",
                "Nivå 5: Risikostyring integrert i realiseringsarbeid."
            ]
        },
        {
            "id": 15,
            "title": "Balanse mellom gevinster og ulemper",
            "question": "Hvordan vurderes balansen mellom gevinster og ulemper under realiseringen?",
            "scale": [
                "Nivå 1: Balansen vurderes ikke under realisering.",
                "Nivå 2: Balansen vurderes ved store endringer.",
                "Nivå 3: Regelmessig vurdering av balansen.",
                "Nivå 4: Systematisk overvåkning av balansen.",
                "Nivå 5: Balansevurdering integrert i beslutninger."
            ]
        },
        {
            "id": 16,
            "title": "Dokumentasjon og gevinstrealiseringsplan",
            "question": "Hvordan brukes gevinstrealiseringsplanen under realiseringen?",
            "scale": [
                "Nivå 1: Gevinstrealiseringsplanen brukes ikke.",
                "Nivå 2: Planen refereres til ved behov.",
                "Nivå 3: Planen brukes aktivt i realisering.",
                "Nivå 4: Planen oppdateres og brukes kontinuerlig.",
                "Nivå 5: Planen er sentralt styringsverktøy."
            ]
        },
        {
            "id": 17,
            "title": "Gevinstrealiseringsplan som operativ handlingsplan",
            "question": "Hvordan fungerer gevinstrealiseringsplanen som operativ handlingsplan under realiseringen?",
            "scale": [
                "Nivå 1: Planen brukes ikke som operativ handlingsplan.",
                "Nivå 2: Planen brukes til enkelte operasjoner.",
                "Nivå 3: Planen er integrert i operativ styring.",
                "Nivå 4: Planen er aktivt operativt verktøy.",
                "Nivå 5: Planen driver operativ virksomhet."
            ]
        },
        {
            "id": 18,
            "title": "Endringsberedskap og operativ mottaksevne",
            "question": "Hvordan utvikles endringsberedskap og mottaksevne under realiseringen?",
            "scale": [
                "Nivå 1: Endringsberedskap utvikles ikke.",
                "Nivå 2: Begrenset fokus på endringsberedskap.",
                "Nivå 3: Systematisk arbeid med endringsberedskap.",
                "Nivå 4: Målrettet utvikling av mottaksevne.",
                "Nivå 5: Høy mottaksevne og endringsberedskap."
            ]
        },
        {
            "id": 19,
            "title": "Kommunikasjon og forankring",
            "question": "Hvordan opprettholdes kommunikasjon og forankring under realiseringen?",
            "scale": [
                "Nivå 1: Kommunikasjon avtar under realisering.",
                "Nivå 2: Begrenset kommunikasjon om realisering.",
                "Nivå 3: Regelmessig kommunikasjon om fremdrift.",
                "Nivå 4: Systematisk kommunikasjon om realisering.",
                "Nivå 5: Kontinuerlig dialog om realiseringsarbeid."
            ]
        },
        {
            "id": 20,
            "title": "Eierskap og ansvar",
            "question": "Hvordan utøves eierskap og ansvar under realiseringen?",
            "scale": [
                "Nivå 1: Eierskap og ansvar svekkes.",
                "Nivå 2: Begrenset eierskap i realiseringsfasen.",
                "Nivå 3: Tydelig eierskap for realisering.",
                "Nivå 4: Aktivt utøvd eierskap.",
                "Nivå 5: Sterk eierskapskultur i realisering."
            ]
        },
        {
            "id": 21,
            "title": "Periodisering og forankring",
            "question": "Hvordan justeres periodisering og forankring under realiseringen?",
            "scale": [
                "Nivå 1: Periodisering justeres ikke.",
                "Nivå 2: Store justeringer i periodisering.",
                "Nivå 3: Regelmessig revisjon av periodisering.",
                "Nivå 4: Dynamisk tilpasning av periodisering.",
                "Nivå 5: Fleksibel periodisering under realisering."
            ]
        },
        {
            "id": 22,
            "title": "Realisme og engasjement",
            "question": "Hvordan opprettholdes realisme og engasjement under realiseringen?",
            "scale": [
                "Nivå 1: Realisme og engasjement avtar.",
                "Nivå 2: Begrenset fokus på å opprettholde engasjement.",
                "Nivå 3: Arbeid med å opprettholde realisme og engasjement.",
                "Nivå 4: Systematisk arbeid for å styrke troverdighet.",
                "Nivå 5: Høy troverdighet og engasjement."
            ]
        },
        {
            "id": 23,
            "title": "Bygge momentum og tidlig gevinstuttak",
            "question": "Hvordan brukes tidlig gevinstuttak for å bygge momentum i realiseringsfasen?",
            "scale": [
                "Nivå 1: Ingen systematisk bruk av tidlig gevinstuttak.",
                "Nivå 2: Enkelte suksesser brukes til å motivere.",
                "Nivå 3: Bevissthet på viktigheten av momentum.",
                "Nivå 4: Strategisk bruk av tidlige gevinster.",
                "Nivå 5: Momentum systematisk bygget og vedlikeholdt."
            ]
        }
    ],
    "Realisert": [
        {
            "id": 1,
            "title": "Bruk av tidligere læring og gevinstdata",
            "question": "Hvordan dokumenteres og deles læring fra gevinstrealiseringen for fremtidig bruk?",
            "scale": [
                "Nivå 1: Ingen dokumentasjon eller deling av læring.",
                "Nivå 2: Enkelte erfaringer deles uformelt.",
                "Nivå 3: Systematisk dokumentasjon av læring.",
                "Nivå 4: Læring deles og diskuteres i organisasjonen.",
                "Nivå 5: Læring integrert i organisasjonens kunnskapsbase."
            ]
        },
        {
            "id": 2,
            "title": "Strategisk retning og gevinstforståelse",
            "question": "Hvordan bidro den strategiske retningen til gevinstrealiseringens suksess?",
            "scale": [
                "Nivå 1: Strategisk retning bidro lite til suksess.",
                "Nivå 2: Strategi var viktig for enkelte gevinster.",
                "Nivå 3: Strategi bidro til flere gevinster.",
                "Nivå 4: Strategi var avgjørende for gevinstrealisering.",
                "Nivå 5: Strategi og gevinstrealisering fullt integrert."
            ]
        },
        {
            "id": 3,
            "title": "Gevinstkart og visualisering",
            "question": "Hvordan bidro gevinstkartet til gevinstrealiseringens suksess?",
            "scale": [
                "Nivå 1: Gevinstkartet bidro lite til suksess.",
                "Nivå 2: Kartet var nyttig for enkelte gevinster.",
                "Nivå 3: Kartet bidro til flere gevinster.",
                "Nivå 4: Kartet var viktig for gevinstrealisering.",
                "Nivå 5: Kartet var avgjørende for suksess."
            ]
        },
        {
            "id": 4,
            "title": "Strategisk kobling og KPI-er",
            "question": "Hvordan bidro den strategiske koblingen og KPI-ene til gevinstrealisering?",
            "scale": [
                "Nivå 1: Strategisk kobling bidro lite.",
                "Nivå 2: Kobling var viktig for enkelte gevinster.",
                "Nivå 3: Kobling bidro til flere gevinster.",
                "Nivå 4: Kobling var avgjørende for realisering.",
                "Nivå 5: Full integrasjon mellom strategi og realisering."
            ]
        },
        {
            "id": 5,
            "title": "Avgrensning av programgevinst",
            "question": "Hvordan bidro avgrensningsarbeidet til gevinstrealiseringens troverdighet?",
            "scale": [
                "Nivå 1: Avgrensning bidro lite til troverdighet.",
                "Nivå 2: Avgrensning viktig for enkelte gevinster.",
                "Nivå 3: Avgrensning bidro til troverdighet for flere gevinster.",
                "Nivå 4: Avgrensning var avgjørende for troverdighet.",
                "Nivå 5: Avgrensning styrket troverdighet betydelig."
            ]
        },
        {
            "id": 6,
            "title": "Nullpunkter og estimater",
            "question": "Hvordan bidro nullpunkter og estimater til gevinstrealiseringens nøyaktighet?",
            "scale": [
                "Nivå 1: Nullpunkter og estimater bidro lite.",
                "Nivå 2: Estimater var nøyaktige for enkelte gevinster.",
                "Nivå 3: Estimater var nøyaktige for flere gevinster.",
                "Nivå 4: Høy nøyaktighet i estimater.",
                "Nivå 5: Estimater var svært nøyaktige."
            ]
        },
        {
            "id": 7,
            "title": "Hypotesetesting og datagrunnlag",
            "question": "Hvordan bidro hypotesetesting og datagrunnlag til gevinstrealiseringens kvalitet?",
            "scale": [
                "Nivå 1: Testing og datagrunnlag bidro lite.",
                "Nivå 2: Testing viktig for enkelte gevinster.",
                "Nivå 3: Testing bidro til kvalitet for flere gevinster.",
                "Nivå 4: Testing var avgjørende for kvalitet.",
                "Nivå 5: Testing og datagrunnlag styrket kvalitet betydelig."
            ]
        },
        {
            "id": 8,
            "title": "Interessentengasjement",
            "question": "Hvordan bidro interessentengasjement til gevinstrealiseringens suksess?",
            "scale": [
                "Nivå 1: Interessentengasjement bidro lite.",
                "Nivå 2: Engasjement viktig for enkelte gevinster.",
                "Nivå 3: Engasjement bidro til flere gevinster.",
                "Nivå 4: Engasjement var avgjørende for suksess.",
                "Nivå 5: Interessenter var drivkrefter for suksess."
            ]
        },
        {
            "id": 9,
            "title": "Gevinstforutsetninger",
            "question": "Hvordan bidro håndtering av gevinstforutsetninger til realiseringens suksess?",
            "scale": [
                "Nivå 1: Forutsetningshåndtering bidro lite.",
                "Nivå 2: Håndtering viktig for enkelte gevinster.",
                "Nivå 3: Håndtering bidro til flere gevinster.",
                "Nivå 4: Håndtering var avgjørende for suksess.",
                "Nivå 5: Forutsetningshåndtering var suksessfaktor."
            ]
        },
        {
            "id": 10,
            "title": "Prinsipielle og vilkårsmessige kriterier",
            "question": "Hvordan bidro håndtering av kriterier til gevinstrealisering?",
            "scale": [
                "Nivå 1: Kriteriehåndtering bidro lite.",
                "Nivå 2: Håndtering viktig for enkelte gevinster.",
                "Nivå 3: Håndtering bidro til flere gevinster.",
                "Nivå 4: Håndtering var avgjørende for realisering.",
                "Nivå 5: Kriteriehåndtering styrket realisering."
            ]
        },
        {
            "id": 11,
            "title": "Enighet om nullpunkter/estimater",
            "question": "Hvordan bidro enighet om nullpunkter og estimater til realiseringens suksess?",
            "scale": [
                "Nivå 1: Enighet bidro lite til suksess.",
                "Nivå 2: Enighet viktig for enkelte gevinster.",
                "Nivå 3: Enighet bidro til flere gevinster.",
                "Nivå 4: Enighet var avgjørende for suksess.",
                "Nivå 5: Full enighet styrket suksess betydelig."
            ]
        },
        {
            "id": 12,
            "title": "Disponering av kostnads- og tidsbesparelser",
            "question": "Hvordan bidro disponering av besparelser til gevinstrealiseringens verdiskapning?",
            "scale": [
                "Nivå 1: Disponering bidro lite til verdiskapning.",
                "Nivå 2: Disponering viktig for enkelte gevinster.",
                "Nivå 3: Disponering bidro til verdi for flere gevinster.",
                "Nivå 4: Disponering var avgjørende for verdiskapning.",
                "Nivå 5: Optimal disponering maksimerte verdi."
            ]
        },
        {
            "id": 13,
            "title": "Måling av effektivitet og produktivitet",
            "question": "Hvordan bidro måling av effektivitet og produktivitet til gevinstrealisering?",
            "scale": [
                "Nivå 1: Måling bidro lite til realisering.",
                "Nivå 2: Måling viktig for enkelte gevinster.",
                "Nivå 3: Måling bidro til flere gevinster.",
                "Nivå 4: Måling var avgjørende for realisering.",
                "Nivå 5: Måling drevet gevinstrealisering."
            ]
        },
        {
            "id": 14,
            "title": "Operasjonell risiko og ulemper",
            "question": "Hvordan bidro håndtering av risiko og ulemper til gevinstrealiseringens robusthet?",
            "scale": [
                "Nivå 1: Risikohåndtering bidro lite.",
                "Nivå 2: Håndtering viktig for enkelte gevinster.",
                "Nivå 3: Håndtering bidro til robusthet for flere gevinster.",
                "Nivå 4: Håndtering var avgjørende for robusthet.",
                "Nivå 5: Risikohåndtering styrket robusthet betydelig."
            ]
        },
        {
            "id": 15,
            "title": "Balanse mellom gevinster og ulemper",
            "question": "Hvordan bidro balansevurdering til gevinstrealiseringens bærekraft?",
            "scale": [
                "Nivå 1: Balansevurdering bidro lite.",
                "Nivå 2: Vurdering viktig for enkelte gevinster.",
                "Nivå 3: Vurdering bidro til bærekraft for flere gevinster.",
                "Nivå 4: Vurdering var avgjørende for bærekraft.",
                "Nivå 5: Balansevurdering styrket bærekraft betydelig."
            ]
        },
        {
            "id": 16,
            "title": "Dokumentasjon og gevinstrealiseringsplan",
            "question": "Hvordan bidro gevinstrealiseringsplanen til gevinstrealiseringens suksess?",
            "scale": [
                "Nivå 1: Planen bidro lite til suksess.",
                "Nivå 2: Planen viktig for enkelte gevinster.",
                "Nivå 3: Planen bidro til flere gevinster.",
                "Nivå 4: Planen var avgjørende for suksess.",
                "Nivå 5: Planen var suksessfaktor for realisering."
            ]
        },
        {
            "id": 17,
            "title": "Gevinstrealiseringsplan som operativ handlingsplan",
            "question": "Hvordan bidro gevinstrealiseringsplanen som operativ handlingsplan til suksess?",
            "scale": [
                "Nivå 1: Planen som handlingsplan bidro lite.",
                "Nivå 2: Planen viktig for enkelte operasjoner.",
                "Nivå 3: Planen bidro til flere operasjoner.",
                "Nivå 4: Planen var avgjørende for operativ suksess.",
                "Nivå 5: Planen drevet operativ gevinstrealisering."
            ]
        },
        {
            "id": 18,
            "title": "Endringsberedskap og operativ mottaksevne",
            "question": "Hvordan bidro endringsberedskap og mottaksevne til gevinstrealisering?",
            "scale": [
                "Nivå 1: Beredskap og mottaksevne bidro lite.",
                "Nivå 2: Beredskap viktig for enkelte gevinster.",
                "Nivå 3: Beredskap bidro til flere gevinster.",
                "Nivå 4: Beredskap var avgjørende for realisering.",
                "Nivå 5: Høy mottaksevne drevet realisering."
            ]
        },
        {
            "id": 19,
            "title": "Kommunikasjon og forankring",
            "question": "Hvordan bidro kommunikasjon og forankring til gevinstrealiseringens suksess?",
            "scale": [
                "Nivå 1: Kommunikasjon bidro lite til suksess.",
                "Nivå 2: Kommunikasjon viktig for enkelte gevinster.",
                "Nivå 3: Kommunikasjon bidro til flere gevinster.",
                "Nivå 4: Kommunikasjon var avgjørende for suksess.",
                "Nivå 5: God kommunikasjon styrket suksess betydelig."
            ]
        },
        {
            "id": 20,
            "title": "Eierskap og ansvar",
            "question": "Hvordan bidro eierskap og ansvar til gevinstrealiseringens suksess?",
            "scale": [
                "Nivå 1: Eierskap og ansvar bidro lite.",
                "Nivå 2: Eierskap viktig for enkelte gevinster.",
                "Nivå 3: Eierskap bidro til flere gevinster.",
                "Nivå 4: Eierskap var avgjørende for suksess.",
                "Nivå 5: Sterkt eierskap drevet suksess."
            ]
        },
        {
            "id": 21,
            "title": "Periodisering og forankring",
            "question": "Hvordan bidro periodisering og forankring til gevinstrealiseringens effektivitet?",
            "scale": [
                "Nivå 1: Periodisering bidro lite til effektivitet.",
                "Nivå 2: Periodisering viktig for enkelte gevinster.",
                "Nivå 3: Periodisering bidro til effektivitet for flere gevinster.",
                "Nivå 4: Periodisering var avgjørende for effektivitet.",
                "Nivå 5: God periodisering maksimerte effektivitet."
            ]
        },
        {
            "id": 22,
            "title": "Realisme og engasjement",
            "question": "Hvordan bidro realisme og engasjement til gevinstrealiseringens troverdighet?",
            "scale": [
                "Nivå 1: Realisme og engasjement bidro lite.",
                "Nivå 2: Realisme viktig for enkelte gevinster.",
                "Nivå 3: Realisme bidro til troverdighet for flere gevinster.",
                "Nivå 4: Realisme var avgjørende for troverdighet.",
                "Nivå 5: Høy troverdighet styrket realisering."
            ]
        },
        {
            "id": 23,
            "title": "Bygge momentum og tidlig gevinstuttak",
            "question": "Hvordan bidro arbeid med momentum og tidlig gevinstuttak til langsiktig suksess?",
            "scale": [
                "Nivå 1: Momentum og tidlig uttak bidro lite.",
                "Nivå 2: Tidlig uttak viktig for enkelte gevinster.",
                "Nivå 3: Tidlig uttak bidro til momentum for flere gevinster.",
                "Nivå 4: Momentum var avgjørende for suksess.",
                "Nivå 5: Momentum og tidlig uttak drevet langsiktig suksess."
            ]
        }
    ]
}

# ============================================================================
# DATALAGRING
# ============================================================================
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'rb') as f:
                return pickle.load(f)
        except:
            pass
    return {'projects': {}}

def save_data(data):
    with open(DATA_FILE, 'wb') as f:
        pickle.dump(data, f)

def get_data():
    if 'app_data' not in st.session_state:
        st.session_state.app_data = load_data()
    return st.session_state.app_data

def persist_data():
    save_data(st.session_state.app_data)

# ============================================================================
# STYLING
# ============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Source Sans Pro', sans-serif; }

.main-header {
    font-size: 2rem;
    color: #172141;
    text-align: center;
    margin-bottom: 0.3rem;
    font-weight: 700;
}

.sub-header {
    font-size: 0.95rem;
    color: #0053A6;
    text-align: center;
    margin-bottom: 1.5rem;
}

.phase-header {
    color: #172141;
    border-bottom: 3px solid #64C8FA;
    padding-bottom: 0.5rem;
    font-weight: 600;
    font-size: 1.3rem;
}

.info-box {
    background: linear-gradient(135deg, #C4EFFF 0%, #F2FAFD 100%);
    padding: 1rem;
    border-radius: 10px;
    border-left: 4px solid #64C8FA;
    margin: 0.8rem 0;
}

.success-box {
    background: linear-gradient(135deg, #DDFAE2 0%, #F2FAFD 100%);
    padding: 1rem;
    border-radius: 10px;
    border-left: 4px solid #35DE6D;
    margin: 0.8rem 0;
}

.warning-box {
    background: linear-gradient(135deg, rgba(255, 160, 64, 0.15) 0%, #F2FAFD 100%);
    padding: 1rem;
    border-radius: 10px;
    border-left: 4px solid #FFA040;
    margin: 0.8rem 0;
}

.critical-box {
    background: linear-gradient(135deg, rgba(255, 107, 107, 0.15) 0%, #F2FAFD 100%);
    padding: 1rem;
    border-radius: 10px;
    border-left: 4px solid #FF6B6B;
    margin: 0.8rem 0;
}

.metric-card {
    background: #F2FAFD;
    padding: 1rem;
    border-radius: 10px;
    border-left: 4px solid #0053A6;
    text-align: center;
    margin: 0.3rem 0;
}

.metric-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #172141;
}

.metric-label {
    font-size: 0.75rem;
    color: #666;
    text-transform: uppercase;
}

.stButton > button {
    background: linear-gradient(135deg, #0053A6 0%, #172141 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    font-weight: 600;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 83, 166, 0.3);
}

.stExpander {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    margin: 0.3rem 0;
}

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #64C8FA 0%, #35DE6D 100%);
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HJELPEFUNKSJONER
# ============================================================================
def get_score_color(score):
    if score >= 4.5: return "#35DE6D"
    elif score >= 3.5: return "#64C8FA"
    elif score >= 2.5: return "#FFA040"
    else: return "#FF6B6B"

def get_score_text(score):
    if score >= 4.5: return "Høy modenhet"
    elif score >= 3.5: return "God modenhet"
    elif score >= 2.5: return "Moderat modenhet"
    elif score >= 1.5: return "Begrenset modenhet"
    else: return "Lav modenhet"

def calculate_project_stats(project):
    """Beregn statistikk for et prosjekt"""
    if not project.get('interviews'):
        return None
    
    all_scores = {}
    for phase in phases_data:
        all_scores[phase] = {}
        for q in phases_data[phase]:
            all_scores[phase][q['id']] = []
    
    for interview in project['interviews'].values():
        for phase, questions in interview.get('responses', {}).items():
            for q_id, resp in questions.items():
                if resp.get('score', 0) > 0:
                    all_scores[phase][int(q_id)].append(resp['score'])
    
    stats = {
        'phases': {},
        'questions': {},
        'total_interviews': len(project['interviews']),
        'overall_avg': 0,
        'improvement_areas': []
    }
    
    all_avgs = []
    
    for phase in phases_data:
        phase_scores = []
        stats['questions'][phase] = {}
        
        for q in phases_data[phase]:
            scores = all_scores[phase][q['id']]
            if scores:
                avg = np.mean(scores)
                stats['questions'][phase][q['id']] = {
                    'avg': avg,
                    'min': min(scores),
                    'max': max(scores),
                    'count': len(scores),
                    'title': q['title'],
                    'scores': scores
                }
                phase_scores.append(avg)
                all_avgs.append(avg)
                
                if avg < 3:
                    stats['improvement_areas'].append({
                        'phase': phase,
                        'question_id': q['id'],
                        'question': q['title'],
                        'score': avg
                    })
        
        if phase_scores:
            stats['phases'][phase] = {
                'avg': np.mean(phase_scores),
                'min': min(phase_scores),
                'max': max(phase_scores),
                'scores': phase_scores
            }
    
    if all_avgs:
        stats['overall_avg'] = np.mean(all_avgs)
    
    stats['improvement_areas'].sort(key=lambda x: x['score'])
    
    return stats

# ============================================================================
# VISUALISERINGER - MULTIDIMENSJONALE CHARTS
# ============================================================================
def create_phase_radar_chart(phase_data, title="Modenhet per fase"):
    """Radardiagram for faser"""
    if not phase_data or len(phase_data) < 3:
        return None
    
    categories = list(phase_data.keys())
    values = [phase_data[c]['avg'] for c in categories]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(0, 83, 166, 0.3)',
        line=dict(color='#0053A6', width=3),
        name='Gjennomsnitt'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickvals=[1, 2, 3, 4, 5],
                gridcolor='#C4EFFF',
                linecolor='#64C8FA'
            ),
            angularaxis=dict(gridcolor='#C4EFFF'),
            bgcolor='#F2FAFD'
        ),
        showlegend=False,
        title=dict(text=title, font=dict(size=16, color='#172141')),
        height=450,
        margin=dict(l=80, r=80, t=80, b=80),
        paper_bgcolor='white'
    )
    
    return fig

def create_detailed_phase_radar(question_data, phase_name):
    """Detaljert radardiagram for alle spørsmål i en fase"""
    if not question_data or len(question_data) < 3:
        return None
    
    # Sorter etter spørsmåls-ID
    sorted_items = sorted(question_data.items(), key=lambda x: x[0])
    
    categories = [f"{qid}. {data['title'][:25]}..." if len(data['title']) > 25 else f"{qid}. {data['title']}" 
                  for qid, data in sorted_items]
    values = [data['avg'] for _, data in sorted_items]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(100, 200, 250, 0.3)',
        line=dict(color='#64C8FA', width=2),
        name=phase_name
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickvals=[1, 2, 3, 4, 5],
                gridcolor='#e0e0e0'
            ),
            bgcolor='#F2FAFD'
        ),
        showlegend=False,
        title=dict(text=f"Detaljert modenhet: {phase_name}", font=dict(size=14, color='#172141')),
        height=550,
        margin=dict(l=120, r=120, t=80, b=80),
        paper_bgcolor='white'
    )
    
    return fig

def create_interview_comparison_radar(project, phase_name):
    """Sammenlign intervjuer i radardiagram"""
    if not project.get('interviews') or len(project['interviews']) < 2:
        return None
    
    fig = go.Figure()
    
    colors = ['#0053A6', '#64C8FA', '#35DE6D', '#FFA040', '#FF6B6B', '#9C27B0', '#795548']
    
    for idx, (int_id, interview) in enumerate(project['interviews'].items()):
        int_name = interview['info'].get('interviewee', f'Intervju {idx+1}')[:15]
        
        if phase_name in interview.get('responses', {}):
            q_ids = sorted([int(qid) for qid in interview['responses'][phase_name].keys()])
            
            categories = []
            values = []
            
            for qid in q_ids:
                resp = interview['responses'][phase_name].get(str(qid), {})
                if resp.get('score', 0) > 0:
                    # Finn tittel
                    title = str(qid)
                    for q in phases_data[phase_name]:
                        if q['id'] == qid:
                            title = f"{qid}. {q['title'][:15]}..."
                            break
                    categories.append(title)
                    values.append(resp['score'])
            
            if len(categories) >= 3:
                fig.add_trace(go.Scatterpolar(
                    r=values + [values[0]],
                    theta=categories + [categories[0]],
                    name=int_name,
                    fill='toself',
                    opacity=0.5,
                    line=dict(color=colors[idx % len(colors)], width=2)
                ))
    
    if not fig.data:
        return None
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5])
        ),
        showlegend=True,
        title=dict(text=f"Sammenligning: {phase_name}", font=dict(size=14, color='#172141')),
        height=500,
        paper_bgcolor='white'
    )
    
    return fig

def create_bar_chart(phase_data, title="Score per fase"):
    """Søylediagram for faser"""
    if not phase_data:
        return None
    
    categories = list(phase_data.keys())
    values = [phase_data[c]['avg'] for c in categories]
    colors = [get_score_color(v) for v in values]
    
    fig = go.Figure(data=[
        go.Bar(
            x=categories,
            y=values,
            marker_color=colors,
            text=[f'{v:.2f}' for v in values],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color='#172141')),
        xaxis_title="",
        yaxis_title="Score",
        yaxis=dict(range=[0, 5.5], gridcolor='#e0e0e0'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=400
    )
    
    return fig

def create_heatmap(stats):
    """Heatmap over alle spørsmål og faser"""
    if not stats or not stats.get('questions'):
        return None
    
    phases = list(phases_data.keys())
    max_questions = max(len(phases_data[p]) for p in phases)
    
    z_data = []
    y_labels = []
    
    for q_num in range(1, max_questions + 1):
        row = []
        for phase in phases:
            if phase in stats['questions'] and q_num in stats['questions'][phase]:
                row.append(stats['questions'][phase][q_num]['avg'])
            else:
                row.append(None)
        z_data.append(row)
        y_labels.append(f"Sp. {q_num}")
    
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=phases,
        y=y_labels,
        colorscale=[
            [0, '#FF6B6B'],
            [0.25, '#FFA040'],
            [0.5, '#FFD93D'],
            [0.75, '#64C8FA'],
            [1, '#35DE6D']
        ],
        zmin=1,
        zmax=5,
        colorbar=dict(title='Score', tickvals=[1, 2, 3, 4, 5]),
        hoverongaps=False
    ))
    
    fig.update_layout(
        title=dict(text='Modenhetsoversikt - Alle spørsmål', font=dict(size=16, color='#172141')),
        xaxis_title="Fase",
        yaxis_title="Spørsmål",
        height=600,
        paper_bgcolor='white'
    )
    
    return fig

# ============================================================================
# HOVEDAPPLIKASJON
# ============================================================================
def main():
    data = get_data()
    
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("bane_nor_logo.png.jpg", width=180)
        except:
            st.markdown("### 🚂 Bane NOR")
    
    st.markdown('<h1 class="main-header">Modenhetsvurdering</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Gevinstrealisering | Systematisk vurdering med automatisk lagring</p>', unsafe_allow_html=True)
    
    # Hovednavigasjon
    tab1, tab2, tab3, tab4 = st.tabs([
        "📁 Prosjekter",
        "🎤 Intervju", 
        "📊 Resultater",
        "📋 Rapport"
    ])
    
    # ==========================================================================
    # TAB 1: PROSJEKTER
    # ==========================================================================
    with tab1:
        st.markdown("## Prosjektoversikt")
        
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.markdown("### ➕ Nytt prosjekt")
            with st.form("new_project"):
                project_name = st.text_input("Prosjektnavn", placeholder="F.eks. ERTMS Østlandet")
                project_desc = st.text_area("Beskrivelse", placeholder="Kort beskrivelse...", height=80)
                
                if st.form_submit_button("Opprett prosjekt", use_container_width=True):
                    if project_name:
                        project_id = datetime.now().strftime("%Y%m%d%H%M%S")
                        data['projects'][project_id] = {
                            'name': project_name,
                            'description': project_desc,
                            'created': datetime.now().isoformat(),
                            'interviews': {}
                        }
                        persist_data()
                        st.success(f"✅ Prosjekt '{project_name}' opprettet!")
                        st.rerun()
                    else:
                        st.error("Skriv inn et prosjektnavn")
        
        with col1:
            st.markdown("### Mine prosjekter")
            
            if not data['projects']:
                st.markdown('<div class="info-box">Ingen prosjekter ennå. Opprett et nytt prosjekt for å starte →</div>', unsafe_allow_html=True)
            else:
                for proj_id, project in data['projects'].items():
                    num_interviews = len(project.get('interviews', {}))
                    stats = calculate_project_stats(project)
                    avg_score = stats['overall_avg'] if stats else 0
                    
                    with st.expander(f"📁 {project['name']} ({num_interviews} intervjuer)", expanded=False):
                        col_a, col_b = st.columns([3, 1])
                        
                        with col_a:
                            st.write(f"**Beskrivelse:** {project.get('description', 'Ingen')}")
                            st.write(f"**Opprettet:** {project['created'][:10]}")
                            
                            if num_interviews > 0 and avg_score > 0:
                                st.write(f"**Gjennomsnittlig modenhet:** {avg_score:.2f} ({get_score_text(avg_score)})")
                                
                                st.write("**Intervjuer:**")
                                for int_id, interview in project['interviews'].items():
                                    info = interview.get('info', {})
                                    st.write(f"• {info.get('interviewee', 'Ukjent')} ({info.get('role', '-')}) - {info.get('date', '')}")
                        
                        with col_b:
                            if st.button("🗑️ Slett", key=f"del_{proj_id}"):
                                del data['projects'][proj_id]
                                persist_data()
                                st.rerun()
    
    # ==========================================================================
    # TAB 2: INTERVJU
    # ==========================================================================
    with tab2:
        st.markdown("## Gjennomfør intervju")
        
        if not data['projects']:
            st.warning("⚠️ Opprett et prosjekt først under 'Prosjekter'-fanen")
        else:
            project_options = {p['name']: pid for pid, p in data['projects'].items()}
            selected_project_name = st.selectbox("Velg prosjekt", options=list(project_options.keys()))
            selected_project_id = project_options[selected_project_name]
            project = data['projects'][selected_project_id]
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🆕 Start nytt intervju")
                with st.form("new_interview"):
                    interviewer = st.text_input("Intervjuer (deg)", placeholder="Ditt navn")
                    interviewee = st.text_input("Intervjuobjekt *", placeholder="Navn på personen")
                    role = st.text_input("Rolle/stilling", placeholder="F.eks. Prosjektleder")
                    date = st.date_input("Dato", value=datetime.now())
                    
                    if st.form_submit_button("▶️ Start intervju", use_container_width=True):
                        if interviewee:
                            interview_id = datetime.now().strftime("%Y%m%d%H%M%S")
                            project['interviews'][interview_id] = {
                                'info': {
                                    'interviewer': interviewer,
                                    'interviewee': interviewee,
                                    'role': role,
                                    'date': date.strftime('%Y-%m-%d')
                                },
                                'responses': {}
                            }
                            persist_data()
                            st.session_state['active_interview'] = {
                                'project_id': selected_project_id,
                                'interview_id': interview_id
                            }
                            st.success(f"✅ Intervju med {interviewee} startet!")
                            st.rerun()
                        else:
                            st.error("Skriv inn navn på intervjuobjekt")
            
            with col2:
                st.markdown("### 📝 Fortsett eksisterende")
                if project['interviews']:
                    interview_options = {
                        f"{i['info']['interviewee']} ({i['info']['date']})": iid 
                        for iid, i in project['interviews'].items()
                    }
                    selected_interview = st.selectbox("Velg intervju", options=list(interview_options.keys()))
                    
                    if st.button("Fortsett dette intervjuet", use_container_width=True):
                        st.session_state['active_interview'] = {
                            'project_id': selected_project_id,
                            'interview_id': interview_options[selected_interview]
                        }
                        st.rerun()
                else:
                    st.info("Ingen intervjuer i dette prosjektet ennå")
            
            # Aktivt intervju
            if 'active_interview' in st.session_state:
                active = st.session_state['active_interview']
                
                if active['project_id'] in data['projects']:
                    project = data['projects'][active['project_id']]
                    if active['interview_id'] in project['interviews']:
                        interview = project['interviews'][active['interview_id']]
                        
                        st.markdown("---")
                        st.markdown(f"### 🎤 Intervju: **{interview['info']['interviewee']}** ({interview['info']['role']})")
                        
                        # Fremdrift
                        total_q = sum(len(phases_data[p]) for p in phases_data)
                        answered_q = sum(
                            1 for phase in interview.get('responses', {}).values() 
                            for resp in phase.values() 
                            if resp.get('score', 0) > 0
                        )
                        
                        st.progress(answered_q / total_q)
                        st.caption(f"Besvart: {answered_q} av {total_q} spørsmål ({answered_q/total_q*100:.0f}%)")
                        
                        # Faser
                        phase_tabs = st.tabs(list(phases_data.keys()))
                        
                        for phase_tab, phase_name in zip(phase_tabs, phases_data.keys()):
                            with phase_tab:
                                if phase_name not in interview['responses']:
                                    interview['responses'][phase_name] = {}
                                
                                # Vis antall besvart i denne fasen
                                phase_answered = sum(1 for resp in interview['responses'][phase_name].values() if resp.get('score', 0) > 0)
                                st.caption(f"📊 {phase_answered} av {len(phases_data[phase_name])} besvart i denne fasen")
                                
                                for q in phases_data[phase_name]:
                                    q_id = str(q['id'])
                                    
                                    if q_id not in interview['responses'][phase_name]:
                                        interview['responses'][phase_name][q_id] = {'score': 0, 'notes': ''}
                                    
                                    resp = interview['responses'][phase_name][q_id]
                                    status = "✅" if resp['score'] > 0 else "⬜"
                                    score_display = f" → Nivå {resp['score']}" if resp['score'] > 0 else ""
                                    
                                    with st.expander(f"{status} {q['id']}. {q['title']}{score_display}"):
                                        st.markdown(f"**{q['question']}**")
                                        
                                        st.markdown("**Modenhetsskala:**")
                                        for level in q['scale']:
                                            st.write(f"- {level}")
                                        
                                        st.markdown("---")
                                        
                                        new_score = st.radio(
                                            "Velg nivå:",
                                            options=[0, 1, 2, 3, 4, 5],
                                            index=resp['score'],
                                            key=f"s_{phase_name}_{q_id}",
                                            horizontal=True,
                                            format_func=lambda x: "Ikke vurdert" if x == 0 else f"Nivå {x}"
                                        )
                                        
                                        new_notes = st.text_area(
                                            "Notater:",
                                            value=resp['notes'],
                                            key=f"n_{phase_name}_{q_id}",
                                            placeholder="Begrunnelse, sitater, observasjoner...",
                                            height=80
                                        )
                                        
                                        if st.button("💾 Lagre", key=f"save_{phase_name}_{q_id}"):
                                            interview['responses'][phase_name][q_id] = {
                                                'score': new_score,
                                                'notes': new_notes
                                            }
                                            persist_data()
                                            st.success("Lagret!")
                                            st.rerun()
                        
                        # Avslutt intervju
                        st.markdown("---")
                        col1, col2, col3 = st.columns([1, 1, 1])
                        with col2:
                            if st.button("✅ Avslutt intervju", use_container_width=True):
                                del st.session_state['active_interview']
                                st.success("Intervju avsluttet og lagret!")
                                st.rerun()
    
    # ==========================================================================
    # TAB 3: RESULTATER
    # ==========================================================================
    with tab3:
        st.markdown("## Resultater og analyse")
        
        if not data['projects']:
            st.warning("Ingen prosjekter å vise")
        else:
            project_options = {p['name']: pid for pid, p in data['projects'].items()}
            selected_project_name = st.selectbox("Velg prosjekt", options=list(project_options.keys()), key="results_proj")
            selected_project_id = project_options[selected_project_name]
            project = data['projects'][selected_project_id]
            
            stats = calculate_project_stats(project)
            
            if not stats or stats['total_interviews'] == 0:
                st.info("Ingen intervjuer gjennomført for dette prosjektet ennå")
            else:
                # Nøkkeltall
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Intervjuer</div>
                            <div class="metric-value">{stats['total_interviews']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    color = get_score_color(stats['overall_avg'])
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Gjennomsnitt</div>
                            <div class="metric-value" style="color: {color}">{stats['overall_avg']:.2f}</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    if stats['phases']:
                        min_phase = min(stats['phases'].items(), key=lambda x: x[1]['avg'])
                        st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-label">Svakeste fase</div>
                                <div style="font-size: 0.9rem; font-weight: 600;">{min_phase[0][:15]}</div>
                                <div style="color: {get_score_color(min_phase[1]['avg'])}">{min_phase[1]['avg']:.2f}</div>
                            </div>
                        """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Forbedringsområder</div>
                            <div class="metric-value" style="color: #FFA040">{len(stats['improvement_areas'])}</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Overordnede visualiseringer
                st.markdown("### 📈 Overordnet modenhet")
                col1, col2 = st.columns(2)
                
                with col1:
                    if stats['phases'] and len(stats['phases']) >= 3:
                        radar = create_phase_radar_chart(stats['phases'], "Modenhet per fase")
                        if radar:
                            st.plotly_chart(radar, use_container_width=True)
                    else:
                        st.info("Trenger data fra minst 3 faser for radardiagram")
                
                with col2:
                    bar = create_bar_chart(stats['phases'], "Gjennomsnittsscore per fase")
                    if bar:
                        st.plotly_chart(bar, use_container_width=True)
                
                # Heatmap
                st.markdown("### 🗺️ Heatmap - Alle spørsmål")
                heatmap = create_heatmap(stats)
                if heatmap:
                    st.plotly_chart(heatmap, use_container_width=True)
                
                # Detaljerte radardiagrammer per fase
                st.markdown("---")
                st.markdown("### 🔍 Detaljert analyse per fase")
                
                for phase_name in phases_data.keys():
                    if phase_name in stats['questions'] and stats['questions'][phase_name]:
                        with st.expander(f"📊 {phase_name} - Detaljert radardiagram", expanded=False):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                detailed_radar = create_detailed_phase_radar(stats['questions'][phase_name], phase_name)
                                if detailed_radar:
                                    st.plotly_chart(detailed_radar, use_container_width=True)
                            
                            with col2:
                                # Sammenligning av intervjuer
                                comparison = create_interview_comparison_radar(project, phase_name)
                                if comparison:
                                    st.plotly_chart(comparison, use_container_width=True)
                                else:
                                    st.info("Trenger 2+ intervjuer for sammenligning")
                            
                            # Tabell
                            st.markdown("**Detaljerte scores:**")
                            table_data = []
                            for q_id, q_data in sorted(stats['questions'][phase_name].items()):
                                table_data.append({
                                    'Nr': q_id,
                                    'Spørsmål': q_data['title'],
                                    'Gjennomsnitt': f"{q_data['avg']:.2f}",
                                    'Min': q_data['min'],
                                    'Maks': q_data['max'],
                                    'Svar': q_data['count']
                                })
                            st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
                
                # Forbedringsområder
                st.markdown("---")
                st.markdown("### 🎯 Forbedringsområder (score < 3)")
                
                if not stats['improvement_areas']:
                    st.markdown('<div class="success-box">✅ Ingen kritiske forbedringsområder identifisert!</div>', unsafe_allow_html=True)
                else:
                    for area in stats['improvement_areas'][:15]:
                        box_class = "critical-box" if area['score'] < 2 else "warning-box"
                        st.markdown(f"""
                            <div class="{box_class}">
                                <strong>{area['phase']}</strong> - Sp. {area['question_id']}: {area['question']}<br>
                                Score: <strong>{area['score']:.2f}</strong> ({get_score_text(area['score'])})
                            </div>
                        """, unsafe_allow_html=True)
    
    # ==========================================================================
    # TAB 4: RAPPORT
    # ==========================================================================
    with tab4:
        st.markdown("## Generer rapport")
        
        if not data['projects']:
            st.warning("Ingen prosjekter å generere rapport for")
        else:
            project_options = {p['name']: pid for pid, p in data['projects'].items()}
            selected_project_name = st.selectbox("Velg prosjekt", options=list(project_options.keys()), key="report_proj")
            selected_project_id = project_options[selected_project_name]
            project = data['projects'][selected_project_id]
            
            stats = calculate_project_stats(project)
            
            if not stats or stats['total_interviews'] == 0:
                st.info("Gjennomfør minst ett intervju for å generere rapport")
            else:
                st.markdown("### Rapportinnstillinger")
                
                include_details = st.checkbox("Inkluder detaljerte spørsmålssvar", value=True)
                include_notes = st.checkbox("Inkluder notater fra intervjuer", value=True)
                
                if st.button("📄 Generer rapport", use_container_width=True):
                    report = []
                    report.append("=" * 70)
                    report.append("MODENHETSVURDERING - GEVINSTREALISERING")
                    report.append("Bane NOR - Konsern Controlling")
                    report.append("=" * 70)
                    report.append("")
                    report.append(f"Prosjekt: {project['name']}")
                    report.append(f"Beskrivelse: {project.get('description', '-')}")
                    report.append(f"Rapport generert: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                    report.append(f"Antall intervjuer: {stats['total_interviews']}")
                    report.append("")
                    
                    report.append("-" * 70)
                    report.append("SAMMENDRAG")
                    report.append("-" * 70)
                    report.append(f"Samlet modenhetsnivå: {stats['overall_avg']:.2f} ({get_score_text(stats['overall_avg'])})")
                    report.append("")
                    
                    report.append("Modenhet per fase:")
                    for phase, phase_stat in stats['phases'].items():
                        report.append(f"  {phase}: {phase_stat['avg']:.2f} (min: {phase_stat['min']:.1f}, maks: {phase_stat['max']:.1f})")
                    report.append("")
                    
                    report.append("-" * 70)
                    report.append("FORBEDRINGSOMRÅDER (Score < 3)")
                    report.append("-" * 70)
                    if stats['improvement_areas']:
                        for area in stats['improvement_areas']:
                            report.append(f"  [{area['phase]}] Sp. {area['question_id']}: {area['question']}")
                            report.append(f"    Score: {area['score']:.2f}"),
                    else:
                        report.append("  Ingen kritiske forbedringsområder identifisert.")
                    report.append("")
                    
                    if include_details:
                        report.append("-" * 70)
                        report.append("DETALJERTE RESULTATER PER FASE")
                        report.append("-" * 70)
                        
                        for phase in phases_data:
                            if phase in stats['questions']:
                                report.append(f"\n{phase.upper()}")
                                report.append("-" * 40)
                                for q_id, q_data in sorted(stats['questions'][phase].items()):
                                    report.append(f"  {q_id}. {q_data['title']}")
                                    report.append(f"     Gjennomsnitt: {q_data['avg']:.2f} | Min: {q_data['min']} | Maks: {q_data['max']} | Svar: {q_data['count']}")
                    
                    if include_notes:
                        report.append("")
                        report.append("-" * 70)
                        report.append("INTERVJUNOTATER")
                        report.append("-" * 70)
                        
                        for int_id, interview in project['interviews'].items():
                            info = interview['info']
                            report.append(f"\n{info['interviewee']} ({info['role']}) - {info['date']}")
                            report.append("-" * 40)
                            
                            has_notes = False
                            for phase, questions in interview.get('responses', {}).items():
                                for q_id, resp in questions.items():
                                    if resp.get('notes'):
                                        has_notes = True
                                        q_title = ""
                                        for q in phases_data.get(phase, []):
                                            if str(q['id']) == q_id:
                                                q_title = q['title']
                                                break
                                        report.append(f"  [{phase}] {q_id}. {q_title}")
                                        report.append(f"  Score: {resp['score']} | Notat: {resp['notes']}")
                                        report.append("")
                            
                            if not has_notes:
                                report.append("  (Ingen notater)")
                    
                    report.append("")
                    report.append("=" * 70)
                    report.append("SLUTT PÅ RAPPORT")
                    report.append("=" * 70)
                    
                    report_text = "\n".join(report)
                    
                    st.text_area("Rapport", value=report_text, height=400)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "📥 Last ned rapport (.txt)",
                            data=report_text,
                            file_name=f"modenhet_{project['name']}_{datetime.now().strftime('%Y%m%d')}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    
                    with col2:
                        # CSV eksport
                        csv_data = []
                        for phase in stats['questions']:
                            for q_id, q_data in stats['questions'][phase].items():
                                csv_data.append({
                                    'Fase': phase,
                                    'SpørsmålID': q_id,
                                    'Tittel': q_data['title'],
                                    'Gjennomsnitt': round(q_data['avg'], 2),
                                    'Min': q_data['min'],
                                    'Maks': q_data['max'],
                                    'AntallSvar': q_data['count']
                                })
                        
                        csv_df = pd.DataFrame(csv_data)
                        csv_string = csv_df.to_csv(index=False, sep=';')
                        
                        st.download_button(
                            "📥 Last ned data (.csv)",
                            data=csv_string,
                            file_name=f"modenhet_data_{project['name']}_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8rem;">
        Modenhetsvurdering v3.0 | Bane NOR - Konsern Controlling<br>
        💾 Alt lagres automatisk | 📊 23 spørsmål per fase | 🎤 Multi-intervju støtte
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
