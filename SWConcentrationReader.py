# Created by Stephen A. Wood
# stephen.wood@mail.utoronto.ca
# Copyright (c) 2014 Stephen Wood. See included LICENSE file.

#test

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
	TIME_STRING = 'time'
	MAX_AGE_MODEL_START = 9
	MIN_AGE_MODEL_START = 0

	# PUBLIC API
	# METHODS BELOW

	def __init__(self, filename, startyear=s.DEFAULT_START_YEAR, age_at_model_start=s.DEFAULT_AGE_AT_MODEL_START): # initializer / constructor

		# error checks
		if age_at_model_start < self.MIN_AGE_MODEL_START or age_at_model_start > self.MAX_AGE_MODEL_START:
			raise Exception('Invalid age at model start: %d for file %s' % (age_at_model_start, filename))

		super(SWHumanConcentrationReader, self).__init__()
		self.filename = filename
		# if not any(s.upper() in filename.upper() for s in self.ACCEPTED_FILENAMES):
		# 	raise IOError, 'Error, invalid human concentration file entered.'
		self.startyear = startyear
		self.age_at_model_start = age_at_model_start
		self.data = self.__read_file(filename)
		self.endyear = int(self.data[len(self.data) - 1][0]) / s.HOURS_IN_YEAR + self.startyear
		self.timestep = self.__determine_timestep()
		self.time_step_dict = self.__create_time_step_dict()
		self.column_dict = self.__create_column_dict()

	def concentration_for_individual_at_sampling(self, birth_year, sampling_year):
		"""Gets the individual's concentration at time of sampling."""
		if not self.__is_year_in_simulation(sampling_year):
			raise SWInvalidYearException('Error, sampling year %d is not in the simulation' % (sampling_year))
		c = self.concentration_profile_for_individual_born_in_year(birth_year)
		index = self.__get_index_for_person_at_sampling(birth_year, sampling_year, c)
		return c[index]

	def concentration_profile_for_individual_born_in_year(self, birth_year):
		"""Get the lifetime concentration for the individual."""
		self.__check_year(birth_year)

		number_of_years_in_sim = self.__get_number_of_years_in_sim_for_person_born_in_year(birth_year)
		hour = 0 if self.__is_person_born_before_simulation_start(birth_year) else self.__convert_year_to_hour(birth_year)

		number_of_points = number_of_years_in_sim * s.HOURS_IN_YEAR / self.timestep

		start_index = self.time_step_dict[hour]
		end_index = start_index + number_of_points
		column = self.column_dict[birth_year]

		concentration = [float(x[column]) for x in self.data[start_index:end_index]]
		return concentration

	def extract_default_concentrations(self):
		"""List of concentration profiles for people born after model start."""
		start = self.startyear - self.age_at_model_start
		end = self.startyear - self.age_at_model_start + s.HUMAN_MAX_AGE
		increment = s.DEFAULT_AGE_SPREAD
		return [self.concentration_profile_for_individual_born_in_year(year) for year in range(start, end, increment)]

	def extract_CBAT_for_year(self, year):
		"""Get the cross-sectional body burden age trend for the specified year."""
		if not self.__is_year_in_simulation(year):
			raise SWInvalidYearException('Invalid year entered for CBAT')
		hour = self.__convert_year_to_hour(year)
		ages = self.__get_ages_for_CBAT(year)
		hour_index = self.time_step_dict[hour] - 1
		CBAT_values = self.data[hour_index][1:]
		ages, CBAT_values = [list(x) for x in zip(*sorted(zip(ages, CBAT_values), key = itemgetter(0)))]
		return (ages, CBAT_values)

	# PRIVATE API
	# Methods below should not be accessed outside of this class.

	def __is_year_in_simulation(self, year):
		"""determine if the year is in the simulation"""
		return year >= self.startyear and year <= self.endyear

	def __get_index_for_person_at_sampling(self, birth_year, sampling_year, concentration_profile):
		"""get the index for the concentration profile depending on the age at sampling"""
		age = sampling_year - birth_year

		if age <= 0: raise SWInvalidYearException('Error, sampling year is before the person was born!')

		if self.__is_person_older_than_max_age(age) and self.__is_person_born_before_simulation_start(birth_year):
			return len(concentration_profile) - 1
		elif self.__is_person_older_than_max_age(age):
			return len(concentration_profile) - 1
		elif self.__is_person_born_before_simulation_start(birth_year):
			return (sampling_year - self.startyear) * s.HOURS_IN_YEAR / self.timestep - 1
		else:
			return (sampling_year - birth_year) * s.HOURS_IN_YEAR / self.timestep - 1

	def __is_person_older_than_max_age(self, age):
		"""determine if person is older than the max model supported age"""
		return age > s.HUMAN_MAX_AGE

	def __get_number_of_years_in_sim_for_person_born_in_year(self, birth_year):
		"""determine how many years the person spends in the simulation"""
		# need to check multiple conditions -
		# 1) person who is born before the simulation starts
		# 2) person whos max age(80) is not reached when the simulation ends
		# 3) person who fulfills both 1 AND 2 - this case should be tested first
		# last case is a person who lives the default 80 years in the simulation.
		if self.__is_person_born_before_simulation_start(birth_year) and self.__is_person_alive_after_simulation_end(birth_year): # condition 3
			return self.endyear - self.startyear
		elif self.__is_person_alive_after_simulation_end(birth_year): # condition 2
			return self.endyear - birth_year
		elif self.__is_person_born_before_simulation_start(birth_year): # condition 1
			return s.HUMAN_MAX_AGE - (self.startyear - birth_year)
		else:
			return s.HUMAN_MAX_AGE

	def __is_person_alive_after_simulation_end(self, birth_year):
		"""determine if person is still alive when the simulation ends"""
		return (birth_year + s.HUMAN_MAX_AGE) > self.endyear

	def __is_person_born_before_simulation_start(self, birth_year):
		"""determine if person is born before the simulation start year"""
		return self.startyear > birth_year

	def __get_ages_for_CBAT(self, sampling_year):
		"""get the ages for a cross-sectional body burden age trend at the specified sampling year"""
		return [sampling_year - year for year in self.__get_birth_years_at_year(sampling_year)]

	def __get_birth_years_at_year(self, sampling_year):
		"""get the birth years for a cross-sectional body burden age trend at the specified sampling year"""
		return [birth_year for i in range(1, s.NUMBER_OF_HUMANS + 1) for birth_year in self.column_dict if self.__satisfy_cbat_condition(i, sampling_year, birth_year)]

	def __satisfy_cbat_condition(self, i, sampling_year, year):
		"""see if the birth year is the closest to the sampling year"""
		return i == self.column_dict[year] and (sampling_year - year) <= s.HUMAN_MAX_AGE and (sampling_year - year) > 0

	@staticmethod
	def __read_file(filename):
		"""read the file and return it as a list"""
		with open(filename, 'rU') as csvfile:
			t = csv.reader(csvfile, delimiter = ',', quotechar= '"')
			return [line for line in t]

	def __create_column_dict(self):
		#essentially a map that links the year a person was born in to the column they reside in within C.txt file.
		years = range(self.startyear - self.age_at_model_start - s.HUMAN_MAX_AGE + s.DEFAULT_AGE_SPREAD, self.endyear, s.DEFAULT_AGE_SPREAD)
		return {year : s.NUMBER_OF_HUMANS - (i % s.NUMBER_OF_HUMANS) for i, year in enumerate(years)}

	def __create_time_step_dict(self):
		# dict structure: {hour : index of that hour}
		start_index = self.__determine_index_at_data_start()
		return {int(self.data[i][0]) : i for i in range(start_index, len(self.data))}

	def __determine_index_at_data_start(self):
		for i, row in enumerate(self.data):
			if any(s.lower() == self.TIME_STRING.lower() for s in row):
				return i + 1;

	def __determine_timestep(self):
		i = self.__determine_index_at_data_start()
		return int(self.data[i + 1][0]) - int(self.data[i][0])

	def __check_year(self, year):
		if not year in self.column_dict:
			raise SWInvalidYearException(self.INVALID_YEAR_ENTERED)

	def __convert_year_to_hour(self, year):
		return (year - self.startyear) * s.HOURS_IN_YEAR

class SWInvalidYearException(Exception):
	def __init__(self, message):
		self.message = message
	def __str__(self):
		return repr(self.message)
