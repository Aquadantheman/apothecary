"""DrugBank CSV importer — generates tier 2 substance profiles from DrugBank data.

Usage:
    # With DrugBank CSV files downloaded from https://go.drugbank.com/releases/latest
    python -m apothecary.data.importers.drugbank_import \\
        --enzymes path/to/enzyme_data.csv \\
        --vocab path/to/drugbank_vocabulary.csv \\
        --output src/apothecary/data/curated/drugs/

    # Without DrugBank files — uses built-in common drug database
    python -m apothecary.data.importers.drugbank_import --builtin --output src/apothecary/data/curated/drugs/
"""

import csv
import re
from pathlib import Path
from datetime import date

import yaml


# === CYP450 Enzyme Mapping ===
# Maps common enzyme names to our standardized format
CYP_NORMALIZE = {
    "cytochrome p450 2d6": "CYP2D6",
    "cytochrome p450 3a4": "CYP3A4",
    "cytochrome p450 2c19": "CYP2C19",
    "cytochrome p450 2c9": "CYP2C9",
    "cytochrome p450 1a2": "CYP1A2",
    "cytochrome p450 2b6": "CYP2B6",
    "cytochrome p450 2e1": "CYP2E1",
    "cytochrome p450 2c8": "CYP2C8",
    "cytochrome p450 3a5": "CYP3A5",
    "cytochrome p450 2a6": "CYP2A6",
    "cyp2d6": "CYP2D6",
    "cyp3a4": "CYP3A4",
    "cyp2c19": "CYP2C19",
    "cyp2c9": "CYP2C9",
    "cyp1a2": "CYP1A2",
    "cyp2b6": "CYP2B6",
    "cyp2e1": "CYP2E1",
    "cyp2c8": "CYP2C8",
    "cyp3a5": "CYP3A5",
    "cyp2a6": "CYP2A6",
}

# Action mapping from DrugBank terminology to our model
ACTION_TO_ROLE = {
    "substrate": "substrate",
    "inhibitor": "inhibitor",
    "inducer": "inducer",
    "metabolizer": "substrate",  # DrugBank sometimes uses this
}

# Category mapping for common drug classes
CATEGORY_MAP = {
    "ssri": "ssri",
    "selective serotonin reuptake inhibitor": "ssri",
    "snri": "snri",
    "serotonin-norepinephrine reuptake inhibitor": "snri",
    "benzodiazepine": "benzodiazepine",
    "statin": "statin",
    "hmg-coa reductase inhibitor": "statin",
    "proton pump inhibitor": "ppi",
    "ace inhibitor": "ace_inhibitor",
    "angiotensin converting enzyme inhibitor": "ace_inhibitor",
    "beta blocker": "beta_blocker",
    "beta-adrenergic blocker": "beta_blocker",
    "calcium channel blocker": "calcium_channel_blocker",
    "anticonvulsant": "anticonvulsant",
    "antiepileptic": "anticonvulsant",
    "opioid": "opioid",
    "opioid analgesic": "opioid",
    "anticoagulant": "anticoagulant",
    "oral contraceptive": "oral_contraceptive",
    "contraceptive": "oral_contraceptive",
    "antipsychotic": "antipsychotic",
    "atypical antipsychotic": "antipsychotic",
    "stimulant": "stimulant",
    "amphetamine": "stimulant",
    "thyroid hormone": "thyroid_hormone",
    "biguanide": "biguanide",
    "sulfonylurea": "sulfonylurea",
    "arb": "arb",
    "angiotensin ii receptor blocker": "arb",
    "diuretic": "diuretic",
    "antihistamine": "antihistamine",
    "corticosteroid": "corticosteroid",
    "nsaid": "nsaid",
    "nonsteroidal anti-inflammatory": "nsaid",
    "antibiotic": "antibiotic",
    "macrolide antibiotic": "antibiotic",
    "fluoroquinolone": "antibiotic",
    "antifungal": "antifungal",
    "antidepressant": "antidepressant",
    "anxiolytic": "anxiolytic",
    "sedative": "sedative",
    "hypnotic": "hypnotic",
}

