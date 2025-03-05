import csv

# Open input CSV and output TSV files
with (
    open("atlas_info_v3.csv", "r") as infile,
    open("atlas_dseg.tsv", "w", newline="") as outfile,
):
    # Create CSV reader and TSV writer
    reader = csv.DictReader(infile)
    writer = csv.writer(outfile, delimiter="\t")

    # Write header
    writer.writerow(["index", "name", "abbreviation", "color"])

    # Process each row
    for row in reader:
        # Convert RGB to hex color code
        color = "#{:02x}{:02x}{:02x}".format(
            int(row["red"]), int(row["green"]), int(row["blue"])
        )

        # Write selected columns to TSV
        writer.writerow([row["id"], row["name"], row["acronym"], color])
