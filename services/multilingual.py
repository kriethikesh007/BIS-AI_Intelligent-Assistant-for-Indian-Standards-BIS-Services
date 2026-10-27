import re
import logging
from typing import Dict, Any, Tuple, List, Optional

logger = logging.getLogger("bis_ai.multilingual")

# Supported languages
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil"
}

# Regex for protected entities: Standard numbers, IS numbers, technical codes, Karat grades, clauses, URLs, official names
PROTECTED_ENTITY_REGEX = re.compile(
    r'(?P<url>https?://[^\s<>"]+)|'
    r'(?P<is_std>\b(?:IS|आईएस|ஐஎஸ்)\s*(?:/?\s*(?:Part|Section|Sec|भाग|பகுதி)\s*[\d\w/]+)?\s*[\:\-]?\s*\d+(?:[\:\-]\d+)?\b)|'
    r'(?P<acronym>\b(?:HUID|ISI\s*Mark|ISI|CRS|FMCS|MSCS|NABL|AHC|STQC|CML|DPIIT|MSME|BIS\s*CARE|ManakOnline|ISO/IEC\s*17025|ISO/IEC\s*17065|ISO|IEC|BIS|QCO)\b)|'
    r'(?P<karat>\b(?:24K999|23K958|22K916|20K833|18K750|14K585|24K|23K|22K|20K|18K|14K|999|958|916|833|750|585)\b)|'
    r'(?P<rating>\b\d+\s*(?:A|V|Hz|W|kW|kg|mm|cm|litre|litres|ml|rpm|Grade\s*\d+|K)\b)|'
    r'(?P<clause>\b(?:Clause\s+[\d\.]+|Section\s+\d+|Schedule\s+[IVX]+|Rule\s+\d+|Table\s+\d+)\b)',
    re.IGNORECASE
)

# Multi-word Hindi phrases mapped to English
HINDI_PHRASES = [
    ("पानी की बोतलें", "packaged drinking water bottles"),
    ("पानी की बोतल", "packaged drinking water bottle"),
    ("बोतलबंद पानी", "packaged drinking water"),
    ("पीने का पानी", "packaged drinking water"),
    ("पीने के पानी", "packaged drinking water"),
    ("पेयजल बोतल", "packaged drinking water bottle"),
    ("पेयजल", "drinking water"),
    ("दो पहिया वाहन", "two wheeler motorcycle"),
    ("दो पहिया", "two wheeler motorcycle"),
    ("दोपहिया वाहन", "two wheeler motorcycle"),
    ("दोपहिया", "two wheeler motorcycle"),
    ("सोने के आभूषण", "gold jewellery"),
    ("सोने का आभूषण", "gold jewellery"),
    ("सोने के गहने", "gold jewellery"),
    ("सोने का गहना", "gold jewellery"),
    ("सोने की शुद्धता", "gold purity"),
    ("चांदी के आभूषण", "silver jewellery"),
    ("चांदी के बर्तन", "silver artefacts"),
    ("प्लग और सॉकेट", "electric plug and socket"),
    ("प्लग और साकेट", "electric plug and socket"),
    ("बिजली के प्लग", "electric plug socket"),
    ("लिथियम आयन बैटरी", "lithium ion battery"),
    ("लिथियम बैटरी", "lithium ion battery"),
    ("पोर्टलैंड सीमेंट", "portland cement"),
    ("टीएमटी स्टील बार", "tmt steel bars"),
    ("टीएमटी स्टील", "tmt steel bars"),
    ("टीएमटी बार", "tmt steel bars"),
    ("सौर इन्वर्टर", "solar photovoltaic inverter"),
    ("सोलर इन्वर्टर", "solar photovoltaic inverter"),
    ("सौर ऊर्जा", "solar energy"),
    ("बिजली के तार", "electric cables"),
    ("बिजली का तार", "electric cables"),
    ("घरेलू बिजली के तार", "domestic electric cables"),
    ("प्रेशर कुकर", "pressure cooker"),
    ("दबाव कुकर", "pressure cooker"),
    ("गैस सिलेंडर", "lpg gas cylinder"),
    ("एलपीजी सिलेंडर", "lpg gas cylinder"),
    ("आपातकालीन रोशनी", "rechargeable led emergency lighting"),
    ("आपातकालीन लाइट", "rechargeable led emergency lighting"),
    ("इमरजेंसी लाइट", "rechargeable led emergency lighting"),
    ("खिलौनों की सुरक्षा", "safety of toys"),
    ("बच्चों के खिलौने", "children toys safety"),
    ("इलेक्ट्रिक प्रेस", "electric iron"),
    ("इलेक्ट्रिक इस्त्री", "electric iron"),
    ("कपड़े की इस्त्री", "electric iron"),
    ("इयरफ़ोन", "earphones"),
    ("ईयरफ़ोन", "earphones"),
    ("हेडफ़ोन", "headphones"),
    
    # Grammatical & conceptual phrases
    ("किस उत्पाद से संबंधित है", "which product does it cover"),
    ("किस उत्पाद के लिए है", "which product is it for"),
    ("किस उत्पाद के लिए लागू है", "which product does it apply to"),
    ("कौन सा मानक लागू होता है", "which standard applies"),
    ("कौन सा मानक लागू है", "which standard applies"),
    ("कौन से उत्पाद कवर होते हैं", "which products are covered"),
    ("आवेदन कैसे करें", "how to apply"),
    ("आवेदन कैसे कर सकते हैं", "how to apply"),
    ("प्रमाणन के लिए कैसे आवेदन करें", "how to apply for certification"),
    ("लाइसेंस कैसे प्राप्त करें", "how to get licence"),
    ("सत्यापन कैसे करें", "how to verify"),
    ("जांच कैसे करें", "how to verify"),
    ("रिपोर्ट कैसे करें", "how to report complaint"),
    ("शिकायत कैसे दर्ज करें", "how to report complaint"),
    ("शिकायत दर्ज करने की प्रक्रिया", "complaint redressal procedure"),
    ("नकली मार्क की रिपोर्ट", "report fake counterfeit mark"),
    ("नकली निशान की रिपोर्ट", "report fake counterfeit mark"),
    ("भारतीय मानक क्या है", "what is Indian Standard"),
    ("मानक संख्या", "standard number"),
    ("प्रमाणन योजना", "certification scheme"),
    ("अनिवार्य प्रमाणन", "mandatory certification"),
    ("स्वैच्छिक प्रमाणन", "voluntary certification"),
    ("हॉलमार्क सत्यापन", "hallmark verification"),
    ("हॉलमार्किंग नियम", "hallmarking rules"),
    ("लाइसेंस प्रक्रिया", "licensing procedure"),
    ("परीक्षण प्रयोगशाला", "testing laboratory"),
    ("जांच प्रयोगशाला", "testing laboratory"),
    ("केंद्रीय प्रयोगशाला", "Central Laboratory"),
    ("उपभोक्ता शिकायत", "consumer complaint"),
    ("शिकायत निवारण", "grievance redressal"),
    ("शुल्क में छूट", "fee concessions"),
    ("लाइसेंस शुल्क", "licence fee"),
    ("के लिए लागू", "applies to"),
    ("लागू होता है", "applies to"),
    ("लागू होती है", "applies to"),
    ("से संबंधित है", "covers relates to"),
    ("के बारे में", "about"),
    ("क्या है", "what is"),
    ("क्या होता है", "what is")
]

# Single-word Hindi dictionary
HINDI_WORDS = {
    "मानक": "standard",
    "नियम": "rules",
    "प्रक्रिया": "procedure",
    "आवेदन": "apply application",
    "सत्यापन": "verification verify",
    "प्रमाणन": "certification",
    "अनिवार्य": "mandatory",
    "स्वैच्छिक": "voluntary",
    "लाइसेंस": "licence license",
    "योजना": "scheme",
    "स्कीम": "scheme",
    "छूट": "concessions rebate",
    "रियायत": "concessions",
    "शुल्क": "fee fees",
    "परीक्षण": "testing",
    "जांच": "testing",
    "प्रयोगशाला": "laboratory",
    "प्रयोगशालाएं": "laboratories",
    "प्रयोगशालाओं": "laboratories",
    "लैब": "laboratory",
    "शुद्धता": "purity",
    "हॉलमार्क": "hallmarking",
    "हॉलमार्किंग": "hallmarking",
    "सोना": "gold",
    "स्वर्ण": "gold",
    "चांदी": "silver",
    "आभूषण": "jewellery",
    "गहने": "jewellery",
    "जेवर": "jewellery",
    "उपभोक्ता": "consumer",
    "शिकायत": "complaint",
    "निवारण": "redressal",
    "जुर्माना": "penalty",
    "दंड": "penalty",
    "नकली": "counterfeit fake",
    "जाली": "counterfeit fake",
    "गैरकानूनी": "illegal",
    "हेलमेट": "helmet",
    "पानी": "water",
    "जल": "water",
    "सीमेंट": "cement",
    "खिलौने": "toys",
    "खिलौना": "toy",
    "स्टील": "steel",
    "लोहा": "iron",
    "तार": "wires cables",
    "केबल": "cables",
    "सॉकेट": "socket",
    "साकेट": "socket",
    "प्लग": "plug",
    "बैटरी": "battery",
    "कुकर": "cooker",
    "सिलेंडर": "cylinder",
    "गीज़र": "water heater geyser",
    "उत्पाद": "product",
    "उत्पादों": "products",
    "उत्पादक": "manufacturer",
    "निर्माता": "manufacturer",
    "सामग्री": "material",
    "गुणवत्ता": "quality",
    "पहिया": "wheeler",
    "सुरक्षा": "safety",
    "सुरक्षात्मक": "protective",
    "क्या": "what",
    "कौन": "which",
    "कौनसा": "which",
    "कौनसी": "which",
    "किस": "which",
    "किससे": "which",
    "किसे": "whom",
    "कैसे": "how",
    "कहाँ": "where",
    "कहां": "where",
    "कवर": "cover",
    "संबंधित": "related",
    "लागू": "applies",
    "होता": "is",
    "होती": "is",
    "है": "is",
    "हैं": "are",
    "के": "for",
    "लिए": "for",
    "में": "in",
    "से": "from",
    "का": "of",
    "की": "of",
    "को": "to"
}

