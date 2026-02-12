import deepdish
import numpy as np

import os
import sys
import argparse


def main(args):
	base_dir = args.base_dir
	folds = args.folds
	shaptype = args.shaptype

	avg_projected_shap = None
	raw = None
	avg_shap = None

	# loop over folds
	for fold in folds:
		print(f"\t {fold}")
		fold_dir = f"{base_dir}/{fold}"
		
		# load shap scores
		deepshap = deepdish.io.load(f"{base_dir}/{fold}.{shaptype}_scores.h5")
		
		# sum up the shap scores
		if raw is None:
			avg_projected_shap = deepshap["projected_shap"]["seq"]
			raw = deepshap["raw"]["seq"]
			avg_shap = deepshap["shap"]["seq"]
		else:
			assert(np.array_equal(raw, deepshap["raw"]["seq"]))
			avg_projected_shap += deepshap["projected_shap"]["seq"]
			avg_shap += deepshap["shap"]["seq"]


	# divide by 5 to average over folds
	print("\taveraging...")
	avg_projected_shap /= len(folds)
	avg_shap /= len(folds)

	print("\tsaving...")
	deepshap_output = {"projected_shap": {"seq": avg_projected_shap},
					"raw": {"seq": raw},
					"shap": {"seq": avg_shap}}
	deepdish.io.save(f"{base_dir}/average.{shaptype}.h5", deepshap_output)

	# done.

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Average deepSHAP scores over folds.')
	parser.add_argument('--base_dir', type=str, help='Base directory containing fold{0,1,2,3,4}')
	parser.add_argument('--shaptype', type=str, help='Type of SHAP scores to average: "counts" or "profile"')
	parser.add_argument('--folds', type=str, nargs='+', default=["fold0", "fold1", "fold2", "fold3", "fold4"], help='Folds to average over')
	args = parser.parse_args()

	main(args)


		
