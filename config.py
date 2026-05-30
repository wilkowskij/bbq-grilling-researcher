"""Curated BBQ/grilling sources and topic seeds.

The Tavily client uses BBQ_DOMAINS as an include_domains allowlist so the
corpus stays on pitmaster-grade material instead of generic food media.
"""

BBQ_DOMAINS = [
    "amazingribs.com",
    "meatchurch.com",
    "heygrillhey.com",
    "smokingmeatforums.com",
    "thesmokering.com",
    "bbqbrethren.com",
    "seriouseats.com",
    "mybackyardlife.com",
    "tasteofbbq.com",
    "grillmasteruniversity.com",
    "smokedbbqsource.com",
    "barbecuebible.com",
    "killerhogs.com",
    "atbbq.com",
    "pitmasterx.com",
    "thespruceeats.com",
    "texasmonthly.com",
    "bbqnews.com",
]

BBQ_NEWSLETTERS = [
    ("AmazingRibs Pitmaster", "https://amazingribs.com/newsletter"),
    ("Meathead's Pitmaster Club", "https://pitmaster.amazingribs.com"),
    ("Texas Monthly BBQ", "https://www.texasmonthly.com/newsletters/"),
    ("Smoked BBQ Source", "https://www.smokedbbqsource.com/"),
    ("Hey Grill Hey", "https://heygrillhey.com/"),
    ("Meat Church Weekly", "https://www.meatchurch.com/"),
]

WEEKLY_TOPICS = [
    "brisket bark and pellicle",
    "offset smoker fuel management",
    "pork shoulder injection vs dry brine",
    "competition rib glaze techniques",
    "Alabama white sauce variants",
    "Carolina vinegar mop sauce",
    "reverse sear vs sous vide steak",
    "wood pellet flavor differences",
    "Texas hot guts sausage recipes",
    "tri-tip Santa Maria style",
]

CONTRARIAN_LENSES = [
    "What does the conventional wisdom get wrong?",
    "Which pitmasters publicly disagree, and why?",
    "Is the gear/technique actually worth it, or is it cargo-cult BBQ?",
    "What is the evidence the dogma is based on, and does it hold up?",
]


# Map of credible pitmaster / source identifiers (lowercase, no spaces) ->
# their public Instagram handle. The brief is required to pick exactly ONE
# of these to feature; anything not in this map is rejected so we don't
# hallucinate fake @-tags into the caption.
KNOWN_PITMASTER_HANDLES = {
    "amazingribs": "@amazingribs",
    "meathead": "@amazingribs",
    "heygrillhey": "@heygrillhey",
    "susiebulloch": "@heygrillhey",
    "aaronfranklin": "@franklinbarbecue",
    "franklinbarbecue": "@franklinbarbecue",
    "meatchurch": "@meatchurch",
    "mattpittman": "@meatchurch",
    "malcomreed": "@howtobbqright",
    "howtobbqright": "@howtobbqright",
    "killerhogs": "@howtobbqright",
    "smokedbbqsource": "@smokedbbqsource",
    "chudsbbq": "@chudsbbq",
    "bradleyrobinson": "@chudsbbq",
    "kosmosq": "@kosmosq",
    "pitmasterx": "@pitmasterx",
    "rogerthat": "@pitmasterx",
    "barbecuebible": "@steven_raichlen",
    "stevenraichlen": "@steven_raichlen",
    "texasmonthly": "@texasmonthly",
    "seriouseats": "@seriouseats",
    "atbbq": "@atbbq",
    "bigpoppasmokers": "@bigpoppasmokers",
    "traeger": "@traegergrills",
    "weber": "@webergrills",
}