# Multi-word Tamil phrases mapped to English
TAMIL_PHRASES = [
    # Multi-word product & standard queries
    ("பாதுகாப்பு தலைக்கவசத்திற்கான தரநிலை என்ன", "protective helmet standard"),
    ("பாதுகாப்பு தலைக்கவசம்", "protective helmet"),
    ("தலைக்கவசத்திற்கான தரநிலை", "helmet standard"),
    ("தலைக்கவசத்திற்கான", "protective helmet"),
    ("தலைக்கவசம்", "helmet"),
    ("குடிநீர் பாட்டில்", "drinking water bottle"),
    ("பாட்டில் குடிநீர்", "packaged drinking water"),
    ("குடிநீர்", "packaged drinking water"),
    ("தண்ணீர் பாட்டில்", "drinking water bottle"),
    ("இரு சக்கர வாகனம்", "two wheeler motorcycle"),
    ("இருசக்கர வாகனம்", "two wheeler motorcycle"),
    ("இரு சக்கர", "two wheeler motorcycle"),
    ("இருசக்கர", "two wheeler motorcycle"),
    ("தங்க நகைகள்", "gold jewellery"),
    ("தங்க நகை", "gold jewellery"),
    ("தங்க ஆபரணம்", "gold jewellery"),
    ("தங்கத்தின் தூய்மை", "gold purity"),
    ("வெள்ளி நகைகள்", "silver jewellery"),
    ("வெள்ளி பொருட்கள்", "silver artefacts"),
    ("பிளக் மற்றும் சாக்கெட்", "electric plug and socket"),
    ("மின் பிளக்", "electric plug socket"),
    ("லித்தியம் அயன் பேட்டரி", "lithium ion battery"),
    ("போர்ட்லேண்ட் சிமெண்ட்", "portland cement"),
    ("டிஎம்டி எஃகு", "tmt steel bars"),
    ("எஃகு கம்பிகள்", "steel reinforcement bars"),
    ("சூரிய மின்மாற்றி", "solar photovoltaic inverter"),
    ("சோலார் இன்வெர்ட்டர்", "solar photovoltaic inverter"),
    ("மின் கம்பிகள்", "electric cables"),
    ("பிரஷர் குக்கர்", "pressure cooker"),
    ("எல்பிஜி சிலிண்டர்", "lpg gas cylinder"),
    ("அவசர விளக்கு", "rechargeable led emergency lights"),
    ("பொம்மைகளின் பாதுகாப்பு", "safety of toys"),
    ("மின் இஸ்திரி பெட்டி", "electric iron"),
    ("இயர்போன்களுக்கான தரநிலை என்ன", "earphones standard what"),
    ("இயர்போன்களுக்கான தரநிலை", "earphones standard"),
    ("இயர்போன்களுக்கான", "earphones"),
    ("இயர்போன்கள்", "earphones"),
    ("இயர்போன்", "earphones"),
    ("ஹெட்போன்", "headphones"),
    
    # Grammatical & conceptual phrases
    ("எந்தப் பொருளுக்கான தரநிலை", "which product standard does it cover"),
    ("எந்த பொருளுக்கான தரநிலை", "which product standard does it cover"),
    ("எந்த தயாரிப்புக்கானது", "which product is it for"),
    ("எந்த பொருளுக்கு பொருந்தும்", "which product does it apply to"),
    ("எந்த தரநிலை பொருந்தும்", "which standard applies"),
    ("எப்படி விண்ணப்பிக்கலாம்", "how can one apply"),
    ("விண்ணப்பிப்பது எப்படி", "how to apply"),
    ("சான்றிதழுக்கு எப்படி விண்ணப்பிக்கலாம்", "how to apply for certification"),
    ("சான்றிதழ் பெறுவது எப்படி", "how to get certification"),
    ("எப்படி சரிபார்ப்பது", "how to verify"),
    ("சரிபார்ப்பது எப்படி", "how to verify"),
    ("புகார் அளிப்பது எப்படி", "how to report complaint"),
    ("போலி முத்திரையை எப்படி புகார் செய்வது", "how to report counterfeit fake mark"),
    ("போலி பிஐஎஸ் முத்திரை", "counterfeit fake BIS mark"),
    ("போலி ஐஎஸ்ஐ முத்திரை", "counterfeit fake ISI mark"),
    ("என்றால் என்ன", "what is"),
    ("இந்திய தரநிலை", "Indian Standard"),
    ("தரநிலை எண்", "standard number"),
    ("சான்றிதழ் திட்டம்", "certification scheme"),
    ("கட்டாய சான்றிதழ்", "mandatory certification"),
    ("தன்னார்வ சான்றிதழ்", "voluntary certification"),
    ("ஹால்மார்க் சரிபார்ப்பு", "hallmark verification"),
    ("ஹால்மார்க் விதிகள்", "hallmarking rules"),
    ("உரிம நடைமுறை", "licensing procedure"),
    ("பரிசோதனை ஆய்வகம்", "testing laboratory"),
    ("மத்திய ஆய்வகம்", "Central Laboratory"),
    ("நுகர்வோர் புகார்", "consumer complaint"),
    ("புகார் தீர்வு", "grievance redressal"),
    ("கட்டண சலுகை", "fee concessions"),
    ("விண்ணப்ப கட்டணம்", "application fee"),
    ("விதிகள் என்ன", "rules"),
    ("தரநிலை என்ன", "standard what"),
    ("தரநிலை எது", "standard which"),
    ("பொருந்தும்", "applies to"),
    ("என்ன", "what")
]

# Single-word Tamil dictionary
TAMIL_WORDS = {
    "தரநிலை": "standard",
    "விதிகள்": "rules",
    "நடைமுறை": "procedure",
    "விண்ணப்பம்": "application apply",
    "விண்ணப்பிக்கலாம்": "apply application",
    "விண்ணப்பிக்க": "apply",
    "சரிபார்ப்பு": "verification verify",
    "சரிபார்க்க": "verify",
    "சரிபார்ப்பது": "verify verification",
    "சான்றிதழ்": "certification",
    "சான்றிதழுக்கு": "certification",
    "கட்டாய": "mandatory",
    "கட்டாயமானது": "mandatory",
    "தன்னார்வ": "voluntary",
    "உரிமம்": "licence license",
    "திட்டம்": "scheme",
    "சலுகை": "concessions",
    "சலுகைகள்": "concessions",
    "கட்டணம்": "fees",
    "கட்டணங்கள்": "fees",
    "பரிசோதனை": "testing",
    "சோதனை": "testing",
    "ஆய்வகம்": "laboratory",
    "தூய்மை": "purity",
    "தரம்": "quality",
    "ஹால்மார்க்": "hallmarking",
    "தங்கம்": "gold",
    "வெள்ளி": "silver",
    "நகைகள்": "jewellery",
    "நகை": "jewellery",
    "ஆபரணம்": "jewellery",
    "நுகர்வோர்": "consumer",
    "புகார்": "complaint",
    "தீர்வு": "redressal",
    "அபராதம்": "penalty",
    "போலி": "counterfeit fake",
    "சட்டவிரோத": "illegal",
    "பாதுகாப்பு": "safety protective",
    "தலைக்கவசம்": "helmet",
    "தலைக்கவச": "helmet",
    "தலைக்கவசத்திற்கு": "helmet for",
    "தலைக்கவசத்திற்கான": "helmet for",
    "ஹெல்மெட்": "helmet",
    "ஹெல்மெட்டுக்கு": "helmet",
    "தண்ணீர்": "water",
    "சிமெண்ட்": "cement",
    "பொம்மைகள்": "toys",
    "பொம்மை": "toy",
    "எஃகு": "steel",
    "இரும்பு": "iron",
    "கம்பிகள்": "cables bars",
    "கேபிள்": "cable",
    "விளக்கு": "light",
    "பேட்டரி": "battery",
    "குக்கர்": "cooker",
    "சிலிண்டர்": "cylinder",
    "பொருள்": "product",
    "பொருட்கள்": "products",
    "பொருளுக்கு": "product",
    "பொருளுக்கான": "product",
    "பொருளுக்கானது": "product",
    "தயாரிப்பு": "product",
    "உற்பத்தியாளர்": "manufacturer",
    "உற்பத்தியாளர்கள்": "manufacturers",
    "தயாரிப்பாளர்": "manufacturer",
    "என்ன": "what",
    "எது": "which",
    "எந்த": "which",
    "எந்தப்": "which",
    "எதற்கான": "for what for which",
    "எதற்காக": "for what",
    "எதன்": "of what",
    "எப்படி": "how",
    "எங்கு": "where",
    "எங்கே": "where",
    "பொருந்தும்": "applies",
    "உள்ளது": "is",
    "அதை": "it",
    "ஒரு": "a"
}

# Hinglish (Romanized Hindi) mapping
HINGLISH_PHRASES = [
    (r"\bhelmet ke liye\b", "helmet for"),
    (r"\bhelmet ka\b", "helmet"),
    (r"\bhelmet ki\b", "helmet"),
    (r"\bhelmet ke\b", "helmet"),
    (r"\b(\w+)\s+ka\s+standard\b", r"\1 standard"),
    (r"\b(\w+)\s+ki\s+standard\b", r"\1 standard"),
    (r"\b(\w+)\s+ke\s+standard\b", r"\1 standard"),
    (r"\bke baare mein batao\b", "about"),
    (r"\bke baare mein\b", "about"),
    (r"\bke bare me batao\b", "about"),
    (r"\bke bare me\b", "about"),
    (r"\bbata do\b", "tell show"),
    (r"\bbata de\b", "tell show"),
    (r"\bbata dena\b", "tell show"),
    (r"\bbataiye\b", "tell show"),
    (r"\bbataye\b", "tell show"),
    (r"\bbatao\b", "tell show"),
    (r"\bbhai\b", ""),
    (r"\byaar\b", ""),
    (r"\bke liye\b", "for"),
    (r"\bkya hai\b", "what is"),
    (r"\bkaun sa\b", "which"),
    (r"\bkaun si\b", "which"),
    (r"\bkaise karein?\b", "how to"),
    (r"\bkaise kare\b", "how to"),
    (r"\bkaise\b", "how"),
    (r"\blagu hota hai\b", "applies to"),
    (r"\blagu hoti hai\b", "applies to"),
    (r"\blagu hai\b", "applies to"),
    (r"\blagu\b", "applies to"),
    (r"\bse sambandhit hai\b", "related to covers"),
    (r"\bse sambandhit\b", "related to covers"),
    (r"\bsambandhit\b", "related to"),
    (r"\bkis product ke liye hai\b", "for which product"),
    (r"\bkis product ke liye\b", "for which product"),
    (r"\bkis product\b", "which product"),
    (r"\bkis\b", "which"),
    (r"\bchahiye\b", "required"),
    (r"\bkisko\b", "whom"),
    (r"\bpani ki botal\b", "drinking water bottle"),
    (r"\bpani botal\b", "drinking water bottle"),
    (r"\bsone ke gahne\b", "gold jewellery"),
    (r"\bsone ki shuddhata\b", "gold purity"),
    (r"\bnakli mark\b", "counterfeit fake mark"),
    (r"\bshulk\b", "fees"),
    (r"\byojana\b", "scheme")
]

# Tanglish (Romanized Tamil) mapping
TANGLISH_PHRASES = [
    (r"\bhelmet-?ku\b", "helmet for"),
    (r"\bwater-?ku\b", "water for"),
    (r"\b(\w+)-ku\b", r"\1 for"),
    (r"\b(\w+)-kku\b", r"\1 for"),
    (r"\b ku \b", " for "),
    (r"\b kku \b", " for "),
    (r"\benna\b", "what is"),
    (r"\bedhu\b", "which"),
    (r"\bendha\b", "which"),
    (r"\beppadi\b", "how to"),
    (r"\bpaththi\b", "about"),
    (r"\bsollunga\b", "tell"),
    (r"\bvidhigal\b", "rules"),
    (r"\bpanradhu\b", "to do"),
    (r"\bthanga nagai\b", "gold jewellery"),
    (r"\bthanni bottle\b", "drinking water bottle"),
    (r"\bthanni\b", "water")
]


