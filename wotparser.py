#! /usr/bin/python

# This program scrapes data from the World of Tanks wiki 
# (wiki.worldoftanks.com) and dumps it in to a CSV file.
# Requires BeautifulSoup Python module:
# (http://www.crummy.com/software/BeautifulSoup/)
#
# Written by Tor5oBoy (iamtorsoboy@gmail.com)

# System imports
import datetime
import optparse
import re
import urllib2

# 3rd party imports
from bs4 import BeautifulSoup

class WotWikiParser(object):
    '''WotWikiParser is designed to scan, parse, and download tank data from
    the World of Tanks wiki. There are several methods available:
        - findVerion(): Call this to find the current version of WoT.
        - findTanks(): Used to find all vehicles from each country.
        - parseTankData(): Parse values for each tank.
        - docCreate(): Write the data out to a CSV file.'''

    def __init__(self):
        self._tank_types = ['Light Tanks', 'Medium Tanks', 'Heavy Tanks',
                            'Tank Destroyers', 'Self-Propelled Guns']

    @property
    def tank_types(self):
        '''Return tank_types via getter.'''
        return self._tank_types

    @tank_types.setter
    def tank_types(self, types):
        '''Return tank_types via getter.'''
        self._tank_types = types

    def findVersion(self, url, region='NA'):
        '''Find the current version of the game. An optional region can be
        specified. Available countries: Asia, EU, NA. Default: NA.'''
        # Initialize the soup.
        try:
            html = urllib2.urlopen(url).read()
        except:
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
        version = soup.find('b', text=re.compile(server)).find_next('a').contents[0]
        return version

    def findTanks(self, url):
        '''Find all the tanks! Scrapes the full list of tanks for each country
        passed and returns the list in an array. Expects a url in the form of:
        wiki.worldoftanks.com/USSR.'''
        # Initialize the soup.
        try:
            html = urllib2.urlopen(url).read()
        except:
            print 'Failed to open URL: ' + url
            exit(1)
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        #tank_types = ['Light Tanks', 'Medium Tanks', 'Heavy Tanks', 
        #              'Tank Destroyers', 'Self-Propelled Guns']
        # Grab the url for each tank type in the list above.
        for tank_type in self.tank_types:
            if soup.find('div', text=re.compile(tank_type)):
                tanks = soup.find('div', text=re.compile(tank_type)).find_next('ul').find_all('li')
                for t in tanks:
                    link = t.find('a').get('href')
                    links.append(link.strip('/'))
        return links

    def parseTankData(self, url):
        '''Parse tank data for url passed. Expects a url for a tank 
        (e.g. http://wiki.worldoftanks.com/T1_Cunningham). The method then uses
        BeautifulSoup to find values for various tank aspect, such as Hit
        Points and Hull Armor. A dictionary is returned with these values in
        the form of { "key" : "value" }.'''
        # Temp fix for SU-14 page since it is a pointer to two other pages. The
        # SU-14 was renamed to the SU-14-2.
        if re.match('(.+)SU-14$', url):
            url = url + '-2'
        # Initialize the soup.
        try:
            html = urllib2.urlopen(url).read()
        except:
            print 'Failed to open URL: ' + url
            exit(1)
        soup = BeautifulSoup(html, 'html.parser')
        info = soup.find('div', {'class':'Tank'})
        # Initialize all the values in case they don't appear in the HTML.
        tank_vals = {'premium':'No','tank_name':'N/A','tank_country':'N/A',
                     'tank_class':'N/A','tank_tier':'N/A','bt_min':'N/A',
                     'bt_max':'N/A','top_hp':'N/A','top_traverse':'N/A',
                     'top_pwr_rto':'N/A','top_hull_armor':'N/A',
                     'top_tur_armor':'N/A','top_dmg_min':'N/A',
                     'top_dmg_max':'N/A','top_penetration':'N/A',
                     'top_rof':'N/A','top_accuracy':'N/A','top_aim_time':'N/A',
                     'top_tur_traverse':'N/A','top_tur_elevation':'N/A',
                     'top_fire_chance':'N/A','top_view_range':'N/A',
                     'top_sig_range':'N/A'}
        # If we find data in the soup, start parsing it.
        if info:
            print 'Found tank at %s' % url
            # Parse the key/value pairs in the list and if there is a <div> tag
            # in the <span> use that, otherwise just use the span for the vals.
            categories = {'Rate of Fire':'top_rof',
                          'Traverse':'top_traverse',
                          'Accuracy':'top_accuracy',
                          'Aim time':'top_aim_time',
                          'Gun Traverse Speed':'top_tur_traverse',
                          'Turret Traverse':'top_tur_traverse',
                          'View Range':'top_view_range',
                          'Signal Range':'top_sig_range'}
            for k,v in categories.items():
                if info.find('th', text=re.compile(k)):
                    if info.find('th', text=re.compile(k)).find_next('span', 'top').div:
                        tank_vals[v] = info.find('th', text=re.compile(k)).find_next('span', 'top').div.contents[0]
                    else:
                        tank_vals[v] = info.find('th', text=re.compile(k)).find_next('span', 'top').contents[0]
            # Parse the key/value pairs in the list and use the <span> tag
            # to grab the values.
            categories2 = {'Hit Points':'top_hp',
                           'Power/Wt Ratio':'top_pwr_rto',
                           'Penetration':'top_penetration',
                           'Chance of Fire':'top_fire_chance'}
            for k,v in categories2.items():
                if info.find('th', text=re.compile(k)):
                    tank_vals[v] = info.find('th', text=re.compile(k)).find_next('span', 'top').contents[0]
            # Look for the tank name.
            if info.select('.mw-headline'):
                # Premium tanks have an <img> tag so we need to try to remove
                # that so we can just grab the name.
                tank_name = info.select('.mw-headline')[0]
                try:
                    tank_name.img.extract()
                except:
                    pass
                # Fix some character encoding.
                tank_name = tank_name.contents[0].replace(u'\xa0', u'')
                tank_name = tank_name.replace(u'\xe4', u'a')
                tank_name = tank_name.replace(u'\xe2', u'a')
                tank_name = tank_name.replace(u'\xf6', u'o')
                tank_vals['tank_name'] = tank_name
            # Find the tank country.
            if info.select('.NTC > tr > td'):
                tank_vals['tank_country'] = info.select('.NTC > tr > td')[0].contents[0]
            # Find the tank class (light, medium, td, etc.)
            if info.select('.NTC > tr > td'):
                tank_vals['tank_class'] = info.select('.NTC > tr > td')[1].contents[0]
            # Look for the tank tier, remove the word 'Tier' and replace the 
            # Roman numerals with numbers (helps with sorting).
            if info.select('.NTC > tr > td'):
                roms = {'I':'1', 'II':'2', 'III':'3', 'IV':'4', 'V':'5', 
                        'VI':'6', 'VII':'7', 'VIII':'8', 'IX':'9', 'X':'10'}
                tank_tier = info.select('.NTC > tr > td')[2].contents[0].strip('Tier ')
                if tank_tier in roms:
                    tank_tier = roms[tank_tier]
                tank_vals['tank_tier'] = tank_tier
            # Find the battle tiers. This really needs a more precise method
            # since there could be more <td> tags with background colors in
            # the page, but this works for now. Split them in to the high and
            # low values.
            if info.find_all('td', style=re.compile('background-color')):
                battle_tiers = info.find_all('td', style=re.compile('background-color'))
                tiers = []
                for b in battle_tiers:
                    tiers.append(int(b.contents[0]))
                tank_vals['bt_min'] = min(tiers)
                tank_vals['bt_max'] = max(tiers)
            # Find the hull armor values. Place a single quote in front so 
            # spreadsheet software doesn't try to interpret the data as a date.
            if info.find('th', text=re.compile('Hull Armor')):
                hull = info.find('th', text=re.compile('Hull Armor')).find_next('td')
                if re.match(r'^<td><span(.*)>(.+)</td>$', str(hull)):
                    tank_vals['top_hull_armor'] = '\'' + hull.find_next('span', 'top').contents[0]
                else:
                    tank_vals['top_hull_armor'] = '\'' + str(hull.contents[0])
            # Find the turret armor values. Place a single quote in front so 
            # spreadsheet software doesn't try to interpret the data as a date.
            if info.find('th', text=re.compile('Turret Armor')):
                turret = info.find('th', text=re.compile('Turret Armor')).find_next('td')
                if re.match(r'^<td><span(.*)>(.+)</td>$', str(turret)):
                    tank_vals['top_tur_armor'] = '\'' + turret.find_next('span', 'top').contents[0]
                else:
                    tank_vals['top_tur_armor'] = '\'' + str(turret.contents[0])
            # Grab the damage range and split it in to min and max values.
            if info.find('th', text=re.compile('Damage')):
                top_dmg = info.find('th', text=re.compile('Damage')).find_next('span', 'top').contents[0]
                if re.match('[0-9\.]+\-[0-9\.]+', top_dmg):
                    tank_vals['top_dmg_min'], tank_vals['top_dmg_max'] = top_dmg.split('-')
                else:
                    dmg_list = top_dmg.split('/')
                    dmg = []
                    for i in dmg_list:
                        if '.' in i:
                            dmg.append(float(i))
                        else:
                            dmg.append(int(i))
                    tank_vals['top_dmg_min'] = min(dmg)
                    tank_vals['top_dmg_max'] = max(dmg)
            # Grab the elevation values and reassemble them.
            if info.find('th', text=re.compile('Elevation Arc')):
                top_elev_min = info.find('th', text=re.compile('Elevation Arc')).find_next('span', 'top').contents[0]
                top_elev_max = info.find('th', text=re.compile('Elevation Arc')).find_next('span', 'top').contents[2]
                tank_vals['top_tur_elevation'] = str(top_elev_min) + str(top_elev_max)
        else:
            print 'Something went wrong or no info found at %s!' % url
        return tank_vals

    def docCreate(self, version, tank_data, outfile):
        '''Open file for writing and write the data. Expects the WoT version
        from findVersion(), the tank data from parseTankData(), and a file
        name to output to.'''
        sep = '\t'
        headers = ['Vehicle', 'Class', 'Tier', 'Min Battle Tier', 
                   'Max Battle Tier', 'Country', 'Power Ratio (hp/t)',
                   'Traverse Speed (d/s)', 'Hit Points', 'Hull Armor (mm)',
                   'Turret Armor (mm)', 'Min Dmg (HP)', 'Max Dmg (HP)',
                   'Rate of Fire (r/m)', 'Penetration (mm)', 'Aim Time (s)',
                   'Accuracy (m)', 'Gun/Turret Traverse (d/s)',
                   'View Range (m)', 'Signal Range (m)', 
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
            # Write the tank data in the order from the list.
            tank_vals = ['tank_name', 'tank_class', 'tank_tier', 'bt_min',
                         'bt_max', 'tank_country', 'top_pwr_rto', 
                         'top_traverse', 'top_hp', 'top_hull_armor',
                         'top_tur_armor', 'top_dmg_min', 'top_dmg_max',
                         'top_rof', 'top_penetration', 'top_aim_time',
                         'top_accuracy', 'top_tur_traverse', 'top_view_range',
                         'top_sig_range', 'top_tur_elevation']
            for tank in tank_data:
                for val in tank_vals:
                    f.write(str(tank[val]) + sep)
                f.write('\n')

if __name__ == '__main__':
    # Command line options
    usage_text = 'This program is designed to parse data from the World of ' + \
    'Tanks wiki. By default it will parse the data for all vehicles in all ' + \
    'countries. See the options below for parsing specific data. ' + \
    '\n\n' + \
    'Please note: Specifying vehicles is mutually exclusive from ' + \
    'specifying countries or vehicle types.'
    parser = optparse.OptionParser(usage=usage_text)
    parser.add_option('-c', '--countries', default=None, dest='countries',
        help='Available countries: USA, UK, Germany, France, USSR, China. ' +
        'Specify one or more in a comma separated list. Default: all.')
    parser.add_option('-f', '--file', default=None, dest='outfile',
        help='File write data to. Default: WoT_Tank_data.csv.')
    parser.add_option('-t', '--types', default=None, dest='types',
        help='Available types: Light, Medium, Heavy, TD, SPG. Specify ' +
        'one or more in a comma separated list. Default: all.')
    parser.add_option('-v', '--vehicles', default=None, dest='vehicles',
        help='Specify a vehicle name in quotes. Specify one or more in a ' +
        'comma separated list. Example: "Tiger II, T-34, WZ-120".')
    (options, args) = parser.parse_args()
    # Prevent using specific vehicles with types or countries.
    if options.vehicles and (options.types or options.countries):
        print 'Vehicles cannot be specified with countries or types.'
        exit(1)

    # Setup some default values.
    data = []
    outfile = 'WoT_Tank_Data.csv'
    countries = ['USA', 'UK', 'Germany', 'France', 'USSR', 'China']
    wiki = 'http://wiki.worldoftanks.com/'
    tank_types = {'Light':'Light Tanks', 'Medium':'Medium Tanks',
                  'Heavy':'Heavy Tanks', 'TD':'Tank Destroyers',
                  'SPG':'Self-Propelled Guns'}
    # Initialize the class.
    w = WotWikiParser()
    version = w.findVersion(wiki)
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
            data.append(w.parseTankData(wiki + v))
    else:
        # Parse countries array, find all tanks each that country's page, and
        # parse the data for those tanks.
        for country in countries:
            tank_list = w.findTanks(wiki + country)
            for tank in tank_list:
                print 'Looking for: ' + tank
                data.append(w.parseTankData(wiki + tank))
    # Write the compiled data to the document.
    print 'Writing data to document'
    w.docCreate(version, data, outfile)
