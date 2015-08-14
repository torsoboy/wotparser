#! /usr/bin/python

# This program scrapes data from the World of Tanks wiki 
# (wiki.wargaming.net) and dumps it in to a CSV file. Requires BeautifulSoup4
# Python module: (http://www.crummy.com/software/BeautifulSoup/)
#
# Written by Tor5oBoy (iamtorsoboy@gmail.com)

# System imports
import datetime
import optparse
import os
import re
import urllib2

# 3rd party imports
from bs4 import BeautifulSoup


class WotWikiParser(object):
    """WotWikiParser is designed to scan, parse, and download tank data from
    the World of Tanks wiki. There are several methods available:
        - findVersion(): Call this to find the current version of WoT.
        - findTanks(): Used to find all vehicles from each country.
        - parseTankData(): Parse values for each tank.
        - docCreate(): Write the data out to a CSV file."""

    def __init__(self):
        self._tank_types = ['Light Tanks', 'Medium Tanks', 'Heavy Tanks',
                            'Tank Destroyers', 'Self-Propelled Guns']

    @property
    def tank_types(self):
        """Return tank_types via getter."""
        return self._tank_types

    @tank_types.setter
    def tank_types(self, types):
        """Return tank_types via getter."""
        self._tank_types = types

    def findVersion(self, url, region='NA'):
        """Find the current version of the game. An optional region can be
        specified. Available countries: Asia, EU, NA. Default: NA."""
        # Initialize the soup.
        try:
            html = urllib2.urlopen(url).read()
        except urllib2.URLError:
            print 'Failed to open URL: ' + url
            exit(1)
        soup = BeautifulSoup(html, 'html.parser')
        # Based on the region passed, look for the version in the <a> tag.
        if 'NA' in region:
            server = 'NA Server:'
        elif 'EU' in region:
            server = 'EU Server:'
        elif 'Asia' in region:
            server = 'Asian Server:'
        wotver = soup.find('b', text=re.compile(server)).find_next('a').contents[0]
        return wotver

    def findTanks(self, url):
        """Find all the tanks! Scrapes the full list of tanks for each country
        passed and returns the list in an array. Expects a url in the form of:
        wiki.wargaming.net/en/ussr."""
        # Initialize the soup.
        try:
            html = urllib2.urlopen(url).read()
        except urllib2.URLError:
            print 'Failed to open URL: ' + url
            exit(1)
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        # Grab the url for each tank type in self.tank_types.
        for tank_type in self.tank_types:
            if soup.find('span', text=re.compile(tank_type)):
                tanks = soup.find('span', text=re.compile(tank_type)).find_next('ul').find_all('a')
                for t in tanks:
                    link = t.get('href')
                    links.append(link)
        return links

    def parseTankData(self, url):
        """Parse tank data for url passed. Expects a url for a tank 
        (e.g. http://wiki.wargaming.net/en/T1_Cunningham). The method then uses
        BeautifulSoup to find values for various tank aspect, such as Hit
        Points and Hull Armor. A dictionary is returned with these values in
        the form of { "key" : "value" }."""
        # Initialize the soup.
        try:
            html = urllib2.urlopen(url).read()
        except urllib2.URLError:
            print 'Failed to open URL: ' + url
            exit(1)
        info = BeautifulSoup(html, 'html.parser')
        # Initialize all the values in case they don't appear in the HTML.
        tank_vals = {'tank_status': 'Standard', 'tank_name': 'N/A',
                     'tank_country': 'N/A', 'tank_class': 'N/A',
                     'tank_tier': 'N/A', 'bt_min': 'N/A', 'bt_max': 'N/A',
                     'top_hp': 'N/A', 'top_traverse': 'N/A',
                     'top_pwr_rto': 'N/A', 'top_hull_armor': 'N/A',
                     'top_tur_traverse': 'N/A', 'top_fire_chance': 'N/A',
                     'top_view_range': 'N/A', 'top_sig_range': 'N/A',
                     'top_tur_armor': 'N/A', 'gun_dmg': 'N/A',
                     'gun_penetration': 'N/A', 'gun_rof': 'N/A',
                     'gun_accuracy': 'N/A', 'gun_elevation': 'N/A',
                     'gun_aim_time': 'N/A'}
        # If we find data in the soup, start parsing it.
        if info:
            print 'Found tank at %s' % url
            # Parse the key/value pairs in the list and if there is a <span> tag
            # that matches, find the previous 'top' <span> tag with the value.
            categories = {'Traverse': 'top_traverse',
                          'Gun Traverse Speed': 'top_tur_traverse',
                          'Turret Traverse': 'top_tur_traverse',
                          'Hit Points': 'top_hp',
                          'Power/Wt Ratio': 'top_pwr_rto',
                          'Chance of Fire': 'top_fire_chance',
                          'Turret Armor': 'top_tur_armor',
                          'Damage': 'gun_dmg',
                          'Penetration': 'gun_penetration',
                          'Elevation Arc': 'gun_elevation'}
            for k, v in categories.items():
                try:
                    val = info.find('span', text=re.compile(k)).find_previous('span', {'class': 'top'})
                except AttributeError:
                    val = None
                if val:
                    tank_vals[v] = val.text
            # Fix encoding to remove degree symbol
            tank_vals['gun_elevation'] = tank_vals['gun_elevation'].replace(u'\xb0', u'')
            # Parse the key/value pairs in the list and use the <span> tag,
            # <class> tag, <div> tag, and 'next_sibling' to get values.
            categories2 = {'Rate of Fire': 'gun_rof',
                           'Accuracy': 'gun_accuracy',
                           'Aim time': 'gun_aim_time',
                           'View Range': 'top_view_range',
                           'Signal Range': 'top_sig_range'}
            for k, v in categories2.items():
                try:
                    val = info.find('span', text=re.compile(k)).find_previous('span', {'class': 'top'}).find('div').next_sibling
                except AttributeError:
                    val = None
                if val:
                    tank_vals[v] = val.strip('\n')
            # Look for the tank name using <div> and <span> tags.
            try:
                tank_name = info.find('div', {'class': 'b-performance_border'}).find('span', {'class': 'mw-headline'})
            except AttributeError:
                tank_name = None
            if tank_name:
                # Premium, Gift, and Unavailable tanks have an <img> tag.
                # Remove tag to get tank name and status (premium, etc.).
                try:
                    img = tank_name.img.extract()
                except:
                    img = None
                # Fix some character encodings.
                tank_name = tank_name.text
                tank_name = tank_name.replace(u'\xa0', u'')
                tank_name = tank_name.replace(u'\xdf', u'B')
                tank_name = tank_name.replace(u'\xe4', u'a')
                tank_name = tank_name.replace(u'\xe2', u'a')
                tank_name = tank_name.replace(u'\xf6', u'o')
                tank_vals['tank_name'] = tank_name
                if img:
                    tank_vals['tank_status'] = img.get('alt', '')
            # Find the tank country, class, and tier.
            try:
                tank_data = info.find('div', {'class': 'b-performance_position'})
            except AttributeError:
                tank_data = None
            if tank_data:
                tank_vals['tank_country'], \
                tank_vals['tank_class'], \
                tank_vals['tank_tier'] = tank_data.text.split(' | ')
            # Look for the tank tier, remove the word 'Tier' and replace the
            # Roman numerals with numbers for sorting.
            roms = {'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5',
                    'VI': '6', 'VII': '7', 'VIII': '8', 'IX': '9', 'X': '10'}
            tank_vals['tank_tier'] = tank_vals['tank_tier'].strip('Tier ')
            if tank_vals['tank_tier'] in roms:
                tank_vals['tank_tier'] = roms[tank_vals['tank_tier']]
            # Find the MIN and MAX battle tiers in which tank fights.
            try:
                battle_tiers = info.find('span', {'class': 'b-battles-levels_interval'}).children
                tiers = []
                for bt in battle_tiers:
                    tiers.append(int(bt.text))
            except AttributeError:
                battle_tiers = None
            if battle_tiers:
                tank_vals['bt_min'] = min(tiers)
                tank_vals['bt_max'] = max(tiers)

            # Find the hull armor value using <span> tag and strip 'mm'.
            try:
                hull_armor = info.find('span', text=re.compile('Hull Armor')).find_previous('span', {'class': 't-performance_right'}).text
            except AttributeError:
                hull_armor = None
            if hull_armor:
                tank_vals['top_hull_armor'] = hull_armor.strip(' mm')
        else:
            print 'Something went wrong or no info found at %s!' % url
        # Add a single quote to the start of some values to tell spreadsheet to
        # treat the value as-is without trying to convert it to a date, etc.
        tank_vals['top_tur_armor'] = '\'' + tank_vals['top_tur_armor']
        tank_vals['gun_dmg'] = '\'' + tank_vals['gun_dmg']
        tank_vals['gun_penetration'] = '\'' + tank_vals['gun_penetration']
        tank_vals['top_hull_armor'] = '\'' + tank_vals['top_hull_armor']
        tank_vals['gun_elevation'] = '\'' + tank_vals['gun_elevation']
        return tank_vals

    def docCreate(self, version, tank_data, outfile):
        """Open file for writing and write the data. Expects the WoT version
        from findVersion(), the tank data from parseTankData(), and a file
        name to output to."""
        sep = '\t'
        headers = ['Vehicle Details', 'Defense',
                   'Offense']
        sub_headers = ['Vehicle', 'Class', 'Tier', 'Min Battle Tier', 
                       'Max Battle Tier', 'Country', 'Status',
                       'Power Ratio (hp/t)', 'Traverse Speed (d/s)',
                       'Gun/Turret Traverse (d/s)', 'View Range (m)',
                       'Signal Range (m)',  'Hit Points', 'Hull Armor (mm)',
                       'Turret Armor (mm)', 'Damage (HP)', 'Penetration (mm)',
                       'Rate of Fire (r/m)', 'Aim Time (s)', 'Accuracy (m)',
                       'Front Elevation (degrees)']
        with open(outfile, 'w') as f:
            # Write the WoT version.
            f.write('WoT Version:%s%s%s%s' % (sep, str(version), sep, sep))
            # Write the document creation date.
            now = datetime.datetime.now()
            d = now.strftime('%Y-%m-%d %H:%M')
            f.write('Created:%s\'%s\n' % (sep, str(d)))
            # Write the headers
            for h in headers:
                f.write(h + sep)
            f.write('\n')
            # Write the sub-headers
            for s in sub_headers:
                f.write(s + sep)
            f.write('\n')
            # Write the tank data in the order from the list.
            tank_vals = ['tank_name', 'tank_class', 'tank_tier', 'bt_min',
                         'bt_max', 'tank_country', 'tank_status', 'top_pwr_rto',
                         'top_traverse', 'top_tur_traverse', 'top_view_range',
                         'top_sig_range', 'top_hp', 'top_hull_armor',
                         'top_tur_armor', 'gun_dmg', 'gun_penetration',
                         'gun_rof', 'gun_aim_time', 'gun_accuracy',
                         'gun_elevation']
            for td in tank_data:
                for val in tank_vals:
                    try:
                        f.write(str(td[val]) + sep)
                    except UnicodeEncodeError:
                        print 'Failed to write: ', td[val]
                f.write('\n')

