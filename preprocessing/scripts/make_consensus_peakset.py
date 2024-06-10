import pandas as pd
import argparse
import os


###
# HELPER FUNCTIONS
###
def load_peaks(peak_file):
	peak_df = pd.read_csv(peak_file, sep="\t", names=["chro", "start", "end", "name", "score", "strand", "signal", "p", "q", "summit"])
	return peak_df

def add_peak(accepted_peaks_dict, accepted_peaks_df, new_peak):
	np_chro, np_start, np_end = new_peak
	if np_chro in accepted_peaks_dict:
		accepted_peaks_dict_chro = accepted_peaks_dict[np_chro]
		peak_unique = True
		for p in accepted_peaks_dict_chro:
			if peak_overlap(p, (np_start, np_end)):
				peak_unique = False
				break
		if peak_unique:
			accepted_peaks_dict[np_chro] += [(np_start, np_end)]
			accepted_peaks_df = pd.concat([accepted_peaks_df, pd.DataFrame({"chro": np_chro, "start": np_start, "end": np_end}, index=[0])], ignore_index=True)
	else:
		accepted_peaks_dict[np_chro] = [(np_start, np_end)]
		accepted_peaks_df = pd.concat([accepted_peaks_df, pd.DataFrame({"chro": np_chro, "start": np_start, "end": np_end}, index=[0])], ignore_index=True)
	return accepted_peaks_dict, accepted_peaks_df

def peak_overlap(peaka, peakb):
	return ((peakb[0] < peaka[0]) and (peakb[1] >= peaka[0])) or ((peakb[0] >= peaka[0]) and (peakb[0] < peaka[1]))

def expand_3col_to_10col(df):
	
	for i in ['name', 'score', 'strand', 'signalValue', 'pValue', 'qValue']: #range(4, 10):
		df[f'col{i}'] = '.'
	df.iloc[:, 1] = df.iloc[:, 1].astype(int)
	df.iloc[:, 2] = df.iloc[:, 2].astype(int)
	df['summit'] = (df.iloc[:, 2] - df.iloc[:, 1]) // 2
	return df


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Find union of peaks from multiple peak files')
	parser.add_argument('--peaks_dir', type=str, help='Path to input file')
	parser.add_argument('--output', type=str, help='Path to output file')

	args = parser.parse_args()
	###
	# CODE START
	###
	peaks_dir = args.peaks_dir
	peaks = []
	for f in os.listdir(peaks_dir):
		if f.endswith("_overlap_filtered.narrowPeak"):
			peaks.append(load_peaks(f"{peaks_dir}/{f}"))
	if len(peaks) == 1:
		peaks_combined = peaks[0]
		peaks_combined.to_csv(args.output, sep='\t', header=False, index=False)
	else:
		peaks_combined = pd.concat(peaks, ignore_index=True)
		peaks_combined = peaks_combined.sort_values("q", ascending=False)
		peaks_combined = peaks_combined.reset_index(drop=True)

		accepted_peaks_dict = {}
		accepted_peaks_df = pd.DataFrame()
		for index, row in peaks_combined.iterrows():
			if index%10000 == 0:
				print(index)
			p_summit = row["start"] + row["summit"]
			p = (row["chro"], p_summit - 250, p_summit + 250)
			accepted_peaks_dict, accepted_peaks_df = add_peak(accepted_peaks_dict, accepted_peaks_df, p)
		accepted_peaks_df = accepted_peaks_df.sort_values(by=["chro", "start"], ascending=[True, True])
		accepted_peaks_df = accepted_peaks_df.reset_index(drop=True)

		# out_loc = os.path.join(args.out_dir, 'union_peaks.narrowPeak')
		os.makedirs(os.path.dirname(args.output), exist_ok=True)

		df = expand_3col_to_10col(accepted_peaks_df)
		df.to_csv(args.output, sep='\t', header=False, index=False)