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
    <div style='text-align: center; color: #BA0C2F;'>
        <h1> </h1>
        <h3>Bane NOR</h3>
    </div>
    """, unsafe_allow_html=True)

# Komplett spørresett fra dokumentet
phases_data = {
    "Planlegging": [
        {
            "id": 1,
            "title": "Bruk av tidligere læring og gevinstdata",
            "question": "Hvordan anvendes erfaringer og læring fra tidligere prosjekter og gevinstarbeid i planleggingen av nye gevinster fra leveransen(er)?",
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
                "Nivå 3: Gevinster er dokumentert og delvis knyttet til strategiske mål, men grunnlaget har usikkerhet.",
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
                "Nivå 2: Delvis omtalt, men uklart hva som er innenfor programmet.",
                "Nivå 3: Avgrensning er gjort i plan, men ikke dokumentert grundig.",
                "Nivå 4: Avgrensning er dokumentert og anvendt i beregninger.",
                "Nivå 5: Effektisolering er standard praksis og brukes systematisk."
            ]
        },
        {
            "id": 6,
            "title": "Nullpunkter og estimater",
            "question": "Er nullpunkter og estimater etablert, testet og dokumentert på en konsistent og troverdig måte med hensyn til variasjoner mellom strekninger?",
            "scale": [
                "Nivå 1: Nullpunkter mangler eller bygger på uprøvde antagelser, uten hensyn til strekningens spesifikke forhold.",
                "Nivå 2: Enkelte nullpunkter finnes, men uten felles metode og uten vurdering av variasjoner mellom strekninger.",
                "Nivå 3: Nullpunkter og estimater er definert, men med høy usikkerhet knyttet til lokale forhold.",
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
            "id": 10,
            "title": "Operasjonell risiko og ulemper",
            "question": "Er mulige negative konsekvenser eller ulemper knyttet til operasjonelle forhold identifisert, vurdert og håndtert i planen?",
            "scale": [
                "Nivå 1: Negative effekter ikke vurdert.",
                "Nivå 2: Kjent, men ikke håndtert.",
                "Nivå 3: Beskrevet, men ikke fulgt opp systematisk.",
                "Nivå 4: Håndtert og overvåket med tilpasning til ulike operasjonelle scenarier.",
                "Nivå 5: Systematisk vurdert og del av gevinstdialogen med kontinuerlig justering."
            ]
        },
        {
            "id": 11,
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
            "id": 12,
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
            "id": 13,
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
            "id": 14,
            "title": "Operativ gevinstrealiseringsplan",
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
            "id": 15,
            "title": "Periodisering og forankring",
            "question": "Er gevinstrealiseringsplanen periodisert, validet og godkjent av ansvarlige eiere?",
            "scale": [
                "Nivå 1: Ingen tidsplan eller forankring.",
                "Nivå 2: Tidsplan foreligger, men ikke validet.",
                "Nivå 3: Delvis forankret hos enkelte eiere.",
                "Nivå 4: Fullt forankret og koordinert med budsjett- og styringsprosesser.",
                "Nivå 5: Planen brukes aktivt i styringsdialog og rapportering."
            ]
        },
         {
            "id": 16,
            "title": "Disponering av kostnads- og tidsbesparelser",
            "question": "Hvordan er kostnads- og tidsbesparelser planlagt disponert, og hvordan måles effektene av bruken av disse ressursene?",
            "scale": [
                "Nivå 1: Ingen plan for disponering eller måling av besparelser.",
                "Nivå 2: Delvis oversikt, men ikke dokumentert eller fulgt opp.",
                "Nivå 3: Plan finnes for enkelte områder, men uten systematikk.",
                "Nivå 4: Disponering og effekter dokumentert og målt.",
                "Nivå 5: Frigjorte ressurser disponeres strategisk og måles som del av gevinstrealiseringen."
            ]
        },
        {
            "id": 17,
            "title": "Eierskap og ansvar",
            "question": "Er ansvar og roller tydelig definert for å sikre gjennomføring og gevinstuttak?",
            "scale": [
                "Nivå 1: Ansvar er uklart eller mangler.",
                "Nivå 2: Ansvar er delvis definert, men ikke praktisert.",
                "Nivå 3: Ansvar er kjent, men samhandling varierer.",
                "Nivå 4: Roller og ansvar fungerer godt i praksis.",
                "Nivå 5: Sterkt eierskap og kultur for ansvarliggjøring."
            ]
        },
        {
            "id": 18,
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
            "id": 19,
            "title": "Prinsipielle og vilkårsmessige kriterier",
            "question": "Er forutsetninger og kriterier som påvirker gevinstene tydelig definert og dokumentert i planen?",
            "scale": [
                "Nivå 1: Ingen kriterier dokumentert.",
                "Nivå 2: Forutsetninger beskrevet uformelt.",
                "Nivå 3: Forutsetninger dokumentert i deler av planverket.",
                "Nivå 4: Kritiske forutsetninger analysert og håndtert i planen.",
                "Nivå 5: Forutsetninger overvåkes og inngår i risikostyringen."
            ]
        },
        {
            "id": 20,
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
            "id": 21,
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
            "title": "Oppfølging av måltall og operativ justering",
            "question": "Hvor systematisk følges måltallene opp, og justeres estimatene njen forutsetningene endres - inkludert endringer i operative forhold som strekninger og togfremføring?",
            "scale": [
                "Nivå 1: Ingen oppfølging eller justering.",
                "Nivå 2: Oppfølging skjer sporadisk uten tilpasning til operative forhold.",
                "Nivå 3: Måltall følges opp, men uten system for justering basert på strekningsvariasjoner.",
                "Nivå 4: Systematisk oppfølging og jevnlig revisjon av estimater med hensyn til operative endringer.",
                "Nivå 5: Oppfølging og justering integrert i styringsdialoger med kontinuerlig tilpasning til lokale forhold."
            ]
        },
        {
            "id": 2,
            "title": "Oppfølging av kostnads- og tidsbesparelser",
            "question": "Hvordan måles og følges faktisk realiserte kostnads- og tidsbesparelser opp?",
            "scale": [
                "Nivå 1: Ikke målt.",
                "Nivå 2: Delvis målt, men uten system.",
                "Nivå 3: Målt for enkelte gevinster.",
                "Nivå 4: Systematisk måling og rapportering etablert.",
                "Nivå 5: Resultatene brukes aktivt til læring og kontinuerlig forbedring."
            ]
        },
        {
            "id": 3,
            "title": "Bruk av frigjorte ressurser",
            "question": "Hvordan brukes og måles frigjorte tids- og kostnadsressurser i linjen?",
            "scale": [
                "Nivå 1: Ikke vurdert eller dokumentert.",
                "Nivå 2: Delvis omtalt, men ikke målt.",
                "Nivå 3: Bruk dokumentert for enkelte tiltak.",
                "Nivå 4: Målt og rapportert systematisk.",
                "Nivå 5: Bruken av frigjorte ressurser integrert i gevinstrealisering og verdiskapingsmåling."
            ]
        },
        {
            "id": 4,
            "title": "Tydelighet i gevinstuttak",
            "question": "Er det tydelig definert hvordan gevinstene skal hentes ut, og oppleves det som realistisk?",
            "scale": [
                "Nivå 1: Uklart hva som skal hentes ut.",
                "Nivå 2: Gevinstuttak definert, men lite realistisk.",
                "Nivå 3: Plan finnes, men mangler forankring i praksis.",
                "Nivå 4: Klart og realistisk gevinstuttak planlagt.",
                "Nivå 5: Gevinstuttak fullt integrert i operativ virksomhet."
            ]
        },
        {
            "id": 5,
            "title": "Håndtering av prissatte gevinster",
            "question": "Dersom prissatte gevinster beholdes i linjen, er det tydeliggjort hvordan de disponeres?",
            "scale": [
                "Nivå 1: Ingen oversikt over disponering.",
                "Nivå 2: Delvis definert, men ikke målt.",
                "Nivå 3: Klare føringer, men svak oppfølging.",
                "Nivå 4: Disponering dokumentert og fulgt opp.",
                "Nivå 5: Systematisk praksis med måling av bieffekter."
            ]
        },
        {
            "id": 6,
            "title": "Operasjonell ulempehåndtering",
            "question": "Hvordan følges ulemper, ressursbelastning og negative bieffekter knyttet til operasjonelle forhold opp?",
            "scale": [
                "Nivå 1: Ingen oppfølging av ulemper.",
                "Nivå 2: Delvis registrert, men ikke håndtert.",
                "Nivå 3: Ulemper rapporteres, men ikke koblet til gevinstarbeid.",
                "Nivå 4: Oppfølging systematisk og integrert i gevinststyring med tilpasning til operative forhold.",
                "Nivå 5: Balansert oppfølging av gevinster og ulemper inngår i lærings- og forbedringsarbeid med kontinuerlig justering."
            ]
        },
        {
            "id": 7,
            "title": "Balanse mellom gevinster og ulemper",
            "question": "Hvordan vurderes balansen mellom gevinster og ulemper under gjennomføringen?",
            "scale": [
                "Nivå 1: Ingen vurdering av balanse under gjennomføring.",
                "Nivå 2: Balansen vurderes uformelt ved behov.",
                "Nivå 3: Balansen vurderes i noen styringsmøter.",
                "Nivå 4: Systematisk vurdering av balansen og justering av tiltak.",
                "Nivå 5: Kontinuerlig vurdering van balansen er en integrert del av styringen."
            ]
        },
        {
            "id": 8,
            "title": "Tiltaksplan og korrigerende handling",
            "question": "Er det etablert tiltak eller prosesser for å redusere gapet mellom forventede og faktiske gevinster?",
            "scale": [
                "Nivå 1: Ingen tiltak iverksatt.",
                "Nivå 2: Tiltak vurderes ad hoc.",
                "Nivå 3: Tiltaksplan finnes, men ikke systematisk fulgt opp.",
                "Nivå 4: Tiltak implementert og overvåket.",
                "Nivå 5: Kontinuerlig forbedringssløyfe etablert for gevinstjustering."
            ]
        },
        {
            "id": 9,
            "title": "Motivasjon og realisme",
            "question": "Oppleves det fortsatt engasjement og tro på gevinstuttakene blant interessenter og ansvarlige?",
            "scale": [
                "Nivå 1: Lav motivasjon og tillit.",
                "Nivå 2: Begrenset engasjement.",
                "Nivå 3: Stabil motivasjon, men med enkelte tvilsspørsmål.",
                "Nivå 4: Sterkt engasjement og felles tro på gevinstene.",
                "Nivå 5: Høy motivasjon og tydelig kultur for gevinstrealisering."
            ]
        },
        {
            "id": 10,
            "title": "Tidlig gevinstuttak",
            "question": "Er det planlagt og gjennomført tiltak for tidlig gevinstuttak, og brukes erfaringene videre?",
            "scale": [
                "Nivå 1: Ingen tiltak for tidlig uttak.",
                "Nivå 2: Tidlige gevinster skjer tilfeldig.",
                "Nivå 3: Plan for tidlig uttak finnes, men svak oppfølging.",
                "Nivå 4: Tidlig uttak dokumentert og analysert.",
                "Nivå 5: Tidlig uttak brukes aktivt som læringsgrunnlag."
            ]
        },
        {
            "id": 11,
            "title": "Nye gevinstmuligheter",
            "question": "Er det etablert en prosess for å identifisere og realisere nye gevinstmuligheter underveis?",
            "scale": [
                "Nivå 1: Ingen prosess for å avdekke nye gevinster.",
                "Nivå 2: Nye gevinster oppdages tilfeldig.",
                "Nivå 3: Nye gevinster dokumenteres, men ikke strukturert.",
                "Nivå 4: Prosess finnes og følges for nye muligheter.",
                "Nivå 5: Nye gevinster systematisk identifisert og integrert."
            ]
        },
        {
            "id": 12,
            "title": "Leveransers relevans og validering",
            "question": "Er leveransene fortsatt relevante og validerbare gitt gjeldende forutsetninger?",
            "scale": [
                "Nivå 1: Leveranser ikke vurdert for relevans.",
                "Nivå 2: Enkelte leveranser vurdert, men uten metode.",
                "Nivå 3: Vurdering gjennomført, men usystematisk.",
                "Nivå 4: Leveranser valideres jevnlig.",
                "Nivå 5: Leveranser kontinuerlig vurdert opp mot gevinstforutsetninger."
            ]
        },
        {
            "id": 13,
            "title": "Interessentforståelse",
            "question": "Er det tilstrekkelig forståelse blant interessenter for hvordan leveransene skaper de ønskede gevinstene?",
            "scale": [
                "Nivå 1: Ingen felles forståelse.",
                "Nivå 2: Delvis forståelse blant enkelte interessenter.",
                "Nivå 3: Forståelse etablert, men variabel i praksis.",
                "Nivå 4: God og felles forståelse blant de fleste interessenter.",
                "Nivå 5: Full forståelse integrert i kultur og kommunikasjon."
            ]
        },
        {
            "id": 14,
            "title": "Kommunikasjon og holdninger",
            "question": "Hvordan jobbes det med kommunikasjon og håndtering av interessenters holdninger gjennom gevinstarbeidet?",
            "scale": [
                "Nivå 1: Ingen strukturert kommunikasjon.",
                "Nivå 2: Kommunikasjon skjer ved behov.",
                "Nivå 3: Kommunikasjonsplan finnes, men ikke aktivt brukt.",
                "Nivå 4: Kommunikasjon er systematisk og målrettet.",
                "Nivå 5: Kommunikasjon integrert i styring og endringsledelse."
            ]
        },
        {
            "id": 15,
            "title": "Kompetanse og kapasitet",
            "question": "Har involverte aktører tilstrekkelig kompetanse og kapasitet til å motta leveranser og realisere gevinstene?",
            "scale": [
                "Nivå 1: Manglende kompetanse og kapasitet.",
                "Nivå 2: Delvis tilstede, men ujevnt fordelt.",
                "Nivå 3: Tilstrekkelig for enkelte leveranser, men ikke helhetlig.",
                "Nivå 4: God dekning og støtte i organisasjonen.",
                "Nivå 5: Kapasitet og kompetanse strategisk planlagt og fulgt opp."
            ]
        },
        {
            "id": 16,
            "title": "Eierskap til gevinstrealisering",
            "question": "Er det tydelig hvem som har eierskap til gevinstoppfølging og realisering i gjennomføringsfasen?",
            "scale": [
                "Nivå 1: Uklart eierskap eller overlappende ansvar.",
                "Nivå 2: Delvis definert, men lite praktisert.",
                "Nivå 3: Eierskap synlig, men svak oppfølging.",
                "Nivå 4: Klart eierskap utøves aktivt i prosesser og rapportering.",
                "Nivå 5: Eierskap fullintegrert i styringsstruktur og kultur."
            ]
        },
        {
            "id": 17,
            "title": "Aktiv bruk av gevinstrealiseringsplanen",
            "question": "Brukes gevinstrealiseringsplanen aktivt som operativt styringsverktøy i linjen?",
            "scale": [
                "Nivå 1: Planen brukes ikke etter utarbeidelse.",
                "Nivå 2: Brukes sporadisk.",
                "Nivå 3: Brukes i enkelte prosjekter, ikke konsekvent.",
                "Nivå 4: Planen er integrert i linjestyringen.",
                "Nivå 5: Planen er sentralt styringsdokument i virksomheten."
            ]
        },
        {
            "id": 18,
            "title": "Integrasjon i styringsdialoger",
            "question": "Er gevinstdiskusjoner en integrert del av virksomhetens styringsdialoger og oppfølgingsmøter?",
            "scale": [
                "Nivå 1: Ikke del av styring.",
                "Nivå 2: Tema tas opp ad hoc.",
                "Nivå 3: Delvis fast tema i noen styringsfora.",
                "Nivå 4: Fast og strukturert del av styring.",
                "Nivå 5: Gevinstdialoger kontinuerlig integrert i lederoppfølging."
            ]
        },
        {
            "id": 19,
            "title": "Risikostyring og forutsetninger",
            "question": "Er risikostyring knyttet til de viktigste gevinstforutsetningene etablert og aktivt brukt?",
            "scale": [
                "Nivå 1: Ingen risikostyring.",
                "Nivå 2: Risikoer identifisert, men ikke håndtert.",
                "Nivå 3: Tiltak finnes, men følges svakt opp.",
                "Nivå 4: Risikostyring integrert i gevinstplanen.",
                "Nivå 5: Risikostyring aktiv del av gevinstrealisering og læring."
            ]
        },
        {
            "id": 20,
            "title": "Eksterne påvirkninger",
            "question": "Er eksterne faktorer og endringer som kan påvirke gevinstrealisering vurdert og håndtert?",
            "scale": [
                "Nivå 1: Ikke vurdert.",
                "Nivå 2: Identifisert, men ikke fulgt opp.",
                "Nivå 3: Delvis håndtert gjennom prosjekter.",
                "Nivå 4: Aktivt vurdert i plan og tiltak.",
                "Nivå 5: Løpende vurdert i styringsdialog og risikostyring."
            ]
        },
        {
            "id": 21,
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
            "title": "Faktisk gevinstuttak",
            "question": "Hentes gevinstene ut i tråd med gevinstrealiseringsplanen og innenfor planlagte tidsrammer?",
            "scale": [
                "Nivå 1: Gevinster realiseres ikke eller følges ikke opp.",
                "Nivå 2: Enkelte gevinster hentes ut, men uten strukturert oppfølging.",
                "Nivå 3: Planmessig gevinstuttak, men med avvik og svak rapportering.",
                "Nivå 4: De fleste gevinster realiseres i tråd med plan og følges opp.",
                "Nivå 5: Systematisk gevinstuttak med dokumentert læring og kontinuerlig forbedring."
            ]
        },
        {
            "id": 2,
            "title": "Oppfølging av kostnads- og tidsbesparelser",
            "question": "Hvordan måles og følges faktisk realiserte kostnads- og tidsbesparelser opp i realiseringsfasen?",
            "scale": [
                "Nivå 1: Ikke målt.",
                "Nivå 2: Delvis målt, men uten system.",
                "Nivå 3: Målt for enkelte gevinster.",
                "Nivå 4: Systematisk måling og rapportering etablert.",
                "Nivå 5: Resultatene brukes aktivt til læring og kontinuerlig forbedring."
            ]
        },
        {
            "id": 3,
            "title": "Bruk og effekt av frigjorte ressurser",
            "question": "Hvordan brukes og dokumenteres effekten av frigjorte ressurser under realiseringen?",
            "scale": [
                "Nivå 1: Ikke dokumentert.",
                "Nivå 2: Delvis beskrevet.",
                "Nivå 3: Dokumentert for enkelte tiltak.",
                "Nivå 4: Systematisk målt og rapportert.",
                "Nivå 5: Effekter målt og brukt i strategisk planlegging og prioritering."
            ]
        },
        {
            "id": 4,
            "title": "Avvik og justering",
            "question": "Når gevinster ikke realiseres som planlagt, analyseres årsakene og iverksettes korrigerende tiltak?",
            "scale": [
                "Nivå 1: Ingen analyse av avvik.",
                "Nivå 2: Avvik registreres, men ikke fulgt opp.",
                "Nivå 3: Avvik håndteres reaktivt.",
                "Nivå 4: Avvik analyseres og tiltak dokumenteres.",
                "Nivå 5: Systematisk læring og forbedring basert på avviksanalyse."
            ]
        },
        {
            "id": 5,
            "title": "Operasjonell ulempeoppfølging",
            "question": "Hvordan følges ulemper, ressursbelastning og negative bieffekter knyttet til operasjonelle forhold opp under realiseringen?",
            "scale": [
                "Nivå 1: Ingen oppfølging av ulemper.",
                "Nivå 2: Delvis registrert, men ikke håndtert.",
                "Nivå 3: Ulemper rapporteres, men ikke koblet til gevinstarbeid.",
                "Nivå 4: Oppfølging systematisk og integrert i gevinststyring med tilpasning til operative forhold.",
                "Nivå 5: Balansert oppfølging av gevinster og ulemper inngår i lærings- og forbedringsarbeid med kontinuerlig justering."
            ]
        },
        {
            "id": 6,
            "title": "Balanse mellom gevinster og ulemper",
            "question": "Hvordan vurderes balansen mellom gevinster og ulemper under realiseringen?",
            "scale": [
                "Nivå 1: Ingen vurdering av balanse under realisering.",
                "Nivå 2: Balansen vurderes uformelt ved behov.",
                "Nivå 3: Balansen vurderes i noen styringsmøter.",
                "Nivå 4: Systematisk vurdering av balansen og justering av tiltak.",
                "Nivå 5: Kontinuerlig vurdering av balansen er en integrert del av styringen."
            ]
        },
        {
            "id": 7,
            "title": "Strategisk effekt og måloppnåelse",
            "question": "I hvilken grad støtter realiserte gevinster organisasjonens strategiske mål?",
            "scale": [
                "Nivå 1: Ingen sammenheng med strategiske mål.",
                "Nivå 2: Enkelte gevinster støtter strategien indirekte.",
                "Nivå 3: De fleste gevinster koblet til strategi, men uten måling.",
                "Nivå 4: Klart dokumentert bidrag til strategiske mål.",
                "Nivå 5: Gevinstene brukes aktivt for å justere og forbedre strategien."
            ]
        },
        {
            "id": 8,
            "title": "Bruk og oppdatering av gevinstrealiseringsplan",
            "question": "Er gevinstrealiseringsplanen oppdatert og brukt som styringsverktøy under realiseringen?",
            "scale": [
                "Nivå 1: Planen brukt kun i planlegging.",
                "Nivå 2: Oppdatert sporadisk.",
                "Nivå 3: Følges delvis, men uten systematisk revisjon.",
                "Nivå 4: Aktivt brukt og oppdatert ved endringer.",
                "Nivå 5: Integrert styringsdokument for løpende gevinstrealisering."
            ]
        },
        {
            "id": 9,
            "title": "Systematisk gevinstarbeid",
            "question": "Foregår det et strukturert og koordinert arbeid med å følge opp, dokumentere og realisere gevinster?",
            "scale": [
                "Nivå 1: Ingen systematikk.",
                "Nivå 2: Enkelte initiativ, men uten koordinering.",
                "Nivå 3: System finnes, men brukes ujevnt.",
                "Nivå 4: Koordinert gevinstarbeid mellom linje og program.",
                "Nivå 5: Helhetlig gevinststyring etablert som del av virksomhetsstyringen."
            ]
        },
        {
            "id": 10,
            "title": "Eierskap og ansvar i realisering",
            "question": "Utøves eierskap og ansvar tydelig under gevinstrealiseringen?",
            "scale": [
                "Nivå 1: Uklart eierskap i realiseringsfasen.",
                "Nivå 2: Delvis eierskap, men uten praksis.",
                "Nivå 3: Tydelig ansvar, men svak oppfølging.",
                "Nivå 4: Eierskap utøves aktivt i gevinststyring.",
                "Nivå 5: Eierskap og ansvar fullt integrert i linjeledelse."
            ]
        },
        {
            "id": 11,
            "title": "Engasjement og motivasjon",
            "question": "Opprettholdes motivasjon og engasjement blant interessenter og eiere for å hente ut gevinster?",
            "scale": [
                "Nivå 1: Lavt engasjement og redusert fokus.",
                "Nivå 2: Engasjement finnes hos få aktører.",
                "Nivå 3: Stabil motivasjon, men ikke felles eierskap.",
                "Nivå 4: Høyt engasjement og kontinuerlig kommunikasjon.",
                "Nivå 5: Sterk og vedvarende gevinstkultur i organisasjonen."
            ]
        },
        {
            "id": 12,
            "title": "Endringsledelse og kultur",
            "question": "Hvordan håndteres endringsledelse for å støtte realisering av gevinster og varig atferdsendring?",
            "scale": [
                "Nivå 1: Ingen plan for endringsledelse.",
                "Nivå 2: Ad hoc-tilnærming, lite koordinert.",
                "Nivå 3: Plan for endring finnes, men ikke målt effekt.",
                "Nivå 4: Endringsledelse implementert i praksis.",
                "Nivå 5: Endringsledelse er integrert del av styring og kulturbygging."
            ]
        },
        {
            "id": 13,
            "title": "Kapasitet og mottaksevne",
            "question": "Har organisasjonen tilstrekkelig kapasitet, kompetanse og støtte for å realisere gevinstene i praksis?",
            "scale": [
                "Nivå 1: Mangel på ressurser og kapasitet.",
                "Nivå 2: Delvis kapasitet, men ustabil.",
                "Nivå 3: Kapasitet tilstede, men varierende evne til implementering.",
                "Nivå 4: Tilstrekkelig ressurser og støtteapparat.",
                "Nivå 5: Robust kapasitet med kontinuerlig kompetanseutvikling."
            ]
        },
        {
            "id": 14,
            "title": "Realisme og troverdighet",
            "question": "Vurderes estimater og gevinstforventninger som realistiske i lys av erfaringer underveis?",
            "scale": [
                "Nivå 1: Estimater urealistiske og ikke justert.",
                "Nivå 2: Delvis justert, men ikke dokumentert.",
                "Nivå 3: Justert ved behov, men uten struktur.",
                "Nivå 4: Systematisk vurdering og dokumentasjon av realisme.",
                "Nivå 5: Kontinuerlig vurdering og læring brukt til justering."
            ]
        },
        {
            "id": 15,
            "title": "Risikostyring",
            "question": "Er risikostyring aktivt brukt til å håndtere usikkerhet knyttet til gevinstrealisering?",
            "scale": [
                "Nivå 1: Ingen risikostyring.",
                "Nivå 2: Risikoer kjent, men ikke håndtert.",
                "Nivå 3: Tiltak iverksatt, men uten oppfølging.",
                "Nivå 4: Risikostyring integrert i gevinststyringen.",
                "Nivå 5: Risikoanalyser brukes løpende til læring og beslutning."
            ]
        },
        {
            "id": 16,
            "title": "Kommunikasjon og involvering",
            "question": "Hvordan kommuniseres fremdrift og resultater, og i hvilken grad er interessentene fortsatt engasjert?",
            "scale": [
                "Nivå 1: Lite eller ingen kommunikasjon.",
                "Nivå 2: Informasjon deles ustrukturert.",
                "Nivå 3: Kommunikasjon planlagt, men lite evaluert.",
                "Nivå 4: Strukturert og målrettet kommunikasjon.",
                "Nivå 5: Kontinuerlig dialog og åpen rapportering."
            ]
        },
        {
            "id": 17,
            "title": "Læring og forbedring",
            "question": "Er det etablert prosesser for læring og forbedring basert på erfaringer fra gevinstrealiseringen?",
            "scale": [
                "Nivå 1: Ingen læringsprosess.",
                "Nivå 2: Erfaringer deles uformelt.",
                "Nivå 3: Læring dokumenteres, men ikke systematisk brukt.",
                "Nivå 4: Læringssløyfer implementert og brukt i planlegging.",
                "Nivå 5: Kontinuerlig læring styrer metode- og prosessforbedring."
            ]
        },
        {
            "id": 18,
            "title": "Varighet og bærekraft",
            "question": "Er realiserte gevinster bærekraftige over tid, og er det planlagt tiltak for å bevare effektene?",
            "scale": [
                "Nivå 1: Gevinster forsvinner etter leveranse.",
                "Nivå 2: Tiltak for varighet mangler.",
                "Nivå 3: Enkelte gevinster sikres, men uten struktur.",
                "Nivå 4: Planlagte tiltak sikrer varighet og forankring.",
                "Nivå 5: Langsiktig gevinstforvaltning integrert i styring."
            ]
        },
        {
            "id": 19,
            "title": "Nye og uforutsette gevinster",
            "question": "Blir nye eller uforutsette gevinster oppdaget og utnyttet underveis i realiseringen?",
            "scale": [
                "Nivå 1: Nye gevinster ikke identifisert.",
                "Nivå 2: Oppdaget tilfeldig, men ikke utnyttet.",
                "Nivå 3: Dokumentert, men ikke systematisk håndtert.",
                "Nivå 4: Nye gevinster vurderes og innarbeides i planverk.",
                "Nivå 5: Nye gevinster systematisk identifisert og integrert."
            ]
        },
        {
            "id": 20,
            "title": "Samspill og organisering",
            "question": "Hvordan fungerer samspillet mellom program, linje og støttefunksjoner i realiseringsarbeidet?",
            "scale": [
                "Nivå 1: Samhandling svak og ustrukturert.",
                "Nivå 2: Samarbeid skjer ad hoc.",
                "Nivå 3: Samhandling eksisterer, men ikke koordinert.",
                "Nivå 4: Godt samarbeid med tydelige grensesnitt.",
                "Nivå 5: Sømløst samspill og koordinert styring på tvers."
            ]
        },
        {
            "id": 21,
            "title": "Bygge momentum og tidlig gevinstuttak",
            "question": "Hvordan brukes tidlig gevinstuttak for å bygge momentum i realiseringsfasen?",
            "scale": [
                "Nivå 1: Ingen systematisk bruk av tidlig gevinstuttak for momentum.",
                "Nivå 2: Enkelte suksesser brukes til å motivere.",
                "Nivå 3: Bevissthet på viktigheten av momentum, men begrenset handling.",
                "Nivå 4: Strategisk bruk av tidlige gevinster for å akselerere realisering.",
                "Nivå 5: Momentum systematisk bygget og vedlikeholdt gjennom hele fasen."
            ]
        }
    ],
    "Realisert": [
        {
            "id": 1,
            "title": "Faktisk resultatoppnåelse",
            "question": "Ble gevinstene realisert som planlagt i henhold til gevinstrealiseringsplanen?",
            "scale": [
                "Nivå 1: Ingen dokumentasjon på gevinstrealisering.",
                "Nivå 2: Enkelte gevinster dokumentert, men uten struktur.",
                "Nivå 3: Realiserte gevinster dokumentert, men med avvik fra plan.",
                "Nivå 4: De fleste gevinster realisert i tråd med plan og rapportert.",
                "Nivå 5: Full realisering og dokumentasjon av resultater, inkludert læring."
            ]
        },
        {
            "id": 2,
            "title": "Strategisk effekt",
            "question": "I hvilken grad bidrar realiserte gevinster til organisasjonens strategiske mål?",
            "scale": [
                "Nivå 1: Ingen måloppnåelse målt mot strategi.",
                "Nivå 2: Enkelte sammenhenger observert, men ikke dokumentert.",
                "Nivå 3: Tydelig kobling mellom flere gevinster og strategiske mål.",
                "Nivå 4: Systematisk måling av gevinstbidrag til strategi.",
                "Nivå 5: Strategisk målstyring styrkes av gevinstdata og analyser."
            ]
        },
        {
            "id": 3,
            "title": "Kost--nytte og verdiskaping",
            "question": "Kan de realiserte gevinstene rettferdiggjøre investeringen (kost--nytte-forhold)?",
            "scale": [
                "Nivå 1: Ingen vurdering av gevinst vs. kostnad.",
                "Nivå 2: Delvis beregning, men uten dokumentert metode.",
                "Nivå 3: Beregning finnes, men usikkerhet høy.",
                "Nivå 4: Kost--nytte-forhold dokumentert og analysert.",
                "Nivå 5: Kost--nytte-analyser brukes aktivt i prioriteringer."
            ]
        },
        {
            "id": 4,
            "title": "Bruk og effekt av frigjorte ressurser",
            "question": "Hvordan brukes og dokumenteres effekten av frigjorte ressurser etter programslutt?",
            "scale": [
                "Nivå 1: Ikke dokumentert.",
                "Nivå 2: Delvis beskrevet.",
                "Nivå 3: Dokumentert for enkelte tiltak.",
                "Nivå 4: Systematisk målt og rapportert.",
                "Nivå 5: Effekter målt og brukt i strategisk planlegging og prioritering."
            ]
        },
        {
            "id": 5,
            "title": "Langsiktig balanse mellom gevinster og ulemper",
            "question": "Hvordan følges balansen mellom realiserte gevinster og eventuelle varige ulemper opp etter programslutt?",
            "scale": [
                "Nivå 1: Ingen oppfølging etter avslutning.",
                "Nivå 2: Delvis omtalt, men ikke målt.",
                "Nivå 3: Enkelte vurderinger dokumentert.",
                "Nivå 4: Systematisk oppfølging etablert.",
                "Nivå 5: Langsiktig balanse mellom gevinster og ulemper integrert i virksomhetsstyringen."
            ]
        },
        {
            "id": 6,
            "title": "Dokumentasjon og datakvalitet",
            "question": "Er dokumentasjon av realiserte gevinster fullstendig, verifisert og kvalitetssikret?",
            "scale": [
                "Nivå 1: Ingen eller fragmentert dokumentasjon.",
                "Nivå 2: Delvis dokumentert, men lite kvalitetssikret.",
                "Nivå 3: Dokumentasjon finnes, men ujevn kvalitet.",
                "Nivå 4: Kvalitetssikret dokumentasjon på alle hovedgevinster.",
                "Nivå 5: Datagrunnlag og dokumentasjon fullt integrert i rapportering."
            ]
        },
        {
            "id": 7,
            "title": "Forankring av gevinstforvaltning",
            "question": "Er ansvaret for å videreføre og forvalte realiserte gevinster tydelig plassert i linjen?",
            "scale": [
                "Nivå 1: Ingen tydelig forvaltningsansvar.",
                "Nivå 2: Uformelt ansvar hos enkelte aktører.",
                "Nivå 3: Forvaltningsansvar etablert, men uten struktur.",
                "Nivå 4: Ansvar for gevinstforvaltning tydelig plassert og aktivt utøvd.",
                "Nivå 5: Gevinstforvaltning integrert i linjeledelse."
            ]
        },
        {
            "id": 8,
            "title": "Systematisk arbeid med gevinster",
            "question": "Videreføres gevinstarbeidet som en del av virksomhetens ordinære styrings- og forbedringsprosesser?",
            "scale": [
                "Nivå 1: Gevinstarbeidet avsluttes etter programmet.",
                "Nivå 2: Enkelte aktiviteter videreføres, men uten struktur.",
                "Nivå 3: Delvis integrert i forbedringsarbeid.",
                "Nivå 4: Gevinstarbeidet formelt del av virksomhetsstyringen.",
                "Nivå 5: Gevinstarbeid fullt integrert i plan-, budsjett- og resultatstyring."
            ]
        },
        {
            "id": 9,
            "title": "Kultur og holdningsendring",
            "question": "I hvilken grad har programmet bidratt til varig kultur- og holdningsendring i organisasjonen?",
            "scale": [
                "Nivå 1: Ingen varig endring observert.",
                "Nivå 2: Enkelte endringer, men ikke forankret.",
                "Nivå 3: Endring skjer, maar avhenger av enkeltpersoner.",
                "Nivå 4: Endring tydelig forankret i praksis og ledelse.",
                "Nivå 5: Varig kulturendring etablert og målbart synlig."
            ]
        },
        {
            "id": 10,
            "title": "Læring og erfaringsoverføring",
            "question": "Er læring fra gevinstrealiseringen systematisk dokumentert, delt og brukt i nye prosjekter?",
            "scale": [
                "Nivå 1: Ingen læringsprosess.",
                "Nivå 2: Uformell erfaringsdeling.",
                "Nivå 3: Dokumentert, men ikke brukt videre.",
                "Nivå 4: Erfaringer systematisk overført og anvendt.",
                "Nivå 5: Læring integrert i virksomhetens styringsmodell."
            ]
        },
        {
            "id": 11,
            "title": "Standardisering og metodeforbedring",
            "question": "Er erfaringer og metoder fra gevinstrealiseringen brukt til å forbedre organisasjonens gevinststyringsmodell?",
            "scale": [
                "Nivå 1: Ingen forbedring av metode.",
                "Nivå 2: Enkeltforbedringer foreslått, men ikke gjennomført.",
                "Nivå 3: Forbedringer implementert i deler av organisasjonen.",
                "Nivå 4: Standardisert praksis etablert og brukt bredt.",
                "Nivå 5: Kontinuerlig metodeutvikling basert på måling og erfaring."
            ]
        },
        {
            "id": 12,
            "title": "Risikostyring og robusthet",
            "question": "Hvordan håndteres risikoer og usikkerhet som påvirker videreføring av realiserte gevinster?",
            "scale": [
                "Nivå 1: Risikoer ikke vurdert etter programslutt.",
                "Nivå 2: Risikoer kjent, men håndteres ikke.",
                "Nivå 3: Delvis overvåking av risikoer.",
                "Nivå 4: Risikoer aktivt håndtert og kommunisert.",
                "Nivå 5: Risikostyring integrert i gevinstforvaltning."
            ]
        },
        {
            "id": 13,
            "title": "Kapasitet og kompetanse etter avslutning",
            "question": "Har organisasjonen nødvendig kapasitet og kompetanse til å opprettholde og videreutvikle gevinstene?",
            "scale": [
                "Nivå 1: Kompetanse forsvinner med prosjektet.",
                "Nivå 2: Enkelte ressurser videreføres, men uten plan.",
                "Nivå 3: Kapasitet og kompetanse opprettholdes delvis.",
                "Nivå 4: Planlagt overføring og opplæring gjennomført.",
                "Nivå 5: Kompetanse og kapasitet forankret i organisasjonsstrukturen."
            ]
        },
        {
            "id": 14,
            "title": "Kommunikasjon og deling av resultater",
            "question": "Er realiserte gevinster og læring kommunisert bredt internt og eksternt?",
            "scale": [
                "Nivå 1: Ingen kommunikasjon av resultater.",
                "Nivå 2: Begrenset intern deling.",
                "Nivå 3: Resultater kommunisert internt, men lite analysert.",
                "Nivå 4: Kommunikasjon planlagt og målrettet.",
                "Nivå 5: Aktiv og inspirerende kommunikasjon brukt som kulturbygging."
            ]
        },
        {
            "id": 15,
            "title": "Nye gevinster og videre utvikling",
            "question": "Oppdages og utnyttes nye gevinstmuligheter etter programslutt?",
            "scale": [
                "Nivå 1: Nye gevinster ikke vurdert.",
                "Nivå 2: Nye gevinster oppstår, men ikke fanget opp.",
                "Nivå 3: Delvis fanget opp i forbedringsarbeid.",
                "Nivå 4: Nye gevinster systematisk identifisert og vurdert.",
                "Nivå 5: Nye gevinster brukes aktivt i kontinuerlig utvikling."
            ]
        },
        {
            "id": 16,
            "title": "Bærekraft og varighet",
            "question": "Er de realiserte gevinstene bærekraftige over tid, og er det etablert mekanismer for å sikre varig effekt?",
            "scale": [
                "Nivå 1: Gevinster varer kun kort tid.",
                "Nivå 2: Tiltak for varighet mangler.",
                "Nivå 3: Enkelte gevinster vedlikeholdes.",
                "Nivå 4: Planlagt oppfølging for varighet.",
                "Nivå 5: Varig gevinstforvaltning etablert i styringen."
            ]
        },
        {
            "id": 17,
            "title": "Helhetsvurdering av modenhet",
            "question": "Hvordan vurderes helheten i organisasjonens modenhet for gevinstrealisering etter programmet?",
            "scale": [
                "Nivå 1: Ingen struktur for gevinstrealisering.",
                "Nivå 2: Isolert kompetanse og erfaring.",
                "Nivå 3: Grunnleggende system på plass.",
                "Nivå 4: Moden organisasjon med læring og forvaltning.",
                "Nivå 5: Fullt integrert gevinststyring i kultur og virksomhetsstyring."
            ]
        },
        {
            "id": 18,
            "title": "Bygge momentum og tidlig gevinstuttak",
            "question": "Hvordan har arbeid med momentum og tidlig gevinstuttak bidratt til langsiktig suksess?",
            "scale": [
                "Nivå 1: Ingen varig effekt fra tidlig gevinstuttak.",
                "Nivå 2: Begrenset læring fra tidlige gevinster.",
                "Nivå 3: Noen erfaringer dokumentert for fremtidig bruk.",
                "Nivå 4: Systematisk læring fra momentum-bygging implementert.",
                "Nivå 5: Momentum og tidlig gevinstuttak er kjerneelementer i organisasjonens gevinstkultur."
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
        line=dict(color='#BA0C2F'),  # Bane NOR rød
        fillcolor='rgba(186, 12, 47, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickvals=[1, 2, 3, 4, 5]
            )),
        showlegend=False,
        title="Modenhet per Fase - Radardiagram",
        height=400
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
        line=dict(color='#BA0C2F'),  # Bane NOR
        fillcolor='rgba(186, 12, 47, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickvals=[1, 2, 3, 4, 5]
            )),
        showlegend=False,
        title=f"Detaljert Modenhet - {phase_name}",
        height=500,
        margin=dict(l=100, r=100, t=80, b=80)
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
        report.append("Ingen forbedringsområder identifisert")
    
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
            self.cell(0, 10, 'Modenhetsvurdering - Gevinstrealisering', 0, 1, 'C')
            self.ln(5)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Side {self.page_no()}', 0, 0, 'C')
    
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Titel
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'MODENHETSVURDERING - GEVINSTREALISERING', 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, clean_text(f'Rapport generert: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'), 0, 1)
    pdf.ln(10)
    
    # Sammendrag
    stats = calculate_stats()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'SAMMENDRAG', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    for phase, stat in stats.items():
        if stat['count'] > 0:
            pdf.cell(0, 8, clean_text(f'{phase}: {stat["count"]}/{stat["total"]} fullført - Gjennomsnitt: {stat["average"]:.2f}'), 0, 1)
    
    pdf.ln(10)
    
    # Detaljert resultat
    for phase in phases_data:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, clean_text(f'FASE: {phase.upper()}'), 0, 1)
        pdf.set_font('Arial', '', 10)
        
        for question in phases_data[phase]:
            response = st.session_state.responses[phase][question['id']]
            if response['completed'] and response['score'] > 0:
                # Bruk clean_text for alle tekster
                status = "[OK]" if response['completed'] else "[X]"
                pdf.multi_cell(0, 8, clean_text(f'{status} {question["id"]}. {question["title"]} - Score: {response["score"]}'))
                if response['notes']:
                    pdf.set_font('Arial', 'I', 8)
                    pdf.multi_cell(0, 6, clean_text(f'Notater: {response["notes"]}'))
                    pdf.set_font('Arial', '', 10)
                pdf.ln(2)
        
        pdf.ln(5)
    
    # Vesentlige forbedringsområder
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'VESENTLIGE FORBEDRINGSOMRÅDER (Score < 3)', 0, 1)
    pdf.set_font('Arial', '', 10)
    
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
    # Bane NOR fargepalett
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #BA0C2F;
            text-align: center;
            margin-bottom: 1rem;
        }
        .phase-header {
            color: #BA0C2F;
            border-bottom: 2px solid #BA0C2F;
            padding-bottom: 0.5rem;
        }
        .stProgress > div > div > div > div {
            background-color: #BA0C2F;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">PRO20 Modenhetsvurdering-Gevinstrealisering</h1>', unsafe_allow_html=True)
    st.markdown("**Interaktiv vurdering av modenhet i gevinstrealisering gjennom fire faser**")
    st.markdown("---")
    
    # Initialiser session state
    initialize_session_state()
    
    # Sidebar for navigasjon og oversikt
    with st.sidebar:
        st.markdown('<h2 style="color: #BA0C2F;"> Oversikt</h2>', unsafe_allow_html=True)
        
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
            
            st.subheader("📈 Fremdrift")
            st.progress(progress)
            st.write(f"**{phase_stats['count']}/{phase_stats['total']}** spørsmål fullført")
            
            if phase_stats['count'] > 0:
                st.write(f"Gjennomsnittsscore: **{phase_stats['average']:.2f}**")
        
        st.markdown("---")
        st.subheader("⚡ Hurtigstatistikk")
        for phase, stat in stats.items():
            if stat['count'] > 0:
                st.write(f"**{phase}:** {stat['average']:.2f}")
    
    # Hovedinnhold - spørsmålsvisning
    st.markdown(f'<h2 class="phase-header">📋 {selected_phase}</h2>', unsafe_allow_html=True)
    
    # Alle spørsmål i expandere
    for question in phases_data[selected_phase]:
        response = st.session_state.responses[selected_phase][question['id']]
        
        with st.expander(
            f"🔹 {question['id']}. {question['title']} - "
            f"Score: {response['score'] if response['completed'] else 'Ikke vurdert'}",
            expanded=False
        ):
            # Bruk "Spørsmål:" i stedet for å gjenta nummeret
            st.write(f"**Spørsmål:** {question['question']}")
            
            # Modenhetsskala
            st.subheader(" Modenhetsskala:")
            for i, level in enumerate(question['scale']):
                # Fjern duplisert "Nivå X:" fra visningen
                level_text = level
                if level_text.startswith(f"Nivå {i+1}:"):
                    # Behold bare én "Nivå X:" i teksten
                    level_text = level_text
                st.write(f"**{level_text}**")
            
            # Score input
            current_score = response['score']
            new_score = st.radio(
                "Velg vurdering:",
                options=[1, 2, 3, 4, 5],
                index=current_score-1 if current_score > 0 else 0,
                key=f"score_{selected_phase}_{question['id']}",
                horizontal=True
            )
            
            # Notater
            current_notes = response['notes']
            new_notes = st.text_area(
                "📝 Notater og kommentarer:",
                value=current_notes,
                key=f"notes_{selected_phase}_{question['id']}",
                placeholder="Skriv dine observasjoner her...",
                height=100
            )
            
            # Lagre knapp
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("💾 Lagre svar", key=f"save_{selected_phase}_{question['id']}", use_container_width=True):
                    st.session_state.responses[selected_phase][question['id']] = {
                        'score': new_score,
                        'notes': new_notes,
                        'completed': True
                    }
                    st.success("✅ Svar lagret!")
                    st.rerun()
    
    # Resultatseksjon
    st.markdown("---")
    st.markdown('<h2 style="color: #BA0C2F;">📈 Resultatoversikt</h2>', unsafe_allow_html=True)
    
    if st.button(" Generer Full Rapport", type="primary", use_container_width=True):
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
                    title="📊 Gjennomsnittsscore per Fase",
                    labels={'x': 'Fase', 'y': 'Gjennomsnittsscore'},
                    color=averages,
                    color_continuous_scale=['#FF6B6B', '#FFD166', '#06D6A0', '#118AB2', '#073B4C']
                )
                fig_bar.update_layout(yaxis_range=[0, 5.5])
                st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            # Radardiagram (kun hvis minst 3 faser har data)
            phases_with_data = [phase for phase in stats if stats[phase]['count'] > 0]
            if len(phases_with_data) >= 3:
                radar_fig = generate_radar_chart(stats)
                st.plotly_chart(radar_fig, use_container_width=True)
        
        # Detaljerte radardiagrammer per fase
        st.subheader(" Detaljert Modenhet per Fase")
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
                    st.info(f"ℹ️ Ingen data tilgjengelig for {phase}")
        
        # Detaljert rapport
        st.subheader("📋 Detaljert Rapport")
        
        # Last ned knapper for forskjellige formater
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # TXT rapport
            report_text = generate_report()
            st.download_button(
                label="📄 Last ned rapport som TXT",
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
                        label="📊 Last ned rapport som PDF",
                        data=pdf_output,
                        file_name=f"modenhetsvurdering_rapport_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"❌ Kunne ikke generere PDF: {e}")
        
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
                label="📈 Last ned data som CSV",
                data=csv_string,
                file_name=f"modenhetsvurdering_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # Forbedringsområder
        st.subheader("⚠️ Forbedringsområder")
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
                    st.write(f"🔸 {question['title']} (Score: {score})")
        
        if not improvement_found:
            st.success("✅ Ikke vesentlige forbedringsområder identifisert! Det jobbes aktivt med gevinstrealisering")
    
    # Informasjon om appen
    with st.expander("ℹ️ Om denne appen"):
        st.markdown("""
        **Funksjonalitet:**
        - Vurder modenhet i gevinstrealisering gjennom 4 faser
        - Auto-lagring av alle svar
        - Generer visuelle rapporter og diagrammer
        - Identifiser forbedringsområder
        - Eksporter rapporter i TXT, PDF og CSV format
        
        **📖 Bruk:**
        1. Velg fase i sidebar
        2. Gå gjennom hvert spørsmål
        3. Velg score og skriv notater
        4. Trykk "Lagre svar" for hvert spørsmål
        5. Trykk "Generer Full Rapport" for resultater
        
        **💾 OBS! Data lagres lokalt i nettleseren og forsvinner ved oppdatering.**
        
        ** Ikoner fra Bane NOR:**
        - 🎯 Mål - Strategisk retning
        - ⚡ Momentum - Tidlig gevinstuttak
        - ⚠️ Advarsel - Forbedringsområder
        """)

if __name__ == "__main__":
    main()
