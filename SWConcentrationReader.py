# Created by Stephen Wood
# Copyright (c) 2014 Stephen Wood. See included LICENSE file.
#


import csv
from operator import itemgetter
import SWSettings as s

class SWHumanConcentrationReader(object):
	"""docstring for ConcentrationReader

	A class designed to help extract information from
	either a CMAN.txt or CWOMAN.txt that is generated
	from ACC-HUMAN.

	"""
	ACCEPTED_FILENAMES = ['CMAN', 'CWOMAN', 'seqn']
	INVALID_YEAR_ENTERED = 'Invalid year entered'

	# PUBLIC API
	# METHODS BELOW

	def __init__(self, filename, startyear=s.DEFAULT_START_YEAR, age_at_model_start=s.DEFAULT_AGE_AT_MODEL_START): # initializer / constructor

		#startyear and age_at_model_start are default params. Likely don't need to be changed.
		#Age at model start must be a value between 0 and 9 (inclusive).

		super(SWHumanConcentrationReader, self).__init__()
		self.filename = filename
		# if not any(s.upper() in filename.upper() for s in self.ACCEPTED_FILENAMES):
		# 	raise IOError, 'Error, invalid human concentration file entered.'
		self.concentrations = {}
		self.startyear = startyear
		self.age_at_model_start = age_at_model_start
		self.data = self.read_file(filename)
		self.endyear = int( self.data[len(self.data) - 1][0] ) / s.HOURS_IN_YEAR + self.startyear
		self.timestep = self.determine_timestep()
		self.time_step_dict = self.create_time_step_dict()
		self.column_dict = self.create_column_dict()

	def concentration_for_individual_at_sampling(self, birth_year, sampling_year):

		# grab the concentration profile for this individual.
		c = self.concentration_profile_for_individual_born_in_year(birth_year)

		year_diff = sampling_year - birth_year # Check how old this individual is at sampling.
		#Necessary to find which value to take from their concentration profile.

		# If there is an individual who is greater than 80 years old at the time of sampling, 
		# I want to just take the last concentration value from that person.

		if year_diff > s.HUMAN_MAX_AGE: # dealing with a person older than 80.
			year_diff = s.HUMAN_MAX_AGE - (self.startyear - birth_year)
		elif birth_year < self.startyear: # if an individual is born before sim start but not older than 80.
			year_diff = sampling_year - self.startyear
		index = year_diff * s.HOURS_IN_YEAR / self.timestep - 1

		return c[index]

	def concentration_profile_for_individual_born_in_year(self, birth_year):
		#check if the year has already been calculated. Probably saves no time at all.
		if birth_year in self.concentrations:
			return self.concentrations[birth_year]

		#check that the year being asked for makes sense.

		self.check_year(birth_year)
		hour = self.convert_year_to_hour(birth_year)

		number_of_years_in_sim = s.HUMAN_MAX_AGE
		if (self.endyear - birth_year) < s.HUMAN_MAX_AGE:
			number_of_years_in_sim = self.endyear - birth_year # just check if it is a human who is near the end of simulation.

		# check if this individual is born before the simulation start year.
		if birth_year < self.startyear:
			number_of_years_in_sim = s.HUMAN_MAX_AGE - (self.startyear - birth_year)
			hour = 0

		number_of_points = number_of_years_in_sim * s.HOURS_IN_YEAR / self.timestep

		start_index = self.time_step_dict[hour]
		end_index = start_index + number_of_points
		column = self.column_dict[birth_year]

		concentration = [float(x[column]) for x in self.data[start_index:end_index]]

		self.concentrations.update( {birth_year : concentration} )

		return concentration

	def extract_default_concentrations(self):
		start = self.startyear - self.age_at_model_start
		end = self.startyear - self.age_at_model_start + s.HUMAN_MAX_AGE
		increment = s.DEFAULT_AGE_SPREAD
		return [self.concentration_profile_for_individual_born_in_year(year) for year in range(start, end, increment)]

	def extract_CBAT_for_year(self, year):

		if year > self.endyear or year < self.startyear:
			raise Exception, 'Invalid year entered for CBAT.'

		hour = self.convert_year_to_hour(year)
		ages = self.get_ages_for_CBAT(year)
		hour_index = self.time_step_dict[hour]
		row = self.data[hour_index]
		CBAT_values = row[1:]
		#sort
		ages, CBAT_values = [list(x) for x in zip(*sorted(zip(ages, CBAT_values), key = itemgetter(0)))]

		return (ages, CBAT_values)

	# PRIVATE API
	# Methods below should not be accessed outside of this class.
	# 

	def get_ages_for_CBAT(self, year):
		ret_list = []

		for i in range(0, s.NUMBER_OF_HUMANS):
			age = year - (self.startyear - self.age_at_model_start - i * s.DEFAULT_AGE_SPREAD)
			while age > s.HUMAN_MAX_AGE:
				age -= s.HUMAN_MAX_AGE
			ret_list.append(age)
		return ret_list

	def read_file(self, filename):
		data = []
		with open(filename, 'rU') as csvfile:
			t = csv.reader(csvfile, delimiter = ',', quotechar= '"')
			for row in t:
				data.append(row)
		return data

	def create_column_dict(self):
		#essentially a map that links the year a person was born in to the column they reside in within C.txt file.
		ret_dict = {}
		i = 0
		for year in range(self.startyear - self.age_at_model_start - s.HUMAN_MAX_AGE + s.DEFAULT_AGE_SPREAD, self.endyear, s.DEFAULT_AGE_SPREAD):
			column = s.NUMBER_OF_HUMANS - (i % s.NUMBER_OF_HUMANS)
			#print 'year', year, 'is in column', column
			i += 1
			ret_dict.update( {year : column} )
		return ret_dict

	def create_time_step_dict(self):
		# dict structure: {hour : index of that hour}

		ret_dict = {}

		start_index = 0

		for row in self.data:
			if row[0].upper() == 'Time'.upper():
				break
			start_index += 1

		start_index += 1

		for i in range(start_index, len(self.data), 1):
			hour = int(self.data[i][0])
			ret_dict.update({hour : i})

		#print ret_dict
		return ret_dict


	def determine_timestep(self):
		index = 0

		for row in self.data:
			if row[0].upper() == 'Time'.upper():
				#print 'found it'
				break
			index += 1

		timestep = int(self.data[index + 2][0]) - int(self.data[index + 1][0])

		return timestep		

	def check_year(self, year):
		if year in self.column_dict:
			return
		else:
			raise KeyError, self.INVALID_YEAR_ENTERED

	def convert_year_to_hour(self, year):
		return (year - self.startyear) * s.HOURS_IN_YEAR