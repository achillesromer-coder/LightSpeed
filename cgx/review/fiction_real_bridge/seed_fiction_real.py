"""Build a bounded, bibliography-backed cross-world fixture. No external bulk hydration."""
from __future__ import annotations
from pathlib import Path
import json,sys
from bridge_engine import SCHEMA,ROOT,stable_review_id,compile_graph,resolve,travel
HERE=Path(__file__).resolve().parent
sources=[]
def source(id,url,role):
 sources.append({"id":id,"url":url,"role":role,"source_bytes_hydrated":False,
                 "sha256":None,"rights_note":"External metadata/reference link only; no publication text or imagery copied",
                 "admission":"review-candidate"})
source("film-transcript","https://transcripts.simpleremix.com/script.php/hackers-1995-TSV","scene dialogue cross-check")
source("retro-technical","https://retrocomputing.stackexchange.com/questions/10997/were-any-of-the-books-mentioned-in-this-scene-from-the-movie-hackers-real","historical identification; community evidence, not primary")
source("norton-catalog","https://books.google.com/books/about/The_Peter_Norton_Programmer_s_Guide_to_t.html?id=ta9QAAAAMAAJ","publisher/year bibliographic record")
source("orange-national-archive","https://nsarchive.gwu.edu/document/18466-national-security-archive-department-defense","DoD standard 1985")
source("bsd-freebsd","https://docs-archive.freebsd.org/doc/13.0-RELEASE/usr/local/share/doc/freebsd/en/books/handbook/bibliography-osinternals.html","FreeBSD bibliographic confirmation")
source("dragon-catalog","https://books.google.com/books?id=-4Q_AQAAIAAJ","1986 compilers title/authors")
source("nsc-red","https://www.nationalacademies.org/read/1581/chapter/7","Trusted Network Interpretation identification")
source("posix-red-jargon","https://retrocomputing.stackexchange.com/questions/10997/were-any-of-the-books-mentioned-in-this-scene-from-the-movie-hackers-real/11000","historic terminology and conflation, secondary")
source("klingon-institute","https://www.kli.org/about-klingon/klingon-history/","institutional documentation of actual spoken conlang")
source("hitchhiker-publisher","https://www.panmacmillan.com.au/9781743033258/","real published book")
source("hitchhiker-fiction","https://en.wikipedia.org/wiki/The_Hitchhiker%27s_Guide_to_the_Galaxy_%28fictional%29","distinct diegetic guide, encyclopedia secondary")
source("w3c-prov","https://www.w3.org/TR/prov-o/","external provenance ontology")
source("w3c-skos","https://www.w3.org/TR/skos-reference/","context-sensitive mapping distinctions")
source("wikidata-worlds","https://www.wikidata.org/wiki/Wikidata:WikiProject_Fictional_universes","fictional analog vs inspiration distinction")
nodes=[];m=[];edges=[];names={}
def node(key,title,kind,owner,source_ids,facets,aliases=()):
 n={"identity_key":key,"id":stable_review_id("node",key),"title":title,"kind":kind,
    "owner_domain":owner,"aliases":list(aliases),"source_ids":list(source_ids),
    "facets":facets,"admission_state":"proposed","canonical_object_minted":False}
 nodes.append(n);names[key]=n["id"];return n["id"]
def mention(key,context,label,source_ids,candidates=(),status="review-supported",aliases=(),notes=""):
 item={"identity_key":key,"id":stable_review_id("mention",key),"context_node":context,
       "label":label,"aliases":list(aliases),"source_ids":list(source_ids),
       "candidate_ids":list(candidates),"status":status,
       "notes":notes,"time_context":"fictional-film-scene-1995" if context==names["film:hackers-1995"] else "diegetic-reference"}
 m.append(item);names[key]=item["id"];return item["id"]
