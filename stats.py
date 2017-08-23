from bs4 import BeautifulSoup
from json import loads
from time import sleep
import csv
import requests

'''Profile tags for testing '''
# 9890JJJV, PRR2LUGO, 9VUQUGCP, PL2UV8J
# 8QU0PCQ

'''Clan tags for testing'''
# 2CQQVQCU, QYLPC9C, G9CL0QJ
# statsroyale.com/clan/2CQQVQCU

# Return player tag taking input as URL or player tag itself
def getTag(tag):
	if not tag.find('/') == -1:
		tag = tag[::-1]
		pos = tag.find('/')
		tag = tag[:pos]
		tag = tag[::-1]
	return tag

# Return parsed profile page using BS4
def parseURL(tag, element):
	tag = getTag(tag)
	if element == 'profile':
		link = 'http://statsroyale.com/profile/' + tag
	elif element == 'battles':
		link = 'http://statsroyale.com/matches/' + tag
	elif element == 'clan':
		link = 'http://statsroyale.com/clan/' + tag
	response = requests.get(link).text
	soup = BeautifulSoup(response, 'html.parser')
	return soup

# Refresh player battles
def refresh(tag, element):
	tag = getTag(tag)
	if element == 'profile':
		link = 'http://statsroyale.com/profile/' + tag + '/refresh'
	elif element == 'battles':
		link = 'http://statsroyale.com/matches/' + tag + '/refresh'
	elif element == 'clan':
		link = 'http://statsroyale.com/clan/' + tag + '/refresh'
	return requests.get(link)

# Return player's username and level
def getProfileBasic(tag):
	soup = parseURL(tag, element='profile')
	basic = soup.find('div', {'class':'statistics__userInfo'})
	stats = {}

	level = basic.find('span', {'class':'statistics__userLevel'}).get_text()
	stats[u'level'] = int(level)

	username = basic.find('div', {'class':'ui__headerMedium statistics__userName'}).get_text()
	username = username.replace('\n', '')[:-3].lstrip().rstrip()
	stats[u'username'] = username

	clan = basic.get_text().replace(level, '').replace(username, '').lstrip().rstrip()
	if clan == 'No Clan':
		stats[u'clan'] = None
	else:
		stats[u'clan'] = clan

	return stats


# Return highest_trophies, donations, etc
def getProfile(tag, refresh=False):
	if refresh:
		refresh(tag, element='profile')
		sleep(20.1)
	stats = getProfileBasic(tag)
	soup = parseURL(tag, element='profile')

	stats[u'profile'] = {}
	profile = soup.find('div', {'class':'statistics__metrics'})

	for div in profile.find_all('div', {'class':'statistics__metric'}):
		result = (div.find_all('div')[0].get_text().replace('\n', '')).lstrip().rstrip()
		try:
			result = int(result)
		except ValueError:
			pass
		item = div.find_all('div')[1].get_text().replace(' ', '_').lower()
		stats[u'profile'][item] = result
	return stats

# Get battles stats for both winner and loser
def getBattleSide(area, side):
	battles = {}
	side = area.find('div', {'class':'replay__player replay__' + side + 'Player'})
	try:
		battles[u'date'] = area.find('div', {'class': 'replay__date ui__smallText'}).get_text()
	except TypeError:
		print ("# date error")
		return
	battles[u'id'] = side.find('a', {'class':'ui__link'})['href'][9:]
	username = side.find('div', {'class':'replay__userName'}).get_text()
	battles[u'username'] = username.lstrip().rstrip()

	clan = side.find('div', {'class':'replay__clanName ui__mediumText'}).get_text()
	clan = clan.lstrip().rstrip()

	if clan == 'No Clan':
		battles[u'clan'] = None
	else:
		battles[u'clan'] = clan


	try:
		trophies = side.find('div', {'class':'replay__trophies'}).get_text()
		trophies = int(trophies.lstrip().rstrip())
	except AttributeError:
		print ("# 2v2")
		return

	battles[u'troops'] = {}

	troops = side.find_all('div', {'class':'replay__card'})
	for troop in troops:
		troop_name = troop.find('img')['src'].replace('/images/cards/full/', '')
		troop_name = troop_name[:-4]

		level = troop.find('span').get_text()
		level = int(level.replace('Lvl', ''))
		battles[u'troops'][troop_name] = level

	return battles

