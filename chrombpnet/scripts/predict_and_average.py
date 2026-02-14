import argparse
import pyBigWig
import numpy as np
import pandas as pd
import pyfaidx
from tensorflow.keras.utils import get_custom_objects
from tensorflow.keras.models import load_model
import tensorflow as tf
import chrombpnet.evaluation.make_bigwigs.bigwig_helper as bigwig_helper
import chrombpnet.training.utils.losses as losses
import chrombpnet.training.utils.data_utils as data_utils 
import chrombpnet.training.utils.one_hot as one_hot
from deeplift.dinuc_shuffle import dinuc_shuffle
import h5py
import json
from tqdm import tqdm

NARROWPEAK_SCHEMA = ["chr", "start", "end", "1", "2", "3", "4", "5", "6", "summit"]

#TODO: REIMPLEMENT WRITING AVERAGED PREDICTIONS AS h5 FILE
def write_predictions_h5py(output_prefix, profile, logcts, coords):
    # open h5 file for writing predictions
    output_h5_fname = "{}_predictions.h5".format(output_prefix)
    h5_file = h5py.File(output_h5_fname, "w")
    # create groups
    coord_group = h5_file.create_group("coords")
    pred_group = h5_file.create_group("predictions")

    num_examples=len(coords)

    coords_chrom_dset =  [str(coords[i][0]) for i in range(num_examples)]
    coords_center_dset =  [int(coords[i][1]) for i in range(num_examples)]

    dt = h5py.special_dtype(vlen=str)

    # create the "coords" group datasets
    coords_chrom_dset = coord_group.create_dataset(
        "coords_chrom", data=np.array(coords_chrom_dset, dtype=dt),
        dtype=dt, compression="gzip")
    coords_start_dset = coord_group.create_dataset(
        "coords_center", data=coords_center_dset, dtype=int, compression="gzip")

    # create the "predictions" group datasets
    profs_dset = pred_group.create_dataset(
        "profs",
        data=profile,
        dtype=float, compression="gzip")
    logcounts_dset = pred_group.create_dataset(
        "logcounts", data=logcts,
        dtype=float, compression="gzip")

    # close hdf5 file
    h5_file.close()


# need full paths!
def parse_args():
    parser = argparse.ArgumentParser(description="Make model predictions on given regions and output to bigwig file.Please read all parameter argument requirements. PROVIDE ABSOLUTE PATHS!")
    parser.add_argument("-cm", "--chrombpnet-model", type=str, action="append", required=True, help="Path to chrombpnet model h5")
    parser.add_argument("-sfx", "--suffix", type=str, required=True, help="Custom suffix to add to the output bigwig file in format '_chrombpnet[suffix].bw'")
    parser.add_argument("-r", "--regions", type=str, required=True, help="10 column BED file of length = N which matches f['projected_shap']['seq'].shape[0]. The ith region in the BED file corresponds to ith entry in importance matrix. If start=2nd col, summit=10th col, then the input regions are assumed to be for [start+summit-(inputlen/2):start+summit+(inputlen/2)]. Should not be piped since it is read twice!")
    parser.add_argument("-g", "--genome", type=str, required=True, help="Genome fasta")
    parser.add_argument("-c", "--chrom-sizes", type=str, required=True, help="Chromosome sizes 2 column tab-separated file")
    parser.add_argument("-op", "--output-prefix", type=str, required=True, help="Output bigwig file")
    parser.add_argument("-os", "--output-prefix-stats", type=str, default=None, required=False, help="Output stats on bigwig")
    parser.add_argument("-b", "--batch-size", type=int, default=64)
    parser.add_argument("-t", "--tqdm", type=int,default=0, help="Use tqdm. If yes then you need to have it installed.")
    parser.add_argument("-d", "--debug-chr", nargs="+", type=str, default=None, help="Run for specific chromosomes only (e.g. chr1 chr2) for debugging")
    parser.add_argument("-bw", "--bigwig", type=str, default=None, help="If provided .h5 with predictions are output along with calculated metrics considering bigwig as groundtruth.")
    parser.add_argument("-ds", "--dinuc-shuffle", action="store_true", help="If provided, will dinucleotide shuffle all specified regions before running predictions")
    args = parser.parse_args()
    print(args)
    return args