def edge(key,source_id,target_id,relation,refs,scope,epistemic="review-supported",owner="media",notes=""):
 edges.append({"identity_key":key,"id":stable_review_id("edge",key),"from":source_id,
              "to":target_id,"type":relation,"source_ids":list(refs),
              "claim_scope":scope,"epistemic_state":epistemic,"assertion_owner":owner,
              "admission_state":"proposed","authority_transfer":False,"equivalence":None,
              "notes":notes})
# Source-qualified concepts, not native objects.
film=node("film:hackers-1995","Hackers (1995)","creative_work","media",
          ["film-transcript"],{"empirical_work":True,"fictional_setting":True,"publication_year":1995},
          ["Hackers film","Hackers 1995"])
orange=node("standard:dod-5200.28-std-1985","Trusted Computer System Evaluation Criteria","documented_standard","standards",
            ["orange-national-archive"],{"empirical_work":True,"published_year":1985,"identifier":"DoD 5200.28-STD"},
            ["Orange Book","DoD security criteria"])
norton=node("book:norton-ibm-pc-1985","The Peter Norton Programmer's Guide to the IBM PC","real_work","bibliography",
            ["norton-catalog"],{"empirical_work":True,"published_year":1985,"isbn_10":"0914845462"},
            ["Pink-Shirt Book","Pink Shirt Book","Peter Norton IBM PC guide"])
bsd=node("book:leffler-design-4.3bsd-1989","The Design and Implementation of the 4.3BSD UNIX Operating System","real_work","bibliography",
         ["bsd-freebsd"],{"empirical_work":True,"published_year":1989,"isbn_10":"0201061961"},
         ["Devil Book","Daemon Book","Unix Bible"])
dragon86=node("book:aho-sethi-ullman-compilers-1986","Compilers: Principles, Techniques, and Tools","real_work","bibliography",
              ["dragon-catalog"],{"empirical_work":True,"published_year":1986,"isbn_10":"0201100886"},
              ["Dragon Book","Compiler Design","Red Dragon Book"])
dragon77=node("book:aho-ullman-principles-compiler-design-1977","Principles of Compiler Design","real_work","bibliography",
              ["retro-technical"],{"empirical_work":True,"published_year":1977,"match_note":"Different earlier book, shares Dragon Book nickname"},
              ["Green Dragon Book"])
tni=node("standard:ncsc-tg-005-1987","Trusted Network Interpretation of the Trusted Computer System Evaluation Criteria","documented_standard","standards",
         ["nsc-red"],{"empirical_work":True,"published_year":1987,"identifier":"NCSC-TG-005"},
         ["Red Book (NSA)","NSA Trusted Networks","Trusted Network Interpretation"])
posix=node("standard:ieee-1003.1-1990","IEEE 1003.1-1990 (POSIX)","documented_standard","standards",
           ["posix-red-jargon"],{"empirical_work":True,"published_year":1990,"identifier":"IEEE 1003.1-1990","scope":"nickname reference only"},
           ["Ugly Red Book That Won't Fit On A Shelf","POSIX Red Book"])
klingon=node("language:klingon-marc-okrands-conlang","Klingon (constructed language)","constructed_language","linguistics",
            ["klingon-institute"],{"fictional_origin":True,"real_world_usage":True,
            "spoken_by_humans":True,"linguistic_system":True,
            "not_evidence_of_fictional_species":True,"rights_and_grammar_access":"separate review"},
            ["Klingon language","tlhIngan Hol","Klingon"])
star_trek=node("fictional-franchise:star-trek","Star Trek franchise","creative_work","fiction",
               ["klingon-institute"],{"empirical_work":True,"fictional_setting":True},
               ["Star Trek"])
practice=node("practice:klingon-human-speakers","Documented human Klingon speaking and study","documented_practice","linguistics",
               ["klingon-institute"],{"empirical_activity":True,"performed_by_real_humans":True,
                "documented_by":"Klingon Language Institute","not_proof_of_inworld_species":True},
               ["Klingon speaker community","Speaking Klingon"])
