from colorfight import Colorfight
import time
import websockets
import random
from colorfight.constants import BLD_GOLD_MINE, BLD_ENERGY_WELL, BLD_FORTRESS, BLD_HOME

# Create a Colorfight Instance. This will be the object that you interact
# with.
game = Colorfight()
upgrade_home_flag = False
max_out_pace = False

def check_to_upgrade_home(home_cell):
	global game
	global upgrade_home_flag
	print("CHECKING IF CAN UPGRADE")
	print("home cell building level: %d" %home_cell.building.level)
	print("gold i will have: %d" %(game.me.gold + game.me.gold_source))
	print("energy I will have: %d" %(game.me.energy + game.me.energy_source))
	print("flag: %r" %upgrade_home_flag)
	if home_cell.building.level < 3 and game.me.gold + game.me.gold_source > home_cell.building.level * 1000 and game.me.energy + game.me.energy_source > home_cell.building.level * 1000:
		upgrade_home_flag = True
	


def upgrade_home(home_cell, cmd_list):
	global game
	global upgrade_home_flag

	if game.me.gold > home_cell.building.level * 1000 and game.me.energy > home_cell.building.level * 1000:
		c = game.game_map[home_cell.position]
		cmd_list.append(game.upgrade(home_cell.position))
		game.me.energy -= c.building.level * 1000
		game.me.gold -= c.building.level * 1000
		upgrade_home_flag = False

def choose_squares(cmd_list, atk_list):
	global game
	for cell in game.me.cells.values():
	# Check the surrounding position
		for pos in cell.position.get_surrounding_cardinals():
			# Get the MapCell object of that position
			c = game.game_map[pos]


def find_home_cell():
	global game
	for cell in game.me.cells.values():
		if cell.building.name == "home":
			print("FOUND HOME")
			print(cell.position)
			return cell
			

def choose_atk_by_rsc_sum(cmd_list, atk_list):
	global game

	rsc_queue = []
	temp_queue = []
	for cell in game.me.cells.values():
	# Check the surrounding position
		for pos in cell.position.get_surrounding_cardinals():
		# Get the MapCell object of that position
			c = game.game_map[pos]

			if c.owner != game.uid and c.position not in temp_queue and len(me.cells) < 900: 
				rsc_sum = c.natural_gold + c.natural_energy
				c_val = (c.attack_cost / rsc_sum) * 10000 + c.attack_cost
				item = (c_val, pos, c.attack_cost)
				rsc_queue.append(item)
				temp_queue.append(c.position)
				print("cell (%d,%d). n_gold: %d. n_eng: %d. atk_cost: %d" %(pos.x, pos.y, c.natural_gold, c.natural_energy, c.attack_cost))
				print(item)

	rsc_queue.sort(key=lambda tup: tup[0])
	no_atk_queue = []
	for cell in rsc_queue:
		pos = cell[1]
		c = game.game_map[pos]
		if c.attack_cost < game.me.energy:
			cmd_list.append(game.attack(pos, c.attack_cost))
			print("We are attacking ({}, {}) with {} energy".format(pos.x, pos.y, c.attack_cost + 3))
			game.me.energy = game.me.energy - c.attack_cost - 3
		else:
			no_atk_queue.append(cell)
			

	for my_cell in game.me.cells.values():
		if game.me.energy > 0:
			adj_enemy = False
			for adj_c in my_cell.position.get_surrounding_cardinals():
				c2 = game.game_map[adj_c]
				if c2.owner != game.uid:
					adj_enemy = True
			if adj_enemy:
				cmd_list.append(game.attack(my_cell.position, 1))
				game.me.energy -= 1

	for cell in no_atk_queue:
		pos = cell[1]
		c = game.game_map[pos]

		if game.me.energy > 0:
			adj_enemy = False
			for adj_c in c.position.get_surrounding_cardinals():
				c2 = game.game_map[adj_c]
				if c2.owner != game.uid:
					adj_enemy = True
			if adj_enemy:
				cmd_list.append(game.attack(c.position, 1))
				game.me.energy -= 1

