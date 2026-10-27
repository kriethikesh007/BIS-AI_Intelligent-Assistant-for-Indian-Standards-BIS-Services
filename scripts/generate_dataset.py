import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Balanced and enriched intent classification dataset
dataset = [
  # STANDARD_RECOMMENDATION
  {"text": "Which Indian standard applies to packaged drinking water bottles?", "intent": "STANDARD_RECOMMENDATION"},
  {"text": "What standard should I follow for manufacturing motorcycle helmets?", "intent": "STANDARD_RECOMMENDATION"},
  {"text": "Recommend the standard for 16A electric plug and wall socket outlets.", "intent": "STANDARD_RECOMMENDATION"},
  {"text": "Which BIS specification is used for mobile phone lithium-ion batteries?", "intent": "STANDARD_RECOMMENDATION"},
  {"text": "Which standard applies to laptop computer safety requirements?", "intent": "STANDARD_RECOMMENDATION"},
  {"text": "What is the standard for plastic and mechanical toys safety?", "intent": "STANDARD_RECOMMENDATION"},
  {"text": "Which standard should be used for OPC 53 grade cement manufacturing?", "intent": "STANDARD_RECOMMENDATION"},
  {"text": "What is the Indian standard for TMT steel rebars in concrete construction?", "intent": "STANDARD_RECOMMENDATION"},
  {"text": "What standard governs gold jewellery fineness and purity?", "intent": "STANDARD_RECOMMENDATION"},
  {"text": "Which standard is for electric iron household appliances?", "intent": "STANDARD_RECOMMENDATION"},
  {"text": "What is the specification standard for tap water and potable water?", "intent": "STANDARD_RECOMMENDATION"},
  {"text": "Which standard covers 925 sterling silver purity marking?", "intent": "STANDARD_RECOMMENDATION"},
  {"text": "Suggest the applicable standard code for power banks and battery cells.", "intent": "STANDARD_RECOMMENDATION"},
  {"text": "Which Indian standard do I need to manufacture safety helmets?", "intent": "STANDARD_RECOMMENDATION"},
  {"text": "What standard applies to 20 litre water jars?", "intent": "STANDARD_RECOMMENDATION"},
  {"text": "Recommend the relevant standard for steel rods and deformed bars.", "intent": "STANDARD_RECOMMENDATION"},
  {"text": "Which standard is required for domestic electric switches and plugs?", "intent": "STANDARD_RECOMMENDATION"},

  # STANDARD_INFORMATION
  {"text": "Explain the scope and clauses of IS 14543:2016 for drinking water.", "intent": "STANDARD_INFORMATION"},
  {"text": "What are the testing parameters in IS 4151 for two wheeler helmets?", "intent": "STANDARD_INFORMATION"},
  {"text": "Can you give me details of IS 1293 electrical socket requirements?", "intent": "STANDARD_INFORMATION"},
  {"text": "What does IS 16046 specify for rechargeable battery cells?", "intent": "STANDARD_INFORMATION"},
  {"text": "Explain the chemical and physical requirements under IS 269 cement standard.", "intent": "STANDARD_INFORMATION"},
  {"text": "What are the yield stress requirements in IS 1786 steel standard?", "intent": "STANDARD_INFORMATION"},
  {"text": "What are the fineness grades in IS 1417 gold standard?", "intent": "STANDARD_INFORMATION"},
  {"text": "What is covered under IS 10500 potable water quality limits?", "intent": "STANDARD_INFORMATION"},
  {"text": "Tell me about IS 9873 heavy metal element migration limits in toys.", "intent": "STANDARD_INFORMATION"},
  {"text": "Provide details on IS 302-2-3 safety standards for electric irons.", "intent": "STANDARD_INFORMATION"},
  {"text": "What are the specific clauses and requirements in standard IS 14543?", "intent": "STANDARD_INFORMATION"},
  {"text": "Give me information on standard IS 4151 impact test criteria.", "intent": "STANDARD_INFORMATION"},
  {"text": "Tell me about the technical requirements of IS 16046 Part 2.", "intent": "STANDARD_INFORMATION"},
  {"text": "What are the physical test limits specified in IS 269:2015?", "intent": "STANDARD_INFORMATION"},

  # CERTIFICATION
  {"text": "How do I apply for an ISI mark licence under Scheme I?", "intent": "CERTIFICATION"},
  {"text": "What is Scheme II Compulsory Registration Scheme (CRS) for electronics?", "intent": "CERTIFICATION"},
  {"text": "Explain the Foreign Manufacturers Certification Scheme (FMCS) process.", "intent": "CERTIFICATION"},
  {"text": "What are the factory inspection steps for obtaining a BIS licence?", "intent": "CERTIFICATION"},
  {"text": "What is Certificate of Conformity Scheme IV?", "intent": "CERTIFICATION"},
  {"text": "What fee concessions are available for MSMEs and startups in certification?", "intent": "CERTIFICATION"},
  {"text": "How long does it take to grant a BIS license under simplified procedure?", "intent": "CERTIFICATION"},
  {"text": "Can an overseas manufacturer export goods to India with ISI mark?", "intent": "CERTIFICATION"},
  {"text": "What is the Manakonline portal and how do I register my factory?", "intent": "CERTIFICATION"},
  {"text": "What is Management Systems Certification Scheme MSCS?", "intent": "CERTIFICATION"},
  {"text": "Explain the step by step certification procedure for new manufacturers.", "intent": "CERTIFICATION"},
  {"text": "What documents are required to apply for Scheme 1 ISI certification?", "intent": "CERTIFICATION"},
  {"text": "What is the certification procedure for startups on Manakonline?", "intent": "CERTIFICATION"},
  {"text": "How do I renew my BIS certification licence?", "intent": "CERTIFICATION"},

  # HALLMARKING
  {"text": "What is HUID in gold jewellery?", "intent": "HALLMARKING"},
  {"text": "How do I check if my gold jewellery is genuinely hallmarked?", "intent": "HALLMARKING"},
  {"text": "What are the three mandatory marks in gold hallmarking?", "intent": "HALLMARKING"},
  {"text": "Is hallmarking mandatory for all districts in India?", "intent": "HALLMARKING"},
  {"text": "What is the difference between 22K916 and 18K750 gold hallmarking?", "intent": "HALLMARKING"},
  {"text": "How do jewellers get registered for gold hallmarking?", "intent": "HALLMARKING"},
  {"text": "Can consumers get their un-hallmarked gold tested at an AHC centre?", "intent": "HALLMARKING"},
  {"text": "Explain silver hallmarking standards and purity grades.", "intent": "HALLMARKING"},
  {"text": "What is an Assaying and Hallmarking Centre (AHC)?", "intent": "HALLMARKING"},
  {"text": "How to verify the 6 digit alphanumeric HUID code?", "intent": "HALLMARKING"},
  {"text": "Tell me about gold hallmarking rules and purity signs.", "intent": "HALLMARKING"},
  {"text": "What does 916 mark mean on a gold chain?", "intent": "HALLMARKING"},

  # LABORATORY
  {"text": "Where is the BIS Central Laboratory located and what does it test?", "intent": "LABORATORY"},
  {"text": "Which testing laboratories are approved for lithium battery CRS testing?", "intent": "LABORATORY"},
  {"text": "Find laboratories in Chennai for testing helmets and cement.", "intent": "LABORATORY"},
  {"text": "Where can I get packaged drinking water samples tested?", "intent": "LABORATORY"},
  {"text": "List the BIS regional laboratories across India.", "intent": "LABORATORY"},
  {"text": "Is National Test House NTH recognized by BIS for steel testing?", "intent": "LABORATORY"},
  {"text": "What tests are performed at the Electronics Regional Test Laboratory ERTL?", "intent": "LABORATORY"},
  {"text": "How can an outside laboratory apply for BIS recognition?", "intent": "LABORATORY"},
  {"text": "Where is the BIS Southern Regional Office Laboratory located?", "intent": "LABORATORY"},
  {"text": "Recommend testing lab for packaged drinking water in Ghaziabad.", "intent": "LABORATORY"},
  {"text": "Where are the government approved testing laboratories for electronics?", "intent": "LABORATORY"},
  {"text": "Which lab tests two wheeler motorcycle helmets in Tamil Nadu?", "intent": "LABORATORY"},

  # CONSUMER
  {"text": "How can a consumer file a complaint against fake ISI marked products?", "intent": "CONSUMER"},
  {"text": "How do I verify a CML licence number on the BIS CARE app?", "intent": "CONSUMER"},
  {"text": "What actions does BIS take against counterfeit goods and fake marks?", "intent": "CONSUMER"},
  {"text": "Can consumers verify product authenticity on mobile phones?", "intent": "CONSUMER"},
  {"text": "What should I do if a store is selling substandard non-ISI helmets?", "intent": "CONSUMER"},
  {"text": "How does the BIS CARE mobile app protect consumers?", "intent": "CONSUMER"},
  {"text": "Where can consumers report misuse of the BIS standard mark?", "intent": "CONSUMER"},
  {"text": "How to lodge a consumer grievance regarding fake BIS certification?", "intent": "CONSUMER"},
  {"text": "Can I report a shopkeeper selling duplicate ISI cement?", "intent": "CONSUMER"},
  {"text": "How to track status of consumer complaints filed on BIS CARE?", "intent": "CONSUMER"},

  # GENERAL_BIS
  {"text": "What is the Bureau of Indian Standards and what is its role?", "intent": "GENERAL_BIS"},
  {"text": "What are Quality Control Orders (QCO) issued by the government?", "intent": "GENERAL_BIS"},
  {"text": "What is the 'Know Your Standards' initiative?", "intent": "GENERAL_BIS"},
  {"text": "Can students and educational institutions access Indian Standards for free?", "intent": "GENERAL_BIS"},
  {"text": "What are BIS Standards Clubs in schools and colleges?", "intent": "GENERAL_BIS"},
  {"text": "How many Indian Standards has BIS published so far?", "intent": "GENERAL_BIS"},
  {"text": "What is the BIS Act 2016?", "intent": "GENERAL_BIS"},
  {"text": "Explain the general functions and powers of BIS.", "intent": "GENERAL_BIS"},
  {"text": "What is the purpose of mandatory Quality Control Orders QCO?", "intent": "GENERAL_BIS"},
  {"text": "How does BIS promote standardization among students?", "intent": "GENERAL_BIS"},

  # OTHER
  {"text": "Hello, good morning! Who are you?", "intent": "OTHER"},
  {"text": "What is the weather in New Delhi today?", "intent": "OTHER"},
  {"text": "Tell me a joke about engineers.", "intent": "OTHER"},
  {"text": "Who won the cricket match yesterday?", "intent": "OTHER"},
  {"text": "Help me write a Python script for web scraping.", "intent": "OTHER"},
  {"text": "Can you book a flight ticket for me to Mumbai?", "intent": "OTHER"},
  {"text": "What is the recipe for chocolate cake?", "intent": "OTHER"},
  {"text": "Tell me a story about space exploration.", "intent": "OTHER"},
  {"text": "Who is the prime minister of the country?", "intent": "OTHER"}
]

with open(BASE_DIR / "data" / "intent_dataset.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2)

print(f"Generated {len(dataset)} balanced intent training samples.")
