import csv
import radix
import os
import heatmap


DATASETS_DIR = "datasets/bitcoin/"
OUTPUT_DIR = "frames/"
GEOLOCATION_DB = "datasets/geolocation/GeoLite2-City-Blocks-IPv4.csv"
GEOLOCATION_NAMES_DB = "datasets/geolocation/GeoLite2-City-Locations-en.csv"

CREATE_CSV = True
CREATE_HEATMAP = True

rtree = radix.Radix()

geonames = {}
# geolocation names database from https://dev.maxmind.com/geoip/geoip2/geoip2-city-country-csv-databases/
# format:
# geoname_id,locale_code,continent_code,continent_name,country_iso_code,country_name,subdivision_1_iso_code,subdivision_1_name,subdivision_2_iso_code,subdivision_2_name,city_name,metro_code,time_zone,is_in_european_union
with open(GEOLOCATION_NAMES_DB) as geolocation_names:
    # load in the file
    location_names = csv.reader(geolocation_names)

    # for each row
    for row in location_names:
        # if not first (header) row
        if row[0] != "geoname_id":
            geonames[row[0]] = row[3]

# Open GeoLite2 city dataset to geolocate IP addresses from https://dev.maxmind.com/geoip/geoip2/geoip2-city-country-csv-databases/
# Format:
# network,geoname_id,registered_country_geoname_id,represented_country_geoname_id,is_anonymous_proxy,is_satellite_provider,postal_code,latitude,longitude,accuracy_radius
with open(GEOLOCATION_DB) as geolocations:
    # load in the file
    locations = csv.reader(geolocations)

    # total rows rows
    total_count = 0

    # valid rows
    valid_count = 0

    # for each row in in the locations file
    for row in locations:
        # if not first row
        if row[0] != "network":

            # increment the total counter
            total_count += 1

            try:
                # try to parse a lat and long, radius, and country name
                network = row[0]
                lat = float(row[7])
                lng = float(row[8])
                radius = float(row[9])
                # search the geonames dictionary
                country = geonames[row[1]]
                # print("ip: {}, lat: {}, long: {}".format(row[0], lat, lng))

                # add the node to the tree, store the lat, long, radius, and country name alongside it
                rnode = rtree.add(network)
                rnode.data["lat"] = lat
                rnode.data["long"] = lng
                rnode.data["radius"] = radius
                rnode.data["country"] = country
                rnode.data["used"] = 0

                valid_count += 1
                if valid_count % 100000 == 0:
                    print("{}...".format(valid_count))

            except ValueError:
                # print("Invalid row lat: {}, long: {}".format(row[7], row[8]))
                pass

print("Generated radix tree with {} entries ({}% of rows were valid)".format(valid_count, (valid_count/total_count)*100))

# Open all the Rapid7 scan databases from https://opendata.rapid7.com/sonar.tcp/
# Formatted like:
# timestamp_ts,saddr,sport,daddr,dport,ipid,ttl
files = os.listdir(DATASETS_DIR)
count = 0
for file in files:
    if file.endswith(".csv"):
        count += 1

print("Parsing {} input dataset files".format(count))

# for each file in the directory
for file in files:
    if file.endswith(".csv"):
        unix_time = file.split("-")[3]
        # print(os.path.join("datasets", file))
        print("Parsing database from {}".format(unix_time))

        with open(os.path.join(DATASETS_DIR, file)) as bitcoin_scan:
            # read in the file
            scan = csv.reader(bitcoin_scan)

            # create output file
            output_path = open(os.path.join(OUTPUT_DIR, "output-" + file), "w")
            out_writer = csv.writer(output_path, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
            if CREATE_CSV:
                out_writer.writerow(['unix', 'ip', 'lat', 'long', 'radius'])
                out_writer.writerow(['ip', 'lat', 'long', 'radius', 'country'])

            # lat and long lists for heatmap generation
            lats = []
            lngs = []

            # number of invalid rows in database
            invalid_count = 0
            # number of valid rows in databse
            valid_count = 0
            # number of ip address matches
            matches = 0
            # number of duplicate resolutions
            duplicates = 0

            # row each row in the scan
            for row in scan:
                try:
                    # parse the row
                    ip = row[1]
                    # print("ip: {}".format(ip))

                    # search for the best match in the radix tree
                    rnode = rtree.search_best(ip)
                    if rnode:
                        # if there is a match, create an entry

                        if CREATE_CSV:
                            entry = [ip, rnode.data["lat"], rnode.data["long"], rnode.data["radius"], rnode.data["country"]]
                            out_writer.writerow(entry)

                        if CREATE_HEATMAP:
                            if rnode.data["used"] < 10:
                                lats.append(rnode.data["lat"])
                                lngs.append(rnode.data["long"])
                                rnode.data["used"] += 1
                            else:
                                duplicates += 1

                        matches += 1

                    valid_count += 1
                except ValueError:
                    # print("Invalid row lat: {}, long: {}".format(row[7], row[8]))
                    invalid_count += 1
                    pass

        print("Total {} valid rows and {} matches, {}% ({} invalid rows, {} dupliate entries)".format(valid_count, matches, (matches/valid_count)*100, invalid_count, duplicates))

        print("Generating heatmap...")
        output_path = os.path.join(OUTPUT_DIR, unix_time + "-" + str(matches)  + ".png")
        heatmap.generate(output_path, lngs, lats)