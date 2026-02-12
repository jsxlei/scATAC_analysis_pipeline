import json


cluster_list = "/oak/stanford/groups/akundaje/ryanzhao/cardioid/clusters_index.txt"

modisco_dir = "https://mitra.stanford.edu/kundaje/ryanzhao/cardioid/modisco"

# Generate browser tracks in UW data hub format 
tracks = []

html = """<!DOCTYPE html>
<html>
    <head>
        <title>Cardioid Modisco Reports></title>
    </head>
    <body>
        <h1>Modisco Reports</h1>
"""

with open(cluster_list, "r") as f_cluster: 
    for cluster in f_cluster:
        cluster = cluster.strip()
        report_file = f"{modisco_dir}/{cluster}/modisco_report/motifs.html"
        html += f"        <p><a href={report_file}>{cluster}</a></p>\n"


html += """
    </body>
</html>
"""

with open("/oak/stanford/groups/akundaje/ryanzhao/cardioid/modisco_reports.html", "w") as f_out:
    f_out.write(html)