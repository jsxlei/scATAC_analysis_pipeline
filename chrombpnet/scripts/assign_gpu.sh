#!/bin/bash

# List all available GPUs
AVAILABLE_GPUS=$(nvidia-smi --query-gpu=index --format=csv,noheader)

# Get the next available GPU
NEXT_GPU=$(echo $AVAILABLE_GPUS | awk '{print $1}')

# Shift the available GPUs (move the first one to the end)
AVAILABLE_GPUS=$(echo $AVAILABLE_GPUS | awk '{for(i=2;i<=NF;i++) printf $i " "; print $1}')

# Export the selected GPU and updated list of available GPUs
export CUDA_VISIBLE_DEVICES=$NEXT_GPU
export AVAILABLE_GPUS
