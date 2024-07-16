#!/bin/bash


callpeak () {
	dataset=${1}
	in_dir=${2} #"/mnt/lab_data3/salil512/adult_heart/2_chrombpnet/2_celltype_fragments"
	p1_dir="${in_dir}/pseudorep1"
	p2_dir="${in_dir}/pseudorep2"
	pT_dir="${in_dir}/pseudorepT"
	out_dir=${3} #"/mnt/lab_data3/salil512/adult_heart/2_chrombpnet/3_peaks"
	chr_order=${4} #"/mnt/lab_data3/salil512/adult_heart/0_raw_data/other/GRCh38_EBV_sorted_standard.chrom.sizes.tsv"
	blacklist=${5} #"/mnt/lab_data3/salil512/adult_heart/0_raw_data/other/hg38.blacklist.bed.gz"

	if [ -f "${out_dir}/${dataset}_peaks_overlap_filtered.narrowPeak" ]; then
		echo "${dataset} already completed! skipping..."
		return 1
	fi

	echo "${dataset} calling pseudorep1 peaks..." &
	macs2 callpeak -t ${p1_dir}/${dataset}_sorted.tsv -f BED -n ${dataset}_pseudoreplicate1 -g hs --outdir ${out_dir} -p 0.01 --shift -75 --extsize 150 --nomodel -B --SPMR --keep-dup all --call-summits &> ${out_dir}/log_${dataset}_pseudorep1.txt &
	echo "${dataset} calling pseudorep2 peaks..." &
	macs2 callpeak -t ${p2_dir}/${dataset}_sorted.tsv -f BED -n ${dataset}_pseudoreplicate2 -g hs --outdir ${out_dir} -p 0.01 --shift -75 --extsize 150 --nomodel -B --SPMR --keep-dup all --call-summits &> ${out_dir}/log_${dataset}_pseudorep2.txt &
	echo "${dataset} calling pseudorepT peaks..." &
	macs2 callpeak -t ${pT_dir}/${dataset}_sorted.tsv -f BED -n ${dataset}_pseudoreplicateT -g hs --outdir ${out_dir} -p 0.01 --shift -75 --extsize 150 --nomodel -B --SPMR --keep-dup all --call-summits &> ${out_dir}/log_${dataset}_pseudorepT.txt &
	wait
	echo "${dataset} finished waiting"

	p1_in=${out_dir}/${dataset}_pseudoreplicate1_peaks.narrowPeak
	p2_in=${out_dir}/${dataset}_pseudoreplicate2_peaks.narrowPeak
	pT_in=${out_dir}/${dataset}_pseudoreplicateT_peaks.narrowPeak
	p1_out=${out_dir}/${dataset}_pseudoreplicate1_peaks_top.narrowPeak
	p2_out=${out_dir}/${dataset}_pseudoreplicate2_peaks_top.narrowPeak
	pT_out=${out_dir}/${dataset}_pseudoreplicateT_peaks_top.narrowPeak
	npeaks=300000

	echo "${dataset} getting top peaks..."
        sort -k 8gr,8gr ${p1_in} | head -n ${npeaks} | sort -k 1,1 -k2,2n > ${p1_out}
        sort -k 8gr,8gr ${p2_in} | head -n ${npeaks} | sort -k 1,1 -k2,2n > ${p2_out}
        sort -k 8gr,8gr ${pT_in} | head -n ${npeaks} | sort -k 1,1 -k2,2n > ${pT_out}

	echo "${dataset} intersecting peaks"
        min_overlap=0.5
	# chr_order=$4 #"/mnt/lab_data3/salil512/adult_heart/0_raw_data/other/GRCh38_EBV_sorted_standard.chrom.sizes.tsv"
        overlap_output=${out_dir}/${dataset}_peaks_overlap.narrowPeak
        bedtools intersect -u -a ${pT_out} -b ${p1_out} -g ${chr_order} -f ${min_overlap} -F ${min_overlap} -e -sorted | bedtools intersect -u -a stdin -b ${p2_out} -g ${chr_order} -f ${min_overlap} -F ${min_overlap} -e -sorted > ${overlap_output}

	echo "${dataset} filtering blacklist peaks"
	# blacklist="/mnt/lab_data3/salil512/adult_heart/0_raw_data/other/hg38.blacklist.bed.gz"
        filtered_output=${out_dir}/${dataset}_peaks_overlap_filtered.narrowPeak
        bedtools intersect -v -a ${overlap_output} -b ${blacklist} > ${filtered_output}

	# chr_order= #"/mnt/lab_data3/salil512/adult_heart/0_raw_data/other/GRCh38_EBV_sorted_standard.chrom.sizes.tsv"
	echo "${dataset} making p-value bedgraphs"
	macs2 bdgcmp -m ppois -t ${out_dir}/${dataset}_pseudoreplicate1_treat_pileup.bdg -c ${out_dir}/${dataset}_pseudoreplicate1_control_lambda.bdg -o ${out_dir}/${dataset}_pseudoreplicate1_ppois.bdg & macs2 bdgcmp -m ppois -t ${out_dir}/${dataset}_pseudoreplicate2_treat_pileup.bdg -c ${out_dir}/${dataset}_pseudoreplicate2_control_lambda.bdg -o ${out_dir}/${dataset}_pseudoreplicate2_ppois.bdg & macs2 bdgcmp -m ppois -t ${out_dir}/${dataset}_pseudoreplicateT_treat_pileup.bdg -c ${out_dir}/${dataset}_pseudoreplicateT_control_lambda.bdg -o ${out_dir}/${dataset}_pseudoreplicateT_ppois.bdg
	echo "${dataset} combining p-value bedgraphs"
	macs2 cmbreps -m fisher -i ${out_dir}/${dataset}_pseudoreplicate1_ppois.bdg ${out_dir}/${dataset}_pseudoreplicate2_ppois.bdg ${out_dir}/${dataset}_pseudoreplicateT_ppois.bdg -o ${out_dir}/${dataset}_combined_ppois.bdg
	sort -k1,1 -k2,2n -S 10% ${out_dir}/${dataset}_combined_ppois.bdg | head -n -1 > ${out_dir}/${dataset}_combined_ppois_sorted.bdg
	echo "${dataset} converting p-value bedgraphs to bigwigs"
	bedGraphToBigWig ${out_dir}/${dataset}_combined_ppois_sorted.bdg ${chr_order} ${out_dir}/${dataset}_pval.bw

	echo "${dataset} completed!"

}
export -f callpeak

celltype=$1
fragments_dir=$2
peaks_dir=$3
chr_size=$4
blacklist=$5
callpeak $1 $2 $3 $4 $5

# frags_dir="/mnt/lab_data3/salil512/adult_heart/2_chrombpnet/1_sample_fragments/fragments"
# MAX_PARALLEL=4
# ls ${frags_dir} | cut -d "-" -f 1 | sort | uniq | parallel --linebuffer -j ${MAX_PARALLEL} callpeak {}

# echo "done!"
