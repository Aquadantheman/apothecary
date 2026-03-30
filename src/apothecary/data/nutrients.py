"""Nutrient knowledge base — maps nutrients to food sources, symptoms, and practical advice.

This is the bridge between clinical pharmacology and real life.
Instead of just "you're depleted in X," the system tells you
what to eat, what to watch for, and what to do about it.
"""


# Each nutrient maps to:
#   supplement: primary supplement recommendation
#   food_sources: ranked by bioavailability / practicality
#   symptoms: what deficiency actually feels like
#   lifestyle_tips: non-supplement interventions
#   notes: clinical context

NUTRIENT_PROFILES: dict[str, dict] = {
    "magnesium": {
        "supplement": "Magnesium glycinate 200-400mg in the evening",
        "food_sources": [
            "Pumpkin seeds (1 oz = 156mg, 37% DV)",
            "Dark chocolate (1 oz = 65mg)",
            "Spinach (1 cup cooked = 157mg)",
            "Almonds (1 oz = 80mg)",
            "Black beans (1 cup = 120mg)",
            "Avocado (1 medium = 58mg)",
            "Banana (1 medium = 32mg)",
        ],
        "symptoms": [
            "Muscle cramps or twitching",
            "Difficulty sleeping or restless legs",
            "Anxiety or irritability",
            "Headaches",
            "Fatigue despite adequate sleep",
        ],
        "lifestyle_tips": [
            "Epsom salt baths provide transdermal magnesium absorption",
            "Stress and stimulant use both accelerate magnesium depletion",
            "Evening supplementation supports sleep via GABA modulation",
            "Avoid taking with stimulants — separate by 8+ hours",
        ],
        "notes": "Glycinate form is best absorbed and least likely to cause GI issues. Citrate is cheaper but can cause loose stools. Oxide has poor bioavailability.",
    },

    "vitamin_c": {
        "supplement": "Vitamin C 500-1000mg daily (split doses for better absorption)",
        "food_sources": [
            "Red bell pepper (1 cup = 190mg, 211% DV)",
            "Kiwi (1 medium = 71mg)",
            "Strawberries (1 cup = 89mg)",
            "Broccoli (1 cup cooked = 101mg)",
            "Orange (1 medium = 70mg)",
            "Blueberries (1 cup = 14mg + anthocyanins)",
            "Kale (1 cup = 80mg)",
        ],
        "symptoms": [
            "Slow wound healing",
            "Frequent colds or infections",
            "Fatigue and low mood",
            "Easy bruising",
            "Rough or dry skin",
        ],
        "lifestyle_tips": [
            "Raw fruits/vegetables preserve more vitamin C than cooked",
            "Vitamin C enhances iron absorption — eat together",
            "Smoking depletes vitamin C rapidly",
            "Blueberries provide anthocyanins that scavenge the same ROS as supplemental antioxidants",
        ],
        "notes": "Water-soluble — excess is excreted. Split doses (2x 500mg) absorb better than single 1000mg dose.",
    },

    "folate": {
        "supplement": "Methylfolate (L-5-MTHF) 400-800mcg daily",
        "food_sources": [
            "Lentils (1 cup cooked = 358mcg, 90% DV)",
            "Spinach (1 cup cooked = 263mcg)",
            "Asparagus (1 cup = 268mcg)",
            "Chickpeas (1 cup = 282mcg)",
            "Avocado (1 whole = 163mcg)",
            "Broccoli (1 cup = 168mcg)",
            "Beets (1 cup = 136mcg)",
        ],
        "symptoms": [
            "Fatigue and weakness",
            "Brain fog or difficulty concentrating",
            "Irritability or low mood",
            "Mouth sores",
            "Shortness of breath",
        ],
        "lifestyle_tips": [
            "~40% of people have MTHFR variants that impair folic acid conversion — methylfolate bypasses this",
            "Always pair folate with B12 supplementation to avoid masking B12 deficiency",
            "Folate is critical for neurotransmitter synthesis (serotonin and dopamine both require it)",
            "SSRIs may work better with adequate folate — some psychiatrists add methylfolate to treatment-resistant depression",
        ],
        "notes": "Methylfolate is preferred over folic acid, especially for people on SSRIs/SNRIs. Some evidence suggests L-methylfolate augments antidepressant response.",
    },

    "vitamin_b12": {
        "supplement": "Methylcobalamin (B12) 1000mcg sublingual daily",
        "food_sources": [
            "Clams (3 oz = 84mcg, 3500% DV)",
            "Beef liver (3 oz = 71mcg)",
            "Salmon (3 oz = 4.8mcg)",
            "Eggs (1 large = 0.6mcg)",
            "Fortified nutritional yeast (1 tbsp = 2-4mcg)",
            "Milk (1 cup = 1.2mcg)",
        ],
        "symptoms": [
            "Numbness or tingling in hands/feet",
            "Fatigue and weakness",
            "Memory problems or brain fog",
            "Mood changes or depression",
            "Balance difficulties",
        ],
        "lifestyle_tips": [
            "Sublingual form bypasses GI absorption — important for people on PPIs or metformin",
            "Vegans and vegetarians are at high risk for B12 deficiency",
            "B12 deficiency can mimic or worsen depression and dementia",
            "PPIs reduce stomach acid needed to release B12 from food — supplement separately",
        ],
        "notes": "Methylcobalamin is the active coenzyme form. Cyanocobalamin is cheaper but requires conversion. Deficiency can cause irreversible nerve damage if untreated.",
    },

    "iron": {
        "supplement": "Iron bisglycinate 25-50mg (only if confirmed deficient by bloodwork)",
        "food_sources": [
            "Beef liver (3 oz = 5mg heme iron, well absorbed)",
            "Lentils (1 cup = 6.6mg non-heme iron)",
            "Spinach (1 cup cooked = 6.4mg, but low bioavailability)",
            "Pumpkin seeds (1 oz = 2.5mg)",
            "Dark chocolate (1 oz = 3.4mg)",
            "Tofu (1/2 cup = 3.4mg)",
            "Red meat (3 oz = 2.5mg heme iron)",
        ],
        "symptoms": [
            "Fatigue and weakness (most common)",
            "Pale skin, especially inner eyelids",
            "Cold hands and feet",
            "Shortness of breath during exercise",
            "Brain fog and poor concentration",
            "Restless leg syndrome",
        ],
        "lifestyle_tips": [
            "Pair iron-rich foods with vitamin C to dramatically boost absorption",
            "Separate iron from coffee, tea, and calcium by 2+ hours",
            "Cook in cast iron cookware — it leaches small amounts of absorbable iron into food",
            "Do NOT supplement without a serum ferritin test — excess iron is pro-oxidant and harmful",
        ],
        "notes": "Bisglycinate form is gentler on the stomach than ferrous sulfate. Heme iron (animal sources) absorbs 15-35%, non-heme iron (plant sources) absorbs 2-20%. Always confirm deficiency before supplementing.",
    },

    "sodium": {
        "supplement": "Usually not supplemented — dietary management preferred",
        "food_sources": [
            "Table salt (1/4 tsp = 575mg)",
            "Broth or bouillon",
            "Pickles and fermented vegetables",
            "Cheese",
            "Most people get adequate sodium from diet",
        ],
        "symptoms": [
            "Headache",
            "Nausea and fatigue",
            "Muscle cramps",
            "Confusion (severe hyponatremia)",
        ],
        "lifestyle_tips": [
            "SSRI/SNRI-induced hyponatremia is rare but serious — more common in elderly",
            "If experiencing new-onset headaches or confusion on an SSRI, get sodium levels checked",
            "Usually managed by your prescriber, not by supplementation",
        ],
        "notes": "SIADH-mediated hyponatremia from SSRIs/SNRIs is a clinical issue managed by physicians. Most people do NOT need to supplement sodium. Alert your prescriber if you experience symptoms.",
    },

    "coq10": {
        "supplement": "CoQ10 (ubiquinol form) 100-200mg with a fatty meal",
        "food_sources": [
            "Beef heart (3 oz = 113mg — richest food source)",
            "Sardines (3 oz = 5mg)",
            "Pork (3 oz = 3mg)",
            "Chicken thigh (3 oz = 1.4mg)",
            "Broccoli (1 cup = 0.5mg)",
            "Most dietary intake is far below therapeutic doses",
        ],
        "symptoms": [
            "Muscle pain or weakness (especially with statins)",
            "Fatigue",
            "Exercise intolerance",
        ],
        "lifestyle_tips": [
            "Ubiquinol form absorbs better than ubiquinone, especially over age 40",
            "Take with a meal containing fat — CoQ10 is fat-soluble",
            "If on a statin, start CoQ10 supplementation proactively",
            "CoQ10 is essential for mitochondrial energy production",
        ],
        "notes": "Statin-induced CoQ10 depletion contributes to the muscle pain (myopathy) that causes many people to stop statin therapy. Supplementation may help.",
    },

    "zinc": {
        "supplement": "Zinc picolinate or bisglycinate 15-30mg with food",
        "food_sources": [
            "Oysters (3 oz = 74mg, 673% DV — richest food source)",
            "Beef (3 oz = 5.3mg)",
            "Pumpkin seeds (1 oz = 2.2mg)",
            "Lentils (1 cup = 2.5mg)",
            "Cashews (1 oz = 1.6mg)",
            "Dark chocolate (1 oz = 0.9mg)",
        ],
        "symptoms": [
            "Frequent infections",
            "Loss of taste or smell",
            "Slow wound healing",
            "Hair loss",
            "Skin rashes",
        ],
        "lifestyle_tips": [
            "Take with food to avoid nausea",
            "Chronic zinc supplementation (>40mg/day) can deplete copper — consider a zinc/copper combo",
            "Separate from iron supplements by 2+ hours",
        ],
        "notes": "ACE inhibitors can increase zinc excretion. Zinc is important for immune function and wound healing.",
    },

    "calcium": {
        "supplement": "Calcium citrate 500mg (split doses, not more than 500mg at once)",
        "food_sources": [
            "Yogurt (1 cup = 415mg, 32% DV)",
            "Sardines with bones (3 oz = 325mg)",
            "Milk (1 cup = 300mg)",
            "Kale (1 cup cooked = 177mg)",
            "Tofu (calcium-set, 1/2 cup = 253mg)",
            "Almonds (1 oz = 76mg)",
        ],
        "symptoms": [
            "Muscle cramps",
            "Numbness or tingling",
            "Brittle nails",
            "Increased fracture risk (long-term)",
        ],
        "lifestyle_tips": [
            "Calcium citrate doesn't require stomach acid — better for people on PPIs",
            "Separate from iron, levothyroxine, and certain antibiotics by 2-4 hours",
            "Weight-bearing exercise is as important as calcium for bone health",
            "Vitamin D is required for calcium absorption — supplement both",
            "Split doses: body can only absorb ~500mg at a time",
        ],
        "notes": "PPI-induced calcium malabsorption is a real concern for long-term PPI users. Use calcium citrate (not carbonate) if on a PPI.",
    },

    "copper": {
        "supplement": "Copper bisglycinate 1-2mg daily (usually only needed if supplementing zinc >30mg/day)",
        "food_sources": [
            "Beef liver (3 oz = 12mg, 1333% DV)",
            "Dark chocolate (1 oz = 0.5mg)",
            "Cashews (1 oz = 0.6mg)",
            "Shiitake mushrooms (1 cup = 0.8mg)",
            "Lentils (1 cup = 0.5mg)",
        ],
        "symptoms": [
            "Fatigue and weakness",
            "Frequent infections",
            "Pale skin (from anemia)",
        ],
        "lifestyle_tips": [
            "Copper depletion is almost always caused by chronic zinc supplementation",
            "If taking zinc >30mg/day, add 1-2mg copper",
        ],
        "notes": "Rarely deficient on its own. Usually only an issue with chronic high-dose zinc supplementation.",
    },

    "dopamine": {
        "supplement": "L-tyrosine 500-1000mg in the morning (precursor to dopamine)",
        "food_sources": [
            "Chicken breast (3 oz = high tyrosine content)",
            "Turkey (high in tyrosine and tryptophan)",
            "Eggs (good source of tyrosine)",
            "Almonds and peanuts",
            "Avocado",
            "Bananas (contain L-DOPA in small amounts)",
            "Fava beans (contain L-DOPA)",
        ],
        "symptoms": [
            "Low motivation or apathy",
            "Difficulty concentrating",
            "Fatigue",
            "Mood flatness",
        ],
        "lifestyle_tips": [
            "Protein-rich breakfast provides tyrosine for dopamine synthesis",
            "Exercise increases dopamine receptor sensitivity",
            "Cold exposure (cold showers) acutely increases dopamine",
            "If taking 5-HTP chronically, it can deplete dopamine by competing for the AADC enzyme",
        ],
        "notes": "5-HTP without carbidopa can deplete dopamine over time. If supplementing 5-HTP, consider adding L-tyrosine in the morning (separate by 6+ hours).",
    },
}


def get_nutrient_profile(nutrient: str) -> dict | None:
    """Get the full profile for a nutrient, or None if unknown."""
    return NUTRIENT_PROFILES.get(nutrient.lower())


def get_food_sources(nutrient: str) -> list[str]:
    """Get food sources for a nutrient."""
    profile = NUTRIENT_PROFILES.get(nutrient.lower())
    return profile["food_sources"] if profile else []


def get_symptoms(nutrient: str) -> list[str]:
    """Get deficiency symptoms for a nutrient."""
    profile = NUTRIENT_PROFILES.get(nutrient.lower())
    return profile["symptoms"] if profile else []


def get_lifestyle_tips(nutrient: str) -> list[str]:
    """Get lifestyle tips for a nutrient."""
    profile = NUTRIENT_PROFILES.get(nutrient.lower())
    return profile["lifestyle_tips"] if profile else []
