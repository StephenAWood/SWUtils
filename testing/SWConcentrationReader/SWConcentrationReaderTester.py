# Testing the SWConcentrationReader

# This is designed to test various aspects of the SWHumanConcentrationReader class.

import SWConcentrationReader

main_test = False;
testing_features = True;

# Concentration dict for various years. I have looked in seqn 21005.csv for the concentrations for person born in 1985
# and written them in here. They should agree with what the SWHumanConcentrationReader pulls out of the file.
seqb21005_concentration_dict = { # year : concentration for person born in 1985 (for that year)
	2004 : 3.524,
	2002 : 3.697,
	2001 : 3.804,
	1995 : 4.921,
	#1985 : -1
}

seqn21005_filename = 'seqn 21005.csv'
seqn21005_birth_year = 1985
seqn21005_age_at_model_start = 5

seqn_21005 = SWConcentrationReader.SWHumanConcentrationReader(seqn21005_filename, age_at_model_start = seqn21005_age_at_model_start)

if main_test:
	error_counter = 0

	for sampling_year, concentration in seqb21005_concentration_dict.iteritems():
		predicted = seqn_21005.concentration_for_individual_at_sampling(seqn21005_birth_year, sampling_year)

		if predicted == concentration:
			print 'Good news! %f is equal to %f!' % (predicted, concentration)
		else:
			print 'Error! %f is not equal to %f!' % (predicted, concentration)
			error_counter += 1

		# other way
		# The other way to grab the concentration at sampling:
		# 1) Get column for that individual (based on birth year)
		# 2) Get hour in simulation: (sampling_year - startyear) * 8760
		# 3) Get row index for the hour in simulation (using the time step dict)
		# 4) Access self.data directly using the row and column. Should give the same result.

		column = seqn_21005.column_dict[seqn21005_birth_year]
		row = seqn_21005.time_step_dict[(sampling_year - 1930) * 8760] - 1

		other_method = float(seqn_21005.data[row][column])

		if predicted == concentration and predicted == other_method:
			print 'Good news! %f is equal to %f!' % (predicted, concentration)
		else:
			print 'Error! %f is not equal to %f!' % (other_method, concentration)
			error_counter += 1

	print seqn_21005.create_column_dict()

	try:
		c = seqn_21005.concentration_for_individual_at_sampling(seqn21005_birth_year, seqn21005_birth_year - 30) # A year much before the person was born.
	except Exception as e:
		if isinstance(e, SWConcentrationReader.SWInvalidYearException):
			print 'Good. exception caught.'
			print 'Exception message: %s (%s)' % (e, type(e))
		else:
			print 'Exception was not caught.'
			error_counter += 1

	if error_counter:
		print 'There was atleast 1 error detected.'
	else:
		print 'Good! there were no errors with SWConcentrationReader detected!'

if testing_features:
	#print seqn_21005._SWHumanConcentrationReader__get_ages_for_CBAT(2004)
	x = seqn_21005.extract_CBAT_for_year(2004)
	print x
