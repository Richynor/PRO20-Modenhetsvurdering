import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime
import json
import base64
from io import BytesIO
from fpdf import FPDF
import tempfile
import os

# Konfigurer siden
st.set_page_config(
    page_title="PRO20: Gevinstrealisering - Modenhetsvurdering",
    page_icon=" ",
    layout="wide"
)

# Laste Bane NOR logo
try:
    st.sidebar.image("bane_nor_logo.png.jpg", use_container_width=True)
except FileNotFoundError:
    st.sidebar.markdown("""
    <div style='text-align: center; color: #172141;'>
        <h1> </h1>
        <h3>Bane NOR</h3>
    </div>
    """, unsafe_allow_html=True)

# Komplett spørresett fra dokumentet - Oppdatert med alle spørsmål
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
                "Nivå 1: Ingen vurdering van balanse.",
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
            "question": "Hvordan håndteres avgrensning av programgevinster under gjennomføring nye forhold oppstår?",
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
                "Nivå 2: Noen måleregistreres, men ikke analysert.",
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
                "Nivå 3: Regelmessig vurdering van balansen.",
                "Nivå 4: Systematisk overvåkning van balansen.",
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
            "title": "Periodisierung og forankring",
            "question": "Hvordan justeres periodisering og forankring under gjennomføring?",
            "scale": [
                "Nivå 1: Periodisering justeres ikke under gjennomføring.",
                "Nivå 2: Store justeringer i periodisering.",
                "Nivå 3: Regelmessig revisjon van periodisering.",
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
                "Nivå 4: Proaktiv håndtering van avgrensning.",
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
                "Nivå 2: Noen måleregistreres.",
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

def initialize_session_state():
    """Initialiser session state for å lagre svar"""
    if 'responses' not in st.session_state:
        st.session_state.responses = {}
        for phase in phases_data:
            st.session_state.responses[phase] = {}
            for question in phases_data[phase]:
                st.session_state.responses[phase][question['id']] = {
                    'score': 0,
                    'notes': '',
                    'completed': False
                }

def calculate_stats():
    """Beregn statistikk for alle faser"""
    stats = {}
    for phase in phases_data:
        scores = []
        completed_count = 0
        for question in phases_data[phase]:
            response = st.session_state.responses[phase][question['id']]
            if response['completed'] and response['score'] > 0:
                scores.append(response['score'])
                completed_count += 1
        
        if scores:
            stats[phase] = {
                'average': np.mean(scores),
                'min': min(scores),
                'max': max(scores),
                'count': completed_count,
                'total': len(phases_data[phase])
            }
        else:
            stats[phase] = {
                'average': 0,
                'min': 0,
                'max': 0,
                'count': 0,
                'total': len(phases_data[phase])
            }
    return stats

def generate_radar_chart(stats):
    """Generer radardiagram for modenhet"""
    phases = list(stats.keys())
    averages = [stats[phase]['average'] for phase in phases]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=averages + [averages[0]],  # Lukk radaren
        theta=phases + [phases[0]],
        fill='toself',
        name='Modenhet',
        line=dict(color='#0053A6', width=3),
        fillcolor='rgba(0, 83, 166, 0.2)'
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
            bgcolor='#F2FAFD'
        ),
        showlegend=False,
        title="Modenhet per Fase - Radardiagram",
        title_font=dict(size=14, color='#172141'),
        height=400,
        paper_bgcolor='#F2FAFD',
        plot_bgcolor='#F2FAFD'
    )
    
    return fig

def generate_phase_radar_chart(phase_name, questions, responses):
    """Generer detaljert radardiagram for en spesifikk fase"""
    categories = []
    scores = []
    
    for question in questions:
        response = responses[question['id']]
        if response['completed'] and response['score'] > 0:
            categories.append(f"{question['id']}. {question['title']}")
            scores.append(response['score'])
    
    if not scores:
        return None
    
    # Lukk radaren
    categories.append(categories[0])
    scores.append(scores[0])
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill='toself',
        name='Score',
        line=dict(color='#64C8FA', width=2),
        fillcolor='rgba(100, 200, 250, 0.3)'
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
            bgcolor='#F2FAFD'
        ),
        showlegend=False,
        title=f"Detaljert Modenhet - {phase_name}",
        title_font=dict(size=14, color='#172141'),
        height=500,
        margin=dict(l=100, r=100, t=80, b=80),
        paper_bgcolor='#F2FAFD',
        plot_bgcolor='#F2FAFD'
    )
    
    return fig

