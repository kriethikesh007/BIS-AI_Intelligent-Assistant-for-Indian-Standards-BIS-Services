import pandas as pd
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("expand_intent_dataset")

DATA_PATH = Path("data/training/intent_dataset.csv")

ADDITIONAL_INTENT_SAMPLES = [
    # ── STANDARD_RECOMMENDATION ──
    {"query_text": "Which BIS standard applies to rooftop grid-connected solar inverters?", "intent": "STANDARD_RECOMMENDATION", "category": "Solar Energy", "expected_standard": "IS 16221", "language": "en"},
    {"query_text": "Solar panel manufacturing ke liye kaunsa Indian standard follow karna hoga?", "intent": "STANDARD_RECOMMENDATION", "category": "Solar Photovoltaics", "expected_standard": "IS 14286", "language": "hi"},
    {"query_text": "Air conditioner split AC manufacturing standard enna?", "intent": "STANDARD_RECOMMENDATION", "category": "HVAC", "expected_standard": "IS 1391", "language": "ta"},
    {"query_text": "What is the mandatory standard for industrial steel toe safety footwear?", "intent": "STANDARD_RECOMMENDATION", "category": "Safety Footwear", "expected_standard": "IS 15298", "language": "en"},
    {"query_text": "Safety shoes ke liye kaunsa BIS specification hai?", "intent": "STANDARD_RECOMMENDATION", "category": "Footwear", "expected_standard": "IS 15298", "language": "hi"},
    {"query_text": "What Indian standard governs residential PVC insulated copper cables 1100V?", "intent": "STANDARD_RECOMMENDATION", "category": "Wires & Cables", "expected_standard": "IS 694", "language": "en"},
    {"query_text": "House wiring copper wire ke liye ISI standard batao", "intent": "STANDARD_RECOMMENDATION", "category": "Wires & Cables", "expected_standard": "IS 694", "language": "hi"},
    {"query_text": "Which standard applies to residual current circuit breakers RCCB?", "intent": "STANDARD_RECOMMENDATION", "category": "Switchgear", "expected_standard": "IS 12640", "language": "en"},
    {"query_text": "Underground potable water supply HDPE pipes standard specification", "intent": "STANDARD_RECOMMENDATION", "category": "Piping", "expected_standard": "IS 4984", "language": "en"},
    {"query_text": "What standard should be used for domestic aluminium and steel pressure cookers?", "intent": "STANDARD_RECOMMENDATION", "category": "Utensils", "expected_standard": "IS 2347", "language": "en"},
    {"query_text": "Pressure cooker bananeka mandatory standard kya hai?", "intent": "STANDARD_RECOMMENDATION", "category": "Cookware", "expected_standard": "IS 2347", "language": "hi"},
    {"query_text": "Which standard specifies low carbon welded steel LPG cooking gas cylinders?", "intent": "STANDARD_RECOMMENDATION", "category": "Pressure Vessels", "expected_standard": "IS 3196", "language": "en"},
    {"query_text": "Self-ballasted B22 LED bulb standard and energy performance", "intent": "STANDARD_RECOMMENDATION", "category": "Lighting", "expected_standard": "IS 16102", "language": "en"},
    {"query_text": "LED bulb standard enna details sollu", "intent": "STANDARD_RECOMMENDATION", "category": "Lighting", "expected_standard": "IS 16102", "language": "ta"},
    {"query_text": "Bluetooth wireless earbuds and earphones CRS registration standard", "intent": "STANDARD_RECOMMENDATION", "category": "Electronics", "expected_standard": "IS 616", "language": "en"},

    # ── STANDARD_INFORMATION ──
    {"query_text": "What are the acoustic safety and sound pressure test requirements in IS 616?", "intent": "STANDARD_INFORMATION", "category": "Electronics", "expected_standard": "IS 616", "language": "en"},
    {"query_text": "Explain the damp heat and thermal cycling tests in IS 14286 solar standard", "intent": "STANDARD_INFORMATION", "category": "Solar Photovoltaics", "expected_standard": "IS 14286", "language": "en"},
    {"query_text": "What does IS 694 specify regarding spark test and conductor resistance?", "intent": "STANDARD_INFORMATION", "category": "Wires & Cables", "expected_standard": "IS 694", "language": "en"},
    {"query_text": "Explain Clause 8 operating pressure test in IS 2347 for pressure cookers", "intent": "STANDARD_INFORMATION", "category": "Cookware", "expected_standard": "IS 2347", "language": "en"},
    {"query_text": "IS 2347 pressure test requirements kya hai?", "intent": "STANDARD_INFORMATION", "category": "Cookware", "expected_standard": "IS 2347", "language": "hi"},
    {"query_text": "What are the bursting pressure requirements under IS 3196 LPG cylinders?", "intent": "STANDARD_INFORMATION", "category": "Gas Cylinders", "expected_standard": "IS 3196", "language": "en"},
    {"query_text": "Tell me about IS 12640 residual current tripping limits and verification", "intent": "STANDARD_INFORMATION", "category": "Switchgear", "expected_standard": "IS 12640", "language": "en"},
    {"query_text": "What are the tensile strength requirements for toecaps under IS 15298 Part 2?", "intent": "STANDARD_INFORMATION", "category": "Safety Footwear", "expected_standard": "IS 15298", "language": "en"},
    {"query_text": "Explain lumen maintenance and endurance tests in IS 16102 LED standard", "intent": "STANDARD_INFORMATION", "category": "Lighting", "expected_standard": "IS 16102", "language": "en"},
    {"query_text": "IS 4151 helmet drop impact test protocol details", "intent": "STANDARD_INFORMATION", "category": "Automotive Safety", "expected_standard": "IS 4151", "language": "en"},
    {"query_text": "IS 14543 pesticide residue and coliform limits table", "intent": "STANDARD_INFORMATION", "category": "Drinking Water", "expected_standard": "IS 14543", "language": "en"},
    {"query_text": "IS 1786 steel rebar yield stress 500D grade specifications", "intent": "STANDARD_INFORMATION", "category": "Steel", "expected_standard": "IS 1786", "language": "en"},

    # ── CERTIFICATION ──
    {"query_text": "What is the simplified procedure for grant of licence under Scheme I?", "intent": "CERTIFICATION", "category": "Certification Schemes", "expected_standard": "Scheme I", "language": "en"},
    {"query_text": "BIS licence lene ka simplified procedure kya hai?", "intent": "CERTIFICATION", "category": "Certification Schemes", "expected_standard": "Scheme I", "language": "hi"},
    {"query_text": "What documents are required to register electronics products under Scheme II CRS?", "intent": "CERTIFICATION", "category": "CRS Scheme II", "expected_standard": "Scheme II", "language": "en"},
    {"query_text": "How can foreign manufacturers apply for FMCS licence to export to India?", "intent": "CERTIFICATION", "category": "FMCS", "expected_standard": "FMCS", "language": "en"},
    {"query_text": "Foreign factory inspection audit requirements under FMCS", "intent": "CERTIFICATION", "category": "FMCS", "expected_standard": "FMCS", "language": "en"},
    {"query_text": "What is the annual minimum marking fee concession for micro enterprises?", "intent": "CERTIFICATION", "category": "MSME Concessions", "expected_standard": "BIS Regulations", "language": "en"},
    {"query_text": "MSME manufacturers ku BIS certification fee concession irukka?", "intent": "CERTIFICATION", "category": "MSME", "expected_standard": "BIS Regulations", "language": "ta"},
    {"query_text": "How to renew an expired BIS ISI licence on Manakonline?", "intent": "CERTIFICATION", "category": "Licence Renewal", "expected_standard": "Manakonline", "language": "en"},
    {"query_text": "What is Scheme IV Certificate of Conformity for batches?", "intent": "CERTIFICATION", "category": "Scheme IV", "expected_standard": "Scheme IV", "language": "en"},
    {"query_text": "Factory layout and testing equipment checklist for Scheme I audit", "intent": "CERTIFICATION", "category": "Factory Audit", "expected_standard": "Scheme I", "language": "en"},
    {"query_text": "Can a trader or distributor apply for ISI licence without a factory?", "intent": "CERTIFICATION", "category": "Licence Eligibility", "expected_standard": "Scheme I", "language": "en"},

    # ── HALLMARKING ──
    {"query_text": "Can a jeweller sell 22K gold jewellery without a laser HUID mark?", "intent": "HALLMARKING", "category": "Gold Hallmarking", "expected_standard": "IS 1417", "language": "en"},
    {"query_text": "Bina HUID ke gold jewellery bechna legal hai kya?", "intent": "HALLMARKING", "category": "Gold Hallmarking", "expected_standard": "IS 1417", "language": "hi"},
    {"query_text": "What does 18K750 mean on diamond studded gold bangles?", "intent": "HALLMARKING", "category": "Gold Hallmarking", "expected_standard": "IS 1417", "language": "en"},
    {"query_text": "Gold hallmark 916 means enna puriyala explain panna mudiyuma?", "intent": "HALLMARKING", "category": "Gold Hallmarking", "expected_standard": "IS 1417", "language": "ta"},
    {"query_text": "How do Assaying and Hallmarking Centres test gold purity using fire assay?", "intent": "HALLMARKING", "category": "Assaying", "expected_standard": "IS 1418", "language": "en"},
    {"query_text": "What is the registration process for retail jewellers under the hallmarking scheme?", "intent": "HALLMARKING", "category": "Jeweller Registration", "expected_standard": "Hallmarking", "language": "en"},
    {"query_text": "Can a consumer get old gold jewellery hallmarked at an AHC centre?", "intent": "HALLMARKING", "category": "Consumer Hallmarking", "expected_standard": "IS 1417", "language": "en"},
    {"query_text": "How to verify 6-digit HUID code using the BIS CARE mobile application?", "intent": "HALLMARKING", "category": "HUID Verification", "expected_standard": "BIS CARE", "language": "en"},
    {"query_text": "Silver jewellery hallmarking purity symbols and fineness grades", "intent": "HALLMARKING", "category": "Silver Hallmarking", "expected_standard": "IS 2112", "language": "en"},
    {"query_text": "Velli kolusu silver hallmark symbols enna?", "intent": "HALLMARKING", "category": "Silver Hallmarking", "expected_standard": "IS 2112", "language": "ta"},

    # ── LABORATORY ──
    {"query_text": "Where is the Southern Regional Office Laboratory SROL located in Chennai?", "intent": "LABORATORY", "category": "Regional Labs", "expected_standard": "BIS Directory", "language": "en"},
    {"query_text": "Chennai la helmet test panra approved BIS laboratory enga irukku?", "intent": "LABORATORY", "category": "Testing Lab", "expected_standard": "BIS Directory", "language": "ta"},
    {"query_text": "Which testing laboratories in Mumbai are recognized for cement testing?", "intent": "LABORATORY", "category": "Testing Lab", "expected_standard": "IS 269", "language": "en"},
    {"query_text": "Mumbai testing lab for chemical analysis of steel rebars", "intent": "LABORATORY", "category": "Testing Lab", "expected_standard": "IS 1786", "language": "en"},
    {"query_text": "How can a commercial laboratory apply for BIS Laboratory Recognition Scheme LRS?", "intent": "LABORATORY", "category": "LRS Scheme", "expected_standard": "LRS Guidelines", "language": "en"},
    {"query_text": "NABL accreditation ISO 17025 requirement for BIS testing laboratories", "intent": "LABORATORY", "category": "Accreditation", "expected_standard": "ISO/IEC 17025", "language": "en"},
    {"query_text": "Where can I get domestic water samples tested for pesticide residue in Ghaziabad?", "intent": "LABORATORY", "category": "Testing Lab", "expected_standard": "Central Laboratory", "language": "en"},
    {"query_text": "Delhi NCR me lithium battery testing lab kaunsi hai?", "intent": "LABORATORY", "category": "Testing Lab", "expected_standard": "ERTL", "language": "hi"},
    {"query_text": "What tests are conducted at the Western Regional Office Laboratory WROL Mumbai?", "intent": "LABORATORY", "category": "Regional Labs", "expected_standard": "BIS Directory", "language": "en"},
    {"query_text": "Eastern Regional Office Laboratory Kolkata location and disciplines", "intent": "LABORATORY", "category": "Regional Labs", "expected_standard": "EROL", "language": "en"},

    # ── CONSUMER ──
    {"query_text": "How do I check if an ISI mark on a helmet is fake or authentic?", "intent": "CONSUMER", "category": "Authenticity Verification", "expected_standard": "BIS CARE", "language": "en"},
    {"query_text": "Fake ISI mark helmet verify kaise kare?", "intent": "CONSUMER", "category": "Consumer Redressal", "expected_standard": "BIS CARE", "language": "hi"},
    {"query_text": "Fake ISI mark iruntha eppadi complaint panrathu?", "intent": "CONSUMER", "category": "Grievance", "expected_standard": "BIS CARE", "language": "ta"},
    {"query_text": "What are the legal penalties under Section 29 of BIS Act 2016 for counterfeit marks?", "intent": "CONSUMER", "category": "Statutory Enforcement", "expected_standard": "BIS Act 2016", "language": "en"},
    {"query_text": "How can a consumer track the status of a grievance lodged on BIS CARE?", "intent": "CONSUMER", "category": "Grievance Tracking", "expected_standard": "BIS CARE", "language": "en"},
    {"query_text": "Can I get compensation if a hallmarked jewellery piece has lower purity than 22K?", "intent": "CONSUMER", "category": "Consumer Rights", "expected_standard": "Hallmarking Redressal", "language": "en"},
    {"query_text": "How to verify CM/L licence number on the Manakonline consumer portal?", "intent": "CONSUMER", "category": "Licence Verification", "expected_standard": "Manakonline", "language": "en"},
    {"query_text": "What steps does BIS take upon receiving a complaint of spurious cement?", "intent": "CONSUMER", "category": "Enforcement Raid", "expected_standard": "BIS Enforcement", "language": "en"},
    {"query_text": "Where to report jeweller refusing to provide bill with 6 digit HUID?", "intent": "CONSUMER", "category": "Hallmarking Redressal", "expected_standard": "BIS CARE", "language": "en"},
    {"query_text": "Download link and features of official BIS CARE mobile application", "intent": "CONSUMER", "category": "Mobile App", "expected_standard": "BIS CARE", "language": "en"},

    # ── GENERAL_BIS ──
    {"query_text": "Under which ministry does the Bureau of Indian Standards operate?", "intent": "GENERAL_BIS", "category": "BIS Overview", "expected_standard": "BIS Act 2016", "language": "en"},
    {"query_text": "What is the difference between mandatory Quality Control Orders and voluntary standards?", "intent": "GENERAL_BIS", "category": "Regulatory Framework", "expected_standard": "BIS Act Section 16", "language": "en"},
    {"query_text": "QCO mandatory notification aur voluntary standard me kya antar hai?", "intent": "GENERAL_BIS", "category": "Regulatory Framework", "expected_standard": "BIS Act 2016", "language": "hi"},
    {"query_text": "How can university students view Indian Standards free of cost?", "intent": "GENERAL_BIS", "category": "Know Your Standards", "expected_standard": "Portal Access", "language": "en"},
    {"query_text": "What is the role of technical standardization committees in formulating IS codes?", "intent": "GENERAL_BIS", "category": "Standardization", "expected_standard": "Divisional Councils", "language": "en"},
    {"query_text": "What are the powers of BIS inspecting officers during factory surveillance?", "intent": "GENERAL_BIS", "category": "Surveillance Powers", "expected_standard": "BIS Act 2016", "language": "en"},
    {"query_text": "How does BIS coordinate with international bodies like ISO and IEC?", "intent": "GENERAL_BIS", "category": "International Harmonization", "expected_standard": "ISO/IEC Directives", "language": "en"},
    {"query_text": "What are Standards Clubs established in educational institutions?", "intent": "GENERAL_BIS", "category": "Youth Outreach", "expected_standard": "Standards Clubs", "language": "en"},
    {"query_text": "What is the historical background of ISI becoming Bureau of Indian Standards?", "intent": "GENERAL_BIS", "category": "BIS History", "expected_standard": "BIS Act", "language": "en"},
    {"query_text": "BIS statutory functions and national standard body overview", "intent": "GENERAL_BIS", "category": "Statutory Mandate", "expected_standard": "Section 3 BIS Act", "language": "en"},

    # ── OTHER ──
    {"query_text": "Can you book a train ticket from Chennai to Bangalore for tomorrow?", "intent": "OTHER", "category": "Travel Booking", "expected_standard": "N/A", "language": "en"},
    {"query_text": "What are the latest cricket scores between India and Australia?", "intent": "OTHER", "category": "Sports", "expected_standard": "N/A", "language": "en"},
    {"query_text": "Write a short poem about sunrise over the mountains", "intent": "OTHER", "category": "Creative Writing", "expected_standard": "N/A", "language": "en"},
    {"query_text": "Ek accha chocolate cake recipe bata sakte ho?", "intent": "OTHER", "category": "Cooking", "expected_standard": "N/A", "language": "hi"},
    {"query_text": "How do airplanes fly in the sky without falling?", "intent": "OTHER", "category": "Physics / Aviation", "expected_standard": "N/A", "language": "en"},
    {"query_text": "What is the capital city of France?", "intent": "OTHER", "category": "Geography", "expected_standard": "N/A", "language": "en"},
    {"query_text": "Who directed the movie Inception in 2010?", "intent": "OTHER", "category": "Entertainment", "expected_standard": "N/A", "language": "en"},
    {"query_text": "Help me write a Python script for sorting a dictionary by values", "intent": "OTHER", "category": "Software Engineering", "expected_standard": "N/A", "language": "en"},
    {"query_text": "What is the distance between the Earth and the Moon in kilometers?", "intent": "OTHER", "category": "Astronomy", "expected_standard": "N/A", "language": "en"},
    {"query_text": "Innaiku Chennai weather forecast enna sollunga", "intent": "OTHER", "category": "Weather", "expected_standard": "N/A", "language": "ta"},
    {"query_text": "Recommend some good tourist places to visit in Kerala during monsoon", "intent": "OTHER", "category": "Tourism", "expected_standard": "N/A", "language": "en"}
]

