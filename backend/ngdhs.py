import json
from astroquery.simbad import Simbad
import re


def clean_val(val):
    if isinstance(val, bytes):
        return val.decode('utf-8')
    return str(val)

def clean_name(name):
    return re.sub(r"\s+", " ", name).strip()


def build_messier_catalog():
    print("Building Messier catalog, please wait...")

    messier_list = [f"M{num}" for num in range(1, 111)]  # M1 through M110
    id_list = ",".join(f"'{name}'" for name in messier_list)

    query = f"""
    SELECT basic.main_id, basic.ra, basic.dec, basic.otype, ident.id AS messier_id
    FROM basic
    JOIN ident ON ident.oidref = basic.oid
    WHERE ident.id IN ({id_list})
    """

    table = Simbad.query_tap(query)

    targets = []
    for row in table:
        messier_id = clean_name(clean_val(row['messier_id']))
        name = clean_name(clean_val(row['main_id']))
        ra = clean_val(row['ra'])
        dec = clean_val(row['dec'])
        otype = clean_val(row['otype'])

        targets.append({
            "id": messier_id,
            "name": name,
            "ra": ra,
            "dec": dec,
            "type": otype
        })

    with open("targets.json", "w", encoding="utf-8") as f:
        json.dump(targets, f, indent=4)

    print(f"Successfully built Messier catalog with {len(targets)} objects, saved to targets.json.")


if __name__ == "__main__":
    build_messier_catalog()