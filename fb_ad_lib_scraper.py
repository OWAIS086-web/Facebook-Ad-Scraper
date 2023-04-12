import yaml
import tkinter as tk
import requests
import csv
import re
from tqdm import tqdm
from itertools import product

def save_to_yaml():
    input_value1 = input_entry1.get()
    input_value2 = input_entry2.get()
    data1 = {'access_token': input_value1}
    data2= {'keyword':input_value2}
    with open('token.yaml', 'w') as file:
        yaml.dump(data1, file)
        yaml.dump(data2, file)
        
       
    message_label.config(text="Data saved ")
    
def run_code():

 with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

 assert config['search_total'] % config['page_total'] == 0, \
    "search_total should be a multiple of page_total."
    
 with open('token.yaml', 'r') as f:
      token = yaml.safe_load(f)
 
 params = {
    'access_token': token['access_token'],
    'ad_type': token['keyword'],
    'ad_reached_countries': "['US']",
    'ad_active_status': config['ad_active_status'],
    'search_terms': config.get('search_terms'),
    'search_funding_entity': config.get('search_funding_entity'),
    'search_page_ids': config.get('search_page_ids'),
    'ad_spend': "ad_spend_euro > 10",
    'search_page_ids': ",".join(config.get('search_page_ids', [])),
    'fields': ",".join(config['query_fields']),
    'limit': config['page_total']
}

 REGIONS = set(config['regions'])
 DEMOS = set(product(config['demo_ages'], config['demo_genders']))

 f1 = open('fb_ads.csv', 'w')
 w1 = csv.DictWriter(f1, fieldnames=config['output_fields'],
                    extrasaction='ignore')
 w1.writeheader()

 f2 = open('fb_ads_demos.csv', 'w')
 w2 = csv.DictWriter(f2, fieldnames=config['demo_fields'],
                    extrasaction='ignore')
 w2.writeheader()

 f3 = open('fb_ads_regions.csv', 'w')
 w3 = csv.DictWriter(f3, fieldnames=config['region_fields'],
                    extrasaction='ignore')
 w3.writeheader()

 pbar = tqdm(total=config['search_total'], smoothing=0)

 for _ in range(int(config['search_total'] / config['page_total'])):
    r = requests.get('https://graph.facebook.com/v5.0/ads_archive',
                     params=params)
    
    
    data = r.json()
    
    for ad in data['data']:
        # The ad_id is encoded in the ad snapshot URL
        # and cannot be accessed as a normal field. (?!?!)

        ad_id = re.search(r'\d+', ad['ad_snapshot_url']).group(0)
        ad_url = 'https://www.facebook.com/ads/library/?id=' + ad_id

        # write to the unnested files
        demo_set = set()
        for demo in ad['demographic_distribution']:
            demo.update({'ad_id': ad_id})
            w2.writerow(demo)
            demo_set.add((demo['age'], demo['gender']))

        # Impute a percentage of 0
        # for demos with insufficient data
        unused_demos = DEMOS - demo_set
        for demo in unused_demos:
            w2.writerow({
                'ad_id': ad_id,
                'age': demo[0],
                'gender': demo[1],
                'percentage': 0
            })

        region_set = set()
        for region in ad['region_distribution']:
            region.update({'ad_id': ad_id})
            w3.writerow(region)
            region_set.add(region['region'])

        # Impute a percentage of 0
        # for states with insufficient data
        unused_regions = REGIONS - region_set
        for region in unused_regions:
            w3.writerow({
                'ad_id': ad_id,
                'region': region,
                'percentage': 0
            })

        ad.update({'ad_id': ad_id,
                   'ad_url': ad_url,
                   'impressions_min': ad['impressions']['lower_bound'],
               # WHEN LINE BELOW INCLUDED, CODE DOES NOT RUN
                   #'impressions_max': ad['impressions']['upper_bound'],
                   'spend_min': ad['spend']['lower_bound'],
                   'spend_max': ad['spend']['upper_bound'],
                   })

        w1.writerow(ad)
        pbar.update()

    # if we have scraped all the ads, exit
    if 'paging' not in data:
        break

    params.update({'after': data['paging']['cursors']['after']})

 f1.close()
 f2.close()
 f3.close()
 pbar.close()

window = tk.Tk()

window.geometry("650x250")
window.title("WELLCOME SIR!")
#Add a text label and add the font property to it
label= tk.Label(window, text= "FACEBOOK ADS SCRAPER", font=('Times New Roman bold',20))
label.pack(padx=10, pady=10)

label=tk.Label(window, text="Enter a token", font=('Times New Roman bold',15))
label.pack()

# Create an entry widget for the user to input a value
input_entry1 = tk.Entry(window)
input_entry1.pack()

labe2=tk.Label(window, text="Enter a keyword", font=('Times New Roman bold',15))
labe2.pack()

input_entry2 = tk.Entry(window)
input_entry2.pack()

# Create a button widget to save the input value to the YAML file
save_button = tk.Button(window, text="Enter ", command=save_to_yaml)
save_button.pack()

# Create a label widget to display a message after saving the data
message_label = tk.Label(window)
message_label.pack()


# Create a button widget and attach the 'run_code' function to its command
button = tk.Button(window, text="SCRAPE ADS DATA", command=run_code, width=20, height=2,padx=10, pady=20)

# Place the button widget in the window
button.pack()

# Start the tkinter mainloop
window.mainloop()