# Get battle summary
def getBattles(tag, refresh=True):
	tag = getTag(tag)
	if refresh:
		refresh(tag, element='battles')
		sleep(8.1)

	soup = parseURL(tag, element='battles')

	environment = soup.find_all('div', {'class':'replay__container'})
	battles = []

	for area in environment:
		battle = {}
		battle[u'type'] = area['data-type']

		outcome = area.find('div', {'class':'replay__win ui__headerExtraSmall'})

		if outcome == None:
			battle[u'outcome'] = 'defeat'
		else:
			battle[u'outcome'] = 'victory'

		result = area.find('div', {'class':'replay__recordText ui__headerExtraSmall'}).get_text()
		battle[u'result'] = {}

		wins = int(result.split(' ')[0])
		losses = int(result.split(' ')[-1])
		battle[u'result'][u'wins'], battle[u'result'][u'losses'] = wins, losses

		battle[u'left'] = getBattleSide(area, side='left')
		battle[u'right'] = getBattleSide(area, side='right')

		battles.append(battle)

	return battles

def getClanBasic(tag):
	soup = parseURL(tag, element='clan')
	clan = {}

	title = soup.find('div', {'class':'ui__headerMedium clan__clanName'}).get_text()
	clan[u'name'] = title.lstrip().rstrip()

	description = soup.find('div', {'class':'ui__mediumText'}).get_text()
	clan[u'description'] = description.lstrip().rstrip()

	clan_stats = soup.find_all('div', {'class':'clan__metricContent'})

	for div in clan_stats:
		item = div.find('div', {'class':'ui__mediumText'}).get_text()
		item = item.replace('/', '_').replace(' ', '_').lower()
		result = div.find('div', {'class':'ui__headerMedium'}).get_text()
		result = int(result)
		clan[item] = result

	return clan

# Work in progress
def getClan(tag, refresh=False):
	tag = getTag(tag)
	soup = parseURL(tag, element='clan')
	if refresh:
		refresh(tag, element='clan')
	clan = getClanBasic(tag)
	return clan

# Returns a list with each chest as a dictionary which contains chest name an counter.
def getChestCycle(tag, refresh=False):
	if refresh:
		refresh(tag, element='profile')
		sleep(20.1)
	chest_cycle={}
	chest_list=[]
	soup = parseURL(tag, element='profile')
	chests_queue = soup.find('div', {'class':'chests__queue'})
	chests = chests_queue.find_all('div')
	for chest in chests:
		if 'chests__disabled' in chest['class'][-1]:
			continue # Disabled chests are those chest that player has already got.
		elif 'chests__next' in chest['class'][-1]:
			chest_list.append({'next_chest':chest['class'][0][8:]}) # class=chests__silver chests__next
			continue
		elif 'chests__' in chest['class'][0]:
			print (chest['class'][0])
			chest_name = chest['class'][0][8:]
			counter=chest.find('span', {'class':'chests__counter'}).get_text()
			chest_list.append({'chest':chest_name, 'counter':counter})
	return chest_list

#stats = getProfile(tag='2GRG822L9', refresh=False)
#print(stats) # Bob PUJ8GRJP
#UVRRGRV
listIDs = []
rank = 0