def generate_report():
    """Detaljert rapport"""
    report = []
    report.append("MODENHETSVURDERING - GEVINSTREALISERING")
    report.append("=" * 50)
    report.append(f"Rapport generert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    stats = calculate_stats()
    
    # Sammendrag
    report.append("SAMMENDRAG")
    report.append("-" * 20)
    for phase, stat in stats.items():
        report.append(f"{phase}: {stat['count']}/{stat['total']} fullført - Gjennomsnitt: {stat['average']:.2f}")
    report.append("")
    
    # Detaljert resultat per fase
    for phase in phases_data:
        report.append(f"FASE: {phase.upper()}")
        report.append("-" * 30)
        
        for question in phases_data[phase]:
            response = st.session_state.responses[phase][question['id']]
            status = "[OK]" if response['completed'] else "[X]"
            score = response['score'] if response['score'] > 0 else "Ikke vurdert"
            
            report.append(f"{status} {question['id']}. {question['title']}")
            report.append(f"   Score: {score}")
            if response['notes']:
                report.append(f"   Notater: {response['notes']}")
            report.append("")
    
    # Vesentlige forbedringsområder
    report.append("FORBEDRINGSOMRÅDER (Score < 3)")
    report.append("-" * 30)
    improvement_areas = []
    for phase in phases_data:
        for question in phases_data[phase]:
            response = st.session_state.responses[phase][question['id']]
            if response['completed'] and 0 < response['score'] < 3:
                improvement_areas.append((phase, question, response['score']))
    
    if improvement_areas:
        for phase, question, score in improvement_areas:
            report.append(f"- {phase} - {question['title']} (Score: {score})")
    else:
        report.append("Ingen vesentlige forbedringsområder identifisert. Påpekte forbedringsområder i rapporten bør jobbes med.")
    
    return "\n".join(report)

def clean_text(text):
    """Hjelpefunksjon for å rense tekst for spesialtegn"""
    if text is None:
        return ""
    # Erstatt spesialtegn med vanlig tekst
    replacements = {
        '✓': '[OK]',
        '✗': '[X]',
        '–': '-',
        '—': '-',
        '´': "'",
        '`': "'",
        '•': '-',  # Bullet point til bindestrek
        '\u2022': '-',  # Unicode bullet point til bindestrek
        '´': "'",
        '`': "'"
    }
    cleaned = str(text)
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    return cleaned

def create_pdf_report():
    """Generer PDF rapport"""
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 12)
            self.set_text_color(23, 33, 65)  # #172141
            self.cell(0, 10, 'Modenhetsvurdering - Gevinstrealisering', 0, 1, 'C')
            self.ln(5)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(23, 33, 65)  # #172141
            self.cell(0, 10, f'Side {self.page_no()}', 0, 0, 'C')
    
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Titel
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(23, 33, 65)  # #172141
    pdf.cell(0, 10, 'MODENHETSVURDERING - GEVINSTREALISERING', 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 83, 166)  # #0053A6
    pdf.cell(0, 10, clean_text(f'Rapport generert: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'), 0, 1)
    pdf.ln(10)
    
    # Sammendrag
    stats = calculate_stats()
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(23, 33, 65)  # #172141
    pdf.cell(0, 10, 'SAMMENDRAG', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 0, 0)
    
    for phase, stat in stats.items():
        if stat['count'] > 0:
            pdf.cell(0, 8, clean_text(f'{phase}: {stat["count"]}/{stat["total"]} fullført - Gjennomsnitt: {stat["average"]:.2f}'), 0, 1)
    
    pdf.ln(10)
    
    # Detaljert resultat
    for phase in phases_data:
        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(23, 33, 65)  # #172141
        pdf.cell(0, 10, clean_text(f'FASE: {phase.upper()}'), 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(0, 0, 0)
        
        for question in phases_data[phase]:
            response = st.session_state.responses[phase][question['id']]
            if response['completed'] and response['score'] > 0:
                # Bruk clean_text for alle tekster
                status = "[OK]" if response['completed'] else "[X]"
                pdf.multi_cell(0, 8, clean_text(f'{status} {question["id"]}. {question["title"]} - Score: {response["score"]}'))
                if response['notes']:
                    pdf.set_font('Arial', 'I', 8)
                    pdf.set_text_color(100, 200, 250)  # #64C8FA
                    pdf.multi_cell(0, 6, clean_text(f'Notater: {response["notes"]}'))
                    pdf.set_font('Arial', '', 10)
                    pdf.set_text_color(0, 0, 0)
                pdf.ln(2)
        
        pdf.ln(5)
    
    # Vesentlige forbedringsområder
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(23, 33, 65)  # #172141
    pdf.cell(0, 10, 'VESENTLIGE FORBEDRINGSOMRÅDER (Score < 3)', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 0, 0)
    
    improvement_found = False
    for phase in phases_data:
        for question in phases_data[phase]:
            response = st.session_state.responses[phase][question['id']]
            if response['completed'] and 0 < response['score'] < 3:
                pdf.multi_cell(0, 8, clean_text(f'- {phase} - {question["title"]} (Score: {response["score"]})'))
                improvement_found = True
    
    if not improvement_found:
        pdf.cell(0, 8, 'Ingen forbedringsområder identifisert', 0, 1)
    
    return pdf

def get_pdf_download_link(pdf):
    """Generer download link for PDF"""
    try:
        pdf_output = pdf.output(dest='S').encode('latin-1', 'replace')
    except Exception as e:
        # Fallback til UTF-8 hvis latin-1 feiler
        try:
            pdf_output = pdf.output(dest='S').encode('utf-8', 'replace')
        except:
            st.error(f"Kunne ikke generere PDF: {e}")
            return None
    b64 = base64.b64encode(pdf_output).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="modenhetsvurdering_rapport.pdf">Last ned PDF Rapport</a>'
    return href

def main():
    # FARGEKONFIGURASJON MED  MODENHETSKODING
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #172141;
            text-align: center;
            margin-bottom: 1rem;
            font-weight: bold;
        }
        .phase-header {
            color: #0053A6;
            border-bottom: 3px solid #64C8FA;
            padding-bottom: 0.5rem;
            margin-top: 1rem;
            font-weight: 600;
        }
        .stProgress > div > div > div > div {
            background-color: #35DE6D;
        }
        .stButton > button {
            background-color: #0053A6;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            background-color: #172141;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 83, 166, 0.3);
        }
        .success-box {
            background-color: #DDFAE2;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #35DE6D;
            margin: 1rem 0;
        }
        .info-box {
            background-color: #C4EFFF;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #64C8FA;
            margin: 1rem 0;
        }
        .warning-box {
            background-color: rgba(255, 160, 64, 0.1);
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #FFA040;
            margin: 1rem 0;
        }
        .critical-box {
            background-color: rgba(255, 107, 107, 0.1);
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #FF6B6B;
            margin: 1rem 0;
        }
        .sidebar .sidebar-content {
            background-color: #F2FAFD;
        }
        .stExpander {
            border: 1px solid #64C8FA;
            border-radius: 8px;
            margin: 0.5rem 0;
        }
        .stExpander > div {
            background-color: #F2FAFD;
        }
        h1, h2, h3 {
            color: #172141;
        }
        .score-critical {
            color: #FF6B6B;
            font-weight: bold;
        }
        .score-medium {
            color: #FFA040;
            font-weight: bold;
        }
        .score-good {
            color: #64C8FA;
            font-weight: bold;
        }
        .score-high {
            color: #35DE6D;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">PRO20 Modenhetsvurdering - Gevinstrealisering</h1>', unsafe_allow_html=True)
    st.markdown("**Interaktiv vurdering av modenhet i gevinstrealisering gjennom fire faser**")
    st.markdown("---")
    
    # Initialiser session state
    initialize_session_state()
    
    # Sidebar for navigasjon og oversikt
    with st.sidebar:
        st.markdown('<h2 style="color: #172141;">Oversikt</h2>', unsafe_allow_html=True)
        
        selected_phase = st.selectbox(
            "Velg fase:",
            options=list(phases_data.keys()),
            key="phase_selector"
        )
        
        # Fremdriftsvisning
        stats = calculate_stats()
        if selected_phase in stats:
            phase_stats = stats[selected_phase]
            progress = phase_stats['count'] / phase_stats['total'] if phase_stats['total'] > 0 else 0
            
            st.subheader("Fremdrift")
            st.progress(progress)
            st.write(f"**{phase_stats['count']}/{phase_stats['total']}** spørsmål fullført")
            
            if phase_stats['count'] > 0:
                avg_score = phase_stats['average']
                if avg_score >= 4:
                    score_class = "score-good"
                elif avg_score >= 3:
                    score_class = "score-medium"
                else:
                    score_class = "score-critical"
                st.write(f"Gjennomsnittsscore: **<span class='{score_class}'>{avg_score:.2f}</span>**", unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("Hurtigstatistikk")
        for phase, stat in stats.items():
            if stat['count'] > 0:
                if stat['average'] >= 4:
                    score_class = "score-good"
                elif stat['average'] >= 3:
                    score_class = "score-medium"
                else:
                    score_class = "score-critical"
                st.write(f"**{phase}:** <span class='{score_class}'>{stat['average']:.2f}</span>", unsafe_allow_html=True)
    
    # Hovedinnhold - spørsmålsvisning
    st.markdown(f'<h2 class="phase-header">{selected_phase.upper()}</h2>', unsafe_allow_html=True)
    
    # Vis fasebeskrivelse
    phase_descriptions = {
        "Planlegging": "Fase for strategisk planlegging og forberedelse av gevinstrealisering",
        "Gjennomføring": "Implementeringsfase med kontinuerlig justering og oppfølging", 
        "Realisering": "Fase for faktisk gevinstuttak og verdiskapning",
        "Realisert": "Evaluering og læring fra fullførte gevinstrealiseringer"
    }
    
    st.markdown(f'<div class="info-box">{phase_descriptions.get(selected_phase, "")}</div>', unsafe_allow_html=True)
    
    # Alle spørsmål i expandere
    for question in phases_data[selected_phase]:
        response = st.session_state.responses[selected_phase][question['id']]
        
        expander_label = f"{question['id']}. {question['title']} - "
        if response['completed']:
            score = response['score']
            if score == 5:
                score_class = "score-high"
                score_text = "Høy modenhet"
            elif score == 4:
                score_class = "score-good"
                score_text = "God modenhet"
            elif score == 3:
                score_class = "score-medium"
                score_text = "Moderat modenhet"
            elif score == 2:
                score_class = "score-critical"
                score_text = "Begrenset modenhet"
            else:  # score == 1
                score_class = "score-critical"
                score_text = "Lav modenhet"
            expander_label += f"<span class='{score_class}'>{score} ({score_text})</span>"
        else:
            expander_label += "Ikke vurdert"
        
        with st.expander(expander_label, expanded=False):
            # Bruk "Spørsmål:" i stedet for å gjenta nummeret
            st.write(f"**Spørsmål:** {question['question']}")
            
            # Modenhetsskala - viser kun nivåene i standard sort farge
            st.subheader("Modenhetsskala:")
            for level in question['scale']:
                st.write(level)
            
            # Score input med forklaring i radioknappene
            current_score = response['score']
            st.subheader("Vurdering:")
            new_score = st.radio(
                "Modenhetsnivå:",
                options=[1, 2, 3, 4, 5],
                index=current_score-1 if current_score > 0 else 0,
                key=f"score_{selected_phase}_{question['id']}",
                horizontal=True,
                format_func=lambda x: {
                    1: "Nivå 1 - Lav modenhet",
                    2: "Nivå 2 - Begrenset modenhet", 
                    3: "Nivå 3 - Moderat modenhet",
                    4: "Nivå 4 - God modenhet",
                    5: "Nivå 5 - Høy modenhet"
                }[x]
            )
            
            # Notater
            current_notes = response['notes']
            new_notes = st.text_area(
                "Notater og kommentarer:",
                value=current_notes,
                key=f"notes_{selected_phase}_{question['id']}",
                placeholder="Observasjoner, begrunnelse for score, eller forbedringsforslag her...",
                height=100
            )
            
            # Lagre knapp
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Lagre svar", key=f"save_{selected_phase}_{question['id']}", use_container_width=True):
                    st.session_state.responses[selected_phase][question['id']] = {
                        'score': new_score,
                        'notes': new_notes,
                        'completed': True
                    }
                    st.success("Svar lagret!")
                    st.rerun()
    
    # Resultatseksjon
    st.markdown("---")
    st.markdown('<h2 style="color: #172141;">Resultatoversikt</h2>', unsafe_allow_html=True)
    
    if st.button("Generer Full Rapport", type="primary", use_container_width=True):
        stats = calculate_stats()
        
        # Visuelle visualiseringer
        col1, col2 = st.columns(2)
        
        with col1:
            # Søylediagram
            if any(stats[phase]['count'] > 0 for phase in stats):
                phases_with_data = [phase for phase in stats if stats[phase]['count'] > 0]
                averages = [stats[phase]['average'] for phase in phases_with_data]
                
                fig_bar = px.bar(
                    x=phases_with_data,
                    y=averages,
                    title="Gjennomsnittsscore per Fase",
                    labels={'x': 'Fase', 'y': 'Gjennomsnittsscore'},
                    color=averages,
                    color_continuous_scale=['#FF6B6B', '#FFA040', '#64C8FA', '#35DE6D']
                )
                fig_bar.update_layout(
                    yaxis_range=[0, 5.5],
                    plot_bgcolor='#F2FAFD',
                    paper_bgcolor='#F2FAFD'
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            # Radardiagram (kun hvis minst 3 faser har data)
            phases_with_data = [phase for phase in stats if stats[phase]['count'] > 0]
            if len(phases_with_data) >= 3:
                radar_fig = generate_radar_chart(stats)
                st.plotly_chart(radar_fig, use_container_width=True)
            else:
                st.info("Trenger data fra minst 3 faser for radardiagram")
        
        # Detaljerte radardiagrammer per fase
        st.subheader("Detaljert Modenhet per Fase")
        for phase in phases_data:
            phase_questions = phases_data[phase]
            phase_responses = st.session_state.responses[phase]
            
            # Sjekk om det er noen fullførte spørsmål i fasen
            if any(phase_responses[q['id']]['completed'] for q in phase_questions):
                st.write(f"**{phase}**")
                radar_fig = generate_phase_radar_chart(phase, phase_questions, phase_responses)
                if radar_fig:
                    st.plotly_chart(radar_fig, use_container_width=True)
                else:
                    st.info(f"Ingen data tilgjengelig for detaljert analyse av {phase}")
        
        # Detaljert rapport
        st.subheader("Detaljert Rapport")
        
        # Last ned knapper for forskjellige formater
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # TXT rapport
            report_text = generate_report()
            st.download_button(
                label="Last ned rapport som TXT",
                data=report_text,
                file_name=f"modenhetsvurdering_rapport_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col2:
            # PDF rapport
            try:
                pdf = create_pdf_report()
                if pdf:
                    pdf_output = pdf.output(dest='S').encode('latin-1', 'replace')
                    st.download_button(
                        label="Last ned rapport som PDF",
                        data=pdf_output,
                        file_name=f"modenhetsvurdering_rapport_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"Kunne ikke generere PDF: {e}")
        
        with col3:
            # CSV data
            csv_data = []
            csv_data.append(["Fase", "Spørsmål ID", "Tittel", "Score", "Notater", "Fullført"])
            for phase in phases_data:
                for question in phases_data[phase]:
                    response = st.session_state.responses[phase][question['id']]
                    csv_data.append([
                        phase,
                        question['id'],
                        question['title'],
                        response['score'] if response['completed'] else "Ikke vurdert",
                        response['notes'],
                        "Ja" if response['completed'] else "Nei"
                    ])
            
            df = pd.DataFrame(csv_data[1:], columns=csv_data[0])
            csv_string = df.to_csv(index=False, sep=';')
            st.download_button(
                label="Last ned data som CSV",
                data=csv_string,
                file_name=f"modenhetsvurdering_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # Forbedringsområder
        st.subheader("Forbedringsområder")
        improvement_found = False
        
        for phase in phases_data:
            low_scores = []
            for question in phases_data[phase]:
                response = st.session_state.responses[phase][question['id']]
                if response['completed'] and 0 < response['score'] < 3:
                    low_scores.append((question, response['score']))
                    improvement_found = True
            
            if low_scores:
                st.write(f"**{phase}:**")
                for question, score in low_scores:
                    score_class = "score-critical"
                    st.write(f"- <span class='{score_class}'>{question['title']} (Score: {score} - Lav/Begrenset modenhet)</span>", unsafe_allow_html=True)
        
        if not improvement_found:
            st.markdown('<div class="success-box">Ingen vesentlige forbedringsområder identifisert! Organisasjonen jobber aktivt med gevinstrealisering.</div>', unsafe_allow_html=True)
        
        # Anbefalinger basert på resultater
        st.subheader("Anbefalinger")
        
        total_questions = sum(len(phases_data[phase]) for phase in phases_data)
        completed_questions = sum(stats[phase]['count'] for phase in stats)
        
        if completed_questions == 0:
            st.info("Start med å svare på spørsmålene i fasene ovenfor for å få tilpassede anbefalinger")
        elif completed_questions < total_questions * 0.5:
            st.warning("Fortsett å fylle ut vurderingen for mer presise anbefalinger")
        else:
            overall_avg = np.mean([stats[phase]['average'] for phase in stats if stats[phase]['count'] > 0])
            if overall_avg == 5:
                st.success("Utmerket modenhet! Høy modenhet på alle områder.")
            elif overall_avg >= 4:
                st.success("God modenhet! Fokus på å opprettholde og dokumentere beste praksis.")
            elif overall_avg >= 3:
                st.info("Moderat modenhet! Arbeid med å styrke svakere områder for å oppnå høyere modenhet.")
            else:
                st.markdown('<div class="critical-box">Lav/Begrenset modenhet. Fokuser på de identifiserte forbedringsområdene.</div>', unsafe_allow_html=True)
    
    # Informasjon om appen
    with st.expander("Om denne appen"):
        st.markdown("""
        <div class="info-box">
        **Funksjonalitet:**
        - Vurder modenhet i gevinstrealisering gjennom 4 faser
        - Auto-lagring av alle svar
        - Generer visuelle rapporter og diagrammer
        - Identifiser forbedringsområder
        - Eksporter rapporter i TXT, PDF og CSV format
        
        **Bruk:**
        1. Velg fase i sidebar
        2. Gå gjennom hvert spørsmål
        3. Velg score og skriv notater
        4. Trykk "Lagre svar" for hvert spørsmål
        5. Trykk "Generer Full Rapport" for resultater
        
        **OBS! Data lagres lokalt i nettleseren og forsvinner ved oppdatering.**
        
        **Modenhetskoding:**
        - <span style='color: #FF6B6B'>Rød (1-2)</span>: Lav/Begrenset modenhet
        - <span style='color: #FFA040'>Oransje (3)</span>: Moderat modenhet
        - <span style='color: #64C8FA'>Blå (4)</span>: God modenhet
        - <span style='color: #35DE6D'>Grønn (5)</span>: Høy modenhet
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