def softmax(x, temp=1):
    norm_x = x - np.mean(x,axis=1, keepdims=True)
    return np.exp(temp*norm_x)/np.sum(np.exp(temp*norm_x), axis=1, keepdims=True)

def load_model_wrapper(model_hdf5):
    # read .h5 model
    custom_objects={"multinomial_nll":losses.multinomial_nll, "tf": tf}    
    get_custom_objects().update(custom_objects)    
    model=load_model(model_hdf5, compile=False)
    print("got the model")
    model.summary()
    return model

def main(args):

    initialized_data = False
    inputlens = []
    outputlens = []

    num_models = len(args.chrombpnet_model)
    sum_logits = None
    sum_logcts = None
    for model_path in args.chrombpnet_model:
        tf.keras.backend.clear_session()
        model = load_model_wrapper(model_hdf5=model_path)
        inputlen = int(model.input_shape[1])
        outputlen = int(model.output_shape[0][1])

        inputlens.append(inputlen)
        outputlens.append(outputlen)
        assert all(elem == inputlens[0] for elem in inputlens)
        assert all(elem == outputlens[0] for elem in outputlens) # Make sure that all models have the same input and output size


        if not initialized_data:
            # Load reusable data
            print("Initializing data")
            regions_df = pd.read_csv(args.regions, sep='\t', names=NARROWPEAK_SCHEMA)
            print(regions_df.head())
            with pyfaidx.Fasta(args.genome) as g:
                seqs, regions_used = bigwig_helper.get_seq(regions_df, g, inputlen)
            
            if args.dinuc_shuffle:
                for i in range(len(seqs)):
                    seqs[i] = dinuc_shuffle(seqs[i])

            print(seqs.shape)
            gs = bigwig_helper.read_chrom_sizes(args.chrom_sizes)
            regions = bigwig_helper.get_regions(args.regions, outputlen, regions_used) # output regions

            if args.debug_chr is not None:
                regions_df = regions_df[regions_df['chr'].isin(args.debug_chr)]
                regions = [x for x in regions if x[0] in args.debug_chr]
            regions_df[regions_used].to_csv(args.output_prefix + f"_chrombpnet{args.suffix}_preds.bed", sep="\t", header=False, index=False)

            initialized_data = True

        print("Running prediction with model:", model_path)
        pred_logits_batches, pred_logcts_batches = [], []

        # manually predicting in batches because model.predict tries to concatenate all
        # batch results together into one tensor on GPU, leading to OOM errors
        for i in tqdm(range(0, seqs.shape[0], args.batch_size)):
            seq_batch = seqs[i : i + args.batch_size]
            pred_logits_batch, pred_logcts_batch = model.predict_on_batch(seq_batch)
            pred_logits_batches.append(pred_logits_batch)
            pred_logcts_batches.append(pred_logcts_batch)

        pred_logits = np.vstack(pred_logits_batches)
        pred_logcts = np.vstack(pred_logcts_batches)

        # pred_logits, pred_logcts = model.predict(seqs,
        #                                     batch_size = args.batch_size,
        #                                     verbose=True)

        pred_logits = np.squeeze(pred_logits)

        if sum_logits is None:
            sum_logits = pred_logits.copy()
            sum_logcts = pred_logcts.copy()
        else:
            sum_logits = sum_logits + pred_logits
            sum_logcts = sum_logcts + pred_logcts

    # average and consolidate across folds
    average_logits = sum_logits / num_models
    average_prob = softmax(average_logits)

    average_logcts = sum_logcts / num_models
    average_counts = np.expand_dims(np.exp(average_logcts)[:,0],axis=1)

    avg_overall_prediction = average_counts * average_prob

    bigwig_helper.write_bigwig(avg_overall_prediction, 
                            regions, 
                            gs, 
                            args.output_prefix + f"_chrombpnet{args.suffix}.bw", 
                            outstats_file=args.output_prefix_stats, 
                            debug_chr=args.debug_chr, 
                            use_tqdm=args.tqdm)


if __name__=="__main__":
    args = parse_args()
    main(args)