def getData(personsTag):
	global rank
	rank = 0
	refresh(tag=personsTag, element='profile')
	sleep(1.1)
	refresh(tag=personsTag, element='battles')
	sleep(1.1)
	battles = getBattles(tag=personsTag, refresh=False)
	battlesLength = len(battles)
	for idx, x in enumerate(reversed(battles)):
	#s = list(x['right']['troops'].keys())
	#print(x['right']['trophies'], [str(item) for item in s])
		try:
			if "month" in x['left']['date'] or "year" in x['left']['date'] or "weeks" in x['left']['date'] or "days" in x['left']['date']:
				print ("# more than a week ago")
				continue
		except TypeError:
			break

		if idx == 0 and x['left']['trophies'] > 3000:
			with open('../weight-loss/tyler.csv', 'a') as newFile:
				newFileWriter = csv.writer(newFile)
				newFileWriter.writerow(['# Player Name: ' + x['left']['username'].encode('ascii', 'ignore').decode('ascii') + ' PlayerID: ' +  x['left']['id']])
				newFileWriter.writerow(['2017-07-26', rank,' ']) # rank should be zero starting out
			print ("# ", x['left']['username'])
			print ("2017-07-26, ",)
		elif x['left']['trophies'] < 3000:
			break

		if idx != battlesLength:
			if x['left']['trophies'] == list(reversed(battles))[idx - 1]['left']['trophies']:
				with open('../weight-loss/tyler.csv', 'a') as newFile:
					newFileWriter = csv.writer(newFile)
					newFileWriter.writerow(['# friendly battle ' + str(x['left']['trophies']) + ' ' + str(list(reversed(battles))[idx - 1]['left']['trophies'])])
				print ("# friendly battle ", x['left']['trophies'], list(reversed(battles))[idx - 1]['left']['trophies'])
			elif int(x['left']['trophies']) - int(list(reversed(battles))[idx - 1]['left']['trophies']) > 99 or int(list(reversed(battles))[idx - 1]['left']['trophies']) - int(x['left']['trophies']) > 99:
				print ("# battle difference greater than 99")
				break
			elif  x['left']['trophies'] > 3000:
				with open('../weight-loss/tyler.csv', 'a') as newFile:
					newFileWriter = csv.writer(newFile)
					if x[u'outcome'] == 'victory':
						rank += 25
						print ("2017-07-26, ", rank, ", ", ' '.join('{}{}'.format(unit, level) for unit, level in x['left']['troops'].items()))
						newFileWriter = csv.writer(newFile)
						newFileWriter.writerow(['2017-07-26', rank, ' '.join('{}{}'.format(unit, level) for unit, level in x['left']['troops'].items())])
						rank -= 25
						print ("2017-07-26, ", rank, ", ", ' '.join('{}{}'.format(unit, level) for unit, level in x['right']['troops'].items()))
						newFileWriter = csv.writer(newFile)
						newFileWriter.writerow(['2017-07-26', rank, ' '.join('{}{}'.format(unit, level) for unit, level in x['right']['troops'].items())])
					elif x[u'outcome'] == 'defeat':
						rank -= 25
						print ("2017-07-26, ", rank, ", ", ' '.join('{}{}'.format(unit, level) for unit, level in x['left']['troops'].items()))
						newFileWriter = csv.writer(newFile)
						newFileWriter.writerow(['2017-07-26', rank, ' '.join('{}{}'.format(unit, level) for unit, level in x['left']['troops'].items())])
						rank += 25
						newFileWriter = csv.writer(newFile)
						newFileWriter.writerow(['2017-07-26', rank, ' '.join('{}{}'.format(unit, level) for unit, level in x['right']['troops'].items())])
						print ("2017-07-26, ", rank, ", ", ' '.join('{}{}'.format(unit, level) for unit, level in x['right']['troops'].items()))



		if x['right']['id'] not in listIDs and x['right']['id'] not in personIDs:
			listIDs.append(x['right']['id'])
		else:
			print ("duplicate" , x['right']['id'])
	arr = [str(r) for r in listIDs]
	# print arr

	return arr
	#print "2017-07-26, ", x['left']['trophies'], ", ", ' '.join('{}{}'.format(unit, level) for unit, level in x['left']['troops'].items())

	# print " # ", ' '.join(x['left']['troops'])


