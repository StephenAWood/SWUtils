# SWNhanesReader.py

import csv
import re
import numpy as np
import SWSettings as s
import os

type_dict = {
	'RIAGENDR' : int,
	s.PCB153_CODE : float,
	'RIDAGEYR' : int,
	'LBX153'   : float,
	'LBX138LA' : float,
	'LBX180LA' : float,
	'LBX028LA' : float,
	'LBX052LA' : float,
	'LBX101LA' : float,
	'LBX118LA' : float,
	'BMXBMI'   : float
}

class SWNhanesReader(object):

	READ_DIETARY_INFO = False # save a lot of time reading data if False

	"""docstring for NhanesReader

	A class designed to read all of the NHANES data
	from a specific sampling year
	and store it in a dictionary

	- So it can be easily accessed by whoever wants to work with the NHANES data.
	"""

	# Public API.
	def __init__(self, nhanes_year='2003-2004'):
		super(SWNhanesReader, self).__init__()
		self.nhanes_year = nhanes_year
		self.data = self.obtain_data()

	def concentration_for_seqn_for_pcb(self, seqn, pcb):
		#return self.data[seqn][self.get_nhanes_code_for_pcb(pcb)]
		return self.data.get(seqn).get(self.get_nhanes_code_for_pcb(pcb))

	def get_list_of_seqn_for_pcb(self, pcb='PCB-153'): # Default is PCB-153
		pcb_string = self.get_nhanes_code_for_pcb(pcb)
		return [seqn for seqn in self.data if pcb_string in self.data[seqn]];

	def get_list_of_seqn(self):
		return self.data.keys()

	def get_median_concentration_for_pcb_for_gender(self, pcb, female):
		# get all median concentrations for a particular PCB
		# for male or female
		# for 11-20, 21-30, 31-40, and so on.
		start_age = 11
		end_age = 90
		age_gap = s.DEFAULT_AGE_SPREAD

		ages = []
		concentrations = []

		for i in range (start_age, end_age, age_gap):
			age_group_start = i
			age_group_end = i + age_gap - 1
			age, c = self.get_median_concentration_for_pcb_for_age_group_for_gender(pcb, age_group_start, age_group_end, female)
			ages.append(age)
			concentrations.append(c)

		return [ages, concentrations]


	def get_median_concentration_for_all_ages_for_pcb_for_gender(self, pcb, female):

		# Return the median of the reported NHANES PCB concentrations for a specific gender and specific PCB.

		pcb_string = self.get_nhanes_code_for_pcb(pcb)
		seqn_list = self.get_list_of_seqn_for_pcb(pcb)

		c_list = []

		gender = 2 if female else 1

		for seqn in seqn_list:
			if self.data[seqn][s.GENDER_CODE] == gender:
				c_list.append(self.data[seqn][pcb_string])


		median = np.median(c_list)

		return median

	def get_median_concentration_for_pcb_for_age_group_for_gender(self, pcb, min_age, max_age, female):
		# get median concentration of a PCB
		# for a certain age group
		# and for male or female.
		ages, concentrations = self.get_concentrations_for_pcb_for_age_group_for_gender(pcb, min_age, max_age, female)
		median_concentration = np.median(concentrations)
		median_age = np.median(ages)
		return [median_age, median_concentration]

	def get_concentrations_for_pcb_for_age_group_for_gender(self, pcb, min_age, max_age, female):
		# return all concentrations of a certain PCB
		# for a certain age group
		# and for male or female
		pcb_string = self.get_nhanes_code_for_pcb(pcb)
		seqn_list = self.get_list_of_seqn_for_pcb(pcb)
		gender = self.gender_number_if_female(female)

		ages = []
		concentrations = []

		for seqn in seqn_list:
			if self.data[seqn][s.GENDER_CODE] == gender:
				if self.data[seqn][s.AGE_CODE] >= min_age and self.data[seqn][s.AGE_CODE] <= max_age:
					ages.append(self.data[seqn][s.AGE_CODE])
					concentrations.append(self.data[seqn][pcb_string])

		return [ages, concentrations]

	def get_age_and_concentration_for_pcb_for_gender(self, pcb, female):
		pcb_string = self.get_nhanes_code_for_pcb(pcb)
		seqn_list = self.get_list_of_seqn_for_pcb(pcb)
		gender = self.gender_number_if_female(female)

		ages = []
		concentrations = []
		for seqn in seqn_list:
			if self.data[seqn][s.GENDER_CODE] == gender:
				ages.append(self.data[seqn][s.AGE_CODE])
				concentrations.append(self.data[seqn][pcb_string])

		return [ages, concentrations]

	# Private Methods below this line.

	def gender_number_if_female(self, female):
		return 2 if female else 1

	def get_nhanes_code_for_pcb(self, pcb):
		# This method is designed to take any kind of string input (or int maybe)
		# and turn it into the code used in the NHANES data.
		# i.e. Entering 'PCB-153' should give back 'LBX153LA', the lipid adjusted PCB concentration code.
		pcb = str(pcb) # cast to string in case an int was passed.
		pcb_number =  str(re.findall(r'\d+', pcb)[0] if re.findall(r'\d+', pcb) else 0) # extract the PCB congener number
		if len(pcb_number) == 2: pcb_number = '0' + pcb_number # if its 11-99 then a leading 0 must be added
		pcb_string = 'LBX' + pcb_number + 'LA' # construct the string for the code.
		return pcb_string # return

	def cast(self, var):
		return type_dict[var] if var in type_dict else str

	def obtain_data(self):
		ret_dict = {}

		seqn_column = 1
		start_column = 2
		start_row = 1
		header_row = 0

		filenames = [os.path.join(s.NHANES_DATA_PATH, self.folders_dict[self.nhanes_year], name) for name in self.filenames_dict[self.nhanes_year]]

		imported_data = []

		for f in filenames:
			file_import_temp = []
			with open(f, 'rU') as csvfile:
				temp = csv.reader(csvfile, delimiter = ',', quotechar = '"')
				for row in temp:
					file_import_temp.append(row)
			imported_data.append(file_import_temp)

		if imported_data:
			if imported_data[0]:
				for row in imported_data[0][start_row:]:
					seqn = int(row[seqn_column])
					ret_dict.update({seqn : {} })

		for f in imported_data:
			for row in f[start_row:]:
				seqn = int(row[seqn_column])
				for i, header in enumerate(f[header_row][start_column:]):
					header = header.upper()
					column = i + start_column
					try: val = self.cast(header)(row[column])
					except ValueError: continue
					ret_dict[seqn].update({header : val})

		# special read in for diet info
		if self.READ_DIETARY_INFO:
			f = os.path.join(s.NHANES_DATA_PATH, self.folders_dict[self.nhanes_year], 'DR1IFF_C.csv')

			food_number_column = 2
			raw = []

			for seqn in ret_dict:
				ret_dict[seqn].update({'food_index' : {} })

			with open(f, 'rU') as csvfile:
				temp = csv.reader(csvfile, delimiter = ',', quotechar = '"')
				for row in temp:
					raw.append(row)
			for row in raw[start_row:]:
				seqn = int(row[seqn_column])
				food_index = int(row[food_number_column])
				ret_dict[seqn]['food_index'].update({food_index : {}})
				for i, header in enumerate(raw[header_row][3:]):
					header = header.upper()
					column = i + 3
					#print 'brool'
					try: val = self.cast(header)(row[column])
					except ValueError: continue
					ret_dict[seqn]['food_index'][food_index].update({header : val})

		
		return ret_dict

	# Dictionaries containing the appropriate file names.
	filenames_dict = {
		'2003-2004' : ['DEMO_C.csv', 'RHQ_C.csv', 'L28NPB_C.csv', 'BMX_C.csv', 'L28DFP_C.csv', 'DR1TOT_C.csv'],
		'2001-2002' : ['DEMO_B.csv', 'L28POC_B.csv', 'BMX_B.csv'],
		'1999-2000' : ['DEMO.csv', 'LAB28POC.csv', 'BMX.csv']
	}

	folders_dict = {
		'2003-2004' : 'NHANES data 2003-2004',
		'2001-2002' : 'NHANES data 2001-2002',
		'1999-2000' : 'NHANES data 1999-2000'
	}