def expand_training_dataset():
    df = pd.read_csv(DATA_PATH)
    logger.info(f"Loaded {len(df)} initial records from {DATA_PATH}")

    existing_texts = {str(t).lower().strip() for t in df["query_text"]}
    new_rows = []
    
    current_max_id = 0
    for idx_str in df["id"]:
        try:
            num = int(str(idx_str).replace("INT-", "").replace("TRAIN-", ""))
            current_max_id = max(current_max_id, num)
        except ValueError:
            pass

    for sample in ADDITIONAL_INTENT_SAMPLES:
        q_clean = sample["query_text"].lower().strip()
        if q_clean not in existing_texts:
            current_max_id += 1
            new_rows.append({
                "id": f"INT-{current_max_id:04d}",
                "query_text": sample["query_text"],
                "intent": sample["intent"],
                "category": sample["category"],
                "expected_standard": sample["expected_standard"],
                "language": sample["language"],
                "sample_data_flag": "SAMPLE DATA - VERIFY AGAINST OFFICIAL BIS GAZETTE"
            })
            existing_texts.add(q_clean)

    if new_rows:
        new_df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
        new_df.to_csv(DATA_PATH, index=False)
        logger.info(f"Added {len(new_rows)} new high-quality samples. Total dataset size: {len(new_df)}.")
        
        # Also sync to data/processed/intent_dataset.csv
        proc_path = Path("data/processed/intent_dataset.csv")
        new_df.to_csv(proc_path, index=False)
        logger.info(f"Synchronized with {proc_path}.")
    else:
        logger.info("No new unique samples were added (all existed).")

    # Log class distribution
    updated_df = pd.read_csv(DATA_PATH)
    logger.info("Class distribution:\n" + str(updated_df["intent"].value_counts()))
    return len(updated_df)

if __name__ == "__main__":
    expand_training_dataset()
