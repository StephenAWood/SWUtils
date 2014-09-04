# Created by Stephen Wood
# Copyright (c) 2014 Stephen Wood. See included LICENSE file.

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
	TIME_STRING = 'TIME'

	# PUBLIC API
	# METHODS BELOW

	def __init__(self, filename, startyear=s.DEFAULT_START_YEAR, age_at_model_start=s.DEFAULT_AGE_AT_MODEL_START): # initializer / constructor

		#startyear and age_at_model_start are default params. Likely don't need to be changed.
		#Age at model start must be a value between 0 and 9 (inclusive).
		super(SWHumanConcentrationReader, self).__init__()
		self.filename = filename
		# if not any(s.upper() in filename.upper() for s in self.ACCEPTED_FILENAMES):
		# 	raise IOError, 'Error, invalid human concentration file entered.'
		self.startyear = startyear
		self.age_at_model_start = age_at_model_start
		self.data = self.read_file(filename)
		self.endyear = int(self.data[len(self.data) - 1][0]) / s.HOURS_IN_YEAR + self.startyear
		self.timestep = self.determine_timestep()
		self.time_step_dict = self.create_time_step_dict()
		self.column_dict = self.create_column_dict()

	def concentration_for_individual_at_sampling(self, birth_year, sampling_year):
		if not self.is_year_in_simulation(sampling_year):
			raise SWInvalidYearException('Error, sampling year %d is not in the simulation' % (sampling_year))

		# grab the concentration profile for this individual.
		c = self.concentration_profile_for_individual_born_in_year(birth_year)
		index = self.get_index_for_person_at_sampling(birth_year, sampling_year, c)
		return c[index]

		# The other way to grab the concentration at sampling:
		# 1) Get column for that individual (based on birth year)
		# 2) Get hour in simulation: (sampling_year - startyear) * 8760
		# 3) Get row index for the hour in simulation (using the time step dict) and subtract 1
		# 4) Access self.data directly using the row and column. Should give the same result.

	def concentration_profile_for_individual_born_in_year(self, birth_year):

		#check that the year being asked for makes sense.
		self.check_year(birth_year)

		number_of_years_in_sim = self.get_number_of_years_in_sim_for_person_born_in_year(birth_year)
		hour = 0 if self.is_person_born_before_simulation_start(birth_year) else self.convert_year_to_hour(birth_year)

		number_of_points = number_of_years_in_sim * s.HOURS_IN_YEAR / self.timestep

		start_index = self.time_step_dict[hour]
		end_index = start_index + number_of_points
		column = self.column_dict[birth_year]

		concentration = [float(x[column]) for x in self.data[start_index:end_index]]
		return concentration

	def extract_default_concentrations(self):
		start = self.startyear - self.age_at_model_start
		end = self.startyear - self.age_at_model_start + s.HUMAN_MAX_AGE
		increment = s.DEFAULT_AGE_SPREAD
		return [self.concentration_profile_for_individual_born_in_year(year) for year in range(start, end, increment)]

	def extract_CBAT_for_year(self, year):
		if not self.is_year_in_simulation(year):
			raise SWInvalidYearException('Invalid year entered for CBAT')	

		hour = self.convert_year_to_hour(year)
		ages = self.get_ages_for_CBAT(year)
		hour_index = self.time_step_dict[hour]
		row = self.data[hour_index]
		CBAT_values = row[1:]
		#sort
		ages, CBAT_values = [list(x) for x in zip(*sorted(zip(ages, CBAT_values), key = itemgetter(0)))]

		return ages, CBAT_values

	# PRIVATE API
	# Methods below should not be accessed outside of this class.

	def is_year_in_simulation(self, year):
		return year >= self.startyear and year <= self.endyear

	def get_index_for_person_at_sampling(self, birth_year, sampling_year, concentration_profile):
		age = sampling_year - birth_year

		if age <= 0: raise SWInvalidYearException('Error, sampling year is before the person was born!')

		if self.is_person_older_than_max_age(age) and self.is_person_born_before_simulation_start(birth_year):
			return len(concentration_profile) - 1
		elif self.is_person_older_than_max_age(age):
			return len(concentration_profile) - 1
		elif self.is_person_born_before_simulation_start(birth_year):
			return (sampling_year - self.startyear) * s.HOURS_IN_YEAR / self.timestep - 1
		else:
			return (sampling_year - birth_year) * s.HOURS_IN_YEAR / self.timestep - 1

	def is_person_older_than_max_age(self, age):
		return age > s.HUMAN_MAX_AGE

	def get_number_of_years_in_sim_for_person_born_in_year(self, birth_year):

		# need to check multiple conditions -
		# 1) person who is born before the simulation starts
		# 2) person whos max age(80) is not reached when the simulation ends
		# 3) person who fulfills both 1 AND 2 - this case should be tested first
		# last case is a person who lives the default 80 years in the simulation.

		if self.is_person_born_before_simulation_start(birth_year) and self.is_person_alive_after_simulation_end(birth_year): # condition 3
			return self.endyear - self.startyear
		elif self.is_person_alive_after_simulation_end(birth_year): # condition 2
			return self.endyear - birth_year
		elif self.is_person_born_before_simulation_start(birth_year): # condition 1
			return s.HUMAN_MAX_AGE - (self.startyear - birth_year)
		else:
			return s.HUMAN_MAX_AGE

	def is_person_alive_after_simulation_end(self, birth_year):
		return (birth_year + s.HUMAN_MAX_AGE) > self.endyear

	def is_person_born_before_simulation_start(self, birth_year):
		return self.startyear > birth_year

	def get_ages_for_CBAT(self, year):
		ret_list = []

		for i in range(0, s.NUMBER_OF_HUMANS):
			age = year - (self.startyear - self.age_at_model_start - i * s.DEFAULT_AGE_SPREAD)
			while age > s.HUMAN_MAX_AGE:
				age -= s.HUMAN_MAX_AGE
			ret_list.append(age)
		return ret_list

	@staticmethod
	def read_file(filename):
		data = []
		with open(filename, 'rU') as csvfile:
			t = csv.reader(csvfile, delimiter = ',', quotechar= '"')
			for row in t:
				data.append(row)
		return data

	def create_column_dict(self):
		#essentially a map that links the year a person was born in to the column they reside in within C.txt file.
		ret_dict = {}
		years = range(self.startyear - self.age_at_model_start - s.HUMAN_MAX_AGE + s.DEFAULT_AGE_SPREAD, self.endyear, s.DEFAULT_AGE_SPREAD)
		for i, year in enumerate(years):
			column = s.NUMBER_OF_HUMANS - (i % s.NUMBER_OF_HUMANS)
			ret_dict.update({year : column})
		return ret_dict

	def create_time_step_dict(self):
		# dict structure: {hour : index of that hour}
		start_index = self.determine_index_at_data_start()
		return {int(self.data[i][0]) : i for i in range(start_index, len(self.data))}

	def determine_index_at_data_start(self):
		start_index = 0
		for row in self.data:
			if row[0].upper() == self.TIME_STRING.upper():
				start_index +=1
				break
			start_index += 1
		return start_index # this is usually 8. (i.e. 9th row)

	def determine_timestep(self):
		i = self.determine_index_at_data_start()
		return int(self.data[i + 1][0]) - int(self.data[i][0])

	def check_year(self, year):
		if year in self.column_dict:
			return
		else:
			raise SWInvalidYearException(self.INVALID_YEAR_ENTERED)

	def convert_year_to_hour(self, year):
		return (year - self.startyear) * s.HOURS_IN_YEAR

class SWInvalidYearException(Exception):
	def __init__(self, message):
		self.message = message
	def __str__(self):
		return repr(self.message)