guide_novel=node("book:adams-hitchhikers-guide-1979","The Hitchhiker's Guide to the Galaxy (published novel)","real_work","bibliography",
                ["hitchhiker-publisher"],{"empirical_work":True,"published_year":1979,
                "authored_by":"Douglas Adams","not_same_as_diegetic_guide":True},
                ["The Hitchhiker's Guide to the Galaxy","Hitchhiker's Guide novel"])
guide_inworld=node("fictional-entity:hitchhikers-electronic-guide","The Hitchhiker's Guide to the Galaxy (in-universe guide)","fictional_entity","fiction",
                   ["hitchhiker-fiction","hitchhiker-publisher"],{"fictional_origin":True,
                    "empirical_object":False,"real_printed_novel_is_distinct":True},
                   ["The Hitchhiker's Guide to the Galaxy","Guidebook in Hitchhiker's"])
# Six explicitly identified film slots.
green=mention("mention:hackers-books-green",film,"Green Book",["film-transcript","retro-technical"],
              status="unresolved",aliases=["international unix environments"],
              notes="Scene phrase may allude to UNIX/POSIX material; exact physical edition not verified.")
or_m=mention("mention:hackers-books-orange",film,"Orange Book",["film-transcript","retro-technical","orange-national-archive"],[orange],
             aliases=["computer security criteria","DoD Standards"])
pink=mention("mention:hackers-books-pink",film,"Pink-Shirt Book",["film-transcript","retro-technical","norton-catalog"],[norton],
             aliases=["IBM PC guide","pink shirt book"])
devil=mention("mention:hackers-books-devil",film,"Devil Book",["film-transcript","retro-technical","bsd-freebsd"],[bsd],
              aliases=["Unix Bible"])
dragon=mention("mention:hackers-books-dragon",film,"Dragon Book",["film-transcript","retro-technical","dragon-catalog"],[dragon86],
               aliases=["compiler design"])
red=mention("mention:hackers-books-red",film,"Red Book",["film-transcript","retro-technical","nsc-red","posix-red-jargon"],
            [tni,posix],status="ambiguous",aliases=["NSA trusted networks","Ugly Red Book"],
            notes="Film dialogue conflates two separate historical red-book referents.")
guide_mention=mention("mention:hitchhikers-fictional-guide",guide_novel,"Hitchhiker's Guide",["hitchhiker-fiction","hitchhiker-publisher"],
                      [guide_inworld],aliases=["The Hitchhiker's Guide to the Galaxy"])
# Cross-domain edges can refer to one object again without another mint.
for key,mention_id,target_id,refs in [
 ("edge:hackers-orange",or_m,orange,["film-transcript","orange-national-archive"]),
 ("edge:hackers-pink",pink,norton,["film-transcript","norton-catalog"]),
 ("edge:hackers-devil",devil,bsd,["film-transcript","bsd-freebsd"]),
 ("edge:hackers-dragon",dragon,dragon86,["film-transcript","dragon-catalog"]),
]:
 edge(key,mention_id,target_id,"FICTION_MENTIONS_REAL_WORK",refs,"screen_reference")
edge("edge:hackers-green-related-posix",green,posix,"RELATED_NOT_IDENTICAL",
     ["film-transcript","retro-technical"],"comparison","ambiguous",
     notes="Possible historical family, not an exact edition match.")
edge("edge:hackers-dragon-other-edition",dragon,dragon77,"RELATED_NOT_IDENTICAL",
     ["retro-technical"],"comparison","review-supported",
     notes="Earlier Dragon Book nickname applies to a different textbook.")
edge("edge:hackers-red-tni",red,tni,"FICTION_MENTIONS_CANDIDATE",
     ["film-transcript","nsc-red"],"screen_reference","ambiguous")
edge("edge:hackers-red-posix",red,posix,"FICTION_MENTIONS_CANDIDATE",
     ["film-transcript","posix-red-jargon"],"screen_reference","ambiguous")
