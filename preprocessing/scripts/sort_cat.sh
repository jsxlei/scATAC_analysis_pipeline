#!/bin/bash


sortcat () {
	dataset=${1}
	in_dir=${2} 
	out_dir=${3}
	# subfolder=${4} 

	echo "${dataset} concatenating across samples..."
	# find "${in_dir}/${subfolder}" -name "${dataset}*.tsv" -exec cat {} + > "${out_dir}/${subfolder}/${dataset}.tsv"
	find "${in_dir}/fragments" -name "${dataset}*.tsv" -exec cat {} + > "${out_dir}/fragments/${dataset}.tsv"
	find "${in_dir}/pseudorepT" -name "${dataset}*.tsv" -exec cat {} + > "${out_dir}/pseudorepT/${dataset}.tsv"
	find "${in_dir}/pseudorep1" -name "${dataset}*.tsv" -exec cat {} + > "${out_dir}/pseudorep1/${dataset}.tsv"
	find "${in_dir}/pseudorep2" -name "${dataset}*.tsv" -exec cat {} + > "${out_dir}/pseudorep2/${dataset}.tsv"

	# echo "${dataset} sorting ${subfoler}..."
	# sort -k 1,1 -k 2,2n -S 10% --parallel=4 ${out_dir}/${subfoler}/${dataset}.tsv -o ${out_dir}/${subfoler}/${dataset}_sorted.tsv
	mkdir -p ${out_dir}/fragments
	mkdir -p ${out_dir}/pseudorepT
	mkdir -p ${out_dir}/pseudorep1
	mkdir -p ${out_dir}/pseudorep2
	echo "${dataset} sorting fragments..."
	sort -k 1,1 -k 2,2n -S 10% --parallel=4 ${out_dir}/fragments/${dataset}.tsv -o ${out_dir}/fragments/${dataset}_sorted.tsv
	echo "${dataset} sorting pseudorepT..."
	sort -k 1,1 -k 2,2n -S 10% --parallel=4 ${out_dir}/pseudorepT/${dataset}.tsv -o ${out_dir}/pseudorepT/${dataset}_sorted.tsv
	echo "${dataset} sorting pseudorep1..."
	sort -k 1,1 -k 2,2n -S 10% --parallel=4 ${out_dir}/pseudorep1/${dataset}.tsv -o ${out_dir}/pseudorep1/${dataset}_sorted.tsv
	echo "${dataset} sorting pseudorep2..."
	sort -k 1,1 -k 2,2n -S 10% --parallel=4 ${out_dir}/pseudorep2/${dataset}.tsv -o ${out_dir}/pseudorep2/${dataset}_sorted.tsv

	echo "done ${dataset}"
}
export -f sortcat

sortcat $1 $2 $3
# ls ${frags_dir} | cut -d "-" -f 1 | sort | uniq | parallel --linebuffer -j ${MAX_PARALLEL} sortcat {}