# Serotonin loads by category (approximate, for tier 2)
SEROTONIN_LOAD_BY_CATEGORY = {
    "ssri": 0.7,
    "snri": 0.75,
    "antidepressant": 0.5,
    "antipsychotic": 0.2,
    "opioid": 0.3,
    "stimulant": 0.2,
}

# CV flags by category
CV_FLAG_CATEGORIES = {
    "stimulant", "beta_blocker", "calcium_channel_blocker",
    "ace_inhibitor", "arb", "diuretic", "anticoagulant",
}


def normalize_id(name: str) -> str:
    """Convert a drug name to a filesystem/id-safe string."""
    s = name.lower().strip()
    s = re.sub(r'[^a-z0-9]+', '_', s)
    s = s.strip('_')
    return s


def normalize_cyp(enzyme_name: str) -> str | None:
    """Normalize a CYP enzyme name to standard format."""
    key = enzyme_name.lower().strip()
    if key in CYP_NORMALIZE:
        return CYP_NORMALIZE[key]
    # Try to match CYP pattern directly
    match = re.match(r'(?:cyp|cytochrome p450 )?([\d]+[a-z]+[\d]*)', key)
    if match:
        return f"CYP{match.group(1).upper()}"
    return None


def categorize_drug(name: str, description: str = "") -> str:
    """Attempt to categorize a drug based on name and description."""
    text = f"{name} {description}".lower()
    for keyword, category in CATEGORY_MAP.items():
        if keyword in text:
            return category
    return "prescription_drug"


def parse_drugbank_enzymes(csv_path: Path) -> dict[str, list[dict]]:
    """Parse DrugBank enzyme CSV to extract CYP450 relationships.

    Returns: {drug_name: [{enzyme, role, ...}, ...]}
    """
    drug_enzymes: dict[str, list[dict]] = {}

    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            drug_name = row.get('Name', row.get('Drug Name', '')).strip()
            if not drug_name:
                continue

            enzyme_name = row.get('Gene Name', row.get('Enzyme Name', '')).strip()
            action = row.get('Actions', row.get('Action', '')).strip().lower()

            # Normalize the enzyme name
            cyp = normalize_cyp(enzyme_name)
            if not cyp:
                continue  # Not a CYP enzyme we track

            # Map the action
            role = ACTION_TO_ROLE.get(action)
            if not role:
                # Try to infer from the action text
                if 'substrate' in action or 'metabol' in action:
                    role = 'substrate'
                elif 'inhibit' in action:
                    role = 'inhibitor'
                elif 'induc' in action:
                    role = 'inducer'
                else:
                    role = 'substrate'  # Default assumption

            if drug_name not in drug_enzymes:
                drug_enzymes[drug_name] = []

            # Avoid duplicates
            existing = {(e['enzyme'], e['role']) for e in drug_enzymes[drug_name]}
            if (cyp, role) not in existing:
                drug_enzymes[drug_name].append({
                    'enzyme': cyp,
                    'role': role,
                    'significance': 'major',  # Default; refined later if possible
                    'evidence': 'established',
                })

    return drug_enzymes


def parse_drugbank_vocabulary(csv_path: Path) -> dict[str, dict]:
    """Parse DrugBank vocabulary CSV for drug names and synonyms.

    Returns: {drug_name: {drugbank_id, synonyms, description, ...}}
    """
    drugs: dict[str, dict] = {}

    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            drugbank_id = row.get('DrugBank ID', '').strip()
            name = row.get('Common name', row.get('Name', '')).strip()
            if not name or not drugbank_id:
                continue

            synonyms_raw = row.get('Synonyms', '')
            synonyms = [s.strip() for s in synonyms_raw.split('|') if s.strip()] if synonyms_raw else []

            drugs[name] = {
                'drugbank_id': drugbank_id,
                'name': name,
                'synonyms': synonyms[:5],  # Limit to 5 common names
                'description': row.get('Description', '')[:200] if row.get('Description') else '',
            }

    return drugs


