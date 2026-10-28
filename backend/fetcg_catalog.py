import json
from astroquery.simbad import Simbad
import astropy.io.votable

astropy.io.votable.conf.use_fast_converter = False


def clean_val(val):
    if isinstance(val, bytes):
        return val.decode('utf-8')
    return str(val)

def build_messier_catalog():
    print("Building Messier catalog, please wait...")
    custom_simbad = Simbad()
    custom_simbad.add_votable_fields('otype')

    messier_list = [f"M{num}" for num in range(1, 111)]
    print(f"Messier list: {messier_list}")
    table = custom_simbad.query_objects(messier_list)

    targets = []

    for i, row in enumerate(table):
        name = clean_val(row['MAIN_ID'])
        ra = clean_val(row['RA'])
        dec = clean_val(row['DEC'])
        otype = clean_val(row['OTYPE'])

        formatted_ra = ra.replace(" ", "h", 1).replace(" ", "m", 1) + "s"
        formatted_dec = dec.replace(" ", "d", 1).replace(" ", "m", 1) + "s"

        targets.append({
            "id": f"M{i + 1}",
            "name": name,
            "ra": formatted_ra,
            "dec": formatted_dec,
            "type": otype
        })

    with open("targets.json", "w", encoding="utf-8") as f:
        json.dump(targets, f, indent = 4)

    print("Successfully built Messier catalog and saved to targets.json.")


if __name__ == "__main__":
    build_messier_catalog()