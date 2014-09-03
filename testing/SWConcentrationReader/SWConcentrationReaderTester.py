# Testing the SWConcentrationReader

# This is designed to test various aspects of the SWHumanConcentrationReader class.

import SWConcentrationReader

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

error_counter = 0

for sampling_year, concentration in seqb21005_concentration_dict.iteritems():
	predicted = seqn_21005.concentration_for_individual_at_sampling(seqn21005_birth_year, sampling_year)

	if predicted == concentration:
		print 'Good news! %f is equal to %f!' % (predicted, concentration)
	else:
		print 'Error! %f is not equal to %f!' % (predicted, concentration)
		error_counter += 1


try:
	c = seqn_21005.concentration_for_individual_at_sampling(seqn21005_birth_year, seqn21005_birth_year - 30) # A year much before the person was born.
except Exception as e:
	if isinstance(e, SWConcentrationReader.SWInvalidYearException):
		print 'Good. exception caught.'
	else:
		print 'Exception was not caught.'
		error_counter += 1

if error_counter:
	print 'There was atleast 1 error detected.'
else:
	print 'Good! there were no errors with SWConcentrationReader detected!'