class MultilingualService:
    """
    Multilingual NLP Service supporting English, Hindi, and Tamil:
    - Accurate language detection (Devanagari, Tamil, Latin, Romanized Hinglish/Tanglish)
    - Protection of Indian Standard numbers, technical abbreviations, URLs, and clauses
    - Normalization of regional & mixed queries into search-optimized representations
    - Grounded answer localization back into the user's preferred or detected language
    """

    @classmethod
    def mask_entities(cls, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Replaces protected entities (IS numbers, HUID, ISI, URLs, Karat grades, clauses)
        with unique placeholders to prevent translation corruption.
        """
        if not text:
            return text, {}

        entity_map = {}
        counter = 0

        def replacer(match):
            nonlocal counter
            token = f"«__ENT_{counter}__»"
            entity_map[token] = match.group(0).strip()
            counter += 1
            return token

        masked_text = PROTECTED_ENTITY_REGEX.sub(replacer, text)
        return masked_text, entity_map

    @classmethod
    def unmask_entities(cls, text: str, entity_map: Dict[str, str]) -> str:
        """
        Restores protected entities verbatim into the localized text.
        """
        if not text or not entity_map:
            return text

        result = text
        for placeholder, original in entity_map.items():
            result = result.replace(placeholder, original)
        return result

    @classmethod
    def detect_language(cls, text: str) -> str:
        """
        Detects input language:
        - 'hi' for Hindi (Devanagari script or strong Hinglish cues)
        - 'ta' for Tamil (Tamil script or strong Tanglish cues)
        - 'en' for English (Latin script)
        - 'unsupported' for non-Latin / non-Hindi / non-Tamil scripts (fallback to 'en')
        """
        if not text or not text.strip():
            return "en"

        clean_text = text.strip()
        devanagari_count = len([c for c in clean_text if '\u0900' <= c <= '\u097F'])
        tamil_count = len([c for c in clean_text if '\u0B80' <= c <= '\u0BFF'])

        if devanagari_count >= 2:
            return "hi"
        if tamil_count >= 2:
            return "ta"

        # Check for other Indic / non-Latin scripts (Telugu, Bengali, Arabic, Cyrillic, etc.)
        other_scripts_count = len([
            c for c in clean_text 
            if ('\u0980' <= c <= '\u0D7F') or ('\u0600' <= c <= '\u06FF') or ('\u0400' <= c <= '\u04FF')
        ])
        if other_scripts_count >= 3:
            return "unsupported"

        # Check for Romanized Hinglish (Latin script)
        lower_text = clean_text.lower()
        hinglish_phrases = [
            "ke liye", "kya hai", "kaise", "kaun sa", "kaun si", "lagu", "shulk", 
            "yojana", "batao", "bata do", "bata de", "bata dena", "bataiye", "bataye",
            "ke baare mein", "ke bare me", "se sambandhit", "kis product", "pani ki botal",
            "sone ke gahne", "nakli mark"
        ]
        if any(phrase in lower_text for phrase in hinglish_phrases):
            return "hi"

        # Combination heuristic for colloquial Hinglish (e.g., "bhai helmet ka standard bata do")
        has_postposition = bool(re.search(r'\b(?:ka|ki|ke|mein|me|ko|se|hai|hain)\b', lower_text))
        has_conversational = bool(re.search(r'\b(?:bhai|yaar|kripya|namaste|madat|chahiye|jankari|niyam|batao|bataiye|bata)\b', lower_text))
        has_genitive_standard = bool(re.search(r'\b(?:ka|ki|ke)\s+(?:standard|bis|is|quality|mark|rule|rules|spec)\b', lower_text))
        if (has_postposition and has_conversational) or (has_genitive_standard and has_conversational) or has_genitive_standard:
            return "hi"

        # Check for Romanized Tanglish (Latin script)
        tanglish_markers = ["-ku", " enna", "eppadi", "kku", "paththi", "sollunga"]
        if any(marker in lower_text for marker in tanglish_markers):
            return "ta"

        return "en"

    @classmethod
    def process_query(cls, query: str, preferred_lang: Optional[str] = None) -> Dict[str, Any]:
        """
        Processes natural-language queries across English, Hindi, Tamil, and mixed scripts:
        1. Language Detection & User Preference Resolution
        2. Technical Entity Masking
        3. Cross-script Normalization to canonical English domain query
        4. Target Answer Language Determination
        """
        original_query = query.strip() if query else ""
        detected_lang = cls.detect_language(original_query)

        # Resolve target answer language: user preference overrides auto-detection if valid
        if preferred_lang and preferred_lang.lower() in ["en", "hi", "ta"]:
            answer_language = preferred_lang.lower()
        else:
            answer_language = detected_lang if detected_lang in ["hi", "ta"] else "en"

        # Extract standard codes early so they are never lost
        code_match = re.search(r'\b(?:IS|आईएस|ஐஎஸ்)\s*(\d{3,5})\b', original_query, re.IGNORECASE)
        extracted_is_code = f"IS {code_match.group(1)}" if code_match else None

        # Normalize query to English search representation
        has_devanagari = bool(re.search(r'[\u0900-\u097F]', original_query))
        has_tamil = bool(re.search(r'[\u0B80-\u0BFF]', original_query))

        processed_query = original_query
        if has_devanagari:
            processed_query = cls._normalize_hindi_to_english(processed_query)
        if has_tamil:
            processed_query = cls._normalize_tamil_to_english(processed_query)

        # Normalize Romanized Indic expressions (Hinglish / Tanglish)
        processed_query = cls._normalize_mixed_to_english(processed_query)

        # Ensure extracted standard code is explicitly anchored in processed query
        if extracted_is_code and extracted_is_code.lower() not in processed_query.lower():
            processed_query = f"{extracted_is_code} {processed_query}"

        return {
            "original_query": original_query,
            "detected_language": detected_lang,
            "processed_query": processed_query,
            "normalized_query": processed_query,
            "answer_language": answer_language,
            "extracted_is_code": extracted_is_code,
            "is_multilingual": detected_lang in ["hi", "ta"]
        }

    @classmethod
    def _normalize_hindi_to_english(cls, text: str) -> str:
        """
        Translates Hindi query into domain English while protecting numbers and codes.
        """
        masked_text, entity_map = cls.mask_entities(text)
        translated = masked_text

        # 1. Apply multi-word phrases first
        for phrase, eng in HINDI_PHRASES:
            translated = translated.replace(phrase, eng)

        # 2. Apply word substitutions
        tokens = translated.split()
        normalized_tokens = []
        for t in tokens:
            cleaned = re.sub(r'[^\w«»_]', '', t)
            if cleaned in HINDI_WORDS:
                normalized_tokens.append(HINDI_WORDS[cleaned])
            elif t in HINDI_WORDS:
                normalized_tokens.append(HINDI_WORDS[t])
            else:
                normalized_tokens.append(t)

        result = " ".join(normalized_tokens)
        result = cls.unmask_entities(result, entity_map)
        return re.sub(r'\s+', ' ', result).strip()

    @classmethod
    def _normalize_tamil_to_english(cls, text: str) -> str:
        """
        Translates Tamil query into domain English while handling suffixes and protecting codes.
        """
        masked_text, entity_map = cls.mask_entities(text)
        translated = masked_text

        # 1. Apply multi-word phrases first
        for phrase, eng in TAMIL_PHRASES:
            translated = translated.replace(phrase, eng)

        # 2. Tokenize and handle morphological suffixes (e.g. -க்கான, -க்கு, -இல்)
        tokens = translated.split()
        normalized_tokens = []
        for t in tokens:
            cleaned = re.sub(r'[^\w«»_]', '', t)
            
            # Direct match
            if cleaned in TAMIL_WORDS:
                normalized_tokens.append(TAMIL_WORDS[cleaned])
                continue

            # Stem suffixes
            stemmed = cleaned
            stem_found = False
            for suffix in ["த்திற்கான", "த்திற்கு", "க்கானது", "க்கான", "க்கு", "உடைய", "இல்", "ஐ"]:
                if stemmed.endswith(suffix) and len(stemmed) > len(suffix) + 2:
                    base = stemmed[:-len(suffix)]
                    if base in TAMIL_WORDS:
                        normalized_tokens.append(f"{TAMIL_WORDS[base]} for")
                        stem_found = True
                        break
            if stem_found:
                continue

            if t in TAMIL_WORDS:
                normalized_tokens.append(TAMIL_WORDS[t])
            else:
                normalized_tokens.append(t)

        result = " ".join(normalized_tokens)
        result = cls.unmask_entities(result, entity_map)
        return re.sub(r'\s+', ' ', result).strip()

    @classmethod
    def _normalize_mixed_to_english(cls, text: str) -> str:
        """
        Normalizes mixed Hinglish or Tanglish Romanized expressions.
        """
        result = text
        for pattern, eng in HINGLISH_PHRASES:
            result = re.sub(pattern, eng, result, flags=re.IGNORECASE)
        for pattern, eng in TANGLISH_PHRASES:
            result = re.sub(pattern, eng, result, flags=re.IGNORECASE)
        return re.sub(r'\s+', ' ', result).strip()

    @classmethod
    def translate_answer(cls, english_text: str, target_lang: str) -> str:
        """
        Translates generated English response back to user's language (Hindi or Tamil).
        Guarantees that standard numbers, IS numbers, technical codes, Karat grades,
        URLs, and official names are NEVER corrupted.
        """
        if not english_text or target_lang not in ["hi", "ta"]:
            return english_text

        masked_text, entity_map = cls.mask_entities(english_text)

        if target_lang == "hi":
            translated = cls._translate_to_hindi(masked_text)
        elif target_lang == "ta":
            translated = cls._translate_to_tamil(masked_text)
        else:
            translated = masked_text

        return cls.unmask_entities(translated, entity_map)

    @classmethod
    def localize_answer(cls, english_text: str, target_lang: str) -> str:
        return cls.translate_answer(english_text, target_lang)

    @classmethod
    def _translate_to_hindi(cls, text: str) -> str:
        """
        Translates structured English response components into natural, authoritative Hindi.
        """
        replacements = [
            # Strict fallback & system messages
            ("Reliable BIS information could not be found for this query.", "इस प्रश्न के लिए विश्वसनीय बीआईएस (BIS) जानकारी नहीं मिल सकी।"),
            ("I could not find sufficient authoritative BIS information to answer this question reliably.", "इस प्रश्न के लिए पर्याप्त आधिकारिक बीआईएस (BIS) जानकारी नहीं मिल सकी।"),
            
            # Headings and labels
            ("• Technical Scope:", "• तकनीकी दायरा:"),
            ("• Certification Scheme:", "• प्रमाणन योजना:"),
            ("• Key Testing Parameters:", "• मुख्य परीक्षण पैरामीटर:"),
            ("• Description:", "• विवरण:"),
            ("• Application Procedure:", "• आवेदन प्रक्रिया:"),
            ("• Concessions for MSMEs/Startups:", "• एमएसएमई और स्टार्टअप्स के लिए रियायतें:"),
            ("• Accreditation:", "• मान्यता (Accreditation):"),
            ("• Address:", "• पता:"),
            ("• Disciplines:", "• विषय/शाखाएं:"),
            ("• Tested Products:", "• परीक्षित उत्पाद:"),
            ("• Contact:", "• संपर्क:"),
            
            # Key statuses & terms
            ("(Mandatory)", "(अनिवार्य)"),
            ("(Voluntary)", "(स्वैच्छिक)"),
            ("Mandatory Certification", "अनिवार्य प्रमाणन"),
            ("Voluntary Conformity", "स्वैच्छिक अनुरूपता"),
            ("Standard BIS fee structure applies.", "मानक बीआईएस शुल्क संरचना लागू होती है।"),
            
            # Standard Titles
            ("Protective Helmets for Two Wheeler Riders - Specification", "दोपहिया वाहन चालकों के लिए सुरक्षात्मक हेलमेट - विनिर्देश"),
            ("Protective Helmets for Two Wheeler Riders", "दोपहिया वाहन चालकों के लिए सुरक्षात्मक हेलमेट"),
            ("Packaged Drinking Water (Other Than Packaged Natural Mineral Water) - Specification", "पैकेज्ड पेयजल (प्राकृतिक खनिज पानी के अलावा) - विनिर्देश"),
            ("Packaged Drinking Water (Other than Packaged Natural Mineral Water)", "पैकेज्ड पेयजल (प्राकृतिक खनिज पानी के अलावा)"),
            ("Drinking Water Specification", "पीने के पानी का विनिर्देश (पेयजल मानक)"),
            ("Plugs and Socket-Outlets for Domestic and Similar Purposes - Specification", "घरेलू और समान उद्देश्यों के लिए प्लग और सॉकेट-आउटलेट - विनिर्देश"),
            ("Gold and Gold Alloys Jewellery/Artefacts - Fineness and Marking", "सोने और सोने की मिश्र धातुओं के आभूषण/कलाकृतियां - शुद्धता और अंकन"),
            ("Gold and Silver Jewellery / Artefacts", "सोने और चांदी के आभूषण / कलाकृतियां"),
            ("Secondary Cells and Batteries Containing Alkaline or Other Non-Acid Electrolytes - Safety", "क्षारीय या अन्य गैर-अम्लीय इलेक्ट्रोलाइट्स युक्त द्वितीयक सेल और बैटरी - सुरक्षा"),
            ("Information Technology Equipment - Safety - General Requirements", "सूचना प्रौद्योगिकी उपकरण - सुरक्षा - सामान्य आवश्यकताएं"),
            ("Ordinary Portland Cement - Specification", "साधारण पोर्टलैंड सीमेंट - विनिर्देश"),
            ("Ordinary Portland Cement, 43 Grade", "साधारण पोर्टलैंड सीमेंट, 43 ग्रेड"),
            ("High Strength Deformed Steel Bars and Wires for Concrete Reinforcement", "कंक्रीट सुदृढीकरण के लिए उच्च शक्ति विकृत स्टील बार और तार"),
            ("Safety of Toys - Mechanical and Physical Properties and Flammability", "खिलौनों की सुरक्षा - यांत्रिक एवं भौतिक गुण तथा ज्वलनशीलता"),
            ("Safety of Household and Similar Electrical Appliances - Electric Iron", "घरेलू और समान विद्युत उपकरणों की सुरक्षा - इलेक्ट्रिक आयरन"),
            ("Luminaires - Particular Requirements - Emergency Lighting", "ल्यूमिनेयर - विशेष आवश्यकताएं - आपातकालीन प्रकाश व्यवस्था"),
            
            # Scheme descriptions and procedures
            ("Scheme I - Product Certification Scheme (ISI Mark)", "योजना I - उत्पाद प्रमाणन योजना (ISI मार्क)"),
            ("Scheme II - Compulsory Registration Scheme (CRS)", "योजना II - अनिवार्य पंजीकरण योजना (CRS)"),
            ("FMCS - Foreign Manufacturers Certification Scheme", "FMCS - विदेशी निर्माता प्रमाणन योजना"),
            ("Scheme IV - Certificate of Conformity (CoC)", "योजना IV - अनुरूपता प्रमाणपत्र (CoC)"),
            ("Hallmarking Scheme for Precious Metals", "कीमती धातुओं के लिए हॉलमार्किंग योजना"),
            ("Scheme I is the flagship product certification scheme of BIS that allows manufacturers to use the prestigious ISI Mark.", "योजना I बीआईएस की प्रमुख उत्पाद प्रमाणन योजना है जो निर्माताओं को प्रतिष्ठित ISI मार्क का उपयोग करने की अनुमति देती है।"),
            ("1. Online submission of application on Manakonline portal with complete factory details, machinery, testing equipment, and test personnel.", "1. फैक्ट्री विवरण, मशीनरी, परीक्षण उपकरण और कर्मचारियों के साथ मानकऑनलाइन (Manakonline) पोर्टल पर ऑनलाइन आवेदन जमा करना।"),
            ("2. Payment of application fee and pre-visit documentation check.", "2. आवेदन शुल्क का भुगतान और पूर्व-दस्तावेज़ सत्यापन।"),
            ("3. Preliminary factory inspection by BIS auditor to verify manufacturing capability and testing facilities.", "3. विनिर्माण क्षमता और परीक्षण सुविधाओं की जांच के लिए बीआईएस लेखापरीक्षक द्वारा प्रारंभिक कारखाना निरीक्षण।"),
            ("4. Drawing of factory samples and testing in BIS or BIS-recognized laboratory.", "4. कारखाने से नमूने लेना और बीआईएस अथवा मान्यता प्राप्त प्रयोगशाला में उनका परीक्षण।"),
            ("5. Grant of Licence upon successful verification.", "5. सफल सत्यापन और अनुकूल परीक्षण रिपोर्ट के बाद लाइसेंस प्रदान करना।"),
            ("6. Periodic surveillance audits and market surveillance draws.", "6. आवधिक निगरानी ऑडिट और बाजार से नमूना जांच।"),
            ("20% rebate on application fee and annual minimum marking fee for Micro, Small and Medium Enterprises (MSMEs) and recognized Startups, plus 10% rebate for women entrepreneurs.", "सूक्ष्म, लघु और मध्यम उद्यमों (MSME) तथा मान्यता प्राप्त स्टार्टअप्स के लिए आवेदन शुल्क और न्यूनतम मार्किंग शुल्क में 20% की छूट, साथ ही महिला उद्यमियों के लिए 10% अतिरिक्त छूट।"),
            
            # FAQ substantive translations
            ("HUID stands for 'Hallmark Unique Identification', which is a unique 6-digit alphanumeric code laser-engraved onto every single piece of hallmarked gold jewellery alongside the BIS triangle logo and purity fineness mark (e.g., 22K916). Consumers can verify gold purity by entering the 6-digit HUID into the 'Verify HUID' feature of the BIS CARE app. The app displays the Jeweller's registration number, Assaying and Hallmarking Centre (AHC) details, date of hallmarking, and exact purity karatage. Under government rules, no jeweller can sell hallmarked gold jewellery without a valid 6-digit HUID.",
             "HUID का पूर्ण रूप 'हॉलमार्क विशिष्ट पहचान' (Hallmark Unique Identification) है। यह 6 अंकों का एक अद्वितीय अक्षरांकीय (alphanumeric) कोड है जो बीआईएस त्रिभुज लोगो और शुद्धता ग्रेड (जैसे 22K916) के साथ हॉलमार्क वाले प्रत्येक सोने के आभूषण पर लेजर द्वारा उकेरा जाता है। उपभोक्ता बीआईएस केयर (BIS CARE) ऐप के 'Verify HUID' विकल्प में 6 अंकों का HUID दर्ज करके शुद्धता की पुष्टि कर सकते हैं। ऐप पर जौहरी का पंजीकरण नंबर, परख एवं हॉलमार्किंग केंद्र (AHC) का विवरण, हॉलमार्किंग की तिथि और सटीक कैरेट शुद्धता प्रदर्शित होती है। सरकारी नियमों के तहत कोई भी जौहरी वैध 6-अंकीय HUID के बिना हॉलमार्क वाले सोने के आभूषण नहीं बेच सकता।"),
            
            ("Consumers can instantly verify the authenticity of an ISI Mark or CRS Registration using the official 'BIS CARE' mobile app (available on Android & iOS) or through the BIS Manakonline web portal. In the BIS CARE app, click on 'Verify License Details' and enter the 7-digit or 8-digit CML licence number printed underneath the ISI mark. If the number does not match the product or manufacturer, or if an inferior product is supplied, consumers can lodge a complaint directly on the 'Complaints' tab of the BIS CARE app or email complaints@bis.gov.in. BIS conducts investigation raids and seizes fake marked articles under penal provisions of the BIS Act, 2016.",
             "उपभोक्ता आधिकारिक 'BIS CARE' मोबाइल ऐप (Android और iOS पर उपलब्ध) या बीआईएस मानकऑनलाइन वेब पोर्टल के माध्यम से ISI मार्क या CRS पंजीकरण की प्रामाणिकता की तुरंत जांच कर सकते हैं। BIS CARE ऐप में 'Verify License Details' पर क्लिक करें और ISI मार्क के नीचे छपे 7 या 8 अंकों के सीएमएल (CML) लाइसेंस नंबर को दर्ज करें। यदि विवरण मेल नहीं खाता है या घटिया उत्पाद दिया गया है, तो उपभोक्ता BIS CARE ऐप के 'Complaints' टैब पर सीधे शिकायत दर्ज कर सकते हैं या complaints@bis.gov.in पर ईमेल कर सकते हैं। बीआईएस अधिनियम 2016 के दंडात्मक प्रावधानों के तहत बीआईएस जांच छापे मारता है और नकली निशान वाले सामानों को जब्त करता है।"),
            
            # Certification Schemes across Standards
            ("Scheme I (ISI Mark Scheme) - Compulsory under Road Transport Ministry QCO", "योजना I (ISI मार्क योजना) - सड़क परिवहन एवं राजमार्ग मंत्रालय के QCO के तहत अनिवार्य"),
            ("Scheme I (ISI Mark Scheme) - Mandatory Certification under QCO", "योजना I (ISI मार्क योजना) - गुणवत्ता नियंत्रण आदेश (QCO) के तहत अनिवार्य प्रमाणन"),
            ("Scheme I (ISI Mark Scheme) - Compulsory under Electrical Wires and Accessories QCO", "योजना I (ISI मार्क योजना) - विद्युत तार एवं सहायक उपकरण QCO के तहत अनिवार्य"),
            ("Scheme II (Compulsory Registration Scheme - CRS) by MeitY", "योजना II (अनिवार्य पंजीकरण योजना - CRS) इलेक्ट्रॉनिक्स एवं सूचना प्रौद्योगिकी मंत्रालय (MeitY) द्वारा"),
            ("Scheme I (ISI Mark Scheme) - Compulsory under Toys (Quality Control) Order", "योजना I (ISI मार्क योजना) - खिलौने (गुणवत्ता नियंत्रण) आदेश के तहत अनिवार्य"),
            ("Scheme I (ISI Mark Scheme) - Compulsory under Cement (Quality Control) Order", "योजना I (ISI मार्क योजना) - सीमेंट (गुणवत्ता नियंत्रण) आदेश के तहत अनिवार्य"),
            ("Scheme I (ISI Mark Scheme) - Compulsory under Steel & Steel Products QCO", "योजना I (ISI मार्क योजना) - स्टील एवं स्टील उत्पाद QCO के तहत अनिवार्य"),
            ("Hallmarking Scheme under BIS Act 2016 (Mandatory in notified districts)", "बीआईएस अधिनियम 2016 के तहत हॉलमार्किंग योजना (अधिसूचित जिलों में अनिवार्य)"),
            ("Scheme I (ISI Mark Scheme) - Compulsory under Electrical Appliances QCO", "योजना I (ISI मार्क योजना) - घरेलू विद्युत उपकरण QCO के तहत अनिवार्य"),
            ("Scheme II (Compulsory Registration Scheme - CRS) / Scheme I (ISI Mark)", "योजना II (अनिवार्य पंजीकरण योजना - CRS) / योजना I (ISI मार्क)"),
            ("Voluntary Specification / Municipal Testing Standard", "स्वैच्छिक विनिर्देश / नगरपालिका परीक्षण मानक"),
            ("Scheme I (ISI Mark Scheme)", "योजना I (ISI मार्क योजना)"),
            ("Compulsory under Road Transport Ministry QCO", "सड़क परिवहन एवं राजमार्ग मंत्रालय के QCO के तहत अनिवार्य"),
            ("Mandatory Certification under QCO", "गुणवत्ता नियंत्रण आदेश (QCO) के तहत अनिवार्य प्रमाणन"),
            ("Mandatory across designated Indian districts", "अधिसूचित भारतीय जिलों में अनिवार्य"),
            ("Mandatory under CRS", "CRS के तहत अनिवार्य"),
            ("Mandatory under Lighting & Luminaires QCO / CRS", "प्रकाश व्यवस्था एवं ल्यूमिनेयर QCO / CRS के तहत अनिवार्य"),
            ("Voluntary / Guidance for Public Water Suppliers", "सार्वजनिक जल आपूर्तिकर्ताओं के लिए स्वैच्छिक / मार्गदर्शन"),

            # Testing Parameters across Standards
            ("Turbidity, pH, total dissolved solids, hardness, iron, chlorides, nitrates, bacteriological test.", "गंदलापन (Turbidity), पीएच (pH), कुल घुलित ठोस (TDS), कठोरता, लोहा, क्लोराइड, नाइट्रेट और जीवाणु परीक्षण।"),
            ("Insulation resistance, electric strength, temperature rise test, making and breaking capacity, mechanical strength, resistance to heat and fire.", "इन्सुलेशन प्रतिरोध, विद्युत शक्ति, तापमान वृद्धि परीक्षण, मेक और ब्रेक क्षमता, यांत्रिक शक्ति, गर्मी एवं आग प्रतिरोध।"),
            ("Continuous charging at constant voltage, case stress at high ambient temperature, external short circuit, free fall, thermal abuse, crushing of cells.", "निरंतर चार्जिंग, उच्च तापमान पर केस तनाव, बाहरी शॉर्ट सर्किट, फ्री फॉल, थर्मल एब्यूज, सेल क्रशिंग परीक्षण।"),
            ("Protection from electric shock, insulation resistance, energy hazard, earth continuity, clearance and creepage distances, flammability test.", "बिजली के झटके से सुरक्षा, इन्सुलेशन प्रतिरोध, ऊर्जा खतरा, अर्थ निरंतरता, क्लीयरेंस और क्रीपेज दूरी, ज्वलनशीलता परीक्षण।"),
            ("Mechanical and physical properties (sharp edges, small parts), flammability test, migration of certain elements (lead, cadmium, mercury toxicity).", "यांत्रिक एवं भौतिक गुण (नुकीले किनारे, छोटे हिस्से), ज्वलनशीलता परीक्षण, जहरीले तत्वों का प्रवासन (सीसा, कैडमियम, पारा विषाक्तता)।"),
            ("Compressive strength (3 days, 7 days, 28 days), setting time (initial and final), soundness (Le Chatelier), fineness (Blaine air permeability), chemical composition (loss on ignition, insoluble residue).", "कंप्रेसिव स्ट्रेंथ (3 दिन, 7 दिन, 28 दिन), जमने का समय (प्रारंभिक और अंतिम), दृढ़ता (Le Chatelier), महीनता (ब्लेन वायु पारगम्यता), रासायनिक संरचना।"),
            ("0.2 percent proof stress/yield stress, tensile strength, percentage elongation, bend and rebend tests, chemical composition (carbon, sulfur, phosphorus).", "0.2 प्रतिशत प्रूफ स्ट्रेस / यील्ड स्ट्रेस, तन्यता ताकत (Tensile strength), प्रतिशत बढ़ाव (Elongation), बेंड और रिबेंड टेस्ट, रासायनिक संरचना।"),
            ("Fire assay method (IS 1418), X-ray fluorescence (XRF) testing, fineness verification, 6-digit alphanumeric HUID engraving.", "फायर परख विधि (IS 1418), एक्स-रे प्रतिदीप्ति (XRF) परीक्षण, शुद्धता सत्यापन, 6-अंकीय अक्षरांकीय HUID लेजर उत्कीर्णन।"),
            ("Fineness verification by titration/ICP-OES, hallmark logo stamping, sponsor mark.", "अनुमापन (Titration) / ICP-OES द्वारा शुद्धता सत्यापन, हॉलमार्क लोगो अंकन, प्रायोजक चिह्न।"),
            ("Input power and current, heating and thermal stability, leakage current and electric strength, moisture resistance, drop resistance.", "इनपुट शक्ति और करंट, हीटिंग और थर्मल स्थिरता, लीकेज करंट और विद्युत शक्ति, नमी प्रतिरोध, ड्रॉप प्रतिरोध।"),
            ("Emergency operating duration test, battery charge and discharge cycle test, photometrics and luminous output, high temperature endurance, insulation resistance and dielectric strength, changeover operation voltage threshold.", "आपातकालीन संचालन अवधि परीक्षण, बैटरी चार्ज एवं डिस्चार्ज चक्र परीक्षण, फोटोमेट्रिक्स और प्रकाश आउटपुट, उच्च तापमान सहनशीलता, इन्सुलेशन प्रतिरोध एवं डाइइलेक्ट्रिक ताकत।"),

            # Recommendation Explanation & Why Rationales
            ("This standard falls under a Mandatory Quality Control Order (QCO); compliance and BIS certification are required prior to commercial sale in India.", "यह मानक अनिवार्य गुणवत्ता नियंत्रण आदेश (QCO) के अंतर्गत आता है; भारत में व्यावसायिक बिक्री से पहले इसका अनुपालन और बीआईएस (BIS) प्रमाणन अनिवार्य है।"),
            ("This standard is currently Voluntary / Guidance specification. Certification is not legally mandated unless specified in buyer procurement requirements.", "यह मानक वर्तमान में एक स्वैच्छिक / मार्गदर्शन विनिर्देश है। जब तक खरीदार की खरीद आवश्यकताओं में निर्दिष्ट न हो, तब तक प्रमाणन कानूनी रूप से अनिवार्य नहीं है।"),
            ("Recommended because your product description aligns with the 'Mechanical Engineering / Automotive Safety' domain, matching technical parameters for", "अनुशंसित क्योंकि आपका उत्पाद विवरण 'मैकेनिकल इंजीनियरिंग / ऑटोमोटिव सुरक्षा' क्षेत्र से मेल खाता है, और इसके तकनीकी पैरामीटर"),
            ("Recommended because your product description aligns with the 'Food and Agriculture / Water' domain, matching technical parameters for", "अनुशंसित क्योंकि आपका उत्पाद विवरण 'खाद्य एवं कृषि / पेयजल' क्षेत्र से मेल खाता है, और इसके तकनीकी पैरामीटर"),
            ("Recommended because your product description aligns with the 'Civil & Environmental Engineering / Water Supply' domain, matching technical parameters for", "अनुशंसित क्योंकि आपका उत्पाद विवरण 'सिविल एवं पर्यावरण इंजीनियरिंग / जल आपूर्ति' क्षेत्र से मेल खाता है, और इसके तकनीकी पैरामीटर"),
            ("Recommended because your product description aligns with the 'Electrotechnical / Electrical Accessories' domain, matching technical parameters for", "अनुशंसित क्योंकि आपका उत्पाद विवरण 'इलेक्ट्रो-टेक्निकल / विद्युत उपकरण एवं सहायक उपकरण' क्षेत्र से मेल खाता है, और इसके तकनीकी पैरामीटर"),
            ("Recommended because your product description aligns with the 'Electronics & Information Technology / Energy Storage' domain, matching technical parameters for", "अनुशंसित क्योंकि आपका उत्पाद विवरण 'इलेक्ट्रॉनिक्स एवं सूचना प्रौद्योगिकी / ऊर्जा भंडारण' क्षेत्र से मेल खाता है, और इसके तकनीकी पैरामीटर"),
            ("Recommended because your product description aligns with the 'Electronics & Information Technology' domain, matching technical parameters for", "अनुशंसित क्योंकि आपका उत्पाद विवरण 'इलेक्ट्रॉनिक्स एवं सूचना प्रौद्योगिकी' क्षेत्र से मेल खाता है, और इसके तकनीकी पैरामीटर"),
            ("Recommended because your product description aligns with the 'Safety of Consumer Products / Toys' domain, matching technical parameters for", "अनुशंसित क्योंकि आपका उत्पाद विवरण 'उपभोक्ता उत्पादों की सुरक्षा / खिलौने' क्षेत्र से मेल खाता है, और इसके तकनीकी पैरामीटर"),
            ("Recommended because your product description aligns with the 'Civil Engineering / Building Materials' domain, matching technical parameters for", "अनुशंसित क्योंकि आपका उत्पाद विवरण 'सिविल इंजीनियरिंग / निर्माण सामग्री (सीमेंट)' क्षेत्र से मेल खाता है, और इसके तकनीकी पैरामीटर"),
            ("Recommended because your product description aligns with the 'Metallurgical Engineering / Steel & Iron' domain, matching technical parameters for", "अनुशंसित क्योंकि आपका उत्पाद विवरण 'धातुकर्म इंजीनियरिंग / स्टील और लोहा (TMT)' क्षेत्र से मेल खाता है, और इसके तकनीकी पैरामीटर"),
            ("Recommended because your product description aligns with the 'Hallmarking / Precious Metals' domain, matching technical parameters for", "अनुशंसित क्योंकि आपका उत्पाद विवरण 'हॉलमार्किंग / बहुमूल्य धातुएं (सोना एवं चांदी)' क्षेत्र से मेल खाता है, और इसके तकनीकी पैरामीटर"),
            ("Recommended because your product description aligns with the 'Electrotechnical / Household Appliances' domain, matching technical parameters for", "अनुशंसित क्योंकि आपका उत्पाद विवरण 'इलेक्ट्रो-टेक्निकल / घरेलू विद्युत उपकरण' क्षेत्र से मेल खाता है, और इसके तकनीकी पैरामीटर"),
            ("Recommended because your product description aligns with the 'Electrotechnical / Lighting and Luminaires' domain, matching technical parameters for", "अनुशंसित क्योंकि आपका उत्पाद विवरण 'इलेक्ट्रो-टेक्निकल / प्रकाश व्यवस्था एवं ल्यूमिनेयर' क्षेत्र से मेल खाता है, और इसके तकनीकी पैरामीटर"),
            ("Recommended because your product description aligns with the", "अनुशंसित क्योंकि आपका उत्पाद विवरण"),
            ("domain, matching technical parameters for", "क्षेत्र से मेल खाता है, और तकनीकी पैरामीटर"),
            ("based on keywords (domain specifications).", "कीवर्ड (डोमेन विनिर्देशों) के आधार पर।"),
            ("based on keywords", "कीवर्ड के आधार पर"),
            ("Direct authoritative match for Indian Standard", "भारतीय मानक के लिए प्रत्यक्ष आधिकारिक रिकॉर्ड"),
            ("in the authorized BIS catalog.", "अधिकृत बीआईएस (BIS) कैटलॉग में।"),
            ("in the BIS catalog, covering", "बीआईएस कैटलॉग में, जिसमें शामिल है"),
            ("Retrieved record matches product domain and technical requirements for", "प्राप्त रिकॉर्ड उत्पाद क्षेत्र और तकनीकी आवश्यकताओं से मेल खाता है:"),
            ("under authorized BIS catalog.", "अधिकृत बीआईएस कैटलॉग के अंतर्गत।"),
            ("Retrieved procedure covers official BIS regulations and application steps for", "प्राप्त प्रक्रिया आधिकारिक बीआईएस नियमों और आवेदन चरणों को कवर करती है:"),
            ("Authorized testing facility accredited under ISO/IEC 17025 for product testing in", "उत्पाद परीक्षण के लिए ISO/IEC 17025 के तहत मान्यता प्राप्त अधिकृत परीक्षण सुविधा:"),
            ("Authorized guidance issued under the BIS Act 2016 and Consumer Affairs Department regarding", "उपभोक्ता मामले विभाग और बीआईएस अधिनियम 2016 के तहत जारी अधिकृत मार्गदर्शन:"),

            # Common technical phrases
            ("Motorcycle helmets, two wheeler rider helmet, motorcycle safety gear", "मोटरसाइकिल हेलमेट, दोपहिया वाहन चालक हेलमेट, सुरक्षात्मक गियर"),
            ("Packaged Drinking Water, bottled drinking water, mineralized water bottle", "पैकेज्ड पेयजल, बोतलबंद पानी, मिनरलाइज्ड पानी की बोतल"),
            ("Impact absorption test, chin strap retention test, audibility test, peripheral vision test, penetration resistance test.", "प्रभाव अवशोषण परीक्षण (Impact absorption), चिन स्ट्रैप प्रतिधारण परीक्षण, श्रव्यता परीक्षण, परिधीय दृष्टि परीक्षण, प्रवेश प्रतिरोध परीक्षण।"),
            ("Microbiological safety (E. coli, coliform, yeast and mould), heavy metals (lead, cadmium, arsenic), pesticide residues, organoleptic parameters, total dissolved solids.", "सूक्ष्मजीव सुरक्षा (ई. कोलाई, कोलीफॉर्म), भारी धातुएं (सीसा, कैडमियम, आर्सेनिक), कीटनाशक अवशेष और कुल घुलित ठोस (TDS)।"),
            ("Compulsory under Road Transport Ministry QCO", "सड़क परिवहन एवं राजमार्ग मंत्रालय के QCO के तहत अनिवार्य"),
            ("Mandatory Certification under QCO", "गुणवत्ता नियंत्रण आदेश (QCO) के तहत अनिवार्य प्रमाणन")
        ]

        result = text
        for eng, hi in replacements:
            result = result.replace(eng, hi)

        # Chitchat response translation
        if "I am BIS-AI, an intelligent conversational assistant" in result or "Namaste!" in result:
            result = (
                "नमस्ते! मैं बीआईएस-एआई (BIS-AI) हूँ, जो भारतीय मानकों (Indian Standards), "
                "बीआईएस प्रमाणन योजनाओं, हॉलमार्किंग और परीक्षण प्रयोगशालाओं के लिए समर्पित एक आधिकारिक सहायक है। "
                "आज मैं मानकीकरण या बीआईएस सेवाओं में आपकी क्या सहायता कर सकता हूँ?"
            )

        return result

    @classmethod
    def _translate_to_tamil(cls, text: str) -> str:
        """
        Translates structured English response components into natural, authoritative Tamil.
        """
        replacements = [
            # Strict fallback & system messages
            ("Reliable BIS information could not be found for this query.", "இந்தக் கேள்விக்கான நம்பகமான அதிகாரப்பூர்வ பிஐஎஸ் (BIS) தகவல்களைக் கண்டறிய முடியவில்லை."),
            ("I could not find sufficient authoritative BIS information to answer this question reliably.", "இந்தக் கேள்விக்கான போதுமான அதிகாரப்பூர்வ பிஐஎஸ் (BIS) தகவல்களைக் கண்டறிய முடியவில்லை."),
            
            # Headings and labels
            ("• Technical Scope:", "• தொழில்நுட்ப நோக்கம்:"),
            ("• Certification Scheme:", "• சான்றிதழ் திட்டம்:"),
            ("• Key Testing Parameters:", "• முக்கிய பரிசோதனை அளவுருக்கள்:"),
            ("• Description:", "• விளக்கம்:"),
            ("• Application Procedure:", "• விண்ணப்ப நடைமுறை:"),
            ("• Concessions for MSMEs/Startups:", "• குறு, சிறு, நடுத்தர நிறுவனங்கள் / தொடக்க நிறுவனங்களுக்கான சலுகைகள்:"),
            ("• Accreditation:", "• அங்கீகாரம் (Accreditation):"),
            ("• Address:", "• முகவரி:"),
            ("• Disciplines:", "• துறைகள்:"),
            ("• Tested Products:", "• பரிசோதிக்கப்பட்ட தயாரிப்புகள்:"),
            ("• Contact:", "• தொடர்பு:"),
            
            # Key statuses & terms
            ("(Mandatory)", "(கட்டாயமானது)"),
            ("(Voluntary)", "(தன்னார்வமானது)"),
            ("Mandatory Certification", "கட்டாய சான்றிதழ்"),
            ("Voluntary Conformity", "தன்னார்வ இணக்கம்"),
            ("Standard BIS fee structure applies.", "வழக்கமான பிஐஎஸ் கட்டண அமைப்பு பொருந்தும்."),
            
            # Standard Titles
            ("Protective Helmets for Two Wheeler Riders - Specification", "இரு சக்கர வாகன ஓட்டிகளுக்கான பாதுகாப்பு தலைக்கவசங்கள் - விவரக்குறிப்பு"),
            ("Protective Helmets for Two Wheeler Riders", "இரு சக்கர வாகன ஓட்டிகளுக்கான பாதுகாப்பு தலைக்கவசங்கள்"),
            ("Packaged Drinking Water (Other Than Packaged Natural Mineral Water) - Specification", "பாட்டில் குடிநீர் (இயற்கை கனிம நீர் தவிர) - விவரக்குறிப்பு"),
            ("Packaged Drinking Water (Other than Packaged Natural Mineral Water)", "பாட்டில் குடிநீர் (இயற்கை கனிம நீர் தவிர)"),
            ("Drinking Water Specification", "குடிநீர் விவரக்குறிப்பு (குடிநீர் தரம்)"),
            ("Plugs and Socket-Outlets for Domestic and Similar Purposes - Specification", "வீட்டு மற்றும் ஒத்த நோக்கங்களுக்கான பிளக்குகள் மற்றும் சாக்கெட்டுகள் - விவரக்குறிப்பு"),
            ("Gold and Gold Alloys Jewellery/Artefacts - Fineness and Marking", "தங்கம் மற்றும் தங்கக் கலவை நகைகள்/கலைப்பொருட்கள் - தூய்மை மற்றும் முத்திரை"),
            ("Gold and Silver Jewellery / Artefacts", "தங்கம் மற்றும் வெள்ளி நகைகள் / கலைப்பொருட்கள்"),
            ("Secondary Cells and Batteries Containing Alkaline or Other Non-Acid Electrolytes - Safety", "கார அல்லது அமிலமற்ற எலக்ட்ரோலைட்டுகளைக் கொண்ட பேட்டரிகள் - பாதுகாப்பு"),
            ("Information Technology Equipment - Safety - General Requirements", "தகவல் தொழில்நுட்ப உபகரணங்கள் - பாதுகாப்பு - பொதுவான தேவைகள்"),
            ("Ordinary Portland Cement - Specification", "சாதாரண போர்ட்லேண்ட் சிமெண்ட் - விவரக்குறிப்பு"),
            ("Ordinary Portland Cement, 43 Grade", "சாதாரண போர்ட்லேண்ட் சிமெண்ட், 43 தரம்"),
            ("High Strength Deformed Steel Bars and Wires for Concrete Reinforcement", "கான்கிரீட் வலுவூட்டலுக்கான உயர் வலிமை எஃகு கம்பிகள்"),
            ("Safety of Toys - Mechanical and Physical Properties and Flammability", "பொம்மைகளின் பாதுகாப்பு - இயந்திர, இயற்பியல் பண்புகள் மற்றும் எரியும் தன்மை"),
            ("Safety of Household and Similar Electrical Appliances - Electric Iron", "வீட்டு மின்சாதனங்களின் பாதுகாப்பு - மின் இஸ்திரி பெட்டி"),
            ("Luminaires - Particular Requirements - Emergency Lighting", "விளக்குகள் - சிறப்புத் தேவைகள் - அவசர கால விளக்குகள்"),
            
            # Scheme descriptions and procedures
            ("Scheme I - Product Certification Scheme (ISI Mark)", "திட்டம் I - தயாரிப்பு சான்றிதழ் திட்டம் (ISI முத்திரை)"),
            ("Scheme II - Compulsory Registration Scheme (CRS)", "திட்டம் II - கட்டாயப் பதிவு திட்டம் (CRS)"),
            ("FMCS - Foreign Manufacturers Certification Scheme", "FMCS - வெளிநாட்டு உற்பத்தியாளர் சான்றிதழ் திட்டம்"),
            ("Scheme IV - Certificate of Conformity (CoC)", "திட்டம் IV - இணக்கச் சான்றிதழ் (CoC)"),
            ("Hallmarking Scheme for Precious Metals", "விலைமதிப்பற்ற உலோகங்களுக்கான ஹால்மார்க்கிங் திட்டம்"),
            ("Scheme I is the flagship product certification scheme of BIS that allows manufacturers to use the prestigious ISI Mark.", "திட்டம் I என்பது உற்பத்தியாளர்கள் புகழ்பெற்ற ஐஎஸ்ஐ (ISI) முத்திரையைப் பயன்படுத்த அனுமதிக்கும் பிஐஎஸ்-ன் முதன்மை சான்றிதழ் திட்டமாகும்."),
            ("1. Online submission of application on Manakonline portal with complete factory details, machinery, testing equipment, and test personnel.", "1. முழுமையான தொழிற்சாலை விவரங்கள், இயந்திரங்கள், ஆய்வு உபகரணங்களுடன் மணக்ஆன்லைன் (Manakonline) இணையதளத்தில் ஆன்லைனில் விண்ணப்பித்தல்."),
            ("2. Payment of application fee and pre-visit documentation check.", "2. விண்ணப்பக் கட்டணம் செலுத்துதல் மற்றும் ஆவணச் சரிபார்ப்பு."),
            ("3. Preliminary factory inspection by BIS auditor to verify manufacturing capability and testing facilities.", "3. உற்பத்தித் திறன் மற்றும் பரிசோதனை வசதிகளை ஆய்வு செய்ய பிஐஎஸ் அதிகாரியின் தொழிற்சாலை தணிக்கை."),
            ("4. Drawing of factory samples and testing in BIS or BIS-recognized laboratory.", "4. தொழிற்சாலையிலிருந்து மாதிரிகள் எடுக்கப்பட்டு பிஐஎஸ் அங்கீகாரம் பெற்ற ஆய்வகத்தில் பரிசோதித்தல்."),
            ("5. Grant of Licence upon successful verification.", "5. வெற்றிகரமான சரிபார்ப்பு மற்றும் திருப்திகரமான ஆய்வறிக்கைக்குப் பிறகு உரிமம் வழங்குதல்."),
            ("6. Periodic surveillance audits and market surveillance draws.", "6. அவ்வப்போது நடைபெறும் கண்காணிப்புத் தணிக்கைகள் மற்றும் சந்தை மாதிரி பரிசோதனைகள்."),
            ("20% rebate on application fee and annual minimum marking fee for Micro, Small and Medium Enterprises (MSMEs) and recognized Startups, plus 10% rebate for women entrepreneurs.", "குறு, சிறு மற்றும் நடுத்தர நிறுவனங்கள் (MSME) மற்றும் தொடக்க நிறுவனங்களுக்கு விண்ணப்பக் கட்டணம் மற்றும் ஆண்டு முத்திரைக் கட்டணத்தில் 20% தள்ளுபடி, பெண் தொழில்முனைவோருக்கு கூடுதல் 10% தள்ளுபடி."),
            
            # FAQ substantive translations
            ("HUID stands for 'Hallmark Unique Identification', which is a unique 6-digit alphanumeric code laser-engraved onto every single piece of hallmarked gold jewellery alongside the BIS triangle logo and purity fineness mark (e.g., 22K916). Consumers can verify gold purity by entering the 6-digit HUID into the 'Verify HUID' feature of the BIS CARE app. The app displays the Jeweller's registration number, Assaying and Hallmarking Centre (AHC) details, date of hallmarking, and exact purity karatage. Under government rules, no jeweller can sell hallmarked gold jewellery without a valid 6-digit HUID.",
             "HUID என்பது 'ஹால்மார்க் தனித்துவ அடையாள எண்' (Hallmark Unique Identification) என்பதைக் குறிக்கிறது. இது பிஐஎஸ் முக்கோண லோகோ மற்றும் தூய்மை முத்திரையுடன் (எ.கா. 22K916) ஒவ்வொரு தங்க நகையிலும் லேசர் மூலம் பொறிக்கப்பட்ட தனித்துவமான 6 இலக்க எண்ணெழுத்து குறியீடாகும். நுகர்வோர் பிஐஎஸ் கேர் (BIS CARE) செயலியில் உள்ள 'Verify HUID' அம்சத்தில் இந்த 6 இலக்க HUID-ஐ உள்ளிட்டு தங்கத்தின் தூய்மையை சரிபார்க்கலாம். இந்த செயலி நகைக்கடைக்காரரின் பதிவு எண், ஹால்மார்க்கிங் மைய விவரங்கள், தேசப்பட்ட தேதி மற்றும் சரியான காரட் தூய்மையைக் காட்டுகிறது. அரசின் விதிகளின்படி, முறையான 6 இலக்க HUID இல்லாமல் எந்தவொரு நகைக்கடையும் தங்க நகைகளை விற்க முடியாது."),
            
            ("Consumers can instantly verify the authenticity of an ISI Mark or CRS Registration using the official 'BIS CARE' mobile app (available on Android & iOS) or through the BIS Manakonline web portal. In the BIS CARE app, click on 'Verify License Details' and enter the 7-digit or 8-digit CML licence number printed underneath the ISI mark. If the number does not match the product or manufacturer, or if an inferior product is supplied, consumers can lodge a complaint directly on the 'Complaints' tab of the BIS CARE app or email complaints@bis.gov.in. BIS conducts investigation raids and seizes fake marked articles under penal provisions of the BIS Act, 2016.",
             "நுகர்வோர் அதிகாரப்பூர்வ 'BIS CARE' மொபைல் செயலி (Android & iOS) அல்லது மணக்ஆன்லைன் இணையதளம் மூலம் ஐஎஸ்ஐ (ISI) முத்திரை அல்லது சிஆர்எஸ் (CRS) பதிவின் நம்பகத்தன்மையை உடனடியாக சரிபார்க்கலாம். BIS CARE செயலியில் 'Verify License Details' என்பதைத் தேர்வுசெய்து, ஐஎஸ்ஐ முத்திரைக்கு கீழே அச்சிடப்பட்ட 7 அல்லது 8 இலக்க சிஎம்எல் (CML) உரிம எண்ணை உள்ளிடவும். எண் பொருந்தவில்லை என்றாலோ அல்லது தரமற்ற தயாரிப்பு வழங்கப்பட்டாலோ, BIS CARE செயலியில் உள்ள 'Complaints' பிரிவில் நேரடியாக புகார் அளிக்கலாம் அல்லது complaints@bis.gov.in என்ற மின்னஞ்சலில் புகார் தெரிவிக்கலாம். போலி முத்திரை கொண்ட பொருட்களை பிஐஎஸ் சட்டத்தின் கீழ் பறிமுதல் செய்து நடவடிக்கை எடுக்கப்படுகிறது."),
            
            # Certification Schemes across Standards
            ("Scheme I (ISI Mark Scheme) - Compulsory under Road Transport Ministry QCO", "திட்டம் I (ISI முத்திரை திட்டம்) - சாலைப் போக்குவரத்து அமைச்சகத்தின் QCO ஆணையின் கீழ் கட்டாயமானது"),
            ("Scheme I (ISI Mark Scheme) - Mandatory Certification under QCO", "திட்டம் I (ISI முத்திரை திட்டம்) - தரக் கட்டுப்பாட்டு ஆணையின் (QCO) கீழ் கட்டாய சான்றிதழ்"),
            ("Scheme I (ISI Mark Scheme) - Compulsory under Electrical Wires and Accessories QCO", "திட்டம் I (ISI முத்திரை திட்டம்) - மின் கம்பிகள் மற்றும் பாகங்கள் QCO-வின் கீழ் கட்டாயமானது"),
            ("Scheme II (Compulsory Registration Scheme - CRS) by MeitY", "திட்டம் II (கட்டாயப் பதிவுத் திட்டம் - CRS) MeitY அமைச்சகத்தின் கீழ்"),
            ("Scheme I (ISI Mark Scheme) - Compulsory under Toys (Quality Control) Order", "திட்டம் I (ISI முத்திரை திட்டம்) - பொம்மைகள் (தரக் கட்டுப்பாடு) ஆணையின் கீழ் கட்டாயமானது"),
            ("Scheme I (ISI Mark Scheme) - Compulsory under Cement (Quality Control) Order", "திட்டம் I (ISI முத்திரை திட்டம்) - சிமெண்ட் (தரக் கட்டுப்பாடு) ஆணையின் கீழ் கட்டாயமானது"),
            ("Scheme I (ISI Mark Scheme) - Compulsory under Steel & Steel Products QCO", "திட்டம் I (ISI முத்திரை திட்டம்) - எஃகு மற்றும் எஃகு பொருட்கள் QCO-வின் கீழ் கட்டாயமானது"),
            ("Hallmarking Scheme under BIS Act 2016 (Mandatory in notified districts)", "பிஐஎஸ் சட்டம் 2016-ன் கீழ் ஹால்மார்க்கிங் திட்டம் (அறிவிக்கப்பட்ட மாவட்டங்களில் கட்டாயமானது)"),
            ("Scheme I (ISI Mark Scheme) - Compulsory under Electrical Appliances QCO", "திட்டம் I (ISI முத்திரை திட்டம்) - வீட்டு மின்சாதனங்கள் QCO-வின் கீழ் கட்டாயமானது"),
            ("Scheme II (Compulsory Registration Scheme - CRS) / Scheme I (ISI Mark)", "திட்டம் II (கட்டாயப் பதிவுத் திட்டம் - CRS) / திட்டம் I (ISI முத்திரை)"),
            ("Voluntary Specification / Municipal Testing Standard", "தன்னார்வ விவரக்குறிப்பு / நகராட்சி பரிசோதனை தரநிலை"),
            ("Scheme I (ISI Mark Scheme)", "திட்டம் I (ISI முத்திரை திட்டம்)"),
            ("Compulsory under Road Transport Ministry QCO", "சாலைப் போக்குவரத்து அமைச்சகத்தின் QCO ஆணையின் கீழ் கட்டாயமானது"),
            ("Mandatory Certification under QCO", "தரக் கட்டுப்பாட்டு ஆணையின் (QCO) கீழ் கட்டாய சான்றிதழ்"),
            ("Mandatory across designated Indian districts", "அறிவிக்கப்பட்ட இந்திய மாவட்டங்களில் கட்டாயமானது"),
            ("Mandatory under CRS", "CRS-ன் கீழ் கட்டாயமானது"),
            ("Mandatory under Lighting & Luminaires QCO / CRS", "விளக்குகள் மற்றும் அவசர விளக்குகள் QCO / CRS-ன் கீழ் கட்டாயமானது"),
            ("Voluntary / Guidance for Public Water Suppliers", "பொது குடிநீர் விநியோகஸ்தர்களுக்கான தன்னார்வ / வழிகாட்டுதல்"),

            # Testing Parameters across Standards
            ("Turbidity, pH, total dissolved solids, hardness, iron, chlorides, nitrates, bacteriological test.", "கலங்கல் தன்மை (Turbidity), pH அளவு, மொத்த கரைந்த திடப்பொருட்கள் (TDS), கடினத்தன்மை, இரும்பு, குளோரைடு, நைட்ரேட் மற்றும் பாக்டீரியா பரிசோதனை."),
            ("Insulation resistance, electric strength, temperature rise test, making and breaking capacity, mechanical strength, resistance to heat and fire.", "மின்கடத்தா எதிர்ப்பு (Insulation resistance), மின் வலிமை, வெப்பநிலை உயர்வு சோதனை, இயந்திர வலிமை, வெப்பம் மற்றும் தீ எதிர்ப்பு."),
            ("Continuous charging at constant voltage, case stress at high ambient temperature, external short circuit, free fall, thermal abuse, crushing of cells.", "தொடர்ச்சியான சார்ஜிங் சோதனை, உயர் வெப்பநிலையில் அழுத்த சோதனை, வெளிப்புற ஷார்ட் சர்க்யூட், வீழ்ச்சி சோதனை, வெப்ப துஷ்பிரயோகம், பேட்டரி செல்கள் நசுக்கும் சோதனை."),
            ("Protection from electric shock, insulation resistance, energy hazard, earth continuity, clearance and creepage distances, flammability test.", "மின் அதிர்ச்சியிலிருந்து பாதுகாப்பு, மின்கடத்தா எதிர்ப்பு, ஆற்றல் ஆபத்து, பூமி தொடர்ச்சி, இடைவெளி மற்றும் க்ரீபேஜ் தூரம், எரியும் தன்மை சோதனை."),
            ("Mechanical and physical properties (sharp edges, small parts), flammability test, migration of certain elements (lead, cadmium, mercury toxicity).", "இயந்திர மற்றும் இயற்பியல் பண்புகள் (கூர்மையான விளிம்புகள், சிறிய பாகங்கள்), எரியும் தன்மை, நச்சு உலோகங்கள் கசிவு (ஈயம், காட்மியம், பாதரசம்)."),
            ("Compressive strength (3 days, 7 days, 28 days), setting time (initial and final), soundness (Le Chatelier), fineness (Blaine air permeability), chemical composition (loss on ignition, insoluble residue).", "அழுத்த வலிமை (3 நாட்கள், 7 நாட்கள், 28 நாட்கள்), உறையும் நேரம் (தொடக்க மற்றும் இறுதி), உறுதித்தன்மை (Le Chatelier), நுணுக்கம் (Blaine காற்று ஊடுருவல்), வேதியியல் கலவை."),
            ("0.2 percent proof stress/yield stress, tensile strength, percentage elongation, bend and rebend tests, chemical composition (carbon, sulfur, phosphorus).", "0.2 சதவீத ப்ரூஃப் ஸ்ட்ரெஸ் / ஈல்ட் ஸ்ட்ரெஸ், இழுவிசை வலிமை (Tensile strength), நீட்சி சதவீதம், வளைத்தல் மற்றும் மறுவளைத்தல் சோதனை, வேதியியல் கலவை."),
            ("Fire assay method (IS 1418), X-ray fluorescence (XRF) testing, fineness verification, 6-digit alphanumeric HUID engraving.", "ஃபயர் அசே முறை (IS 1418), எக்ஸ்-ரே ஃப்ளோரசன்ஸ் (XRF) சோதனை, தூய்மை சரிபார்ப்பு, 6 இலக்க எண்ணெழுத்து HUID லேசர் பொறித்தல்."),
            ("Fineness verification by titration/ICP-OES, hallmark logo stamping, sponsor mark.", "டைட்ரேஷன் (Titration) / ICP-OES மூலம் தூய்மை சரிபார்ப்பு, ஹால்மார்க் சின்னம் முத்திரை, ஸ்பான்சர் குறி."),
            ("Input power and current, heating and thermal stability, leakage current and electric strength, moisture resistance, drop resistance.", "உள்ளீட்டு சக்தி மற்றும் மின்னோட்டம், வெப்ப நிலைத்தன்மை, கசிவு மின்னோட்டம் மற்றும் மின் வலிமை, ஈரப்பதம் எதிர்ப்பு, கீழே விழுதல் எதிர்ப்பு."),
            ("Emergency operating duration test, battery charge and discharge cycle test, photometrics and luminous output, high temperature endurance, insulation resistance and dielectric strength, changeover operation voltage threshold.", "அவசர கால செயல்பாட்டு கால அளவு சோதனை, பேட்டரி சார்ஜ் மற்றும் டிஸ்சார்ஜ் சுழற்சி சோதனை, ஒளி வெளியீடு (Luminous output), உயர் வெப்பநிலை தாங்கும் திறன், மின்கடத்தா எதிர்ப்பு."),

            # Recommendation Explanation & Why Rationales
            ("This standard falls under a Mandatory Quality Control Order (QCO); compliance and BIS certification are required prior to commercial sale in India.", "இந்தத் தரநிலை கட்டாயத் தரக் கட்டுப்பாட்டு ஆணையின் (QCO) கீழ் வருகிறது; இந்தியாவில் வணிக ரீதியாக விற்பனை செய்வதற்கு முன் இணக்கமும் பிஐஎஸ் (BIS) சான்றிதழும் கட்டாயமாகும்."),
            ("This standard is currently Voluntary / Guidance specification. Certification is not legally mandated unless specified in buyer procurement requirements.", "இந்தத் தரநிலை தற்போது ஒரு தன்னார்வ / வழிகாட்டுதல் விவரக்குறிப்பாகும். வாங்குபவரின் கொள்முதல் தேவைகளில் குறிப்பிடப்பட்டாலன்றி சான்றிதழ் சட்டப்பூர்வமாக கட்டாயமில்லை."),
            ("Recommended because your product description aligns with the 'Mechanical Engineering / Automotive Safety' domain, matching technical parameters for", "பரிந்துரைக்கப்படுகிறது, ஏனெனில் உங்கள் தயாரிப்பு விளக்கம் 'மெக்கானிக்கல் இன்ஜினியரிங் / வாகனப் பாதுகாப்பு' துறையுடன் ஒத்துப்போகிறது, மேலும் இதற்கான தொழில்நுட்ப அளவுருக்கள்"),
            ("Recommended because your product description aligns with the 'Food and Agriculture / Water' domain, matching technical parameters for", "பரிந்துரைக்கப்படுகிறது, ஏனெனில் உங்கள் தயாரிப்பு விளக்கம் 'உணவு மற்றும் விவசாயம் / குடிநீர்' துறையுடன் ஒத்துப்போகிறது, மேலும் இதற்கான தொழில்நுட்ப அளவுருக்கள்"),
            ("Recommended because your product description aligns with the 'Civil & Environmental Engineering / Water Supply' domain, matching technical parameters for", "பரிந்துரைக்கப்படுகிறது, ஏனெனில் உங்கள் தயாரிப்பு விளக்கம் 'சிவில் மற்றும் சுற்றுச்சூழல் பொறியியல் / நீர் வழங்கல்' துறையுடன் ஒத்துப்போகிறது, மேலும் இதற்கான தொழில்நுட்ப அளவுருக்கள்"),
            ("Recommended because your product description aligns with the 'Electrotechnical / Electrical Accessories' domain, matching technical parameters for", "பரிந்துரைக்கப்படுகிறது, ஏனெனில் உங்கள் தயாரிப்பு விளக்கம் 'எலக்ட்ரோடெக்னிகல் / மின் உபகரணங்கள் மற்றும் பாகங்கள்' துறையுடன் ஒத்துப்போகிறது, மேலும் இதற்கான தொழில்நுட்ப அளவுருக்கள்"),
            ("Recommended because your product description aligns with the 'Electronics & Information Technology / Energy Storage' domain, matching technical parameters for", "பரிந்துரைக்கப்படுகிறது, ஏனெனில் உங்கள் தயாரிப்பு விளக்கம் 'மின்னணுவியல் மற்றும் தகவல் தொழில்நுட்பம் / ஆற்றல் சேமிப்பு' துறையுடன் ஒத்துப்போகிறது, மேலும் இதற்கான தொழில்நுட்ப அளவுருக்கள்"),
            ("Recommended because your product description aligns with the 'Electronics & Information Technology' domain, matching technical parameters for", "பரிந்துரைக்கப்படுகிறது, ஏனெனில் உங்கள் தயாரிப்பு விளக்கம் 'மின்னணுவியல் மற்றும் தகவல் தொழில்நுட்பம்' துறையுடன் ஒத்துப்போகிறது, மேலும் இதற்கான தொழில்நுட்ப அளவுருக்கள்"),
            ("Recommended because your product description aligns with the 'Safety of Consumer Products / Toys' domain, matching technical parameters for", "பரிந்துரைக்கப்படுகிறது, ஏனெனில் உங்கள் தயாரிப்பு விளக்கம் 'நுகர்வோர் தயாரிப்புகளின் பாதுகாப்பு / பொம்மைகள்' துறையுடன் ஒத்துப்போகிறது, மேலும் இதற்கான தொழில்நுட்ப அளவுருக்கள்"),
            ("Recommended because your product description aligns with the 'Civil Engineering / Building Materials' domain, matching technical parameters for", "பரிந்துரைக்கப்படுகிறது, ஏனெனில் உங்கள் தயாரிப்பு விளக்கம் 'சிவில் இன்ஜினியரிங் / கட்டுமானப் பொருட்கள் (சிமெண்ட்)' துறையுடன் ஒத்துப்போகிறது, மேலும் இதற்கான தொழில்நுட்ப அளவுருக்கள்"),
            ("Recommended because your product description aligns with the 'Metallurgical Engineering / Steel & Iron' domain, matching technical parameters for", "பரிந்துரைக்கப்படுகிறது, ஏனெனில் உங்கள் தயாரிப்பு விளக்கம் 'உலோகவியல் பொறியியல் / எஃகு மற்றும் இரும்பு (TMT)' துறையுடன் ஒத்துப்போகிறது, மேலும் இதற்கான தொழில்நுட்ப அளவுருக்கள்"),
            ("Recommended because your product description aligns with the 'Hallmarking / Precious Metals' domain, matching technical parameters for", "பரிந்துரைக்கப்படுகிறது, ஏனெனில் உங்கள் தயாரிப்பு விளக்கம் 'ஹால்மார்க்கிங் / விலைமதிப்பற்ற உலோகங்கள் (தங்கம் மற்றும் வெள்ளி)' துறையுடன் ஒத்துப்போகிறது, மேலும் இதற்கான தொழில்நுட்ப அளவுருக்கள்"),
            ("Recommended because your product description aligns with the 'Electrotechnical / Household Appliances' domain, matching technical parameters for", "பரிந்துரைக்கப்படுகிறது, ஏனெனில் உங்கள் தயாரிப்பு விளக்கம் 'எலக்ட்ரோடெக்னிகல் / வீட்டு மின்சாதனங்கள்' துறையுடன் ஒத்துப்போகிறது, மேலும் இதற்கான தொழில்நுட்ப அளவுருக்கள்"),
            ("Recommended because your product description aligns with the 'Electrotechnical / Lighting and Luminaires' domain, matching technical parameters for", "பரிந்துரைக்கப்படுகிறது, ஏனெனில் உங்கள் தயாரிப்பு விளக்கம் 'எலக்ட்ரோடெக்னிகல் / விளக்குகள் மற்றும் அவசர விளக்குகள்' துறையுடன் ஒத்துப்போகிறது, மேலும் இதற்கான தொழில்நுட்ப அளவுருக்கள்"),
            ("Recommended because your product description aligns with the", "பரிந்துரைக்கப்படுகிறது, ஏனெனில் உங்கள் தயாரிப்பு விளக்கம்"),
            ("domain, matching technical parameters for", "துறையுடன் ஒத்துப்போகிறது, மேலும் தொழில்நுட்ப அளவுருக்கள்"),
            ("based on keywords (domain specifications).", "முக்கிய வார்த்தைகளின் (துறை விவரக்குறிப்புகள்) அடிப்படையில்."),
            ("based on keywords", "முக்கிய வார்த்தைகளின் அடிப்படையில்"),
            ("Direct authoritative match for Indian Standard", "இந்திய தரநிலைக்கான நேரடி அதிகாரப்பூர்வ பதிவு"),
            ("in the authorized BIS catalog.", "அங்கீகரிக்கப்பட்ட பிஐஎஸ் (BIS) பட்டியலில்."),
            ("in the BIS catalog, covering", "பிஐஎஸ் பட்டியலில், உள்ளடக்கியது"),
            ("Retrieved record matches product domain and technical requirements for", "மீட்டெடுக்கப்பட்ட பதிவு தயாரிப்புத் துறை மற்றும் தொழில்நுட்பத் தேவைகளுடன் பொருந்துகிறது:"),
            ("under authorized BIS catalog.", "அங்கீகரிக்கப்பட்ட பிஐஎஸ் பட்டியலின் கீழ்."),
            ("Retrieved procedure covers official BIS regulations and application steps for", "மீட்டெடுக்கப்பட்ட நடைமுறை அதிகாரப்பூர்வ பிஐஎஸ் விதிமுறைகள் மற்றும் விண்ணப்ப படிகளை விவரிக்கிறது:"),
            ("Authorized testing facility accredited under ISO/IEC 17025 for product testing in", "தயாரிப்பு பரிசோதனைக்காக ISO/IEC 17025-ன் கீழ் அங்கீகரிக்கப்பட்ட அதிகாரப்பூர்வ பரிசோதனை மையம்:"),
            ("Authorized guidance issued under the BIS Act 2016 and Consumer Affairs Department regarding", "நுகர்வோர் விவகாரங்கள் துறை மற்றும் பிஐஎஸ் சட்டம் 2016-ன் கீழ் வழங்கப்பட்ட அதிகாரப்பூர்வ வழிகாட்டுதல்:"),

            # Common technical phrases
            ("Motorcycle helmets, two wheeler rider helmet, motorcycle safety gear", "இரு சக்கர வாகன தலைக்கவசங்கள், மோட்டார் சைக்கிள் பாதுகாப்பு சாதனம்"),
            ("Packaged Drinking Water, bottled drinking water, mineralized water bottle", "பாட்டில் குடிநீர், பாட்டிலில் அடைக்கப்பட்ட குடிநீர்"),
            ("Impact absorption test, chin strap retention test, audibility test, peripheral vision test, penetration resistance test.", "மோதல் உறிஞ்சுதல் சோதனை (Impact absorption), பட்டா தக்கவைப்பு சோதனை, கேட்கும் திறன் சோதனை, துளையிடல் எதிர்ப்பு சோதனை."),
            ("Microbiological safety (E. coli, coliform, yeast and mould), heavy metals (lead, cadmium, arsenic), pesticide residues, organoleptic parameters, total dissolved solids.", "நுண்ணுயிரி பாதுகாப்பு (E. coli, கோலிஃபார்ம்), கனரக உலோகங்கள் (ஈயம், காட்மியம், ஆர்சனிக்), பூச்சிக்கொல்லி எச்சங்கள் மற்றும் மொத்த கரைந்த திடப்பொருட்கள் (TDS)."),
            ("Compulsory under Road Transport Ministry QCO", "சாலைப் போக்குவரத்து அமைச்சகத்தின் QCO ஆணையின் கீழ் கட்டாயமானது"),
            ("Mandatory Certification under QCO", "தரக் கட்டுப்பாட்டு ஆணையின் (QCO) கீழ் கட்டாய சான்றிதழ்")
        ]

        result = text
        for eng, ta in replacements:
            result = result.replace(eng, ta)

        # Chitchat response translation
        if "I am BIS-AI, an intelligent conversational assistant" in result or "Namaste!" in result:
            result = (
                "வணக்கம்! நான் பிஐஎஸ்-ஏஐ (BIS-AI), இந்திய தரநிலைகள் (Indian Standards), "
                "சான்றிதழ் திட்டங்கள், ஹால்மார்க்கிங் மற்றும் பரிசோதனை ஆய்வகங்களுக்கான பிரத்யேக அதிகாரப்பூர்வ உதவியாளர். "
                "தரநிலைகள் அல்லது பிஐஎஸ் சேவைகள் குறித்து இன்று உங்களுக்கு எவ்வாறு உதவ முடியும்?"
            )

        return result


multilingual_service = MultilingualService
