if [ -z "$SLURM_JOB_ID" ]; then
    echo "RUNNING LOCALLY"
    export CUDNN=cudnn-linux-x86_64-8.1.1_cuda11-archive
    export cuda=cuda-11.2
    export LD_LIBRARY_PATH=/usr/local/$cuda/lib64:/usr/local/$CUDNN/lib64:/usr/local/$CUDNN/include:/usr/local/$cuda/extras/CUPTI/lib64:/usr/local/lib:$LD_LIBRARY_PATH
    export PATH=/usr/local/$cuda/bin:$PATH
    export CUDA_HOME=/usr/local/$cuda
    export CPATH="/usr/local/$CUDNN/include:${CPATH}"
    export LIBRARY_PATH="/usr/local/$CUDNN/lib64:${LIBRARY_PATH}"
    export CPLUS_INCLUDE_PATH=/usr/local/$cuda/include
    export AVAILABLE_GPUS=$(nvidia-smi --query-gpu=index --format=csv,noheader)
else
    echo "RUNNING ON SLURM"
    module load cuda/11.2.0
    module load cudnn/8.1
    module load system pango cairo
fi