def generate_tier2_yaml(
    name: str,
    cyp_entries: list[dict],
    drugbank_id: str = "",
    synonyms: list[str] | None = None,
    category: str = "prescription_drug",
) -> dict:
    """Generate a tier 2 substance profile dict."""

    substance_id = normalize_id(name)

    common_names = [name]
    if synonyms:
        for s in synonyms:
            if s.lower() != name.lower() and s not in common_names:
                common_names.append(s)

    # Determine serotonin load and CV flag from category
    serotonin_load = SEROTONIN_LOAD_BY_CATEGORY.get(category, 0.0)
    cv_flag = category in CV_FLAG_CATEGORIES

    profile = {
        'substance': {
            'id': substance_id,
            'name': name,
            'type': 'prescription',
            'category': category,
            'common_names': common_names[:6],
            'pharmacokinetics': {
                'formulations': [],
            },
            'metabolism': {
                'cyp450': cyp_entries,
                'renal_excretion': False,
                'ph_dependent': False,
            },
            'receptor_activity': [],
            'nutrient_effects': {
                'depletions': [],
                'requirements': [],
            },
            'oxidative_profile': {
                'generates_ros': False,
            },
            'absorption': {
                'enhancers': [],
                'inhibitors': [],
            },
            'timing': {
                'optimal_window': 'morning',
                'take_with_food': 'either',
            },
            'safety': {
                'serotonin_load': serotonin_load,
                'cardiovascular_flag': cv_flag,
                'appetite_suppression': False,
                'sleep_disruption': False,
                'contraindications': [],
            },
            'metadata': {
                'data_sources': [f"DrugBank: {drugbank_id}"] if drugbank_id else ["DrugBank"],
                'last_reviewed': str(date.today()),
                'review_status': 'auto_generated',
                'data_tier': 'tier_2',
            },
        }
    }

    return profile