def getEveryonesData(personsTag):
	global rank
	rank = 0
	refresh(tag=personsTag, element='profile')
	sleep(1.1)
	refresh(tag=personsTag, element='battles')
	sleep(1.1)
	battles = getBattles(tag=personsTag, refresh=False)
	battlesLength = len(battles)
	for idx, x in enumerate(reversed(battles)):
	#s = list(x['right']['troops'].keys())
	#print(x['right']['trophies'], [str(item) for item in s])
		try:
			if "month" in x['left']['date'] or "year" in x['left']['date'] or "weeks" in x['left']['date'] or "days" in x['left']['date']:
				print ("# more than a week ago")
				continue
		except TypeError:
			break

		if idx == 0 and x['left']['trophies'] > 3000:
			with open('../weight-loss/tyler.csv', 'a') as newFile:
				newFileWriter = csv.writer(newFile)
				newFileWriter.writerow(['# Player Name: ' + x['left']['username'].encode('ascii', 'ignore').decode('ascii') + ' PlayerID: ' +  x['left']['id']])
				newFileWriter.writerow(['2017-07-26', rank,' ']) # rank should be zero starting out
			print ("# ", x['left']['username'])
			print ("2017-07-26, ")
		elif x['left']['trophies'] < 3000:
			break

		if idx != battlesLength:
			if x['left']['trophies'] == list(reversed(battles))[idx - 1]['left']['trophies']:
				with open('../weight-loss/tyler.csv', 'a') as newFile:
					newFileWriter = csv.writer(newFile)
					newFileWriter.writerow(['# friendly battle ' + str(x['left']['trophies']) + ' ' + str(list(reversed(battles))[idx - 1]['left']['trophies'])])
				print ("# friendly battle ", x['left']['trophies'], list(reversed(battles))[idx - 1]['left']['trophies'])
			elif int(x['left']['trophies']) - int(list(reversed(battles))[idx - 1]['left']['trophies']) > 99 or int(list(reversed(battles))[idx - 1]['left']['trophies']) - int(x['left']['trophies']) > 99:
				print ("# battle difference greater than 99")
				break
			elif  x['left']['trophies'] > 3000:
				with open('../weight-loss/tyler.csv', 'a') as newFile:
					newFileWriter = csv.writer(newFile)
					if x[u'outcome'] == 'victory':
						rank += 25
						print ("2017-07-26, ", rank, ", ", ' '.join('{}{}'.format(unit, level) for unit, level in x['left']['troops'].items()))
						newFileWriter = csv.writer(newFile)
						newFileWriter.writerow(['2017-07-26', rank, ' '.join('{}{}'.format(unit, level) for unit, level in x['left']['troops'].items())])
						rank -= 25
						print ("2017-07-26, ", rank, ", ", ' '.join('{}{}'.format(unit, level) for unit, level in x['right']['troops'].items()))
						newFileWriter = csv.writer(newFile)
						newFileWriter.writerow(['2017-07-26', rank, ' '.join('{}{}'.format(unit, level) for unit, level in x['right']['troops'].items())])
					elif x[u'outcome'] == 'defeat':
						rank -= 25
						print ("2017-07-26, ", rank, ", ", ' '.join('{}{}'.format(unit, level) for unit, level in x['left']['troops'].items()))
						newFileWriter = csv.writer(newFile)
						newFileWriter.writerow(['2017-07-26', rank, ' '.join('{}{}'.format(unit, level) for unit, level in x['left']['troops'].items())])
						rank += 25
						newFileWriter = csv.writer(newFile)
						newFileWriter.writerow(['2017-07-26', rank, ' '.join('{}{}'.format(unit, level) for unit, level in x['right']['troops'].items())])
						print ("2017-07-26, ", rank, ", ", ' '.join('{}{}'.format(unit, level) for unit, level in x['right']['troops'].items()))