edge("edge:klingon-star-trek",klingon,star_trek,"INSPIRED_BY",
     ["klingon-institute"],"fictional_world",
     notes="A functioning constructed language originated as a creative-work language.")
edge("edge:klingon-real-human-use",klingon,practice,"HAS_REAL_WORLD_PRACTICE",
     ["klingon-institute"],"real_world_practice","review-supported",
     owner="linguistics",notes="Real human learning/speaking is documented, separate from fictional species.")
edge("edge:hitchhikers-guide-mention",guide_mention,guide_inworld,"FICTION_EMBEDS_FICTIONAL_OBJECT",
     ["hitchhiker-fiction"],"fictional_world")
edge("edge:hitchhikers-distinct-real-novel",guide_inworld,guide_novel,"DIFFERENT_REFERENT",
     ["hitchhiker-fiction","hitchhiker-publisher"],"comparison",
     notes="Same title; distinct fictional in-world object and empirical published novel.")
doc={"schema":SCHEMA,"parent":ROOT,"authority":"REVIEW_ONLY","metadata_only":True,
     "native_admission":False,"no_new_canonical_root":True,
     "same_name_does_not_mean_same_identity":True,
     "sources":sources,"nodes":nodes,"mentions":m,"edges":edges,
     "policies":{"unverified_not_false":"A missing catalog match is a frontier, never proof of fictitiousness",
                "identity_one_per_referent":"One proposed entity identity can have many appearances, versions and domain projections",
                "cross_world_sameAs":"Forbidden by default; only typed contextual connections",
                "model_inferences":"Never promoted automatically",
                "language_threshold":"Fictional provenance and empirical language use may coexist",
                "binary_hydration":"None; metadata links only",
                "downstream_model_training":"Not licensed/authorised",
                "release":"Founder and source-owner review required",
                "provenance_namespace":"W3C PROV-O aligned; source locator not source-body digest"}}
g=compile_graph(doc)
out=HERE/"MIRROR_GRAPH_REVIEW_V2.json"
with out.open("x",encoding="utf-8") as f:json.dump(g,f,ensure_ascii=False,sort_keys=True,indent=2)
index={"schema":"CGX-FICTION-REAL-EXAMPLE-RESULTS/0.1","graph_sha256":g["graph_sha256"],
       "cases":{
        "orange_in_hackers":resolve(g,"Orange Book",context_id=film),
        "green_in_hackers":resolve(g,"Green Book",context_id=film),
        "red_in_hackers":resolve(g,"Red Book",context_id=film),
        "dragon_in_hackers":resolve(g,"Dragon Book",context_id=film),
        "hitchhikers_title_no_context":resolve(g,"The Hitchhiker's Guide to the Galaxy"),
        "klingon_real_language":resolve(g,"Klingon language"),
        "nonexistent_unverified_fixture":resolve(g,"Imaginary Theorem Manual No. 3"),
        "red_two-hop_travel":travel(g,red,max_hops=2)
       },"review_state":"NOT_NATIVE_ADMITTED"}
with (HERE/"RESOLUTION_EXAMPLES_V3.json").open("x",encoding="utf-8") as f:json.dump(index,f,ensure_ascii=False,sort_keys=True,indent=2)
print(json.dumps({"source_refs":len(sources),"distinct_entity_candidates":len(nodes),
                  "screen_and_story_mentions":len(m),"qualified_relations":len(edges),
                  "root":ROOT,"graph_sha256":g["graph_sha256"],
                  "red":index["cases"]["red_in_hackers"]["resolution"],
                  "green":index["cases"]["green_in_hackers"]["resolution"],
                  "hitchhikers_shared_name":index["cases"]["hitchhikers_title_no_context"]["resolution"],
                  "language":index["cases"]["klingon_real_language"]["candidates"][0]["facets"],
                  "native_mint":False},indent=2))