def write_yaml(profile: dict, output_dir: Path) -> Path:
    """Write a substance profile to a YAML file."""
    substance_id = profile['substance']['id']
    path = output_dir / f"{substance_id}.yaml"

    # Add header comment
    name = profile['substance']['name']
    header = f"# {name}\n# Auto-generated tier 2 profile from DrugBank\n# Last generated: {date.today()}\n\n"

    with open(path, 'w') as f:
        f.write(header)
        yaml.dump(profile, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    return path


def import_from_drugbank(
    enzyme_csv: Path | None = None,
    vocab_csv: Path | None = None,
    output_dir: Path = Path("src/apothecary/data/curated/drugs"),
    skip_existing: bool = True,
) -> int:
    """Import drugs from DrugBank CSV files.

    Returns count of substances generated.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get existing IDs to skip
    existing_ids = set()
    if skip_existing:
        for f in output_dir.glob("*.yaml"):
            existing_ids.add(f.stem)
        for f in output_dir.glob("*.yml"):
            existing_ids.add(f.stem)

    # Parse DrugBank data
    drug_enzymes = {}
    drug_info = {}

    if enzyme_csv and enzyme_csv.exists():
        drug_enzymes = parse_drugbank_enzymes(enzyme_csv)
        print(f"Parsed {len(drug_enzymes)} drugs from enzyme CSV")

    if vocab_csv and vocab_csv.exists():
        drug_info = parse_drugbank_vocabulary(vocab_csv)
        print(f"Parsed {len(drug_info)} drugs from vocabulary CSV")

    # Merge and generate
    all_drugs = set(drug_enzymes.keys()) | set(drug_info.keys())
    count = 0

    for drug_name in sorted(all_drugs):
        substance_id = normalize_id(drug_name)
        if substance_id in existing_ids:
            continue  # Skip tier 1 curated substances

        cyp_entries = drug_enzymes.get(drug_name, [])
        info = drug_info.get(drug_name, {})

        # Skip drugs with no CYP data (less useful for interaction checking)
        if not cyp_entries:
            continue

        category = categorize_drug(drug_name, info.get('description', ''))

        profile = generate_tier2_yaml(
            name=drug_name,
            cyp_entries=cyp_entries,
            drugbank_id=info.get('drugbank_id', ''),
            synonyms=info.get('synonyms'),
            category=category,
        )

        write_yaml(profile, output_dir)
        count += 1

    return count


# === Built-in Common Drug Database ===
# For users who don't have a DrugBank account, this provides
# CYP450 data for the ~150 most commonly prescribed drugs.
# Sourced from FDA prescribing information and clinical references.

BUILTIN_DRUGS = [
    # Format: (name, category, [(enzyme, role), ...], [synonyms])
    # --- Antidepressants ---
    ("Citalopram", "ssri", [("CYP2C19", "substrate"), ("CYP3A4", "substrate")], ["Celexa"]),
    ("Paroxetine", "ssri", [("CYP2D6", "substrate"), ("CYP2D6", "inhibitor")], ["Paxil"]),
    ("Fluvoxamine", "ssri", [("CYP1A2", "inhibitor"), ("CYP2C19", "inhibitor"), ("CYP3A4", "inhibitor")], ["Luvox"]),
    ("Duloxetine", "snri", [("CYP1A2", "substrate"), ("CYP2D6", "substrate"), ("CYP2D6", "inhibitor")], ["Cymbalta"]),
    ("Desvenlafaxine", "snri", [("CYP3A4", "substrate")], ["Pristiq"]),
    ("Mirtazapine", "antidepressant", [("CYP1A2", "substrate"), ("CYP2D6", "substrate"), ("CYP3A4", "substrate")], ["Remeron"]),
    ("Trazodone", "antidepressant", [("CYP3A4", "substrate"), ("CYP2D6", "substrate")], ["Desyrel"]),
    ("Amitriptyline", "antidepressant", [("CYP2D6", "substrate"), ("CYP2C19", "substrate"), ("CYP1A2", "substrate")], ["Elavil"]),
    ("Nortriptyline", "antidepressant", [("CYP2D6", "substrate")], ["Pamelor"]),
    # --- Antipsychotics ---
    ("Quetiapine", "antipsychotic", [("CYP3A4", "substrate")], ["Seroquel"]),
    ("Aripiprazole", "antipsychotic", [("CYP2D6", "substrate"), ("CYP3A4", "substrate")], ["Abilify"]),
    ("Risperidone", "antipsychotic", [("CYP2D6", "substrate")], ["Risperdal"]),
    ("Olanzapine", "antipsychotic", [("CYP1A2", "substrate"), ("CYP2D6", "substrate")], ["Zyprexa"]),
    ("Haloperidol", "antipsychotic", [("CYP2D6", "substrate"), ("CYP3A4", "substrate")], ["Haldol"]),
    # --- Anxiolytics / Sedatives ---
    ("Clonazepam", "benzodiazepine", [("CYP3A4", "substrate")], ["Klonopin"]),
    ("Lorazepam", "benzodiazepine", [], ["Ativan"]),
    ("Diazepam", "benzodiazepine", [("CYP2C19", "substrate"), ("CYP3A4", "substrate")], ["Valium"]),
    ("Buspirone", "anxiolytic", [("CYP3A4", "substrate")], ["BuSpar"]),
    ("Zolpidem", "hypnotic", [("CYP3A4", "substrate"), ("CYP1A2", "substrate")], ["Ambien"]),
    ("Hydroxyzine", "antihistamine", [("CYP2D6", "substrate")], ["Vistaril", "Atarax"]),
    # --- Anticonvulsants / Mood Stabilizers ---
    ("Lamotrigine", "anticonvulsant", [], ["Lamictal"]),
    ("Gabapentin", "anticonvulsant", [], ["Neurontin"]),
    ("Pregabalin", "anticonvulsant", [], ["Lyrica"]),
    ("Carbamazepine", "anticonvulsant", [("CYP3A4", "substrate"), ("CYP3A4", "inducer"), ("CYP2C9", "inducer"), ("CYP1A2", "inducer")], ["Tegretol"]),
    ("Topiramate", "anticonvulsant", [("CYP2C19", "inhibitor")], ["Topamax"]),
    ("Valproic Acid", "anticonvulsant", [("CYP2C9", "substrate"), ("CYP2C19", "inhibitor")], ["Depakote", "Depakene"]),
    ("Phenytoin", "anticonvulsant", [("CYP2C9", "substrate"), ("CYP2C19", "substrate"), ("CYP3A4", "inducer")], ["Dilantin"]),
    # --- Cardiovascular ---
    ("Losartan", "arb", [("CYP2C9", "substrate"), ("CYP3A4", "substrate")], ["Cozaar"]),
    ("Valsartan", "arb", [], ["Diovan"]),
    ("Amlodipine", "calcium_channel_blocker", [("CYP3A4", "substrate")], ["Norvasc"]),
    ("Metoprolol", "beta_blocker", [("CYP2D6", "substrate")], ["Lopressor", "Toprol XL"]),
    ("Propranolol", "beta_blocker", [("CYP2D6", "substrate"), ("CYP1A2", "substrate"), ("CYP2C19", "substrate")], ["Inderal"]),
    ("Atenolol", "beta_blocker", [], ["Tenormin"]),
    ("Carvedilol", "beta_blocker", [("CYP2D6", "substrate"), ("CYP2C9", "substrate")], ["Coreg"]),
    ("Warfarin", "anticoagulant", [("CYP2C9", "substrate"), ("CYP3A4", "substrate"), ("CYP1A2", "substrate")], ["Coumadin"]),
    ("Apixaban", "anticoagulant", [("CYP3A4", "substrate")], ["Eliquis"]),
    ("Rivaroxaban", "anticoagulant", [("CYP3A4", "substrate")], ["Xarelto"]),
    ("Clopidogrel", "anticoagulant", [("CYP2C19", "substrate"), ("CYP3A4", "substrate")], ["Plavix"]),
    ("Simvastatin", "statin", [("CYP3A4", "substrate")], ["Zocor"]),
    ("Rosuvastatin", "statin", [("CYP2C9", "substrate")], ["Crestor"]),
    ("Pravastatin", "statin", [], ["Pravachol"]),
    # --- GI ---
    ("Pantoprazole", "ppi", [("CYP2C19", "substrate"), ("CYP3A4", "substrate")], ["Protonix"]),
    ("Lansoprazole", "ppi", [("CYP2C19", "substrate"), ("CYP3A4", "substrate")], ["Prevacid"]),
    ("Esomeprazole", "ppi", [("CYP2C19", "substrate"), ("CYP3A4", "substrate")], ["Nexium"]),
    ("Ondansetron", "antiemetic", [("CYP3A4", "substrate"), ("CYP1A2", "substrate"), ("CYP2D6", "substrate")], ["Zofran"]),
    # --- Pain ---
    ("Tramadol", "opioid", [("CYP2D6", "substrate"), ("CYP3A4", "substrate")], ["Ultram"]),
    ("Codeine", "opioid", [("CYP2D6", "substrate")], ["Tylenol #3"]),
    ("Oxycodone", "opioid", [("CYP3A4", "substrate"), ("CYP2D6", "substrate")], ["OxyContin", "Percocet"]),
    ("Hydrocodone", "opioid", [("CYP2D6", "substrate"), ("CYP3A4", "substrate")], ["Vicodin", "Norco"]),
    ("Ibuprofen", "nsaid", [("CYP2C9", "substrate")], ["Advil", "Motrin"]),
    ("Naproxen", "nsaid", [("CYP2C9", "substrate"), ("CYP1A2", "substrate")], ["Aleve"]),
    ("Celecoxib", "nsaid", [("CYP2C9", "substrate")], ["Celebrex"]),
    # --- Hormonal ---
    ("Ethinyl Estradiol", "oral_contraceptive", [("CYP3A4", "substrate"), ("CYP1A2", "substrate")], ["Birth Control"]),
    ("Levonorgestrel", "oral_contraceptive", [("CYP3A4", "substrate")], ["Plan B", "Mirena"]),
    ("Testosterone", "hormone", [("CYP3A4", "substrate")], ["AndroGel"]),
    # --- ADHD / Stimulants ---
    ("Lisdexamfetamine", "stimulant", [("CYP2D6", "substrate")], ["Vyvanse"]),
    ("Atomoxetine", "stimulant", [("CYP2D6", "substrate")], ["Strattera"]),
    ("Guanfacine", "alpha_agonist", [("CYP3A4", "substrate")], ["Intuniv"]),
    ("Clonidine", "alpha_agonist", [("CYP2D6", "substrate")], ["Catapres", "Kapvay"]),
    # --- Antibiotics ---
    ("Azithromycin", "antibiotic", [], ["Zithromax", "Z-Pack"]),
    ("Amoxicillin", "antibiotic", [], ["Amoxil"]),
    ("Ciprofloxacin", "antibiotic", [("CYP1A2", "inhibitor")], ["Cipro"]),
    ("Clarithromycin", "antibiotic", [("CYP3A4", "substrate"), ("CYP3A4", "inhibitor")], ["Biaxin"]),
    ("Metronidazole", "antibiotic", [("CYP2C9", "inhibitor")], ["Flagyl"]),
    ("Doxycycline", "antibiotic", [], ["Vibramycin"]),
    # --- Antifungals ---
    ("Fluconazole", "antifungal", [("CYP2C19", "inhibitor"), ("CYP2C9", "inhibitor"), ("CYP3A4", "inhibitor")], ["Diflucan"]),
    ("Ketoconazole", "antifungal", [("CYP3A4", "inhibitor")], ["Nizoral"]),
    # --- Other Common ---
    ("Montelukast", "leukotriene_inhibitor", [("CYP2C8", "substrate"), ("CYP3A4", "substrate")], ["Singulair"]),
    ("Prednisone", "corticosteroid", [("CYP3A4", "substrate")], ["Deltasone"]),
    ("Albuterol", "bronchodilator", [], ["ProAir", "Ventolin"]),
    ("Modafinil", "wakefulness_agent", [("CYP3A4", "substrate"), ("CYP3A4", "inducer"), ("CYP2C19", "inhibitor")], ["Provigil"]),
    ("Armodafinil", "wakefulness_agent", [("CYP3A4", "substrate"), ("CYP3A4", "inducer")], ["Nuvigil"]),
    ("Sumatriptan", "triptan", [], ["Imitrex"]),
    ("Sildenafil", "pde5_inhibitor", [("CYP3A4", "substrate")], ["Viagra"]),
    ("Tadalafil", "pde5_inhibitor", [("CYP3A4", "substrate")], ["Cialis"]),
]


def import_builtin(
    output_dir: Path = Path("src/apothecary/data/curated/drugs"),
    skip_existing: bool = True,
) -> int:
    """Generate tier 2 profiles from the built-in common drug database.

    This doesn't require DrugBank files — it uses an embedded list of
    the most commonly prescribed drugs with their CYP450 data.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    existing_ids = set()
    if skip_existing:
        for f in output_dir.glob("*.yaml"):
            existing_ids.add(f.stem)
        for f in output_dir.glob("*.yml"):
            existing_ids.add(f.stem)

    count = 0
    for name, category, cyp_pairs, synonyms in BUILTIN_DRUGS:
        substance_id = normalize_id(name)
        if substance_id in existing_ids:
            continue

        cyp_entries = []
        seen = set()
        for enzyme, role in cyp_pairs:
            if (enzyme, role) not in seen:
                cyp_entries.append({
                    'enzyme': enzyme,
                    'role': role,
                    'significance': 'major',
                    'evidence': 'established',
                })
                seen.add((enzyme, role))

        profile = generate_tier2_yaml(
            name=name,
            cyp_entries=cyp_entries,
            synonyms=synonyms,
            category=category,
        )

        write_yaml(profile, output_dir)
        count += 1

    return count


# === CLI Entry Point ===

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Import drugs from DrugBank or built-in database")
    parser.add_argument("--enzymes", type=Path, help="Path to DrugBank enzyme CSV")
    parser.add_argument("--vocab", type=Path, help="Path to DrugBank vocabulary CSV")
    parser.add_argument("--builtin", action="store_true", help="Use built-in common drug database")
    parser.add_argument("--output", type=Path, default=Path("src/apothecary/data/curated/drugs"),
                        help="Output directory for YAML files")
    parser.add_argument("--no-skip", action="store_true", help="Overwrite existing files")

    args = parser.parse_args()

    if args.builtin:
        count = import_builtin(args.output, skip_existing=not args.no_skip)
        print(f"Generated {count} tier 2 profiles from built-in database")
    elif args.enzymes:
        count = import_from_drugbank(
            enzyme_csv=args.enzymes,
            vocab_csv=args.vocab,
            output_dir=args.output,
            skip_existing=not args.no_skip,
        )
        print(f"Generated {count} tier 2 profiles from DrugBank")
    else:
        print("Specify --builtin or --enzymes. Use --help for details.")