def getBestCharacter(personsTag):
	refresh(tag=personsTag, element='profile')
	sleep(1.1)
	refresh(tag=personsTag, element='battles')
	sleep(1.1)
	battles = getBattles(tag=personsTag, event='all', refresh=False)
	for idx, x in enumerate(reversed(battles)):
		if "chr_balloon" in ' '.join(x['right']['troops']):
			if idx > 0:
				if battles[idx]['left']['trophies'] > 1000:
					if battles[idx]['left']['trophies'] < 7000:
						print ("# found")
						print  ("2017-07-26, ", battles[idx-1]['left']['trophies'])
						print  ("2017-07-26, ", x['left']['trophies'], ", ", ' '.join(x['right']['troops']))
					else:
						print ("# greater than or equal to 7000")
				else:
					print ("# less than 1000")
					next
		else:
			print ("# blah")


def mineData(playersTag):
	refresh(tag=playersTag, element='profile')
	sleep(1.1)
	refresh(tag=playersTag, element='battles')
	sleep(1.1)
	battles = getBattles(tag=playersTag, refresh=False)
	battlesLength = len(battles)
	for idx, x in enumerate(reversed(battles)):
		# Check if battle was within 48 hours
		try:
			if "month" in x['left']['date'] or "year" in x['left']['date'] or "weeks" in x['left']['date'] or "days" in x['left']['date']:
				print ("# more than a day ago")
				continue
			else:
				print ("Within 48 hours")
		except TypeError:
			break

		# TODO check minimum rank to account for skill level

		# Make sure it's a ladder battle
		if (battles[idx]['type'] != 'ladder'):
			print ("Battle is not a ladder battle")
			continue

		print(battles[idx])
		# left side
		leftPlayerID = battles[idx]['left']['id']
		leftPlayerCharacters = ' '.join('{}{}'.format(unit, level) for unit, level in x['left']['troops'].items())
		if (battles[idx]['outcome'] == 'victory'):
			winOrLose = 1
		elif (battles[idx]['outcome'] == 'defeat'):
			winOrLose = 0
		with open('./data/ClashRoyale.csv','a') as newFile:
			newFileWriter = csv.writer(newFile)
			newFileWriter.writerow([leftPlayerID, leftPlayerCharacters, winOrLose])

		# right side
		rightPlayersID = battles[idx]['right']['id']
		rightPlayerCharacters = ' '.join('{}{}'.format(unit, level) for unit, level in x['right']['troops'].items())
		with open('./data/ClashRoyale.csv','a') as newFile:
			newFileWriter = csv.writer(newFile)
			newFileWriter.writerow([rightPlayersID, rightPlayerCharacters, int(not winOrLose)])



with open('./data/ClashRoyale.csv','w') as newFile:
    newFileWriter = csv.writer(newFile)
    newFileWriter.writerow(['PlayerID', 'Characters', 'Win or Lose'])

mineData('2GRG822L9')

'''personIDs = ['JR2GYY2Q','R0CRRUVU', 'R99CVRYR', 'JQC8RLG8', 'JPR9RGGP', 'PCCJCV9U', 'JU2LP8QG', 'R02CPVG', '20RRGQQ02', 'QPQ9U9L2', 'JUJCVP9Y', '2J099YJ2R', 'QPL0VR2R', '20Q20QYCV', '90PYJPG8', 'RY202JP', '22Y8UJL08', 'VL9J8989', '20QRGV9PL', 'Y8PR0QU8', 'PR2YCUCQ', 'LJJ00GCG', 'GPPL0P99', 'RJPLVY08', '9J2G8G92', 'YQ0JUL0U']
for idx, x in enumerate(personIDs):
	#getBestCharacter(personIDs[idx])
	listIDs = getData(personIDs[idx])


print ("# Getting everyone else", personIDs)
print ("# ", listIDs)
for idx, x in enumerate(listIDs):
 	#refresh(listIDs[idx], element='profile')
	#refresh(listIDs[idx], element='battles')
	# getEveryonesData(listIDs[idx])
	getEveryonesData(listIDs[idx])
'''
#print(battles[0])
#print(battles[0]['result']['wins'])
#print(battles[0]['left']['troops']['skeleton_horde'])

#clan = getClan(tag='2CQQVQCU', refresh=False)
#print(clan)
#print(getChestCycle(tag='PL2UV8j', refresh=False))