def choose_build_by_max_rsc(cmd_list, home_cell):
	#chooses gold or energy, whichever one is higher
	#loops through all and puts them into a queue. The one with the highest energy gets built first. Secondary check is on lowest other resource. 
	global game

	mult_weight = 1 #ratio is energy/gold rate
	if(home_cell.building.level < 3 and game.me.energy_source > 30 and game.me.gold_source > 30):
		mult_weight = game.me.energy_source / game.me.gold_source

	build_queue = []
	upgrade_queue = []
	
	for cell in game.me.cells.values():
		if cell.building.is_empty:
			#if they are equal, energy seems to happen more
			build_type = "energy_well"
			max_rsc = cell.natural_energy
			min_rsc = cell.natural_gold
			if cell.natural_gold * mult_weight > cell.natural_energy:
				build_type = "gold_mine"
				max_rsc = cell.natural_gold
				min_rsc = cell.natural_energy
			build_queue.append((100/max_rsc, build_type, cell.position, min_rsc))

		else:
			build_type = cell.building.name

			b_lvl = cell.building.level
			c_val = 0
			if b_lvl == 1:
				c_val = 200
			elif b_lvl == 2:
				c_val = 400

			if build_type == "gold_mine":
				c_val = c_val / cell.natural_gold
			elif build_type == "energy_well":
				c_val = c_val / cell.natural_energy

			#( ratio_val, level, build_type, position, )
			upgrade_queue.append((c_val, build_type, cell.position))

	build_queue.sort(key = lambda x: (x[0], x[3]))
	merge_queue = upgrade_queue + build_queue
	merge_queue.sort(key = lambda x: (x[0]))

	for cell in merge_queue:
		b_type = cell[1]
		pos = cell[2]
		c = game.game_map[pos]

		building = BLD_ENERGY_WELL

		if b_type == "gold_mine":
			building = BLD_GOLD_MINE
		elif b_type == "energy_well":
			building = BLD_ENERGY_WELL
		elif b_type == "fortress":
			building = BLD_FORTRESS

		if c.building.is_empty and 100 < game.me.gold:
			cmd_list.append(game.build(pos, building))
			game.me.gold -= 100
		else:
			if c.building.can_upgrade and c.building.upgrade_gold < game.me.gold:
				cmd_list.append(game.upgrade(c.position))
				game.me.gold -= c.building.upgrade_gold

def defend_home(home_cell): 
	global game

def build_home():
	global game

	safe_cell_queue = []

	for cell in game.me.cells.values():
		adj_count = 0
		adj_adj_count = 0
		for pos in cell.position.get_surrounding_cardinals():
			c = game.game_map[pos]

			if c.owner == game.uid:
				adj_count += 1
				adj_adj_count -= 1
				for pos2 in pos.get_surrounding_cardinals():
					c2 = game.game_map[pos2]
					if c2.owner == game.uid:
						adj_adj_count += 1

		safe_cell_queue.append((adj_count, adj_adj_count, cell.position))

	safe_cell_queue.sort(key = lambda x: (x[0], x[1]))

	if len(safe_cell_queue) > 1:
		if game.me.gold > 1000:
			cmd_list.append(game.build(safe_cell_queue[0][2], BLD_HOME))
			return safe_cell_queue[0][2]
	else:
		return None
		


# Connect to the server. This will connect to the public room. If you want to
# join other rooms, you need to change the argument
game.connect(room = 'public2')

# game.register should return True if succeed.
# As no duplicate usernames are allowed, a random integer string is appended
# to the example username. You don't need to do this, change the username
# to your ID.
# You need to set a password. For the example AI, the current time is used
# as the password. You should change it to something that will not change 
# between runs so you can continue the game if disconnected.
if game.register(username = 'please dont crash', \
		password = str(int(time.time()))):
	# This is the game loop
	while True:
		# The command list we will send to the server
		cmd_list = []
		# The list of cells that we want to attack
		my_attack_list = []
		# waits for updated game state from server
		game.update_turn()

		# create your ai in the game
		if game.me == None:
			continue
		me = game.me

		home_cell = find_home_cell()

		if home_cell == None:
			home_cell = build_home()

		if home_cell != None:

			if home_cell.building.level == 3:
				max_out_pace = True
				game.me.gold_source = game.me.gold_source * .75

			check_to_upgrade_home(home_cell)
			if upgrade_home_flag: 
				upgrade_home(home_cell, cmd_list)
			else:
				choose_atk_by_rsc_sum(cmd_list, my_attack_list)
				choose_build_by_max_rsc(cmd_list, home_cell)


		# Send the command list to the server
		result = game.send_cmd(cmd_list)
		print(result)