if __name__ == '__main__':
    # Command line options
    usage_text = 'This program is designed to parse data from the World of ' + \
        'Tanks wiki. By default it will parse the data for all vehicles in ' + \
        'all countries. See the options below for parsing specific data. ' + \
        '\n\n' + \
        'Please note: Specifying vehicles is mutually exclusive from ' + \
        'specifying countries or vehicle types.'
    parser = optparse.OptionParser(usage=usage_text)
    parser.add_option('-c', '--countries', default=None, dest='countries',
                      help='Available countries: USA, UK, Germany, France, ' +
                           'USSR, China, and Japan. Specify one or more in ' +
                           'a comma separated list. Default: all.')
    parser.add_option('-f', '--file', default=None, dest='outfile',
                      help='File to write data to. Default: WoT_Tank_data.csv.')
    parser.add_option('-t', '--types', default=None, dest='types',
                      help='Available types: Light, Medium, Heavy, TD, SPG. ' +
                           'Specify one or more in a comma separated list. ' +
                           'Default: all.')
    parser.add_option('-v', '--vehicles', default=None, dest='vehicles',
                      help='Specify a vehicle name in quotes. Specify one or ' +
                           'more in a comma separated list. Example: ' +
                           '"Tiger II, T-34, WZ-120".')
    (options, args) = parser.parse_args()
    # Prevent specifying vehicles and types or countries.
    if options.vehicles and (options.types or options.countries):
        print 'Vehicles cannot be specified with countries or types.'
        exit(1)

    # Setup some default values.
    data = []
    outfile = os.path.join(os.getcwd(), 'WoT_Tank_Data.csv')
    countries = ['USA', 'UK', 'Germany', 'France', 'USSR', 'China', 'Japan']
    wiki = 'http://wiki.wargaming.net'
    lang = '/en/'
    tank_types = {'Light': 'Light Tanks', 'Medium': 'Medium Tanks',
                  'Heavy': 'Heavy Tanks', 'TD': 'Tank Destroyers',
                  'SPG': 'Self-Propelled Guns'}
    # Initialize the class.
    w = WotWikiParser()
    # Get the WoT version from the wiki.
    version = w.findVersion(wiki + lang + 'World_of_Tanks')
    # If output file is specified on the CLI use that, otherwise use default.
    if options.outfile:
        outfile = options.outfile
    # If countries are specified on the CLI use those, otherwise use the
    # default values.
    if options.countries:
        countries = options.countries.split(',')
    # If vehicle types are specified on the CLI, then reset the tank_types
    # variable to those instead of the default.
    if options.types:
        types = options.types.split(',')
        w.tank_types = []
        for t in types:
            if t in tank_types:
                w.tank_types.append(tank_types[t])
            else:
                print 'Skipping invalid vehicle type: ' + t
    # If vehicle list is passed on CLI, use that list to parse data for
    # specified vehicles, otherwise parse the data for vehicles and
    # countries specified.
    if options.vehicles:
        vehicles = [options.vehicles]
        for v in vehicles:
            v = v.replace(' ', '_')
            data.append(w.parseTankData(wiki + lang + 'Tank:' + v))
    else:
        # Parse countries array, find all tanks each that country's page, and
        # parse the data for those tanks.
        for country in countries:
            country = lang + country
            tank_list = w.findTanks(wiki + country)
            for tank in tank_list:
                print 'Looking for: ' + tank
                data.append(w.parseTankData(wiki + tank))
    # Write the compiled data to the document.
    print 'Writing data to document: ' + outfile
    w.docCreate(version, data, outfile)
